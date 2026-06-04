"""Detect whether the currently focused X11 window is a terminal emulator.

Lives in its own module (no GTK imports) so it can be unit-tested without
pulling in PyGObject / GTK introspection bindings.
"""

import shutil
import subprocess


# WM_CLASS values of common terminal emulators (lowercased for matching).
TERMINAL_WM_CLASSES = frozenset({
    "gnome-terminal-server", "gnome-terminal", "xterm", "uxterm", "konsole",
    "xfce4-terminal", "mate-terminal", "terminator", "tilix", "kitty",
    "alacritty", "urxvt", "rxvt", "wezterm", "wezterm-gui", "guake", "tilda",
    "foot", "footclient", "st", "lxterminal", "sakura", "qterminal",
    "cool-retro-term", "deepin-terminal", "io.elementary.terminal",
})

_HAS_XDOTOOL = shutil.which("xdotool") is not None


def active_window_is_terminal() -> bool:
    """Return True when the currently focused X11 window is a terminal."""
    if not _HAS_XDOTOOL:
        return False
    try:
        r = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowclassname"],
            capture_output=True, text=True, timeout=0.3,
        )
    except Exception:
        return False
    if r.returncode != 0:
        return False
    return r.stdout.strip().lower() in TERMINAL_WM_CLASSES
