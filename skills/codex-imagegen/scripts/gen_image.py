#!/usr/bin/env python3
"""Run an authenticated, image-capable Codex CLI without changing its config.

Python 3.10+, standard library only. Prompt from stdin or --prompt-file.
The workspace-write sandbox is fixed and cannot be overridden by arguments.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

class ImagegenError(Exception):
    pass


def find_codex() -> str:
    found = shutil.which("codex")
    if found:
        return found
    if sys.platform == "darwin":
        for candidate in (
            "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex",
            "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex",
        ):
            if Path(candidate).is_file() and os.access(candidate, os.X_OK):
                return candidate
    raise ImagegenError("Codex CLI not found on PATH. Install or expose the actual Codex CLI first.")


def probe(codex: str) -> dict:
    """Read-only preflight; this does not prove account-level generation access."""
    results = {}
    for key, args in (
        ("version", ["--version"]), ("login", ["login", "status"]),
        ("features", ["features", "list"]), ("help", ["exec", "--help"]),
    ):
        try:
            proc = subprocess.run([codex, *args], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=20, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ImagegenError(f"Codex {key} probe failed: {type(exc).__name__}") from exc
        results[key] = (proc.returncode, proc.stdout + proc.stderr)
    logged_in = results["login"][0] == 0 and bool(
        re.search(r"logged in.*chatgpt", results["login"][1], re.IGNORECASE))
    feature_enabled = results["features"][0] == 0 and bool(
        re.search(r"^image_generation\s+.+\s+true\s*$", results["features"][1], re.MULTILINE))
    supported_exec = results["help"][0] == 0 and all(
        option in results["help"][1] for option in
        ("--sandbox", "workspace-write", "--output-last-message", "--skip-git-repo-check"))
    version = results["version"][1].strip().splitlines()
    return {
        "codex": codex, "version": version[0] if version else "unknown",
        "chatgpt_login": logged_in, "image_generation_enabled": feature_enabled,
        "exec_interface_supported": supported_exec,
        "preflight_passed": logged_in and feature_enabled and supported_exec,
        "actual_generation": "not-tested",
    }


def within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def is_png(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
        return (len(header) == 24 and header[:8] == PNG_SIGNATURE
                and header[12:16] == b"IHDR"
                and int.from_bytes(header[16:20], "big") > 0
                and int.from_bytes(header[20:24], "big") > 0)
    except (OSError, ValueError):
        return False


def requested_output(args: argparse.Namespace, workdir: Path) -> Path:
    if args.out:
        raw = Path(args.out).expanduser()
        target = (raw if raw.is_absolute() else workdir / raw).resolve()
    else:
        slug = re.sub(r"[^\w-]+", "-", args.slug, flags=re.UNICODE).strip("-") or "image"
        target = workdir / "outputs" / f"{dt.date.today().isoformat()}_{slug}_01.png"
    if not within(target, workdir):
        raise ImagegenError("Output must be inside --workdir, matching the workspace-write sandbox.")
    if target.suffix.lower() != ".png":
        raise ImagegenError("Output must use the .png extension.")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def publish_without_overwrite(source: Path, requested: Path) -> Path:
    """Exclusive creation avoids replacing an existing file, including races."""
    base = re.sub(r"_\d{2,}$", "", requested.stem)
    candidate, number = requested, 2
    while True:
        created = False
        try:
            with candidate.open("xb") as dest:
                created = True
                with source.open("rb") as src:
                    shutil.copyfileobj(src, dest)
            return candidate
        except FileExistsError:
            candidate = requested.with_name(f"{base}_{number:02d}{requested.suffix}")
            number += 1
        except OSError:
            if created:
                candidate.unlink(missing_ok=True)
            raise


def recover_explicit_result(last: Path, workdir: Path, started: float) -> Path | None:
    """Never select 'the latest image' from a shared directory or another run."""
    if not last.is_file():
        return None
    lines = [line.strip() for line in last.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        return None
    candidate = Path(lines[0].strip('"')).expanduser()
    if not candidate.is_absolute():
        return None
    generated = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "generated_images"
    if not (within(candidate, generated) or within(candidate, workdir)):
        return None
    try:
        if candidate.stat().st_mtime < started - 1 or not is_png(candidate):
            return None
    except OSError:
        return None
    return candidate.resolve()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--workdir", default=str(Path.cwd()), help="Output workspace")
    result.add_argument("--out", help="Requested PNG path inside workdir; never replaces existing files")
    result.add_argument("--slug", default="image", help="Default output filename label")
    result.add_argument("--ref", action="append", default=[], help="Reference image; repeat as needed")
    result.add_argument("--prompt-file", help="UTF-8 prompt file; otherwise read UTF-8 stdin")
    result.add_argument("--check", action="store_true", help="Read-only preflight JSON; no generation")
    result.add_argument("--timeout", type=int, default=900, help="Generation timeout in seconds")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        codex = find_codex()
        capability = probe(codex)
        if args.check:
            print(json.dumps(capability, ensure_ascii=False, indent=2))
            return 0 if capability["preflight_passed"] else 1
        if not capability["preflight_passed"]:
            raise ImagegenError("Preflight failed. Run --check; an authenticated image-enabled Codex CLI is required.")
        if args.timeout <= 0:
            raise ImagegenError("--timeout must be positive.")
        workdir = Path(args.workdir).expanduser().resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        output = requested_output(args, workdir)
        refs = []
        for ref in args.ref:
            candidate = Path(ref).expanduser().resolve()
            if not candidate.is_file():
                raise ImagegenError(f"Reference image does not exist: {candidate}")
            refs.extend(["-i", str(candidate)])
        if args.prompt_file:
            prompt = Path(args.prompt_file).expanduser().read_text(encoding="utf-8-sig")
        else:
            prompt = sys.stdin.buffer.read().decode("utf-8-sig")
        if not prompt.strip():
            raise ImagegenError("Prompt is empty; supply stdin or --prompt-file.")
        run = workdir / ".codex-imagegen" / uuid.uuid4().hex
        run.mkdir(parents=True)
        generated, last, log = run / "generated.png", run / "last-message.txt", run / "codex.log"
        full_prompt = prompt + (
            "\n\nUse the actual built-in image_gen/imagegen tool for this request. "
            "If it is unavailable in this run, report IMAGEGEN_UNAVAILABLE and stop. "
            "Do not substitute a placeholder, code-drawn raster, API call, or recursive CLI invocation. "
            "Save or copy the actual generated final PNG to this absolute path:\n"
            f"{generated}\n"
            "Return only that absolute path on one line. If copying is unavailable, return only "
            "the absolute path of the actual image produced by this invocation. Do not use older images.\n"
        )
        command = [codex, "exec", "--skip-git-repo-check", "-s", "workspace-write",
                   "-C", str(workdir), *refs, "-o", str(last), "-"]
        started = time.time()
        try:
            with log.open("w", encoding="utf-8") as handle:
                completed = subprocess.run(command, input=full_prompt, text=True, encoding="utf-8",
                                           stdout=handle, stderr=subprocess.STDOUT,
                                           timeout=args.timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            raise ImagegenError(f"Generation timed out; inspect {log} and reconcile before retrying.") from exc
        if completed.returncode:
            raise ImagegenError(f"Codex exited with {completed.returncode}; inspect {log} before retrying.")
        result = generated if is_png(generated) else recover_explicit_result(last, workdir, started)
        if result is None:
            raise ImagegenError(f"No valid current PNG returned. Actual image capability is unverified; inspect {log}.")
        final = publish_without_overwrite(result, output)
        receipt = {**capability, "actual_generation": "output-returned-needs-visual-review",
                   "path_base": "project", "codex": Path(codex).name,
                   "output": final.relative_to(workdir).as_posix(),
                   "source": result.relative_to(workdir).as_posix() if within(result, workdir) else None,
                   "source_origin": "workspace" if within(result, workdir) else "codex-runtime",
                   "log": log.relative_to(workdir).as_posix()}
        (run / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(str(final))
        return 0
    except (ImagegenError, OSError, UnicodeError) as exc:
        print(f"codex-imagegen: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
