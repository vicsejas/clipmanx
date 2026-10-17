import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from clipmanx import history as history_mod
from clipmanx.history import History


def _text_items(history):
    return [item["text"] for item in history.get_all()]


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp_dir = Path(self._tmp.name)
        self._patches = [
            patch.object(history_mod, "DATA_DIR", tmp_dir),
            patch.object(history_mod, "DATA_FILE", tmp_dir / "history.json"),
            patch.object(history_mod, "IMAGES_DIR", tmp_dir / "images"),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        self._tmp.cleanup()

    def test_add_inserts_at_front(self):
        h = History(max_items=5)
        h.add_text("a")
        h.add_text("b")
        self.assertEqual(_text_items(h), ["b", "a"])

    def test_add_dedupes_and_moves_to_front(self):
        h = History(max_items=5)
        h.add_text("a")
        h.add_text("b")
        h.add_text("a")
        self.assertEqual(_text_items(h), ["a", "b"])

    def test_add_caps_at_max_items(self):
        h = History(max_items=3)
        for s in ["a", "b", "c", "d"]:
            h.add_text(s)
        self.assertEqual(_text_items(h), ["d", "c", "b"])

    def test_clear_empties_and_persists(self):
        h = History(max_items=5)
        h.add_text("x")
        h.clear()
        self.assertEqual(h.get_all(), [])
        self.assertEqual(json.loads(history_mod.DATA_FILE.read_text())["items"], [])

    def test_persistence_round_trip(self):
        h1 = History(max_items=5)
        h1.add_text("first")
        h1.add_text("second")
        h2 = History(max_items=5)
        self.assertEqual(_text_items(h2), ["second", "first"])

    def test_loads_legacy_plain_string_items(self):
        history_mod.DATA_DIR.mkdir(parents=True, exist_ok=True)
        history_mod.DATA_FILE.write_text(json.dumps({"items": ["old", "older"]}))
        h = History(max_items=5)
        self.assertEqual(_text_items(h), ["old", "older"])

    def test_add_image_persists_file_and_dedupes(self):
        h = History(max_items=5)
        h.add_image(b"fake-png-bytes", 10, 20)
        items = h.get_all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["type"], "image")
        self.assertEqual(items[0]["width"], 10)
        self.assertEqual(items[0]["height"], 20)
        self.assertTrue(h.image_path(items[0]).exists())

        # Adding the same bytes again dedupes to a single front entry, reusing
        # the same file rather than writing a duplicate.
        h.add_image(b"fake-png-bytes", 10, 20)
        self.assertEqual(len(h.get_all()), 1)

    def test_evicting_image_deletes_its_file(self):
        h = History(max_items=1)
        h.add_image(b"first-image", 1, 1)
        path = h.image_path(h.get_all()[0])
        h.add_image(b"second-image", 2, 2)
        self.assertFalse(path.exists())

    def test_clear_deletes_image_files(self):
        h = History(max_items=5)
        h.add_image(b"some-bytes", 1, 1)
        path = h.image_path(h.get_all()[0])
        h.clear()
        self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
