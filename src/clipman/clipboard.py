import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, Gdk, GLib


class ClipboardMonitor:
    def __init__(self, on_change, settings):
        self.on_change = on_change
        self.settings = settings
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.primary = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        self._last_text = None

        self.clipboard.connect("owner-change", self._on_owner_change)
        self.primary.connect("owner-change", self._on_owner_change)

    def _enabled_for(self, clipboard) -> bool:
        if clipboard is self.clipboard:
            return self.settings.capture_clipboard
        if clipboard is self.primary:
            return self.settings.capture_primary
        return False

    def _on_owner_change(self, clipboard, event):
        if not self._enabled_for(clipboard):
            return
        if event.reason == Gdk.OwnerChange.NEW_OWNER:
            clipboard.request_text(self._on_text_received)
        elif event.reason in (Gdk.OwnerChange.DESTROY, Gdk.OwnerChange.CLOSE) and self._last_text:
            # The selection owner exited (e.g. xclip finished after a pipe).
            # Re-claim the CLIPBOARD selection with the captured text so Ctrl+V
            # returns it instead of falling back to stale content (an old image).
            self.clipboard.set_text(self._last_text, -1)

    def _on_text_received(self, _clipboard, text):
        if text and text != self._last_text:
            self._last_text = text
            self.on_change(text)

    def copy(self, text):
        self.clipboard.set_text(text, -1)
        self.primary.set_text(text, -1)
        self._last_text = text

    def get_text(self):
        text = self.clipboard.wait_for_text()
        if text:
            self._last_text = text
        return text
