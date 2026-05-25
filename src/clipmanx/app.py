import gi
import os
import socket
import threading

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gdk, GLib, Pango
from pathlib import Path

from .clipboard import ClipboardMonitor
from .logger import debug as _dbg
from .history import History
from .settings import Settings

FALLBACK_ICON_NAME = "edit-paste"


def _create_theme_adapted_icon(icon_theme: str) -> Gtk.StatusIcon:
    """Create status icon based on theme setting.

    Icon is from Lucide (https://lucide.dev) under MIT license.

    Args:
        icon_theme: "auto", "light", or "dark"
    """
    assets_dir = Path(__file__).parent / "assets"
    fallback = Gtk.StatusIcon.new_from_icon_name(FALLBACK_ICON_NAME)

    if icon_theme == "auto":
        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings is None:
            use_dark = False
        else:
            theme_name = gtk_settings.get_property("gtk-theme-name") or ""
            prefer_dark = gtk_settings.get_property("gtk-application-prefer-dark-theme")
            use_dark = prefer_dark or "dark" in theme_name.lower()
    else:
        use_dark = icon_theme == "dark"

    icon_file = "icon-white.svg" if use_dark else "icon-black.svg"
    icon_path = assets_dir / icon_file

    if not icon_path.exists():
        return fallback

    try:
        return Gtk.StatusIcon.new_from_file(str(icon_path))
    except Exception:
        return fallback


def truncate(text: str, max_len: int = 60) -> str:
    text = text.replace("\n", " ").replace("\r", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "\u2026"
    return text or "(empty)"


class ClipmanxApp:
    def __init__(self, debug=False):
        self._debug = debug
        _dbg("app.__init__: starting")
        self.settings = Settings()
        self.history = History(max_items=self.settings.max_items)
        self._settings_window = None
        self._popup_window = None
        self.tray = None
        self._socket_server = None

        self._apply_tooltip_delay(self.settings.tooltip_delay)

        _dbg("app.__init__: _setup_tray")
        self._setup_tray(self.settings.icon_theme)

        _dbg("app.__init__: ClipboardMonitor")
        self.monitor = ClipboardMonitor(on_change=self._on_clipboard_change, settings=self.settings)
        existing = self.monitor.get_text()
        if existing:
            self.history.add(existing)
        _dbg("app.__init__: done")

    def _start_socket_server(self):
        """Start socket server for single-instance detection."""
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR", f"/tmp/user-{os.getuid()}")
        socket_path = os.path.join(runtime_dir, "clipmanx.sock")

        try:
            if os.path.exists(socket_path):
                os.remove(socket_path)

            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(socket_path)
            sock.listen(1)

            def accept_connections():
                while True:
                    try:
                        conn, _ = sock.accept()
                        conn.close()
                        GLib.idle_add(lambda: self._show_full_view(self.tray))
                    except Exception:
                        break

            thread = threading.Thread(target=accept_connections, daemon=True)
            thread.start()
            self._socket_server = sock
        except Exception:
            pass

    def _setup_tray(self, theme: str):
        """Create and configure system tray icon with theme-aware styling."""
        _dbg("_setup_tray: theme=%s", theme)
        if self.tray is not None:
            self.tray.set_visible(False)
        self.tray = _create_theme_adapted_icon(theme)
        self.tray.set_tooltip_text("Clipmanx")
        self.tray.set_visible(True)
        # Both left-click (activate) and right-click (popup-menu) open the
        # full-view popup — a single, consistent UI.
        self.tray.connect("activate", self._show_full_view)
        self.tray.connect("popup-menu", lambda icon, _button, _time: self._show_full_view(icon))
        _dbg("_setup_tray: done")

    def _on_clipboard_change(self, text: str):
        if not text:
            return
        self.history.add(text)

    def _copy_to_clipboard(self, text: str):
        self.monitor.copy(text)

    def _clear_history(self, _item=None):
        self.history.clear()

    def _show_settings(self, _item=None):
        try:
            self._show_settings_impl(_item)
        except Exception:
            import traceback
            _dbg("_show_settings: EXCEPTION\n%s", traceback.format_exc())

    def _show_settings_impl(self, _item=None):
        _dbg("_show_settings: called, _settings_window=%s", self._settings_window)
        if self._settings_window is not None:
            _dbg("_show_settings: presenting existing window")
            self._settings_window.present()
            return

        _dbg("_show_settings: creating window")
        win = Gtk.Window(title="Clipmanx Settings")
        _dbg("_show_settings: window created, setting props")
        win.set_default_size(360, 180)
        _dbg("_show_settings: set_default_size ok")
        win.set_border_width(12)
        _dbg("_show_settings: set_border_width ok")
        win.connect("destroy", self._on_settings_closed)
        _dbg("_show_settings: props set, creating box")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        _dbg("_show_settings: box created")
        win.add(box)
        _dbg("_show_settings: box added, creating clip_check")

        clip_check = Gtk.CheckButton(label="Capture system clipboard (Ctrl+C)")
        _dbg("_show_settings: clip_check Gtk created")
        clip_check.set_active(self.settings.capture_clipboard)
        _dbg("_show_settings: clip_check set_active ok")
        clip_check.connect(
            "toggled", lambda b: setattr(self.settings, "capture_clipboard", b.get_active())
        )
        box.pack_start(clip_check, False, False, 0)
        _dbg("_show_settings: clip_check done, creating primary_check")

        primary_check = Gtk.CheckButton(label="Capture selection / xclip (PRIMARY)")
        _dbg("_show_settings: primary_check Gtk created")
        primary_check.set_active(self.settings.capture_primary)
        _dbg("_show_settings: primary_check set_active ok")
        primary_check.connect(
            "toggled", lambda b: setattr(self.settings, "capture_primary", b.get_active())
        )
        box.pack_start(primary_check, False, False, 0)
        _dbg("_show_settings: primary_check done, creating max_items hbox")

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        _dbg("_show_settings: max hbox created")
        label = Gtk.Label(label="Max history items:")
        _dbg("_show_settings: max label created")
        hbox.pack_start(label, False, False, 0)
        _dbg("_show_settings: max label packed")
        adj = Gtk.Adjustment(
            value=self.settings.max_items, lower=1, upper=9999, step_incr=1, page_incr=10
        )
        _dbg("_show_settings: max adj created")
        spin = Gtk.SpinButton(adjustment=adj, climb_rate=1, digits=0)
        _dbg("_show_settings: max spin created")
        spin.connect("value-changed", lambda s: self._on_max_items_changed(int(s.get_value())))
        _dbg("_show_settings: max spin connected")
        hbox.pack_start(spin, False, False, 0)
        _dbg("_show_settings: max spin packed")
        box.pack_start(hbox, False, False, 0)
        _dbg("_show_settings: max_items done, creating theme combo")

        theme_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        _dbg("_show_settings: theme hbox created")
        theme_label = Gtk.Label(label="Icon theme:")
        _dbg("_show_settings: theme label created")
        theme_hbox.pack_start(theme_label, False, False, 0)
        theme_combo = Gtk.ComboBoxText()
        _dbg("_show_settings: theme combo created")
        theme_combo.append("auto", "Auto Detect")
        theme_combo.append("light", "Light")
        theme_combo.append("dark", "Dark")
        _dbg("_show_settings: theme combo appends done")
        theme_combo.set_active_id(self.settings.icon_theme)
        _dbg("_show_settings: theme combo active set")
        theme_combo.connect("changed", self._on_icon_theme_changed)
        _dbg("_show_settings: theme combo connected")
        theme_hbox.pack_start(theme_combo, False, False, 0)
        box.pack_start(theme_hbox, False, False, 0)
        _dbg("_show_settings: theme done, creating tooltip delay")

        delay_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        _dbg("_show_settings: delay hbox created")
        delay_label = Gtk.Label(label="Tooltip delay (ms):")
        _dbg("_show_settings: delay label created")
        delay_hbox.pack_start(delay_label, False, False, 0)
        delay_adj = Gtk.Adjustment(
            value=self.settings.tooltip_delay, lower=0, upper=10000, step_incr=50, page_incr=500
        )
        _dbg("_show_settings: delay adj created, value=%s", self.settings.tooltip_delay)
        delay_spin = Gtk.SpinButton(adjustment=delay_adj, climb_rate=50, digits=0)
        _dbg("_show_settings: delay spin created")
        delay_spin.connect("value-changed", self._on_tooltip_delay_changed)
        _dbg("_show_settings: delay spin connected")
        delay_hbox.pack_start(delay_spin, False, False, 0)
        box.pack_start(delay_hbox, False, False, 0)
        _dbg("_show_settings: tooltip delay done")

        _dbg("_show_settings: widgets done, setting _settings_window")
        self._settings_window = win
        _dbg("_show_settings: calling show_all")
        win.show_all()
        _dbg("_show_settings: show_all returned")

    def _on_settings_closed(self, _win):
        _dbg("_on_settings_closed: clearing _settings_window")
        self._settings_window = None

    def _on_max_items_changed(self, value: int):
        self.settings.max_items = value
        self.history.max_items = value

    def _on_icon_theme_changed(self, combo):
        """Update tray icon when user changes theme preference in settings."""
        theme = combo.get_active_id()
        if theme:
            self.settings.icon_theme = theme
            self._setup_tray(theme)

    def _apply_tooltip_delay(self, delay_ms: int):
        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings is not None:
            gtk_settings.set_property("gtk-tooltip-timeout", delay_ms)

    def _on_tooltip_delay_changed(self, spin):
        delay = int(spin.get_value())
        self.settings.tooltip_delay = delay
        self._apply_tooltip_delay(delay)

    def _on_full_view_settings_clicked(self, popup_win):
        _dbg("_on_full_view_settings_clicked: calling _show_settings")
        self._show_settings()
        _dbg("_on_full_view_settings_clicked: scheduling popup destroy via idle_add")
        GLib.idle_add(popup_win.destroy)
        _dbg("_on_full_view_settings_clicked: done")

    def _show_full_view(self, _icon):
        _dbg("_show_full_view: called, _popup_window=%s", self._popup_window)
        if self._popup_window is not None:
            _dbg("_show_full_view: toggle-closing existing popup")
            self._popup_window.destroy()
            return

        _dbg("_show_full_view: creating new popup")

        win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        win.set_decorated(False)
        win.set_skip_taskbar_hint(True)
        win.set_skip_pager_hint(True)
        win.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        win.set_border_width(1)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        win.add(outer)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_max_content_height(400)
        scroll.set_propagate_natural_height(True)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.BROWSE)

        items = self.history.get_all()[: self.settings.max_items]
        if not items:
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label="(no history)")
            lbl.set_margin_start(12)
            lbl.set_margin_end(12)
            lbl.set_margin_top(8)
            lbl.set_margin_bottom(8)
            row.add(lbl)
            row.set_activatable(False)
            listbox.add(row)
        else:
            for text in items:
                row = Gtk.ListBoxRow()
                lbl = Gtk.Label(label=truncate(text, 50))
                lbl.set_xalign(0)
                lbl.set_margin_start(12)
                lbl.set_margin_end(12)
                lbl.set_margin_top(5)
                lbl.set_margin_bottom(5)
                row.add(lbl)
                listbox.add(row)

        listbox.connect(
            "row-activated",
            lambda _lb, row, _items=items: self._copy_from_full_view(
                _items[row.get_index()], win
            ),
        )
        # Scrollable hover preview (replaces the non-scrollable GTK tooltip)
        listbox.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        listbox.connect(
            "motion-notify-event",
            lambda lb, ev, _items=items: self._on_list_motion(lb, ev, _items, win),
        )
        scroll.add(listbox)
        outer.pack_start(scroll, True, True, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        outer.pack_start(sep, False, False, 0)

        btn_row = Gtk.Box(spacing=0)
        btn_row.set_margin_top(4)
        btn_row.set_margin_bottom(4)
        btn_row.set_margin_start(6)
        btn_row.set_margin_end(6)
        quit_btn = Gtk.Button(label="Quit")
        quit_btn.connect("clicked", lambda _: self._quit())
        btn_row.pack_end(quit_btn, False, False, 0)

        settings_btn = Gtk.Button(label="Settings")
        settings_btn.connect("clicked", lambda _: self._on_full_view_settings_clicked(win))
        btn_row.pack_end(settings_btn, False, False, 4)

        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", lambda _: (self._clear_history(), win.destroy()))
        btn_row.pack_start(clear_btn, False, False, 0)
        outer.pack_start(btn_row, False, False, 0)

        win.connect("focus-out-event", lambda w, _e: (_dbg("popup focus-out-event -> destroy"), w.destroy(), True)[2])
        win.connect("destroy", lambda _w: (_dbg("popup destroy -> clearing _popup_window"), self._hide_row_preview(), setattr(self, "_popup_window", None)))

        win.show_all()
        _dbg("_show_full_view: show_all done, positioning")
        self._position_popup_near_tray(win)
        win.present()
        self._popup_window = win
        _dbg("_show_full_view: popup shown, _popup_window set")

    def _copy_from_full_view(self, text: str, win: Gtk.Window):
        _dbg("_copy_from_full_view: destroying popup, copying text")
        win.destroy()
        self._copy_to_clipboard(text)

    def _on_list_motion(self, listbox, event, items, win):
        """Show a scrollable preview of the row under the pointer."""
        row = listbox.get_row_at_y(int(event.y))
        if row is None:
            return False
        idx = row.get_index()
        if 0 <= idx < len(items):
            self._show_row_preview(items[idx], row, win)
        return False

    def _hide_row_preview(self):
        pop = getattr(self, "_row_preview", None)
        if pop is not None:
            pop.destroy()
        self._row_preview = None
        self._row_preview_text = None

    def _show_row_preview(self, text: str, row: Gtk.Widget, win: Gtk.Window):
        # Skip rebuilding while hovering within the same row
        if getattr(self, "_row_preview", None) and getattr(self, "_row_preview_text", None) == text:
            return
        self._hide_row_preview()
        if not text:
            return

        pop = Gtk.Window(type=Gtk.WindowType.POPUP)
        pop.set_type_hint(Gdk.WindowTypeHint.TOOLTIP)
        pop.set_accept_focus(False)
        pop.set_focus_on_map(False)
        pop.set_border_width(1)

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.OUT)
        pop.add(frame)

        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_cursor_visible(False)
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.set_left_margin(8)
        tv.set_right_margin(8)
        tv.set_top_margin(8)
        tv.set_bottom_margin(8)
        tv.get_buffer().set_text(text)

        # Monitor work area sets the preview's max size.
        display = Gdk.Display.get_default()
        gdkwin = win.get_window()
        monitor = (
            display.get_monitor_at_window(gdkwin) if gdkwin else None
        ) or display.get_primary_monitor()
        geom = monitor.get_workarea()
        width = min(460, geom.width // 2)
        max_h = geom.height - 8

        # Measure the wrapped text height at the fixed width with Pango. A
        # ScrolledWindow's own natural-height guess ignores the wrap width, which
        # is what made short text show a scrollbar and tall text fall short.
        layout = tv.create_pango_layout(text)
        layout.set_width(max(1, width - 20) * Pango.SCALE)
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        _tw, th = layout.get_pixel_size()
        text_height = th + 16 + 8  # top/bottom margins + small padding
        fits = text_height <= max_h
        content_h = text_height if fits else max_h

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(
            Gtk.PolicyType.NEVER,
            Gtk.PolicyType.NEVER if fits else Gtk.PolicyType.AUTOMATIC,
        )
        scroll.set_min_content_width(width)
        scroll.set_max_content_width(width)
        scroll.set_min_content_height(content_h)
        scroll.set_max_content_height(content_h)
        scroll.add(tv)
        frame.add(scroll)

        pop.show_all()

        # Position beside the main window, aligned with the hovered row
        win_x, win_y = win.get_position()
        ww, _wh = win.get_size()
        pw, ph = pop.get_size()

        coords = row.translate_coordinates(win, 0, 0)
        row_y = coords[1] if coords else 0

        x = win_x + ww + 4
        if x + pw > geom.x + geom.width:
            x = win_x - pw - 4
        x = max(geom.x, x)

        y = win_y + row_y
        if y + ph > geom.y + geom.height:
            y = geom.y + geom.height - ph
        y = max(geom.y, y)

        pop.move(x, y)
        self._row_preview = pop
        self._row_preview_text = text

    def _position_popup_near_tray(self, win: Gtk.Window):
        ok, _screen, area, _orient = self.tray.get_geometry()
        if not ok:
            return

        display = Gdk.Display.get_default()
        monitor = display.get_monitor_at_point(
            area.x + area.width // 2, area.y + area.height // 2
        )
        if monitor is None:
            monitor = display.get_primary_monitor()
        geom = monitor.get_geometry()

        win_width, win_height = win.get_size()

        x_right = area.x + area.width + 4
        x_left = area.x - win_width - 4

        if x_right + win_width <= geom.x + geom.width:
            x = x_right
        elif x_left >= geom.x:
            x = x_left
        else:
            x = max(geom.x, min(area.x - win_width // 2, geom.x + geom.width - win_width))

        y = area.y
        if y + win_height > geom.y + geom.height:
            y = geom.y + geom.height - win_height
        y = max(geom.y, y)

        win.move(x, y)

    def _quit(self, _item=None):
        _dbg("_quit: calling Gtk.main_quit")
        Gtk.main_quit()

    def _on_popup_menu(self, _icon, button, time):
        menu = self._build_menu()
        menu.show_all()
        menu.popup(None, None, Gtk.StatusIcon.position_menu, self.tray, button, time)

    def _build_menu(self) -> Gtk.Menu:
        menu = Gtk.Menu()
        items = self.history.get_all()[: self.settings.max_items]

        if not items:
            item = Gtk.MenuItem(label="(no history)")
            item.set_sensitive(False)
            menu.append(item)
        else:
            for text in items:
                label = truncate(text)
                item = Gtk.MenuItem(label=label)
                item.set_has_tooltip(True)
                item.set_tooltip_text(text)
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
        _dbg("run: starting socket server")
        self._start_socket_server()
        _dbg("run: entering Gtk.main")
        try:
            Gtk.main()
        except KeyboardInterrupt:
            Gtk.main_quit()
        _dbg("run: Gtk.main returned")
