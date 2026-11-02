"""The window in the theme's colours: qdarkstyle's palette, swapped.

Tested on the pure functions, not through the theme manager, so that
nothing here reads or writes the stored settings.

"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5")
qdarkstyle = pytest.importorskip("qdarkstyle")

from dataclasses import replace  # noqa: E402

from PyQt5 import QtWidgets  # noqa: E402

from daplis_rtp.gui.theme import (  # noqa: E402
    PRESETS,
    chrome_colours,
    retint,
)


def _palette(theme):
    return (
        qdarkstyle.LightPalette
        if theme.base == "light"
        else qdarkstyle.DarkPalette
    )


def _sheet(palette):
    return qdarkstyle.load_stylesheet(qt_api="pyqt5", palette=palette)


def test_every_palette_colour_is_given_a_theme_colour():
    for theme in PRESETS.values():
        palette = _palette(theme)
        mapping = chrome_colours(palette, theme)
        names = [n for n in dir(palette) if n.startswith("COLOR_")]
        assert len(mapping) == len(names), theme.key


def test_the_two_ends_are_the_theme_s_own_colours():
    for theme in PRESETS.values():
        palette = _palette(theme)
        mapping = chrome_colours(palette, theme)
        assert mapping[palette.COLOR_BACKGROUND_1.lower()] == theme.window
        assert mapping[palette.COLOR_TEXT_1.lower()] == theme.text


def test_the_window_keeps_its_background_shades_in_order():
    """Hover lighter than rest on a dark theme, darker on a light one."""
    for theme in PRESETS.values():
        palette = _palette(theme)
        mapping = chrome_colours(palette, theme)
        shades = [
            mapping[getattr(palette, "COLOR_BACKGROUND_{}".format(i)).lower()]
            for i in range(1, 7)
        ]
        brightness = [
            sum(int(s[j:j + 2], 16) for j in (1, 3, 5)) for s in shades
        ]
        ordered = sorted(brightness, reverse=theme.base == "light")
        assert brightness == ordered, theme.key


def test_the_stylesheet_carries_the_theme_and_not_the_stock_palette():
    theme = PRESETS["cyberpunk"]
    palette = _palette(theme)
    sheet = retint(_sheet(palette), palette, theme).lower()
    assert theme.window in sheet
    assert theme.text in sheet
    # The stock background is gone, since the theme's differs from it
    assert palette.COLOR_BACKGROUND_1.lower() not in sheet


def test_a_colour_is_swapped_once_and_only_once():
    """A swapped colour equal to another palette colour stays as it is."""
    palette = qdarkstyle.DarkPalette
    # The window background set to the palette's own text colour: a
    # replacement done rule by rule would then turn the new background
    # into the theme's text on the next rule.
    theme = replace(PRESETS["midnight"], window=palette.COLOR_TEXT_1.lower())
    qss = "a {{ color: {}; }} b {{ color: {}; }}".format(
        palette.COLOR_BACKGROUND_1, palette.COLOR_TEXT_1
    )
    out = retint(qss, palette, theme)
    assert out == "a {{ color: {}; }} b {{ color: {}; }}".format(
        theme.window, theme.text
    )


def test_colours_outside_the_palette_are_left_alone():
    palette = qdarkstyle.DarkPalette
    out = retint("x { color: #123456; }", palette, PRESETS["midnight"])
    assert out == "x { color: #123456; }"


# Held here, for the rest of the session, rather than by the fixture.
# Dropping the QApplication deletes the process-wide theme manager with
# it, and this module runs before the others that use one: an
# application that ended with this module took the theme down for every
# test after it.
_APP = None


@pytest.fixture(scope="module")
def app():
    """The QApplication, skipped where Qt cannot start."""
    global _APP
    existing = QtWidgets.QApplication.instance()
    if existing is None:
        try:
            existing = QtWidgets.QApplication([])
        except Exception as err:  # noqa: BLE001 - whatever Qt raises
            pytest.skip("no Qt platform available: {}".format(err))
    _APP = existing
    return existing


def test_preferences_offer_the_window_and_status_colours(app):
    from daplis_rtp.gui.preferences import PreferencesDialog

    dialog = PreferencesDialog()
    fields = (
        "window",
        "panel",
        "surface",
        "button",
        "border",
        "text",
        "text_dim",
        "muted",
        "accent",
        "ok",
        "warn",
        "error",
    )
    for field in fields:
        assert field in dialog._colour_buttons, field
    dialog.close()


# ----------------------------------------------------------------------
# The window's roles
# ----------------------------------------------------------------------


@pytest.fixture
def manager(app, monkeypatch):
    """A theme manager that neither reads nor writes the stored settings."""
    from daplis_rtp.gui import theme

    monkeypatch.setattr(theme.ThemeManager, "load", lambda self: None)
    monkeypatch.setattr(theme.ThemeManager, "save", lambda self: None)
    return theme.ThemeManager()


def test_every_preset_fills_the_window_roles():
    for theme in PRESETS.values():
        for field in ("panel", "button", "border", "text_dim"):
            value = getattr(theme, field)
            assert value.startswith("#") and len(value) == 7, (
                theme.key,
                field,
            )


def test_a_derived_role_follows_the_colour_it_comes_from(manager):
    before = manager.theme
    manager.set_override("window", "#203040")
    after = manager.theme
    assert after.panel != before.panel
    assert after.button != before.button
    # Not derived from the window: untouched
    assert after.text_dim == before.text_dim


def test_a_role_set_by_hand_stays_put(manager):
    manager.set_override("button", "#123456")
    manager.set_override("window", "#203040")
    assert manager.theme.button == "#123456"


def test_the_stylesheet_puts_each_role_on_its_widgets(manager):
    manager.set_override("surface", "#010203")
    manager.set_override("button", "#040506")
    sheet = manager.stylesheet()
    fields = sheet[sheet.index("QLineEdit, QSpinBox"):]
    assert "background-color: #010203" in fields
    buttons = sheet[sheet.index("QPushButton, QSpinBox::up-button"):]
    assert "background-color: #040506" in buttons
