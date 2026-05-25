import os
import sys
import socket

# Disable the at-spi accessibility bridge before GTK initializes. Harmless for a
# clipboard manager and avoids a class of a11y/D-Bus stalls.
os.environ.setdefault("NO_AT_BRIDGE", "1")
os.environ.pop("GDK_BACKEND", None)

# NOTE: gi / Gtk / GLib are intentionally NOT imported at module level. Importing
# them starts GLib worker / GDBus background threads, and forking a multi-threaded
# process leaves those threads' locks held forever in the child — the first widget
# that touches that subsystem (e.g. Gtk.SpinButton) then deadlocks. We must fork
# while still single-threaded and import GTK only afterwards, in the child.


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
    debug = "--debug" in sys.argv

    if _activate_existing():
        if debug:
            print("clipmanx: activating existing instance", file=sys.stderr)
        sys.exit(0)

    # Fork to background BEFORE importing GTK so the child starts single-threaded.
    # Set CLIPMANX_NO_FORK=1 to stay in the foreground (debugging).
    if not os.environ.get("CLIPMANX_NO_FORK"):
        if os.fork() != 0:
            sys.exit(0)
        os.setsid()

    # Heavy imports happen post-fork, in the clean (single-threaded) child.
    from .logger import setup as debug_setup

    debug_setup(debug)

    from .app import ClipmanxApp

    app = ClipmanxApp(debug=debug)
    app.run()


if __name__ == "__main__":
    main()
