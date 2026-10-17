import hashlib

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

from .terminal import active_window_is_terminal

# Screenshots and raw framebuffer grabs can be huge; cap the longest side so a
# single clipboard image can't balloon the on-disk image store.
MAX_IMAGE_DIMENSION = 2048


def _scale_down(pixbuf: GdkPixbuf.Pixbuf) -> GdkPixbuf.Pixbuf:
    w, h = pixbuf.get_width(), pixbuf.get_height()
    longest = max(w, h)
    if longest <= MAX_IMAGE_DIMENSION:
        return pixbuf
    scale = MAX_IMAGE_DIMENSION / longest
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    return pixbuf.scale_simple(new_w, new_h, GdkPixbuf.InterpType.BILINEAR)


def _encode_png(pixbuf: GdkPixbuf.Pixbuf):
    try:
        ok, data = pixbuf.save_to_bufferv("png", [], [])
    except GLib.Error:
        return None
    return data if ok else None


class ClipboardMonitor:
    def __init__(self, on_text, on_image, settings):
        self.on_text = on_text
        self.on_image = on_image
        self.settings = settings
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.primary = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        # _last_text / _last_image_hash dedupe emissions across both selections.
        # _last_clipboard_text / _last_clipboard_image are *only* the most recent
        # CLIPBOARD content (at most one is set), used for re-claiming after the
        # CLIPBOARD owner exits — must never carry PRIMARY content, or selecting
        # text would leak into the clipboard.
        self._last_text = None
        self._last_image_hash = None
        self._last_clipboard_text = None
        self._last_clipboard_image = None
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
            self._pending_timeout = GLib.timeout_add(50, lambda: self._request_content(clipboard))
        elif event.reason in (Gdk.OwnerChange.DESTROY, Gdk.OwnerChange.CLOSE):
            # Re-claim CLIPBOARD when its owner exits (e.g. xclip finishing a
            # pipe) so Ctrl+V returns the captured content rather than stale
            # content. Skip the PRIMARY case — doing this for PRIMARY would
            # write every text selection into the system clipboard.
            if clipboard is not self.clipboard:
                return
            if self._last_clipboard_image is not None:
                self.clipboard.set_image(self._last_clipboard_image)
            elif self._last_clipboard_text:
                self.clipboard.set_text(self._last_clipboard_text, -1)

    def _request_content(self, clipboard):
        self._pending_timeout = None
        # Images are only checked on CLIPBOARD: PRIMARY carries text selections
        # and an extra image round-trip there would add latency to every mouse
        # selection for a case that practically never happens.
        if clipboard is self.clipboard:
            clipboard.request_image(self._on_image_received)
        else:
            clipboard.request_text(self._on_text_received)
        return False

    def _on_image_received(self, clipboard, pixbuf):
        if pixbuf is None:
            clipboard.request_text(self._on_text_received)
            return
        pixbuf = _scale_down(pixbuf)
        png_bytes = _encode_png(pixbuf)
        if png_bytes is None:
            return
        digest = hashlib.sha256(png_bytes).hexdigest()
        if digest == self._last_image_hash:
            return
        self._remember_image(pixbuf, digest)
        self.on_image(png_bytes, pixbuf.get_width(), pixbuf.get_height())

    def _on_text_received(self, clipboard, text):
        if not text or text == self._last_text:
            return
        self._last_text = text
        self._last_image_hash = None
        if clipboard is self.clipboard:
            self._last_clipboard_text = text
            self._last_clipboard_image = None
        self.on_text(text)

    def _remember_image(self, pixbuf, digest):
        self._last_image_hash = digest
        self._last_clipboard_image = pixbuf
        self._last_text = None
        self._last_clipboard_text = None

    def capture_current(self):
        """Record whatever CLIPBOARD already holds (used once at startup)."""
        self._request_content(self.clipboard)

    def copy_text(self, text):
        self.clipboard.set_text(text, -1)
        self.primary.set_text(text, -1)
        self._last_text = text
        self._last_image_hash = None
        self._last_clipboard_text = text
        self._last_clipboard_image = None

    def copy_image(self, path):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(path))
        except GLib.Error:
            return
        png_bytes = _encode_png(pixbuf)
        if png_bytes is None:
            return
        self.clipboard.set_image(pixbuf)
        self._remember_image(pixbuf, hashlib.sha256(png_bytes).hexdigest())
