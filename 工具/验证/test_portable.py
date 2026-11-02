"""Behaviour checks for project relocation and independent offline subtitles."""
import importlib.util
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class PortableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / "portable.py"
        if not path.exists():
            cls.portable = None
            return
        spec = importlib.util.spec_from_file_location("portable_tools", path)
        cls.portable = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.portable)

    def module(self):
        self.assertIsNotNone(self.portable, "Project-local launcher is missing")
        return self.portable

    def test_platform_selection_and_unsupported_platform(self):
        p = self.module()
        self.assertEqual(p.platform_key("Darwin", "arm64"), "macos-arm64")
        self.assertEqual(p.platform_key("Darwin", "x86_64"), "macos-x64")
        self.assertEqual(p.platform_key("Windows", "AMD64"), "windows-x64")
        with self.assertRaises(ValueError):
            p.platform_key("Linux", "x86_64")

    def test_relocated_paths_do_not_use_authors_home(self):
        p = self.module()
        with tempfile.TemporaryDirectory(prefix="同事的项目 空格 ") as tmp:
            tools = Path(tmp).resolve() / "工具"
            paths = p.layout(tools, "Darwin", "arm64")
            self.assertEqual(paths["python"], tools / "Python/cpython-3.12.11-macos-aarch64-none/bin/python3.12")
            self.assertEqual(paths["model"], tools / "Whisper模型/faster-whisper-large-v3")
            self.assertEqual(paths["skill"], Path(tmp).resolve() / "skills/jianying-editor")

    def test_environment_does_not_import_global_python_packages(self):
        p = self.module()
        paths = p.layout(Path("/tmp/another project/工具"), "Darwin", "arm64")
        env = p.environment(paths, {"PATH": "/usr/bin", "PYTHONPATH": "/bad/site-packages", "PYTHONHOME": "/bad/python", "VIRTUAL_ENV": "/bad/venv"})
        self.assertNotIn("PYTHONHOME", env)
        self.assertNotIn("VIRTUAL_ENV", env)
        self.assertEqual(env["PYTHONPATH"].split(os.pathsep), [str(paths["packages"]), str(paths["skill"] / "scripts")])
        self.assertEqual(env["PYTHONNOUSERSITE"], "1")
        self.assertEqual(env["HF_HUB_OFFLINE"], "1")
        self.assertTrue(env["PATH"].startswith(str(paths["ffmpeg"].parent)))

    def test_missing_runtime_fails_instead_of_falling_back_to_system(self):
        p = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            paths = p.layout(Path(tmp) / "工具", "Darwin", "arm64")
            with self.assertRaisesRegex(FileNotFoundError, "Python"):
                p.require_payload(paths)

    def test_srt_timings_and_sentence_splitting(self):
        p = self.module()
        segments = [{"start": 1.1, "end": 5.0, "text": "One kiss first. Deal.", "words": [
            {"word": " One", "start": 1.1, "end": 1.4},
            {"word": " kiss", "start": 1.4, "end": 1.7},
            {"word": " first.", "start": 1.7, "end": 2.1},
            {"word": " Deal.", "start": 4.4, "end": 5.0},
        ]}]
        cues = p.subtitle_cues(segments, duration=4.8)
        self.assertEqual(cues, [
            {"start": 1.1, "end": 2.1, "text": "One kiss first."},
            {"start": 4.4, "end": 4.8, "text": "Deal."},
        ])
        self.assertEqual(p.srt_content(cues), "1\n00:00:01,100 --> 00:00:02,100\nOne kiss first.\n\n2\n00:00:04,400 --> 00:00:04,800\nDeal.\n")

    def test_environment_check_is_not_success_when_jianying_setup_is_missing(self):
        p = self.module()
        paths = p.layout(Path(__file__).resolve().parents[1])
        output = io.StringIO()
        with patch("utils.draft_location.resolve_drafts_root", side_effect=RuntimeError("No actual Jianying settings")):
            with contextlib.redirect_stdout(output):
                status = p.main(["check"])
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "needs_setup")


if __name__ == "__main__":
    unittest.main()
