import os
import atexit
import logging
import faulthandler
from pathlib import Path

_log = logging.getLogger("clipmanx")
_handler = None
_log_path = None


def setup(debug: bool) -> None:
    global _handler, _log_path
    if not debug:
        return
    _log_path = Path(__file__).parent.parent.parent / "log.txt"
    _handler = logging.FileHandler(str(_log_path), encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
    _log.addHandler(_handler)
    _log.setLevel(logging.DEBUG)
    _log.debug("=== debug log started (pid=%d) ===", os.getpid())

    crash_path = str(Path(__file__).parent.parent.parent / "crash.log")
    faulthandler.enable(file=open(crash_path, "w"), all_threads=True)

    atexit.register(_flush)


def debug(msg: str, *args) -> None:
    try:
        _log.debug(msg, *args)
        if _handler is not None:
            _handler.flush()
    except Exception:
        pass


def _flush() -> None:
    if _handler is not None:
        try:
            _handler.flush()
            _handler.close()
        except Exception:
            pass
