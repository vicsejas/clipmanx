import gi
import sys
import socket
import os

gi.require_version("Gtk", "3.0")

from gi.repository import GLib

from .app import ClipmanxApp


def _get_socket_path():
    """Get path for the single-instance socket."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", f"/tmp/user-{os.getuid()}")
    return os.path.join(runtime_dir, "clipmanx.sock")


def _activate_existing():
    """Connect to existing instance and request activation."""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect(_get_socket_path())
        sock.send(b"activate")
        sock.close()
        return True
    except Exception:
        return False


def main():
    GLib.unsetenv("GDK_BACKEND")

    # Try to activate existing instance
    if _activate_existing():
        sys.exit(0)

    # No existing instance, create and run new one
    app = ClipmanxApp()
    app.run()


if __name__ == "__main__":
    main()
