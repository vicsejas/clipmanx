import hashlib
import json
import os
from pathlib import Path

XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
DATA_DIR = XDG_DATA_HOME / "clipmanx"
DATA_FILE = DATA_DIR / "history.json"
IMAGES_DIR = DATA_DIR / "images"


class History:
    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self.items: list[dict] = []
        self._load()

    def _load(self):
        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text())
                raw_items = data.get("items", [])
            except (json.JSONDecodeError, OSError):
                raw_items = []
        else:
            raw_items = []
        # Older history files stored plain strings; wrap them as text items.
        self.items = [
            {"type": "text", "text": item} if isinstance(item, str) else item
            for item in raw_items
        ]

    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps({"items": self.items}, indent=2))

    @staticmethod
    def _key(item: dict):
        if item["type"] == "image":
            return ("image", item["file"])
        return ("text", item["text"])

    def _remove_matching(self, item: dict):
        key = self._key(item)
        self.items = [i for i in self.items if self._key(i) != key]

    def _evict_overflow(self):
        if len(self.items) <= self.max_items:
            return
        dropped = self.items[self.max_items :]
        self.items = self.items[: self.max_items]
        for item in dropped:
            self._delete_image_file(item)

    def _delete_image_file(self, item: dict):
        if item["type"] == "image":
            try:
                self.image_path(item).unlink()
            except OSError:
                pass

    def add_text(self, text: str):
        item = {"type": "text", "text": text}
        self._remove_matching(item)
        self.items.insert(0, item)
        self._evict_overflow()
        self._save()

    def add_image(self, png_bytes: bytes, width: int, height: int):
        digest = hashlib.sha256(png_bytes).hexdigest()
        filename = f"{digest}.png"
        item = {"type": "image", "file": filename, "width": width, "height": height}
        self._remove_matching(item)
        path = IMAGES_DIR / filename
        if not path.exists():
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            path.write_bytes(png_bytes)
        self.items.insert(0, item)
        self._evict_overflow()
        self._save()

    def image_path(self, item: dict) -> Path:
        return IMAGES_DIR / item["file"]

    def get_all(self) -> list[dict]:
        return list(self.items)

    def clear(self):
        for item in self.items:
            self._delete_image_file(item)
        self.items.clear()
        self._save()
