import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from .clipboard import ClipboardMonitor
from .history import History
from .settings import Settings

APP_INDICATOR_ICON = "edit-paste"


def truncate(text: str, max_len: int = 60) -> str:
    text = text.replace("\n", " ").replace("\r", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text or "(empty)"


class ClipmanApp:
    def __init__(self):
        self.settings = Settings()
        self.history = History(max_items=self.settings.max_items)
        self._settings_window = None
        self.tray = Gtk.StatusIcon.new_from_icon_name(APP_INDICATOR_ICON)
        self.tray.set_tooltip_text("Clipman")
        self.tray.set_visible(True)
        self.tray.connect("popup-menu", self._on_popup_menu)
        self.tray.connect("activate", lambda icon: self._on_popup_menu(icon, 0, Gtk.get_current_event_time()))

        self.monitor = ClipboardMonitor(on_change=self._on_clipboard_change, settings=self.settings)

        existing = self.monitor.get_text()
        if existing:
            self.history.add(existing)

    def _on_clipboard_change(self, text: str):
        if not text:
            return
        self.history.add(text)

    def _copy_to_clipboard(self, text: str):
        self.monitor.copy(text)

    def _clear_history(self, _item=None):
        self.history.clear()

    def _show_settings(self, _item=None):
        if self._settings_window is not None:
            self._settings_window.present()
            return

        win = Gtk.Window(title="Clipman Settings")
        win.set_default_size(360, 180)
        win.set_border_width(12)
        win.connect("destroy", self._on_settings_closed)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        win.add(box)

        clip_check = Gtk.CheckButton(label="Capture system clipboard (Ctrl+C)")
        clip_check.set_active(self.settings.capture_clipboard)
        clip_check.connect(
            "toggled", lambda b: setattr(self.settings, "capture_clipboard", b.get_active())
        )
        box.pack_start(clip_check, False, False, 0)

        primary_check = Gtk.CheckButton(label="Capture selection / xclip (PRIMARY)")
        primary_check.set_active(self.settings.capture_primary)
        primary_check.connect(
            "toggled", lambda b: setattr(self.settings, "capture_primary", b.get_active())
        )
        box.pack_start(primary_check, False, False, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label(label="Max history items:")
        hbox.pack_start(label, False, False, 0)
        adj = Gtk.Adjustment(
            value=self.settings.max_items, lower=1, upper=9999, step_incr=1, page_incr=10
        )
        spin = Gtk.SpinButton(adjustment=adj, climb_rate=1, digits=0)
        spin.connect("value-changed", lambda s: self._on_max_items_changed(int(s.get_value())))
        hbox.pack_start(spin, False, False, 0)
        box.pack_start(hbox, False, False, 0)

        self._settings_window = win
        win.show_all()

    def _on_settings_closed(self, _win):
        self._settings_window = None

    def _on_max_items_changed(self, value: int):
        self.settings.max_items = value
        self.history.max_items = value

    def _quit(self, _item=None):
        Gtk.main_quit()

    def _on_popup_menu(self, _icon, button, time):
        menu = self._build_menu()
        menu.show_all()
        menu.popup(None, None, Gtk.StatusIcon.position_menu, self.tray, button, time)

    def _build_menu(self) -> Gtk.Menu:
        menu = Gtk.Menu()
        items = self.history.get_all()[:self.settings.max_items]

        if not items:
            item = Gtk.MenuItem(label="(no history)")
            item.set_sensitive(False)
            menu.append(item)
        else:
            for text in items:
                label = truncate(text)
                item = Gtk.MenuItem(label=label)
                item.connect("activate", lambda _, t=text: self._copy_to_clipboard(t))
                menu.append(item)

        menu.append(Gtk.SeparatorMenuItem())

        clear = Gtk.MenuItem(label="Clear History")
        clear.connect("activate", self._clear_history)
        menu.append(clear)

        settings_item = Gtk.MenuItem(label="Settings")
        settings_item.connect("activate", self._show_settings)
        menu.append(settings_item)

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self._quit)
        menu.append(quit_item)

        return menu

    def run(self):
        try:
            Gtk.main()
        except KeyboardInterrupt:
            Gtk.main_quit()
