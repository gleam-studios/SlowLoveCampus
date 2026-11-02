"""Model integrity safeguards retained for the new HTTP deployment strategy."""
import hashlib
import importlib.util
import json
import threading
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BODY = b"first blocksecond block"
STATE = {"body": BODY, "range": True, "requests": []}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_GET(self):
        value = STATE["body"]
        header = self.headers.get("Range")
        STATE["requests"].append(header)
        if header and STATE["range"]:
            start = int(header.split("=")[1].split("-")[0])
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(value)-1}/{len(value)}")
            value = value[start:]
        else:
            self.send_response(200)
        self.send_header("Content-Length", str(len(value)))
        self.end_headers()
        self.wfile.write(value)

class ModelDownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/model.bin"
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
    def setUp(self):
        STATE.update(body=BODY, range=True, requests=[])
    def module(self):
        path = Path(__file__).resolve().parents[1] / "deploy.py"
        self.assertTrue(path.is_file(), "Missing first-run download deployment")
        spec = importlib.util.spec_from_file_location("tested_deploy", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    def fetch(self, path):
        return self.module().fetch_file(self.url, path, hashlib.sha256(BODY).hexdigest(), len(BODY))
    def test_fixed_source_downloads_exact_model_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "model.bin"
            self.fetch(target)
            self.assertEqual(target.read_bytes(), BODY)
            STATE["requests"].clear()
            self.fetch(target)
            self.assertEqual(STATE["requests"], [])
    def test_existing_original_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "model.bin"
            target.write_bytes(b"keep original")
            with self.assertRaises(ValueError):
                self.fetch(target)
            self.assertEqual(target.read_bytes(), b"keep original")
    def test_incomplete_download_keeps_partial_without_publishing_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "model.bin"
            STATE["body"] = BODY[:5]
            with self.assertRaises(OSError):
                self.fetch(target)
            self.assertFalse(target.exists())
            self.assertTrue(Path(str(target) + ".part").exists())
    def test_corruption_leaves_no_completed_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "model.bin"
            STATE["body"] = b"x" * len(BODY)
            with self.assertRaises(ValueError):
                self.fetch(target)
            self.assertFalse(target.exists())
            self.assertFalse(Path(str(target) + ".part").exists())
    def test_manifest_cannot_write_outside_tools_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                self.module().inside(Path(tmp), "../outside")
    def test_resumes_partial_download_at_correct_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "model.bin"
            Path(str(target) + ".part").write_bytes(BODY[:7])
            self.fetch(target)
            self.assertEqual(target.read_bytes(), BODY)
            self.assertEqual(STATE["requests"], ["bytes=7-"])
    def test_server_ignoring_range_restarts_instead_of_appending(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "model.bin"
            Path(str(target) + ".part").write_bytes(BODY[:7])
            STATE["range"] = False
            self.fetch(target)
            self.assertEqual(target.read_bytes(), BODY)

    def test_completed_deployment_reuses_files_without_network_and_preserves_local_history(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            tools = project / "工具"
            python = tools / "Python/fake/bin/python3.12"
            python.parent.mkdir(parents=True)
            python.write_bytes(b"fixture executable")
            metadata = tools / "依赖/macos-arm64/fixture-1.0.dist-info/METADATA"
            metadata.parent.mkdir(parents=True)
            metadata.write_text("Metadata-Version: 2.1\nName: fixture\nVersion: 1.0\n")
            package = tools / "依赖/macos-arm64/fixture/__init__.py"
            package.parent.mkdir()
            package.write_text("# fixture\n")
            metadata.with_name("RECORD").write_text("fixture/__init__.py,,\nfixture-1.0.dist-info/METADATA,,\nfixture-1.0.dist-info/RECORD,,\n../../bin/fixture,,\n../../share/man/man1/fixture.1,,\n")
            workspace = project / "工作区"
            workspace.mkdir()
            history = workspace / "活动排除清单.md"
            history.write_text("preserve local labels", encoding="utf-8")
            record = {"url": self.url, "sha256": hashlib.sha256(BODY).hexdigest(), "bytes": len(BODY)}
            manifest = {"version": 1, "platforms": {"macos-arm64": {
                "python": {"directory": "Python/fake", "executable": "Python/fake/bin/python3.12"},
                "wheels": [{"name": "fixture", "version": "1.0"}],
                "ffmpeg": [{**record, "path": "FFmpeg/macos-arm64/ffmpeg", "gzip": False}]}},
                "model": [{**record, "path": "Whisper模型/faster-whisper-large-v3/model.bin"}]}
            (tools / "部署锁定.json").write_text(json.dumps(manifest), encoding="utf-8")
            module.ensure_deployed(tools, "macos-arm64")
            STATE["requests"].clear()
            module.ensure_deployed(tools, "macos-arm64")
            self.assertEqual(STATE["requests"], [])
            self.assertEqual(history.read_text(encoding="utf-8"), "preserve local labels")
            state = json.loads((tools / ".cache/deployment/macos-arm64.json").read_text())
            self.assertTrue(all(not Path(name).is_absolute() for name in state["files"]))
            (tools / "FFmpeg/macos-arm64/ffmpeg").write_bytes(b"changed")
            self.assertFalse(module.state_matches(tools, state, state["fingerprint"]))

    def test_dependency_metadata_does_not_hide_missing_module(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "依赖/macos-arm64"
            metadata = target / "fixture-1.0.dist-info/METADATA"
            metadata.parent.mkdir(parents=True)
            metadata.write_text("Metadata-Version: 2.1\nName: fixture\nVersion: 1.0\n")
            metadata.with_name("RECORD").write_text("fixture/__init__.py,,\nfixture-1.0.dist-info/RECORD,,\n")
            self.assertFalse(module.packages_match(target, [{"name": "fixture", "version": "1.0"}]))
            with self.assertRaises(ValueError):
                module.install_packages(Path(tmp), "macos-arm64", {"wheels": [{"name": "fixture", "version": "1.0"}]})
            self.assertTrue(metadata.exists())

if __name__ == "__main__":
    unittest.main()
