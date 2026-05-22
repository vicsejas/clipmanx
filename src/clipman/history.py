import json
import os
from pathlib import Path

XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
DATA_DIR = XDG_DATA_HOME / "clipman"
DATA_FILE = DATA_DIR / "history.json"


class History:
    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self.items: list[str] = []
        self._load()

    def _load(self):
        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text())
                self.items = data.get("items", [])
            except (json.JSONDecodeError, OSError):
                self.items = []

    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps({"items": self.items}, indent=2))

    def add(self, text: str):
        if text in self.items:
            self.items.remove(text)
        self.items.insert(0, text)
        if len(self.items) > self.max_items:
            self.items = self.items[:self.max_items]
        self._save()

    def get_all(self) -> list[str]:
        return list(self.items)

    def clear(self):
        self.items.clear()
        self._save()
