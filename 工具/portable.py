"""Project-local tools. No system Python packages or cloud ASR are required."""
import argparse
import importlib
import json
import os
import platform
import re
import site
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


def platform_key(system=None, machine=None):
    system = system or platform.system()
    machine = (machine or platform.machine()).lower()
    if system == "Darwin" and machine in ("arm64", "aarch64"):
        return "macos-arm64"
    if system == "Darwin" and machine in ("x86_64", "amd64"):
        return "macos-x64"
    if system == "Windows" and machine in ("x86_64", "amd64"):
        return "windows-x64"
    raise ValueError(f"Unsupported platform: {system}/{machine}. Available: macOS ARM64, macOS Intel, Windows x64.")


def layout(tools, system=None, machine=None):
    tools = Path(tools).resolve()
    tag = platform_key(system, machine)
    python_tag = {
        "macos-arm64": "macos-aarch64", "macos-x64": "macos-x86_64", "windows-x64": "windows-x86_64",
    }[tag]
    python_root = tools / "Python" / f"cpython-3.12.11-{python_tag}-none"
    win = tag == "windows-x64"
    return {
        "tag": tag, "tools": tools, "project": tools.parent,
        "python": python_root / ("python.exe" if win else "bin/python3.12"),
        "packages": tools / "依赖" / tag,
        "ffmpeg": tools / "FFmpeg" / tag / ("ffmpeg.exe" if win else "ffmpeg"),
        "ffprobe": tools / "FFmpeg" / tag / ("ffprobe.exe" if win else "ffprobe"),
        "model": tools / "Whisper模型/faster-whisper-large-v3",
        "skill": tools.parent / "skills/jianying-editor",
    }


def environment(paths, base=None):
    env = dict(os.environ if base is None else base)
    for key in list(env):
        if key.upper().startswith("PYTHON") or key in ("VIRTUAL_ENV", "JY_SKILL_ROOT"):
            env.pop(key)
    env.update({
        "PYTHONPATH": os.pathsep.join([str(paths["packages"]), str(paths["skill"] / "scripts")]),
        "PYTHONNOUSERSITE": "1", "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8", "JY_SKILL_ROOT": str(paths["skill"]),
        "HF_HUB_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
        "HF_HOME": str(paths["tools"] / ".cache/huggingface"),
        "PATH": os.pathsep.join([str(paths["ffmpeg"].parent), str(paths["python"].parent), env.get("PATH", os.defpath)]),
    })
    return env


def require_payload(paths):
    for key in ("python", "packages", "ffmpeg", "ffprobe"):
        if not paths[key].exists():
            raise FileNotFoundError(f"Missing {key}: {paths[key]}. Run 工具/运行.command or 工具/运行.bat to deploy this platform; no system fallback is used.")


def activate(paths):
    env = environment(paths)
    os.environ.clear()
    os.environ.update(env)
    site.addsitedir(str(paths["packages"]))
    # Prefer bundled distributions even if this file was invoked with another Python.
    if str(paths["packages"]) in sys.path:
        sys.path.remove(str(paths["packages"]))
    sys.path.insert(0, str(paths["packages"]))
    sys.path.insert(0, str(paths["skill"] / "scripts"))


def subtitle_cues(segments, duration):
    cues = []
    for segment in segments:
        words = segment.get("words") or []
        chunks = []
        group = []
        for word in words:
            if group and (word["start"] - group[-1]["end"] > 0.6 or len("".join(w["word"] for w in group)) + len(word["word"]) > 42):
                chunks.append(group)
                group = []
            group.append(word)
            if re.search(r"[.!?。！？][\"'’”]*$", word["word"].strip()):
                chunks.append(group)
                group = []
        if group:
            chunks.append(group)
        candidates = ([{"start": c[0]["start"], "end": c[-1]["end"], "text": "".join(w["word"] for w in c).strip()} for c in chunks]
                      if words else [{"start": segment["start"], "end": segment["end"], "text": segment["text"].strip()}])
        for cue in candidates:
            cue["start"] = round(max(0, cue["start"], cues[-1]["end"] if cues else 0), 3)
            cue["end"] = round(min(duration, cue["end"]), 3)
            if cue["text"] and cue["end"] > cue["start"]:
                cues.append(cue)
    return cues


def srt_content(cues):
    def stamp(value):
        ms = round(value * 1000)
        return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"
    return "\n\n".join(f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i, c in enumerate(cues, 1)) + ("\n" if cues else "")


def transcribe(paths, args):
    import numpy as np
    from faster_whisper import WhisperModel

    source = Path(args.input).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    output = Path(args.output).resolve() if args.output else source.with_suffix("")
    # A prefix is used, not Path.with_suffix, so names containing dots are preserved.
    srt = Path(str(output) + ".srt")
    transcript = Path(str(output) + ".json")
    if srt.exists() or transcript.exists():
        raise FileExistsError(f"Output exists; choose another --output prefix: {output}")
    if not (paths["model"] / "model.bin").is_file():
        raise FileNotFoundError(f'Missing local Whisper model: {paths["model"]}')
    output.parent.mkdir(parents=True, exist_ok=True)
    print("Extracting audio with bundled FFmpeg...", flush=True)
    with tempfile.TemporaryDirectory(prefix="slowlove-asr-") as tmp:
        wav = Path(tmp) / "audio.wav"
        subprocess.run([str(paths["ffmpeg"]), "-v", "error", "-nostdin", "-i", str(source), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)], check=True)
        with wave.open(str(wav)) as audio_file:
            audio = np.frombuffer(audio_file.readframes(audio_file.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    print("Transcribing locally with Whisper large-v3 (CPU/int8)...", flush=True)
    model = WhisperModel(str(paths["model"]), device="cpu", compute_type="int8", cpu_threads=args.threads, local_files_only=True)
    segments, info = model.transcribe(audio, language=None if args.language == "auto" else args.language,
                                      beam_size=5, word_timestamps=True, vad_filter=True,
                                      vad_parameters={"min_silence_duration_ms": 300}, condition_on_previous_text=False)
    result = []
    for segment in segments:
        result.append({"start": segment.start, "end": segment.end, "text": segment.text,
                       "words": [{"word": w.word, "start": w.start, "end": w.end, "probability": w.probability} for w in segment.words or []]})
        print(f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text.strip()}", flush=True)
    duration = len(audio) / 16000
    cues = subtitle_cues(result, duration)
    report = {"engine": "faster-whisper", "model": "large-v3", "local_only": True,
              "path_base": "project", "source": Path(os.path.relpath(source, paths["project"])).as_posix(), "language": info.language, "duration": duration,
              "segments": result, "subtitles": cues}
    # Exclusive creation also prevents overwriting files created while recognition was running.
    with transcript.open("x", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write("\n")
    with srt.open("x", encoding="utf-8") as file:
        file.write(srt_content(cues))
    print(json.dumps({"srt": str(srt), "json": str(transcript), "subtitle_count": len(cues)}, ensure_ascii=False))


def check(paths, load_model=False):
    require_payload(paths)
    versions = {}
    for name in ("numpy", "av", "ctranslate2", "onnxruntime", "faster_whisper"):
        module = importlib.import_module(name)
        versions[name] = getattr(module, "__version__", "loaded")
    from jy_wrapper import JyProject
    for name in ("config.json", "model.bin", "tokenizer.json", "preprocessor_config.json"):
        if not (paths["model"] / name).is_file():
            raise FileNotFoundError(paths["model"] / name)
    executables = {}
    for name in ("ffmpeg", "ffprobe"):
        result = subprocess.run([str(paths[name]), "-version"], check=True, capture_output=True, text=True)
        executables[name] = result.stdout.splitlines()[0]
    if load_model:
        from faster_whisper import WhisperModel
        WhisperModel(str(paths["model"]), device="cpu", compute_type="int8", local_files_only=True)
    from utils.draft_location import resolve_drafts_root, cache_path
    try:
        drafts = {"status": "ok", "root": str(resolve_drafts_root()), "local_record": str(cache_path())}
    except RuntimeError as exc:
        drafts = {"status": "needs_setup", "reason": str(exc)}
    print(json.dumps({"status": "ok" if drafts["status"] == "ok" else "needs_setup", "platform": paths["tag"], "python": Path(os.path.relpath(sys.executable, paths["project"])).as_posix(),
                      "project_skill": "skills/jianying-editor", "model": "工具/Whisper模型/faster-whisper-large-v3",
                      "jianying": drafts,
                      "model_loaded": load_model, "versions": versions, **executables}, ensure_ascii=False, indent=2))
    return 0 if drafts["status"] == "ok" else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description="SlowLoveCampus portable offline editing tools")
    commands = parser.add_subparsers(dest="command")
    diagnostic = commands.add_parser("check", help="Check bundled Python, FFmpeg, model files and draft API")
    diagnostic.add_argument("--load-model", action="store_true")
    drafts = commands.add_parser("drafts", help="Read/remember Jianying's configured draft location")
    drafts.add_argument("--refresh", action="store_true", help="Re-read actual Jianying settings and update this computer's record")
    asr = commands.add_parser("transcribe", help="Recognize audio locally and write SRT/JSON")
    asr.add_argument("input")
    asr.add_argument("--output", help="Output path prefix; existing files will not be overwritten")
    asr.add_argument("--language", default="auto")
    asr.add_argument("--threads", type=int, default=4)
    # Keep the arguments for delegated tools intact, including -c/-m and FFmpeg flags.
    raw = list(sys.argv[1:] if argv is None else argv)
    delegated = raw and raw[0] in ("python", "ffmpeg", "ffprobe")
    paths = layout(Path(__file__).resolve().parent)
    require_payload(paths)
    activate(paths)
    # All relative project arguments have the same meaning from Finder, Codex or another cwd.
    os.chdir(paths["project"])
    if delegated:
        program, extra = raw[0], raw[1:]
        if program == "python":
            return subprocess.call([str(paths["python"]), "-s", *extra], env=dict(os.environ))
        return subprocess.call([str(paths[program]), *extra], env=dict(os.environ))
    args = parser.parse_args(raw)
    if args.command in (None, "check"):
        return check(paths, getattr(args, "load_model", False))
    elif args.command == "drafts":
        from utils.draft_location import resolve_drafts_root, cache_path
        root = resolve_drafts_root(refresh=args.refresh)
        print(json.dumps({"status": "ok", "root": str(root), "local_record": str(cache_path())}, ensure_ascii=False, indent=2))
    elif args.command == "transcribe":
        if args.threads < 1:
            parser.error("--threads must be positive")
        transcribe(paths, args)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError, ImportError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
