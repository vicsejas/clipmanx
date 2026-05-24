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


def _is_running():
    """Check if another instance is already running."""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect(_get_socket_path())
        sock.close()
        return True
    except (FileNotFoundError, ConnectionRefusedError, OSError):
        return False


def main():
    GLib.unsetenv("GDK_BACKEND")

    if _is_running():
        sys.exit(0)

    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    app = ClipmanxApp()
    app.run()


if __name__ == "__main__":
    main()
