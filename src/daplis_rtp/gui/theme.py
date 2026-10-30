"""Where every colour, font size and plot style in the application comes from.

One object holds the lot - the window palette, the accent, the colours
the traces are drawn in, the two font sizes - and one signal says it has
changed. Nothing else in the package hard-codes a colour.

The reason is that the old application chose its colours in a dozen
places: ``plt.style.use("dark_background")`` in three canvas modules,
``#f48383`` and ``teal`` written into the plotting calls, ``qdarkstyle``
on the application, and a ``setPointSize`` on very nearly every widget
built. Changing the look meant finding all of them, and a user who
wanted a lighter background, or a colour they could actually
distinguish, had nowhere to say so.

Two rules keep it that way:

* **Widgets do not set their own font.** The application font is set
  here and inherited; a widget that needs a different one gets an
  object name and a rule in the stylesheet below. A per-widget
  ``setFont`` pins that widget at the size it was built with and
  ignores every later change.
* **Canvases ask for their colours when they draw.** They hold no
  copies, so a theme change is a redraw, not a rebuild.

Settings are stored per user through ``QSettings`` - on Windows in the
registry under ``HKCU\\Software\\DAPLIS\\daplis-rtp`` - so two people
sharing a machine keep their own.

"""

import copy
from dataclasses import dataclass, replace
from typing import Dict, List, Tuple

from PyQt5 import QtCore, QtWidgets

# 'QSettings' needs these to find the right corner of the registry, and
# they must be set before the first 'QSettings' is built.
ORGANISATION = "DAPLIS"
APPLICATION = "daplis-rtp"

# The two font sizes the user can move. The interface one is applied to
# the whole application; the plot one is a starting point that the tabs
# scale up on a wide window, as they did before.
UI_FONT_RANGE = (7, 16)
PLOT_FONT_RANGE = (8, 32)

DEFAULT_UI_FONT_SIZE = 10
DEFAULT_PLOT_FONT_SIZE = 16

# How many series colours a theme carries. Five is what the application
# actually draws - board 1, board 2, the histogram, and the two MZI
# pixels - with one spare, so that a new trace need not mean a new
# theme.
N_SERIES = 5


@dataclass(frozen=True)
class Theme:
    """A complete look: window, controls and plots together.

    Frozen because a theme is a value, not a thing that is edited. The
    user's changes are kept separately, as overrides, and applied with
    ``dataclasses.replace`` when the effective theme is built - so
    "reset to preset" is throwing the overrides away rather than
    reconstructing anything.

    """

    key: str
    name: str
    # 'dark' or 'light'. Picks which of qdarkstyle's two palettes the
    # controls are drawn with; everything else here is ours.
    base: str

    # --- interface -------------------------------------------------
    window: str
    surface: str
    text: str
    muted: str
    accent: str
    ok: str
    warn: str
    error: str

    # --- plots -----------------------------------------------------
    figure_bg: str
    axes_bg: str
    # Ticks and the axis labels - everything that is read as text.
    axes_fg: str
    # The box around the data. Separate from the text because several
    # of the ported styles depend on the difference: Blueprint draws a
    # dim blue frame under bright white labels, and Solarized a grey
    # one under slate text. Set it equal to 'axes_fg' for a theme that
    # wants one colour for the lot.
    axes_edge: str
    grid: str
    series: Tuple[str, ...]
    # The dashed line marking the seam between the two sensor halves on
    # the full-sensor plot, and the vertical lines the grouping switch
    # draws. Distinct from the series colours on purpose: they mark the
    # sensor, not the data.
    marker: str

    # --- effects ---------------------------------------------------
    # The glow under the traces, from 'mplcyberpunk'. Good-looking and
    # not free: it redraws each line several times, which is felt on a
    # stream refreshing every 100 ms, so it is a switch rather than a
    # fact of the application.
    glow: bool
    grid_on: bool

    def colour(self, index):
        """Series colour ``index``, wrapping round rather than raising."""
        return self.series[index % len(self.series)]


PRESETS: Dict[str, Theme] = {}


def _preset(theme):
    PRESETS[theme.key] = theme
    return theme


# Defined dark first, then light, because that is the order they are
# offered in: the menu puts a separator where the base changes, and a
# list that alternates would need one between every pair.
#
# The six after the first two are ports of the matplotlib styles in
# 'komorebi_mpl' (github.com/rngKomorebi/komorebi_mpl). The figure,
# axes, grid and trace colours are that package's; the window
# chrome - and the three status colours - are chosen here, since a
# matplotlib style sheet has nothing to say about a control panel. The
# status colours deliberately sit outside some of the palettes: a
# warning lamp that matches the data it is warning about is not a
# warning.

# The look the application shipped with: a near-black figure, coral
# traces and the 'mplcyberpunk' glow under them. Kept as the default so
# that an existing user opens the new version to the application they
# know.
_preset(
    Theme(
        key="cyberpunk",
        name="Cyberpunk",
        base="dark",
        window="#14181f",
        surface="#1b212b",
        text="#e3e9f2",
        muted="#8c97a8",
        accent="#08f7fe",
        ok="#00e676",
        warn="#ffc400",
        error="#ff5370",
        figure_bg="#0d0f14",
        axes_bg="#0d0f14",
        axes_fg="#c7d0dd",
        axes_edge="#c7d0dd",
        grid="#2a3140",
        series=("#f48383", "#08f7fe", "#fe53bb", "#f5d300", "#00ff9f"),
        marker="#00b8b8",
        glow=True,
        grid_on=False,
    )
)

# The same dark window without the glow. Every redraw is one draw, so
# this is the one to use when a stream is refreshing as fast as the
# files arrive.
_preset(
    Theme(
        key="midnight",
        name="Midnight",
        base="dark",
        window="#19232d",
        surface="#222b35",
        text="#dfe4ec",
        muted="#8a94a3",
        accent="#4d9de0",
        ok="#7fd18b",
        warn="#e7c26b",
        error="#e06c75",
        figure_bg="#19232d",
        axes_bg="#19232d",
        axes_fg="#d8dee9",
        axes_edge="#d8dee9",
        grid="#36404e",
        series=("#e06c75", "#61afef", "#98c379", "#e5c07b", "#c678dd"),
        marker="#56b6c2",
        glow=False,
        grid_on=True,
    )
)

# komorebi_mpl's 'night_wave': synthwave neon on a violet ground. The
# only other theme that earns the glow, because the palette was built
# for it.
_preset(
    Theme(
        key="night_wave",
        name="Night wave",
        base="dark",
        window="#221d2f",
        surface="#382c47",
        text="#ffffff",
        muted="#9a8fb0",
        accent="#eb67f5",
        ok="#44d492",
        warn="#f5eb67",
        error="#fa233e",
        figure_bg="#221d2f",
        axes_bg="#221d2f",
        axes_fg="#f2f2f2",
        axes_edge="#bfbfbf",
        grid="#aac7df",
        series=("#eb67f5", "#88f7e2", "#44d492", "#f5eb67", "#ffa15c"),
        # The grid blue: the one colour in the palette that is not a
        # neon, so a boundary line drawn in it stays a boundary line.
        marker="#aac7df",
        glow=True,
        grid_on=True,
    )
)

# komorebi_mpl's 'blueprint': a CAD drawing. White and ice-blue lines
# on deep navy, with the frame a dimmer blue than the labels - which is
# the whole reason the axis colour is two fields.
_preset(
    Theme(
        key="blueprint",
        name="Blueprint",
        base="dark",
        window="#0d1f3c",
        surface="#142848",
        text="#e8f1fa",
        muted="#b8d4ea",
        accent="#7ec8e3",
        ok="#7ec8e3",
        warn="#f0a030",
        error="#ff6b6b",
        figure_bg="#0d1f3c",
        axes_bg="#0d1f3c",
        axes_fg="#e8f1fa",
        axes_edge="#3a6186",
        grid="#3a6186",
        series=("#f0f4f8", "#7ec8e3", "#a3d9ff", "#4fa3c5", "#c8e6f5"),
        marker="#60b0d4",
        glow=False,
        grid_on=True,
    )
)

# Maximum separation between the data and everything else: pure black,
# white axes, and series colours chosen to stay apart both for normal
# vision and for the common forms of colour blindness.
_preset(
    Theme(
        key="contrast",
        name="High contrast",
        base="dark",
        window="#000000",
        surface="#121212",
        text="#ffffff",
        muted="#b0b0b0",
        accent="#ffd400",
        ok="#00e676",
        warn="#ffd400",
        error="#ff5252",
        figure_bg="#000000",
        axes_bg="#000000",
        axes_fg="#ffffff",
        axes_edge="#ffffff",
        grid="#555555",
        series=("#ffffff", "#ffd400", "#00e5ff", "#ff6ec7", "#7cff00"),
        marker="#00e5ff",
        glow=False,
        grid_on=True,
    )
)

# For a bright room, and for a plot that is going to be printed or
# pasted into a document - a white figure needs no editing afterwards.
_preset(
    Theme(
        key="daylight",
        name="Daylight",
        base="light",
        window="#f0f2f5",
        surface="#ffffff",
        text="#1c2430",
        muted="#5b6675",
        accent="#1565c0",
        ok="#2e7d32",
        warn="#ef6c00",
        error="#c62828",
        figure_bg="#ffffff",
        axes_bg="#ffffff",
        axes_fg="#1c2430",
        axes_edge="#1c2430",
        grid="#d4d9e0",
        series=("#c0392b", "#1565c0", "#2e7d32", "#d35400", "#6a1b9a"),
        marker="#00838f",
        glow=False,
        grid_on=True,
    )
)

# komorebi_mpl's own: sunlight through a forest canopy. Deep gold,
# forest green and sky blue on parchment.
_preset(
    Theme(
        key="komorebi",
        name="Komorebi",
        base="light",
        window="#f0ede2",
        surface="#faf8f0",
        text="#2c2416",
        muted="#6b6252",
        accent="#c8860a",
        ok="#2d6a4f",
        warn="#c8860a",
        error="#9b2335",
        figure_bg="#faf8f0",
        axes_bg="#faf8f0",
        axes_fg="#2c2416",
        axes_edge="#5a5040",
        grid="#c8b898",
        series=("#c8860a", "#2d6a4f", "#4a86b8", "#a0522d", "#6baa25"),
        # The dusk lavender that ends the cycle: nothing else in the
        # palette is close to it.
        marker="#8b7bc8",
        glow=False,
        grid_on=True,
    )
)

# komorebi_mpl's 'earth': terracotta, rust, olive and sage on aged
# paper, with the axes a shade darker than the figure around them.
_preset(
    Theme(
        key="earth",
        name="Earth",
        base="light",
        window="#ede4ce",
        surface="#f5ecd7",
        text="#2c1810",
        muted="#6b5540",
        accent="#9b2335",
        ok="#5e7a28",
        warn="#d4622a",
        error="#9b2335",
        figure_bg="#f5ecd7",
        axes_bg="#ede0c8",
        axes_fg="#2c1810",
        axes_edge="#a08060",
        grid="#c8b898",
        series=("#9b2335", "#d4622a", "#5e7a28", "#8b5e3c", "#c9984a"),
        marker="#4a7462",
        glow=False,
        grid_on=True,
    )
)

# Ethan Schoonover's Solarized, by way of komorebi_mpl. The low
# contrast between the slate text and the cream ground is the point of
# it, not an oversight.
_preset(
    Theme(
        key="solarized",
        name="Solarized",
        base="light",
        window="#eee8d5",
        surface="#fdf6e3",
        text="#586e75",
        muted="#93a1a1",
        accent="#268bd2",
        ok="#859900",
        warn="#b58900",
        error="#dc322f",
        figure_bg="#fdf6e3",
        axes_bg="#eee8d5",
        axes_fg="#657b83",
        axes_edge="#93a1a1",
        grid="#d3ccb8",
        series=("#268bd2", "#dc322f", "#859900", "#d33682", "#2aa198"),
        marker="#b58900",
        glow=False,
        grid_on=True,
    )
)

# komorebi_mpl's 'daplis': this package's own house palette, anchored on
# rebeccapurple and darkorange and chosen to stay legible for the common
# forms of colour blindness. The one to export a figure in.
_preset(
    Theme(
        key="daplis",
        name="Daplis (publication)",
        base="light",
        window="#f2f2f2",
        surface="#ffffff",
        text="#1a1a1a",
        muted="#5a5a5a",
        accent="#663399",
        ok="#008080",
        warn="#ff8c00",
        error="#8b0000",
        figure_bg="#ffffff",
        axes_bg="#ffffff",
        axes_fg="#000000",
        axes_edge="#000000",
        grid="#bfbfbf",
        series=("#663399", "#ff8c00", "#008080", "#fa8072", "#483d8b"),
        marker="#cd5c5c",
        glow=False,
        grid_on=True,
    )
)

DEFAULT_PRESET = "cyberpunk"

# Overrides are stored by field name, but three of the fields are not
# colours the user can pick - they identify the preset itself, and a
# stored override for one of them would survive a preset change and
# make the dialog disagree with what is drawn.
UNOVERRIDABLE = ("key", "name", "base")


def preset_names():
    """``(key, display name)`` for every preset, in the order defined."""
    return [(key, theme.name) for key, theme in PRESETS.items()]


class ThemeManager(QtCore.QObject):
    """The live theme, the user's changes to it, and who to tell.

    One of these exists per process - see :func:`theme_manager`. It is a
    ``QObject`` for one reason: it emits a signal. Everything that draws
    connects to :attr:`changed` and redraws itself, which is what makes
    a colour picked in the Preferences dialog show up on the plot while
    the dialog is still open.

    """

    changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._preset_key = DEFAULT_PRESET
        # Only what the user has actually changed, keyed by field name.
        # Keeping it separate from the theme is what lets a preset be
        # swapped underneath a custom accent colour, and what makes
        # 'reset' a one-liner.
        self._overrides: Dict[str, object] = {}
        self._ui_font_size = DEFAULT_UI_FONT_SIZE
        self._plot_font_size = DEFAULT_PLOT_FONT_SIZE
        self._settings = QtCore.QSettings(ORGANISATION, APPLICATION)
        self.load()

    # -- the effective theme ------------------------------------------

    @property
    def preset_key(self):
        return self._preset_key

    @property
    def theme(self):
        """The preset with the user's overrides laid over it."""
        base = PRESETS.get(self._preset_key, PRESETS[DEFAULT_PRESET])
        if not self._overrides:
            return base
        return replace(base, **self._overrides)

    @property
    def ui_font_size(self):
        return self._ui_font_size

    @property
    def plot_font_size(self):
        return self._plot_font_size

    def overrides(self):
        """A copy, so a caller editing it cannot change the theme."""
        return copy.deepcopy(self._overrides)

    def is_overridden(self, name):
        return name in self._overrides

    # -- changing it ---------------------------------------------------

    def set_preset(self, key, keep_overrides=False):
        """Switch preset.

        The overrides are dropped by default, and that is deliberate:
        picking a new preset and getting the last one's accent back is
        the surprising behaviour, not the helpful one.

        """
        if key not in PRESETS:
            return
        self._preset_key = key
        if not keep_overrides:
            self._overrides.clear()
        self._emit()

    def set_override(self, name, value):
        """Override one field of the preset, or clear it with ``None``."""
        if name in UNOVERRIDABLE:
            return
        if value is None:
            self._overrides.pop(name, None)
        else:
            self._overrides[name] = value
        self._emit()

    def set_series_colour(self, index, colour):
        """Override one trace colour, leaving the others alone."""
        series: List[str] = list(self.theme.series)
        if not 0 <= index < len(series):
            return
        series[index] = colour
        self._overrides["series"] = tuple(series)
        self._emit()

    def set_ui_font_size(self, points):
        self._ui_font_size = _clamp(points, UI_FONT_RANGE)
        self._emit()

    def set_plot_font_size(self, points):
        self._plot_font_size = _clamp(points, PLOT_FONT_RANGE)
        self._emit()

    def reset(self):
        """Back to the shipped defaults, overrides and fonts included."""
        self._preset_key = DEFAULT_PRESET
        self._overrides.clear()
        self._ui_font_size = DEFAULT_UI_FONT_SIZE
        self._plot_font_size = DEFAULT_PLOT_FONT_SIZE
        self._emit()

    def _emit(self):
        self.save()
        self.changed.emit()

    # -- persistence ---------------------------------------------------

    def load(self):
        """Read the stored settings, ignoring anything unrecognised.

        A stored value that no longer names a field - a preset that was
        renamed, a colour written by a newer version - is skipped rather
        than raising. A settings file is not something the user can
        easily repair, so it must never be able to stop the application
        opening.

        """
        s = self._settings
        s.beginGroup("theme")
        key = s.value("preset", DEFAULT_PRESET, type=str)
        self._preset_key = key if key in PRESETS else DEFAULT_PRESET
        self._ui_font_size = _clamp(
            s.value("ui_font_size", DEFAULT_UI_FONT_SIZE, type=int),
            UI_FONT_RANGE,
        )
        self._plot_font_size = _clamp(
            s.value("plot_font_size", DEFAULT_PLOT_FONT_SIZE, type=int),
            PLOT_FONT_RANGE,
        )

        self._overrides.clear()
        fields = set(Theme.__dataclass_fields__)
        s.beginGroup("overrides")
        for name in s.childKeys():
            if name not in fields or name in UNOVERRIDABLE:
                continue
            if name in ("glow", "grid_on"):
                self._overrides[name] = s.value(name, type=bool)
            elif name == "series":
                stored = s.value(name, type=str)
                colours = tuple(
                    part for part in str(stored).split(",") if part
                )
                if colours:
                    self._overrides[name] = colours
            else:
                self._overrides[name] = s.value(name, type=str)
        s.endGroup()
        s.endGroup()

    def save(self):
        s = self._settings
        s.beginGroup("theme")
        s.setValue("preset", self._preset_key)
        s.setValue("ui_font_size", self._ui_font_size)
        s.setValue("plot_font_size", self._plot_font_size)
        # Cleared rather than merged: an override the user has just
        # removed has to leave the stored settings too, or it comes
        # back on the next start.
        s.remove("overrides")
        s.beginGroup("overrides")
        for name, value in self._overrides.items():
            if name == "series":
                s.setValue(name, ",".join(value))
            else:
                s.setValue(name, value)
        s.endGroup()
        s.endGroup()
        s.sync()

    # -- applying it ---------------------------------------------------

    def apply_to_app(self, app=None):
        """Put the current theme on the application.

        The font goes on the ``QApplication`` rather than on the
        widgets, so that every widget built before or after this call
        picks it up. That is the whole reason nothing in the package
        calls ``setFont`` any more.

        """
        app = app or QtWidgets.QApplication.instance()
        if app is None:
            return
        font = app.font()
        font.setPointSize(self._ui_font_size)
        app.setFont(font)
        app.setStyleSheet(self.stylesheet())

    def stylesheet(self):
        """qdarkstyle for the controls, our own rules on top.

        qdarkstyle is kept because it styles the sixty-odd widget
        classes Qt ships and nobody wants to write that. What it does
        not know about is this application's accent colour and the
        handful of named widgets - the tab title, the hint line, the
        log - that need to look different from their neighbours.

        """
        theme = self.theme
        try:
            import qdarkstyle

            palette = (
                qdarkstyle.LightPalette
                if theme.base == "light"
                else qdarkstyle.DarkPalette
            )
            base = qdarkstyle.load_stylesheet(
                qt_api="pyqt5", palette=palette
            )
        except Exception:
            # An application with no stylesheet is plain, not broken -
            # much better than one that will not start because a
            # styling package changed its API.
            base = ""
        return base + _OVERLAY_QSS.format(
            accent=theme.accent,
            text=theme.text,
            muted=theme.muted,
            surface=theme.surface,
            ok=theme.ok,
            warn=theme.warn,
            error=theme.error,
        )

    # -- matplotlib ----------------------------------------------------

    def mpl_rc(self, fontsize=None):
        """The theme as matplotlib rcParams.

        Handed to ``rc_context`` around a draw rather than pushed into
        the global ``rcParams``. The old code called ``plt.style.use``
        at import time and ``plt.rcParams.update`` from inside draws,
        which meant the last canvas to be built decided how all of them
        looked.

        """
        theme = self.theme
        size = self._plot_font_size if fontsize is None else fontsize
        return {
            "figure.facecolor": theme.figure_bg,
            "figure.edgecolor": theme.figure_bg,
            "savefig.facecolor": theme.figure_bg,
            "savefig.edgecolor": theme.figure_bg,
            "axes.facecolor": theme.axes_bg,
            "axes.edgecolor": theme.axes_edge,
            "axes.labelcolor": theme.axes_fg,
            "axes.titlecolor": theme.axes_fg,
            "axes.grid": theme.grid_on,
            "axes.axisbelow": True,
            "grid.color": theme.grid,
            "grid.alpha": 0.45,
            "grid.linestyle": "--",
            "grid.linewidth": 0.8,
            "text.color": theme.axes_fg,
            "xtick.color": theme.axes_fg,
            "ytick.color": theme.axes_fg,
            "xtick.labelcolor": theme.axes_fg,
            "ytick.labelcolor": theme.axes_fg,
            "font.size": size,
            "axes.labelsize": size,
            "xtick.labelsize": size,
            "ytick.labelsize": size,
            "legend.fontsize": size,
            "legend.facecolor": theme.axes_bg,
            "legend.edgecolor": theme.axes_fg,
            "lines.linewidth": 1.6,
            "lines.markersize": 4,
        }


def _clamp(value, bounds):
    low, high = bounds
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = low
    return max(low, min(high, value))


# Rules qdarkstyle has no opinion about. Kept short on purpose: every
# rule here is one more thing that can disagree with the base sheet.
_OVERLAY_QSS = """
QTabBar::tab:selected {{
    border-bottom: 2px solid {accent};
    color: {text};
}}
QTabBar::tab:!selected {{
    color: {muted};
}}
QGroupBox::title {{
    color: {accent};
}}
QLabel#tabTitle {{
    color: {text};
    font-weight: bold;
}}
QLabel#tabHint {{
    color: {muted};
}}
QLabel#readoutValue {{
    color: {accent};
    font-weight: bold;
}}
QPlainTextEdit#logView, QLabel#monoValue {{
    font-family: "Consolas", "DejaVu Sans Mono", monospace;
}}
QPushButton#primaryAction {{
    border: 1px solid {accent};
    font-weight: bold;
}}
QPushButton#primaryAction:hover {{
    background-color: {surface};
    border: 1px solid {accent};
}}
QLabel[ledState="ok"] {{ color: {ok}; }}
QLabel[ledState="warn"] {{ color: {warn}; }}
QLabel[ledState="error"] {{ color: {error}; }}
QLabel[ledState="idle"] {{ color: {muted}; }}
"""


_MANAGER = None


def theme_manager():
    """The process-wide theme.

    Built on first use rather than at import, because ``QSettings``
    wants the organisation and application names set first, and because
    a module that touches Qt state at import time is a module that
    cannot be imported by a test.

    """
    global _MANAGER
    if _MANAGER is None:
        QtCore.QCoreApplication.setOrganizationName(ORGANISATION)
        QtCore.QCoreApplication.setApplicationName(APPLICATION)
        _MANAGER = ThemeManager()
    return _MANAGER


def current_theme():
    """Shorthand for ``theme_manager().theme``."""
    return theme_manager().theme
