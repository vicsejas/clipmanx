import unittest
from unittest.mock import patch

from clipmanx import clipboard as cb


class _Result:
    def __init__(self, stdout, returncode=0):
        self.stdout = stdout
        self.returncode = returncode


class TerminalWindowDetectionTests(unittest.TestCase):
    def test_matches_known_terminal_class(self):
        with patch.object(cb, "_HAS_XDOTOOL", True), patch.object(
            cb.subprocess, "run", return_value=_Result("gnome-terminal-server\n")
        ):
            self.assertTrue(cb._active_window_is_terminal())

    def test_match_is_case_insensitive(self):
        with patch.object(cb, "_HAS_XDOTOOL", True), patch.object(
            cb.subprocess, "run", return_value=_Result("Konsole\n")
        ):
            self.assertTrue(cb._active_window_is_terminal())

    def test_non_terminal_window_returns_false(self):
        with patch.object(cb, "_HAS_XDOTOOL", True), patch.object(
            cb.subprocess, "run", return_value=_Result("Firefox\n")
        ):
            self.assertFalse(cb._active_window_is_terminal())

    def test_missing_xdotool_returns_false(self):
        with patch.object(cb, "_HAS_XDOTOOL", False):
            self.assertFalse(cb._active_window_is_terminal())

    def test_subprocess_failure_returns_false(self):
        with patch.object(cb, "_HAS_XDOTOOL", True), patch.object(
            cb.subprocess, "run", side_effect=OSError("boom")
        ):
            self.assertFalse(cb._active_window_is_terminal())

    def test_nonzero_returncode_returns_false(self):
        with patch.object(cb, "_HAS_XDOTOOL", True), patch.object(
            cb.subprocess, "run", return_value=_Result("", returncode=1)
        ):
            self.assertFalse(cb._active_window_is_terminal())


if __name__ == "__main__":
    unittest.main()
