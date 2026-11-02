"""Real configuration fixtures; never create drafts in the installed application."""
import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class DraftLocationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="同事电脑 空格 ")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()

    def module(self):
        try:
            return importlib.import_module("utils.draft_location")
        except ImportError:
            self.fail("Missing verified, remembered Jianying draft location resolver")

    def fixture(self, folder="Movies/JianyingPro/User Data", target="实际草稿"):
        root = self.home / target
        root.mkdir(exist_ok=True)
        config = self.home / folder / "Config/globalSetting"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text("[General]\ncurrentCustomDraftPath=" + str(root) + "\n", encoding="utf-8")
        return root, config

    def test_remembers_configured_location_and_reuses_it(self):
        m = self.module()
        root, config = self.fixture()
        self.assertEqual(m.resolve_drafts_root(home=self.home, system="Darwin", environ={}), root)
        config.unlink()
        self.assertEqual(m.resolve_drafts_root(home=self.home, system="Darwin", environ={}), root)
        saved = json.loads(m.cache_path(self.home, "Darwin", {}).read_text(encoding="utf-8"))
        self.assertEqual(saved["drafts_root"], str(root))

    def test_missing_settings_never_create_a_guessed_root(self):
        m = self.module()
        with self.assertRaises(RuntimeError):
            m.resolve_drafts_root(home=self.home, system="Darwin", environ={})
        self.assertFalse((self.home / "Movies").exists())

    def test_missing_configured_root_is_not_created(self):
        m = self.module()
        root, _ = self.fixture()
        root.rmdir()
        with self.assertRaises(RuntimeError):
            m.resolve_drafts_root(home=self.home, system="Darwin", environ={})
        self.assertFalse(root.exists())

    def test_conflicting_settings_stop_instead_of_picking_first(self):
        m = self.module()
        self.fixture()
        self.fixture("Library/Application Support/JianyingPro/User Data", "另一个草稿")
        with self.assertRaises(RuntimeError):
            m.resolve_drafts_root(home=self.home, system="Darwin", environ={})

    def test_refresh_is_explicit_and_deleted_cache_root_is_not_recreated(self):
        m = self.module()
        root, config = self.fixture()
        m.resolve_drafts_root(home=self.home, system="Darwin", environ={})
        other = self.home / "新设置"
        other.mkdir()
        config.write_text("[General]\ncurrentCustomDraftPath=" + str(other), encoding="utf-8")
        self.assertEqual(m.resolve_drafts_root(home=self.home, system="Darwin", environ={}), root)
        self.assertEqual(m.resolve_drafts_root(home=self.home, system="Darwin", environ={}, refresh=True), other)
        other.rmdir()
        with self.assertRaises(RuntimeError):
            m.resolve_drafts_root(home=self.home, system="Darwin", environ={})
        self.assertFalse(other.exists())

    def test_windows_configuration_and_cache_are_user_local(self):
        m = self.module()
        root, _ = self.fixture("AppData/Local/JianyingPro/User Data")
        env = {"LOCALAPPDATA": str(self.home / "AppData/Local")}
        self.assertEqual(m.resolve_drafts_root(home=self.home, system="Windows", environ=env), root)
        self.assertEqual(m.cache_path(self.home, "Windows", env), self.home / "AppData/Local/SlowLoveCampus/jianying.json")

    def test_wrapper_rejects_unverified_root_before_creating_it(self):
        from jy_wrapper import JyProject
        root = self.home / "已核验"
        root.mkdir()
        other = self.home / "禁止创建"
        with patch("core.project_base.get_default_drafts_root", return_value=str(root)):
            with self.assertRaises(ValueError):
                JyProject("Test", drafts_root=str(other))
        self.assertFalse(other.exists())

    def test_wrapper_preserves_existing_draft_by_default(self):
        from jy_wrapper import JyProject
        root = self.home / "已核验"
        existing = root / "Existing"
        existing.mkdir(parents=True)
        marker = existing / "keep.txt"
        marker.write_text("original", encoding="utf-8")
        with patch("core.project_base.get_default_drafts_root", return_value=str(root)):
            with self.assertRaises(FileExistsError):
                JyProject("Existing")
        self.assertEqual(marker.read_text(encoding="utf-8"), "original")


if __name__ == "__main__":
    unittest.main()
