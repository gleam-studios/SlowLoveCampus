"""Maintainer-only: resolve the existing exact versions to platform wheel hashes."""
import concurrent.futures
import json
from pathlib import Path
import urllib.request
from urllib.parse import urlsplit
from packaging.tags import cpython_tags, compatible_tags, mac_platforms
from packaging.utils import parse_wheel_filename

TOOLS = Path(__file__).resolve().parents[1]


def metadata(pair):
    name, version = pair
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=30) as response:
        return pair, json.load(response)


def main():
    versions = {tag: [tuple(line.split("==")) for line in (TOOLS / f"依赖清单-{tag}.txt").read_text().splitlines() if line]
                for tag in ("macos-arm64", "macos-x64", "windows-x64")}
    pairs = sorted(set(pair for items in versions.values() for pair in items))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        packages = dict(pool.map(metadata, pairs))
    py = json.loads((TOOLS / "python-sources.json").read_text())
    ffmpeg = json.loads((TOOLS / "ffmpeg-sources.json").read_text())["files"]
    sources = json.loads((TOOLS / "SOURCES.json").read_text())
    msvc = json.loads((TOOLS / "msvc-sources.json").read_text())
    result = {"version": 1, "platforms": {}, "model": []}
    for tag, architecture, osname in [("macos-arm64", "aarch64", "darwin"), ("macos-x64", "x86_64", "darwin"), ("windows-x64", "x86_64", "windows")]:
        platforms = ["win_amd64"] if osname == "windows" else list(mac_platforms((13, 0), "arm64" if architecture == "aarch64" else "x86_64"))
        tags = list(cpython_tags((3, 12), platforms=platforms)) + list(compatible_tags((3, 12), interpreter="cp312", platforms=platforms))
        rank = {tag: index for index, tag in reversed(list(enumerate(tags)))}
        runtime = next(p for p in py["distributions"] if p["arch"]["family"] == architecture and p["os"] == osname)
        directory = "Python/" + runtime["id"].replace("darwin", "macos")
        wheels = []
        for name, version in versions[tag]:
            candidates = []
            for wheel in packages[(name, version)]["urls"]:
                if wheel["packagetype"] != "bdist_wheel" or wheel.get("yanked"):
                    continue
                supported = parse_wheel_filename(wheel["filename"])[3].intersection(rank)
                if supported:
                    candidates.append((min(rank[t] for t in supported), wheel["filename"], wheel))
            if not candidates:
                raise RuntimeError(f"No compatible wheel: {tag}/{name}=={version}")
            wheel = min(candidates)[2]
            if urlsplit(wheel["url"]).hostname != "files.pythonhosted.org":
                raise RuntimeError("Unexpected wheel host")
            wheels.append({"name": name, "version": version, "filename": wheel["filename"], "url": wheel["url"], "sha256": wheel["digests"]["sha256"], "bytes": wheel["size"]})
        binaries = [{"path": p["path"].removeprefix("工具/"), "url": p["url"], "sha256": p["sha256"], "download_sha256": p["download_sha256"], "bytes": p["bytes"], "gzip": p["url"].endswith(".gz")} for p in ffmpeg if f"FFmpeg/{tag}/" in p["path"]]
        result["platforms"][tag] = {"python": {"directory": directory, "executable": directory + ("/python.exe" if osname == "windows" else "/bin/python3.12"), "url": runtime["url"], "sha256": runtime["sha256"]}, "wheels": wheels, "ffmpeg": binaries}
    result["platforms"]["windows-x64"]["msvc"] = {"url": msvc["source"], "sha256": msvc["sha256"], "files": list({Path(p["path"]).name: {"filename": Path(p["path"]).name, "sha256": p["sha256"]} for p in msvc["files"]}.values())}
    revision = sources["whisper_model"]["snapshot"]
    for item in sources["whisper_model"]["files"]:
        name = Path(item["path"]).name
        url = sources["whisper_model"]["license_source"] if name == "LICENSE" else f"https://huggingface.co/Systran/faster-whisper-large-v3/resolve/{revision}/{name}"
        result["model"].append({**item, "url": url})
    (TOOLS / "部署锁定.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": "工具/部署锁定.json", "wheels": {t: len(p["wheels"]) for t, p in result["platforms"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
