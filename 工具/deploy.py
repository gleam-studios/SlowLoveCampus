"""First-run deployment from pinned upstream artifacts; standard library only."""
import base64
import csv
import gzip
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile


def inside(root, reference):
    root = Path(root).resolve()
    candidate = (root / reference).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("Deployment path must stay inside the tools directory")
    return candidate


def digest(path, algorithm="sha256"):
    value = hashlib.new(algorithm)
    with Path(path).open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            value.update(block)
    return value.hexdigest()


def publish(temporary, target):
    # Same-directory hard link publishes atomically and never replaces an existing file.
    os.link(temporary, target)
    Path(temporary).unlink()


def fetch_file(url, target, sha256, expected_bytes=None):
    target = Path(target)
    if target.exists():
        if target.is_file() and digest(target) == sha256:
            return target
        raise ValueError(f"Existing file has a different hash; preserved original: {target.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(str(target) + ".part")
    start = partial.stat().st_size if partial.exists() else 0
    if expected_bytes is not None and start > expected_bytes:
        partial.unlink()
        start = 0
    if not (expected_bytes is not None and start == expected_bytes):
        print(f"Downloading {target.name} ({start} bytes cached)", file=sys.stderr, flush=True)
        headers = {"User-Agent": "SlowLoveCampus-setup/1"}
        if start:
            headers["Range"] = f"bytes={start}-"
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=90) as response:
            append = start > 0 and response.status == 206
            if append and not response.headers.get("Content-Range", "").startswith(f"bytes {start}-"):
                raise OSError("Server returned an unexpected resume range; partial file retained")
            with partial.open("ab" if append else "wb") as stream:
                while block := response.read(4 * 1024 * 1024):
                    stream.write(block)
    if expected_bytes is not None and partial.stat().st_size != expected_bytes:
        raise OSError(f"Incomplete download: {target.name}; run the entry again to resume")
    if digest(partial) != sha256:
        partial.unlink()
        raise ValueError(f"SHA-256 mismatch: {target.name}; no completed file published")
    publish(partial, target)
    return target


def cached_file(tools, record):
    name = record.get("filename") or record["url"].rsplit("/", 1)[-1]
    target = tools / ".cache/downloads" / record["sha256"] / name
    return fetch_file(record["url"], target, record["sha256"], record.get("bytes"))


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".state-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def state_matches(tools, state, fingerprint):
    if state.get("fingerprint") != fingerprint or not state.get("files"):
        return False
    try:
        return all([inside(tools, name).stat().st_size, inside(tools, name).stat().st_mtime_ns] == values
                   for name, values in state["files"].items())
    except (OSError, ValueError):
        return False


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def packages_match(directory, wheels):
    if not directory.is_dir():
        return False
    installed = {normalized(item.metadata["Name"]): item
                 for item in importlib.metadata.distributions(path=[str(directory)])}
    for wheel in wheels:
        distribution = installed.get(normalized(wheel["name"]))
        if distribution is None or distribution.version != wheel["version"]:
            return False
        record = distribution.read_text("RECORD")
        if not record:
            return False
        # Distribution.files filters out missing entries; read the original RECORD instead.
        for row in csv.reader(record.splitlines()):
            if len(row) != 3:
                return False
            name, checksum, size = row
            entry = PurePosixPath(name)
            if entry.suffix in (".pyc", ".pyo") or "__pycache__" in entry.parts:
                continue
            # This project uses library APIs, not wheel console scripts. Older local
            # bundles deliberately omitted those machine-specific entry shims.
            if entry.parts and (entry.parts[0] in ("bin", "Scripts") or
                                (entry.parts[0] == ".." and len(entry.parts) > 1 and entry.parts[-2] in ("bin", "Scripts"))):
                continue
            # pip --target also omits distribution-level man pages (e.g. SymPy).
            if entry.parts and entry.parts[0] == ".." and entry.parts[-4:-2] == ("share", "man"):
                continue
            path = Path(distribution.locate_file(name)).resolve()
            if not path.is_relative_to(directory.resolve()):
                return False
            if not path.is_file() or (size and path.stat().st_size != int(size)):
                return False
            if checksum:
                algorithm, value = checksum.split("=", 1)
                actual = base64.urlsafe_b64encode(bytes.fromhex(digest(path, algorithm))).decode().rstrip("=")
                if actual != value:
                    return False
    return True


def install_packages(tools, tag, platform):
    destination = tools / "依赖" / tag
    if packages_match(destination, platform["wheels"]):
        return
    if destination.exists():
        raise ValueError(f"Existing dependencies are incomplete or differ from lock: 依赖/{tag}; preserved")
    wheelhouse = tools / ".cache/wheels" / tag
    wheelhouse.mkdir(parents=True, exist_ok=True)
    lines = []
    for wheel in platform["wheels"]:
        fetch_file(wheel["url"], wheelhouse / wheel["filename"], wheel["sha256"], wheel["bytes"])
        lines.append(f'{wheel["name"]}=={wheel["version"]} --hash=sha256:{wheel["sha256"]}')
    lock = wheelhouse / "requirements.lock"
    lock.write_text("\n".join(lines) + "\n", encoding="utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".install-", dir=destination.parent))
    try:
        python = inside(tools, platform["python"]["executable"])
        subprocess.run([str(python), "-I", "-m", "pip", "--isolated", "--disable-pip-version-check", "install",
                        "--no-index", "--no-deps", "--no-compile", "--only-binary=:all:", "--require-hashes",
                        "--find-links", str(wheelhouse), "--target", str(stage), "-r", str(lock)],
                       check=True, stdout=sys.stderr)
        if not packages_match(stage, platform["wheels"]):
            raise RuntimeError("Installed dependency versions do not match the lock")
        stage.rename(destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def install_msvc(tools, platform):
    record = platform.get("msvc")
    if not record:
        return
    root = inside(tools, platform["python"]["directory"])
    missing = [item for item in record["files"] if not (root / item["filename"]).is_file()]
    if not missing:
        return
    archive = cached_file(tools, record)
    with zipfile.ZipFile(archive) as wheel:
        for item in missing:
            members = [name for name in wheel.namelist() if Path(name).name == item["filename"]]
            if not members:
                raise ValueError("MSVC runtime wheel lacks a required DLL")
            payload = wheel.read(members[0])
            if hashlib.sha256(payload).hexdigest() != item["sha256"]:
                raise ValueError("MSVC runtime DLL hash mismatch")
            with (root / item["filename"]).open("xb") as stream:
                stream.write(payload)


def install_ffmpeg(tools, records):
    for record in records:
        target = inside(tools, record["path"])
        if not record["gzip"]:
            fetch_file(record["url"], target, record["sha256"], record["bytes"])
            continue
        if target.exists():
            if digest(target) != record["sha256"]:
                raise ValueError("Existing FFmpeg hash differs; original preserved")
            continue
        compressed = cached_file(tools, {"url": record["url"], "sha256": record["download_sha256"]})
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".ffmpeg-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as output, gzip.open(compressed, "rb") as source:
                shutil.copyfileobj(source, output)
            if digest(temporary) != record["sha256"]:
                raise ValueError("Extracted FFmpeg hash mismatch")
            os.chmod(temporary, 0o755)
            publish(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def initialize_local_folders(project):
    workspace = project / "工作区"
    workspace.mkdir(exist_ok=True)
    (project / "输出/视频").mkdir(parents=True, exist_ok=True)
    try:
        with (workspace / "活动排除清单.md").open("x", encoding="utf-8") as stream:
            stream.write("# 活动排除清单\n\n仅记录上海日期与简短核心活动标签。此文件仅在本机维护，不代表已核对项目外历史。\n")
    except FileExistsError:
        pass


def ensure_deployed(tools, tag):
    tools = Path(tools).resolve()
    manifest = json.loads((tools / "部署锁定.json").read_text(encoding="utf-8"))
    if manifest.get("version") != 1 or tag not in manifest["platforms"]:
        raise ValueError("Unsupported deployment manifest/platform")
    platform = manifest["platforms"][tag]
    fingerprint = hashlib.sha256(json.dumps({"state_version": 3, "platform": platform, "model": manifest["model"]}, sort_keys=True).encode()).hexdigest()
    state_path = tools / ".cache/deployment" / f"{tag}.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    if state_matches(tools, state, fingerprint):
        initialize_local_folders(tools.parent)
        return
    lock = tools / ".cache/deployment.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise RuntimeError("Deployment is already running, or a previous process left 工具/.cache/deployment.lock; check it before retrying") from exc
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(str(os.getpid()))
        if not inside(tools, platform["python"]["executable"]).is_file():
            raise FileNotFoundError("Run the platform entry to bootstrap project Python first")
        install_msvc(tools, platform)
        install_packages(tools, tag, platform)
        install_ffmpeg(tools, platform["ffmpeg"])
        for item in manifest["model"]:
            fetch_file(item["url"], inside(tools, item["path"]), item["sha256"], item["bytes"])
        files = {}
        roots = [inside(tools, platform["python"]["directory"]), tools / "依赖" / tag,
                 tools / "FFmpeg" / tag, tools / "Whisper模型/faster-whisper-large-v3"]
        for root in roots:
            for base, directories, names in os.walk(root):
                directories[:] = [name for name in directories if name != "__pycache__"]
                for name in names:
                    path = Path(base) / name
                    if name.endswith((".pyc", ".pyo", ".part")):
                        continue
                    stat = path.stat()
                    files[path.relative_to(tools).as_posix()] = [stat.st_size, stat.st_mtime_ns]
        atomic_json(state_path, {"fingerprint": fingerprint, "files": files})
        initialize_local_folders(tools.parent)
    finally:
        lock.unlink()


def main():
    tools = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("project_portable", tools / "portable.py")
    portable = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(portable)
    paths = portable.layout(tools)
    ensure_deployed(tools, paths["tag"])
    args = sys.argv[1:]
    if args and args[0] == "--run":
        args = args[1:]
    if args == ["setup"]:
        print(json.dumps({"status": "ready", "platform": paths["tag"]}))
        return 0
    return subprocess.call([str(paths["python"]), "-I", "-X", "utf8", str(tools / "portable.py"), *(args or ["check"])])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print(f"SETUP ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
