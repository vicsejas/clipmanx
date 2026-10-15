"""Detect the desktop's dark/light preference and watch for live changes.

Sources, in priority order:
  1. XDG desktop portal ``org.freedesktop.appearance color-scheme``
     (GNOME 42+, Cinnamon, KDE, XFCE with xdg-desktop-portal-*).
  2. GTK settings: ``gtk-application-prefer-dark-theme`` or a theme name
     containing "dark" (classic xsettings-based desktops).
"""

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gio, GLib, Gtk

from .logger import debug as _dbg

PORTAL_BUS_NAME = "org.freedesktop.portal.Desktop"
PORTAL_OBJECT_PATH = "/org/freedesktop/portal/desktop"
PORTAL_SETTINGS_IFACE = "org.freedesktop.portal.Settings"
APPEARANCE_NAMESPACE = "org.freedesktop.appearance"
COLOR_SCHEME_KEY = "color-scheme"

# Portal color-scheme values
COLOR_SCHEME_NO_PREFERENCE = 0
COLOR_SCHEME_DARK = 1
COLOR_SCHEME_LIGHT = 2


def resolve_dark(color_scheme, theme_name: str, prefer_dark: bool) -> bool:
    """Decide whether the desktop is in dark mode.

    An explicit portal preference wins; otherwise fall back to GTK hints.
    """
    if color_scheme == COLOR_SCHEME_DARK:
        return True
    if color_scheme == COLOR_SCHEME_LIGHT:
        return False
    return bool(prefer_dark) or "dark" in (theme_name or "").lower()


class ThemeWatcher:
    """Calls ``on_change(is_dark)`` whenever the desktop dark/light mode flips."""

    def __init__(self, on_change):
        self._on_change = on_change
        self._color_scheme = None
        self._portal = None
        self._gtk_settings = Gtk.Settings.get_default()

        self._connect_portal()
        if self._gtk_settings is not None:
            self._gtk_settings.connect("notify::gtk-theme-name", self._on_gtk_changed)
            self._gtk_settings.connect("notify::gtk-application-prefer-dark-theme", self._on_gtk_changed)

        self._is_dark = self._compute()
        _dbg("ThemeWatcher: color_scheme=%s is_dark=%s", self._color_scheme, self._is_dark)

    @property
    def is_dark(self) -> bool:
        return self._is_dark

    def _connect_portal(self):
        try:
            self._portal = Gio.DBusProxy.new_for_bus_sync(
                Gio.BusType.SESSION,
                Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES,
                None,
                PORTAL_BUS_NAME,
                PORTAL_OBJECT_PATH,
                PORTAL_SETTINGS_IFACE,
                None,
            )
        except GLib.Error as e:
            _dbg("ThemeWatcher: portal unavailable: %s", e)
            return

        self._color_scheme = self._read_portal_color_scheme()
        self._portal.connect("g-signal", self._on_portal_signal)

    def _read_portal_color_scheme(self):
        args = GLib.Variant("(ss)", (APPEARANCE_NAMESPACE, COLOR_SCHEME_KEY))
        # ReadOne is portal v2+; Read is the deprecated fallback.
        for method in ("ReadOne", "Read"):
            try:
                result = self._portal.call_sync(method, args, Gio.DBusCallFlags.NONE, 1000, None)
            except GLib.Error as e:
                _dbg("ThemeWatcher: portal %s failed: %s", method, e)
                # Only an old portal lacking ReadOne warrants retrying with Read;
                # timeouts or a missing key would fail the same way again.
                if e.matches(Gio.dbus_error_quark(), Gio.DBusError.UNKNOWN_METHOD):
                    continue
                return None
            # unpack() recursively unwraps the (possibly nested) variant.
            value = result.unpack()[0]
            if isinstance(value, int):
                return value
        return None

    def _on_portal_signal(self, _proxy, _sender, signal_name, params):
        if signal_name != "SettingChanged":
            return
        namespace, key, value = params.unpack()
        if namespace == APPEARANCE_NAMESPACE and key == COLOR_SCHEME_KEY:
            _dbg("ThemeWatcher: portal color-scheme -> %s", value)
            self._color_scheme = value
            self._refresh()

    def _on_gtk_changed(self, *_args):
        self._refresh()

    def _compute(self) -> bool:
        theme_name = ""
        prefer_dark = False
        if self._gtk_settings is not None:
            theme_name = self._gtk_settings.get_property("gtk-theme-name") or ""
            prefer_dark = self._gtk_settings.get_property("gtk-application-prefer-dark-theme")
        return resolve_dark(self._color_scheme, theme_name, prefer_dark)

    def _refresh(self):
        is_dark = self._compute()
        if is_dark != self._is_dark:
            self._is_dark = is_dark
            _dbg("ThemeWatcher: is_dark -> %s", is_dark)
            self._on_change(is_dark)
