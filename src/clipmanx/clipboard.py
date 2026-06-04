import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, Gdk, GLib

from .terminal import active_window_is_terminal


class ClipboardMonitor:
    def __init__(self, on_change, settings):
        self.on_change = on_change
        self.settings = settings
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.primary = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        # _last_text dedupes emissions across both selections.
        # _last_clipboard_text is *only* the most recent CLIPBOARD content, used
        # for re-claiming after the CLIPBOARD owner exits — must never carry
        # PRIMARY content, or selecting text would leak into the clipboard.
        self._last_text = None
        self._last_clipboard_text = None
        self._pending_timeout = None

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
        # Skip clipboard changes originating from terminal emulators so command
        # output, shell snippets, and copy-on-select noise don't pollute history.
        if self.settings.ignore_terminals and active_window_is_terminal():
            return
        if event.reason == Gdk.OwnerChange.NEW_OWNER:
            if self._pending_timeout:
                GLib.source_remove(self._pending_timeout)
            self._pending_timeout = GLib.timeout_add(50, lambda: self._request_text(clipboard))
        elif event.reason in (Gdk.OwnerChange.DESTROY, Gdk.OwnerChange.CLOSE):
            # Re-claim CLIPBOARD when its owner exits (e.g. xclip finishing a
            # pipe) so Ctrl+V returns the captured text rather than stale
            # content. Skip the PRIMARY case — doing this for PRIMARY would
            # write every text selection into the system clipboard.
            if clipboard is self.clipboard and self._last_clipboard_text:
                self.clipboard.set_text(self._last_clipboard_text, -1)

    def _request_text(self, clipboard):
        self._pending_timeout = None
        clipboard.request_text(self._on_text_received)
        return False

    def _on_text_received(self, clipboard, text):
        if not text or text == self._last_text:
            return
        self._last_text = text
        if clipboard is self.clipboard:
            self._last_clipboard_text = text
        self.on_change(text)

    def copy(self, text):
        self.clipboard.set_text(text, -1)
        self.primary.set_text(text, -1)
        self._last_text = text
        self._last_clipboard_text = text

    def get_text(self):
        text = self.clipboard.wait_for_text()
        if text:
            self._last_text = text
            self._last_clipboard_text = text
        return text
