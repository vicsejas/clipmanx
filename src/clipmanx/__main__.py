import gi

gi.require_version("Gtk", "3.0")

from gi.repository import GLib

from .app import ClipmanxApp


def main():
    GLib.unsetenv("GDK_BACKEND")
    app = ClipmanxApp()
    app.run()


if __name__ == "__main__":
    main()
