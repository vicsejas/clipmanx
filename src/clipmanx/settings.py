import json
import os
from pathlib import Path

XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
CONFIG_DIR = XDG_CONFIG_HOME / "clipmanx"
CONFIG_FILE = CONFIG_DIR / "settings.json"

DEFAULTS = {
    "capture_clipboard": True,
    "capture_primary": True,
    "max_items": 50,
    "icon_theme": "auto",
    "tooltip_delay": 500,
}


class Settings:
    def __init__(self):
        self._values = dict(DEFAULTS)
        self._load()

    def _load(self):
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                return
            for key, default_val in DEFAULTS.items():
                if key in data:
                    self._values[key] = type(default_val)(data[key])

    def _save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(self._values, indent=2))

    @property
    def capture_clipboard(self) -> bool:
        return self._values["capture_clipboard"]

    @capture_clipboard.setter
    def capture_clipboard(self, value: bool):
        self._values["capture_clipboard"] = bool(value)
        self._save()

    @property
    def capture_primary(self) -> bool:
        return self._values["capture_primary"]

    @capture_primary.setter
    def capture_primary(self, value: bool):
        self._values["capture_primary"] = bool(value)
        self._save()

    @property
    def max_items(self) -> int:
        return self._values["max_items"]

    @max_items.setter
    def max_items(self, value: int):
        self._values["max_items"] = max(1, int(value))
        self._save()

    @property
    def icon_theme(self) -> str:
        return self._values["icon_theme"]

    @icon_theme.setter
    def icon_theme(self, value: str):
        if value in ("auto", "light", "dark"):
            self._values["icon_theme"] = value
            self._save()

    @property
    def tooltip_delay(self) -> int:
        return self._values["tooltip_delay"]

    @tooltip_delay.setter
    def tooltip_delay(self, value: int):
        self._values["tooltip_delay"] = max(0, int(value))
        self._save()
