import unittest

from clipmanx.theme import (
    COLOR_SCHEME_DARK,
    COLOR_SCHEME_LIGHT,
    COLOR_SCHEME_NO_PREFERENCE,
    resolve_dark,
)


class ResolveDarkTests(unittest.TestCase):
    def test_portal_dark_wins_over_light_gtk_theme(self):
        self.assertTrue(resolve_dark(COLOR_SCHEME_DARK, "Mint-Y", False))

    def test_portal_light_wins_over_dark_gtk_theme(self):
        self.assertFalse(resolve_dark(COLOR_SCHEME_LIGHT, "Mint-Y-Dark-Blue", True))

    def test_no_preference_falls_back_to_theme_name(self):
        self.assertTrue(resolve_dark(COLOR_SCHEME_NO_PREFERENCE, "Adwaita-dark", False))
        self.assertFalse(resolve_dark(COLOR_SCHEME_NO_PREFERENCE, "Adwaita", False))

    def test_no_portal_falls_back_to_prefer_dark(self):
        self.assertTrue(resolve_dark(None, "Adwaita", True))
        self.assertFalse(resolve_dark(None, "", False))


if __name__ == "__main__":
    unittest.main()
