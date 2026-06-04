import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from clipmanx import history as history_mod
from clipmanx.history import History


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp_dir = Path(self._tmp.name)
        self._patches = [
            patch.object(history_mod, "DATA_DIR", tmp_dir),
            patch.object(history_mod, "DATA_FILE", tmp_dir / "history.json"),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        self._tmp.cleanup()

    def test_add_inserts_at_front(self):
        h = History(max_items=5)
        h.add("a")
        h.add("b")
        self.assertEqual(h.get_all(), ["b", "a"])

    def test_add_dedupes_and_moves_to_front(self):
        h = History(max_items=5)
        h.add("a")
        h.add("b")
        h.add("a")
        self.assertEqual(h.get_all(), ["a", "b"])

    def test_add_caps_at_max_items(self):
        h = History(max_items=3)
        for s in ["a", "b", "c", "d"]:
            h.add(s)
        self.assertEqual(h.get_all(), ["d", "c", "b"])

    def test_clear_empties_and_persists(self):
        h = History(max_items=5)
        h.add("x")
        h.clear()
        self.assertEqual(h.get_all(), [])
        self.assertEqual(json.loads(history_mod.DATA_FILE.read_text())["items"], [])

    def test_persistence_round_trip(self):
        h1 = History(max_items=5)
        h1.add("first")
        h1.add("second")
        h2 = History(max_items=5)
        self.assertEqual(h2.get_all(), ["second", "first"])


if __name__ == "__main__":
    unittest.main()
