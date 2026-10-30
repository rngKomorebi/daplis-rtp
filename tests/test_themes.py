"""Every preset has to be complete and well-formed.

A theme is a wall of hex codes typed by hand, several of them ported
from somewhere else, and a single mistyped one is invisible until
somebody opens that theme: Qt silently ignores an unparseable colour in
a stylesheet, and matplotlib raises only when it next draws.

"""

import os
import re

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5")

from daplis_rtp.gui.theme import (  # noqa: E402
    DEFAULT_PRESET,
    N_SERIES,
    PRESETS,
    Theme,
    preset_names,
)

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

# Everything on a theme that is a single colour.
COLOUR_FIELDS = tuple(
    name
    for name in Theme.__dataclass_fields__
    if name not in ("key", "name", "base", "series", "glow", "grid_on")
)


@pytest.mark.parametrize("key", sorted(PRESETS))
def test_every_colour_is_a_six_digit_hex(key):
    theme = PRESETS[key]
    for field in COLOUR_FIELDS:
        value = getattr(theme, field)
        assert HEX.match(value), "{}.{} = {!r}".format(key, field, value)


@pytest.mark.parametrize("key", sorted(PRESETS))
def test_every_theme_carries_a_full_set_of_trace_colours(key):
    theme = PRESETS[key]
    assert len(theme.series) == N_SERIES
    for colour in theme.series:
        assert HEX.match(colour), "{}: {!r}".format(key, colour)


@pytest.mark.parametrize("key", sorted(PRESETS))
def test_the_base_is_one_qdarkstyle_understands(key):
    assert PRESETS[key].base in ("dark", "light")


@pytest.mark.parametrize("key", sorted(PRESETS))
def test_the_marker_is_not_one_of_the_first_two_traces(key):
    """The seam and the group lines must not read as data.

    They are drawn on the same axes as the trace, so a marker sharing
    its colour turns the boundary between the two sensor halves into
    something that looks like a measurement.

    """
    theme = PRESETS[key]
    assert theme.marker.lower() not in (
        theme.series[0].lower(),
        theme.series[1].lower(),
    )


def test_the_keys_and_names_are_unique():
    names = [name for _key, name in preset_names()]
    assert len(names) == len(set(names))
    assert len(PRESETS) == len(set(PRESETS))


def test_the_default_exists_and_the_dark_ones_come_first():
    """The theme menu draws its separator where the base changes."""
    assert DEFAULT_PRESET in PRESETS
    bases = [PRESETS[key].base for key, _name in preset_names()]
    assert bases == sorted(bases, key=("dark", "light").index)


@pytest.mark.parametrize("key", sorted(PRESETS))
def test_matplotlib_accepts_every_theme(key):
    """The rcParams a theme produces have to be usable as they stand.

    Checked by actually drawing with them: an unparseable colour in
    'rcParams' raises at draw time and nowhere earlier.

    """
    import matplotlib
    from matplotlib.figure import Figure

    from daplis_rtp.gui.theme import theme_manager

    manager = theme_manager()
    original = manager.preset_key
    try:
        manager.set_preset(key)
        with matplotlib.rc_context(manager.mpl_rc()):
            figure = Figure()
            axes = figure.add_subplot(111)
            axes.plot([0, 1], [0, 1], color=PRESETS[key].colour(0))
            axes.axvline(0.5, color=PRESETS[key].marker)
            figure.canvas.draw()
    finally:
        manager.set_preset(original)
