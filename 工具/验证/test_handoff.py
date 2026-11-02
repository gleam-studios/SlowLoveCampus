"""Portable jobs and native credential APIs; no real service calls."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills/rh-minimax-h3/scripts"


class HandoffTests(unittest.TestCase):
    def test_relative_jobs_survive_project_move_and_different_working_directory(self):
        with tempfile.TemporaryDirectory(prefix="迁移测试 空格 ") as tmp:
            project = Path(tmp) / "原项目"
            target = project / "skills/rh-minimax-h3"
            shutil.copytree(SCRIPTS, target / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(SCRIPTS.parent / "references", target / "references")
            assets = project / "资产"
            task = project / "工作区/当前任务"
            assets.mkdir(parents=True)
            task.mkdir(parents=True)
            (assets / "头像.jpeg").write_bytes(b"fixture")
            (task / "prompt.txt").write_text("A natural conversation.", encoding="utf-8")
            run = subprocess.run([sys.executable, str(target / "scripts/build_jobs.py"),
                                  "--prompt-file", str(task / "prompt.txt"), "--output", str(task / "jobs.json"),
                                  "--seconds", "15", "--aspect", "9:16", "--image", str(assets / "头像.jpeg")],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            data = json.loads((task / "jobs.json").read_text(encoding="utf-8"))
            refs = [n["fieldValue"]["$upload"] for n in data["jobs"][0]["nodeInfoList"]
                    if isinstance(n["fieldValue"], dict) and "$upload" in n["fieldValue"]]
            self.assertEqual(set(refs), {"../../资产/头像.jpeg"})
            moved = Path(tmp) / "同事的项目 新位置"
            project.rename(moved)
            result = subprocess.run([sys.executable, str(moved / "skills/rh-minimax-h3/scripts/rh_minimax_h3.py"),
                                     str(moved / "工作区/当前任务/jobs.json"), "--output", str(moved / "工作区/当前任务/生成"),
                                     "--dry-run"], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertFalse((moved / "工作区/当前任务/生成").exists())

    def credentials(self):
        spec = importlib.util.spec_from_file_location("handoff_credentials", SCRIPTS / "credentials.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_receipt_relativizes_only_local_files_and_preserves_business_text(self):
        spec = importlib.util.spec_from_file_location("handoff_h3", SCRIPTS / "rh_minimax_h3.py")
        m = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"credentials": self.credentials()}):
            spec.loader.exec_module(m)
        local = str(ROOT / "工作区/本轮任务/生成/out.mp4")
        prompt = "/ Start with a close-up, then move out."
        data = {"files": [local], "videos": [local], "uploads": {local: "/remote/internal/file"},
                "payload": {"prompt": prompt}, "response": {"path": "/remote/internal/file"}}
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "receipt.json"
            m.save_json(destination, data)
            saved = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(saved["files"], ["工作区/本轮任务/生成/out.mp4"])
        self.assertEqual(saved["uploads"], {"工作区/本轮任务/生成/out.mp4": "/remote/internal/file"})
        self.assertEqual(saved["payload"]["prompt"], prompt)
        self.assertEqual(saved["response"]["path"], "/remote/internal/file")
        self.assertEqual(data["files"], [local])

    def test_windows_private_storage_does_not_call_unix_fchmod(self):
        m = self.credentials()
        class WindowsOS:
            name = "nt"
            def __getattr__(self, name):
                if name == "fchmod":
                    raise AssertionError("Windows has no Unix fchmod")
                return getattr(os, name)
        def run(command, **kwargs):
            if command[0] == "whoami":
                return subprocess.CompletedProcess(command, 0, '"user","S-1-5-21-123-456-789-1001"\n', "")
            if command[0] == "icacls":
                return subprocess.CompletedProcess(command, 0, "ok", "")
            raise AssertionError("Unexpected external command")
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "private/key.env"
            with patch.object(m, "os", WindowsOS()), patch("subprocess.run", side_effect=run):
                m.store_key("offline-synthetic-test-value", destination)
            self.assertEqual(m.read_key(destination), "offline-synthetic-test-value")

    def test_windows_acl_failure_does_not_save_secret(self):
        m = self.credentials()
        class WindowsOS:
            name = "nt"
            def __getattr__(self, name):
                return getattr(os, name)
        def fail(command, **kwargs):
            raise subprocess.CalledProcessError(1, command)
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "key.env"
            with patch.object(m, "os", WindowsOS()), patch("subprocess.run", side_effect=fail):
                with self.assertRaises((OSError, RuntimeError, subprocess.CalledProcessError)):
                    m.store_key("offline-synthetic-test-value", destination)
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_video_review_records_project_relative_input(self):
        with tempfile.TemporaryDirectory(prefix="review-fixture-", dir=ROOT / "工作区") as tmp:
            folder = Path(tmp)
            video = folder / "fixture.mp4"
            made = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                                   "color=c=black:s=160x288:r=10:d=0.3", "-c:v", "libx264", str(video)],
                                  capture_output=True, text=True)
            self.assertEqual(made.returncode, 0, made.stderr)
            result = subprocess.run([sys.executable, str(ROOT / "skills/direct-video/scripts/review_video.py"),
                                     str(video), "--out", str(folder / "review"), "--samples", "2", "--width", "160"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((folder / "review/report.json").read_text(encoding="utf-8"))
            self.assertFalse(Path(report["input"]).is_absolute())
            self.assertEqual((ROOT / report["input"]).resolve(), video.resolve())
            self.assertEqual(report["path_base"], "project")


if __name__ == "__main__":
    unittest.main()
