import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from clipmanx import settings as settings_mod
from clipmanx.settings import Settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp_dir = Path(self._tmp.name)
        self._patches = [
            patch.object(settings_mod, "CONFIG_DIR", tmp_dir),
            patch.object(settings_mod, "CONFIG_FILE", tmp_dir / "settings.json"),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        self._tmp.cleanup()

    def test_defaults_when_no_file(self):
        s = Settings()
        self.assertTrue(s.capture_clipboard)
        self.assertFalse(s.capture_primary)
        self.assertTrue(s.ignore_terminals)
        self.assertEqual(s.max_items, 50)
        self.assertEqual(s.icon_theme, "auto")
        self.assertEqual(s.tooltip_delay, 500)

    def test_setters_persist_to_disk(self):
        s = Settings()
        s.capture_primary = True
        s.ignore_terminals = False
        s.max_items = 100
        s.icon_theme = "dark"
        s.tooltip_delay = 250

        data = json.loads(settings_mod.CONFIG_FILE.read_text())
        self.assertTrue(data["capture_primary"])
        self.assertFalse(data["ignore_terminals"])
        self.assertEqual(data["max_items"], 100)
        self.assertEqual(data["icon_theme"], "dark")
        self.assertEqual(data["tooltip_delay"], 250)

    def test_persistence_round_trip(self):
        s1 = Settings()
        s1.ignore_terminals = False
        s1.tooltip_delay = 1234
        s2 = Settings()
        self.assertFalse(s2.ignore_terminals)
        self.assertEqual(s2.tooltip_delay, 1234)

    def test_invalid_icon_theme_is_ignored(self):
        s = Settings()
        s.icon_theme = "neon"
        self.assertEqual(s.icon_theme, "auto")

    def test_max_items_floored_at_one(self):
        s = Settings()
        s.max_items = 0
        self.assertEqual(s.max_items, 1)
        s.max_items = -5
        self.assertEqual(s.max_items, 1)

    def test_tooltip_delay_floored_at_zero(self):
        s = Settings()
        s.tooltip_delay = -100
        self.assertEqual(s.tooltip_delay, 0)

    def test_corrupt_config_file_falls_back_to_defaults(self):
        settings_mod.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        settings_mod.CONFIG_FILE.write_text("{ not valid json")
        s = Settings()
        self.assertTrue(s.ignore_terminals)
        self.assertEqual(s.max_items, 50)


if __name__ == "__main__":
    unittest.main()
