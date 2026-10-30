"""The one plot widget every tab draws on.

There used to be three of these - ``plot_figure``, ``plot_figure_dual``
and ``plot_figure_MZI`` - which between them were the same eighty lines
copied out three times, with the differences that mattered (a boundary
line here, a second y-axis there) buried among the differences that did
not (one called its styling method ``setplotparameters``, another
``_setplotparameters``). A change to the look had to be made three
times and usually was not.

Here there is one base class holding the figure, the toolbar, the
sizing and the theme, and one small subclass per kind of plot saying
only what that plot draws.

The pattern is *store, then render*. A tab hands in data; the canvas
keeps it and draws. When the theme changes the canvas draws the same
data again. That is what makes a colour picked in Preferences appear on
a plot that was drawn ten minutes ago, and it is why the canvases hold
no copies of theme colours.

"""

import matplotlib

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtWidgets

from daplis_rtp.gui.layout import MIN_CANVAS_HEIGHT, SPACING
from daplis_rtp.gui.theme import theme_manager

# The readout the navigation toolbar writes while the cursor is over the
# axes: the pixel number under the mouse, which is the quickest way to
# tell which pixel a peak belongs to. matplotlib writes it as two lines,
# the coordinates and the colour beneath them.
TOOLBAR_READOUT_SAMPLE = (
    "(x, y) = (255.0, 2000.0)\n[0.957, 0.514, 0.514, 0.0857]"
)

# How far the plot font is allowed to grow with the window, and the
# canvas widths between which it does so. The old tabs each carried
# their own copy of this interpolation, keyed to the width of the whole
# window; keyed to the canvas it belongs to, it no longer changes when a
# control column is added beside it.
FONT_GROWTH = 2.2
FONT_WIDTH_RANGE = (640, 3000)

# A resize arrives as a stream of events, and a redraw is expensive
# enough that doing one per event makes dragging a window edge crawl.
# One redraw, once the dragging stops.
RESIZE_SETTLE_MS = 120


def toolbar_min_width(toolbar, sample=TOOLBAR_READOUT_SAMPLE):
    """Width at which every toolbar button and the readout still fit.

    A ``QToolBar`` squeezed below its contents hides them behind a '>>'
    overflow button rather than forcing its parent wider - its own
    ``minimumSizeHint`` is barely wider than that button - and the
    coordinate readout, being the widest item, is the first to go. It is
    also empty until the cursor reaches the axes, so nothing in the
    toolbar's size hints reserves room for it while it is not needed.

    The width is measured rather than assumed: the readout is asked how
    wide it would be with a full reading in it, which picks up the
    application's font and any padding the style adds, both of which
    differ between machines.

    """
    label = getattr(toolbar, "locLabel", None)
    readout = 0
    if label is not None:
        previous = label.text()
        label.setText(sample)
        readout = label.sizeHint().width()
        label.setText(previous)

    buttons = 0
    for child in toolbar.children():
        if not isinstance(child, QtWidgets.QWidget) or child is label:
            continue
        # The overflow button is the thing we are sizing to avoid
        if child.objectName() == "qt_toolbar_ext_button":
            continue
        buttons += child.sizeHint().width()

    # Layout margins, the spacing between the buttons, and the frame
    return buttons + readout + 32


class BaseCanvas(QtWidgets.QWidget):
    """A matplotlib figure, its toolbar, and the current theme.

    Subclasses override :meth:`draw_data` to say what to draw, and
    :attr:`x_label` / :attr:`y_label` to say what the axes are. Nothing
    else should need overriding.

    """

    x_label = ""
    y_label = ""
    # A second y-axis on the right, for the tabs that compare two
    # quantities. Off by default because a twin axis that is never used
    # still draws a second set of ticks.
    twin = False

    def __init__(self, parent=None, width=7, height=4, dpi=100):
        super().__init__(parent)

        # 'constrained' rather than the fixed 'subplots_adjust'
        # fractions the old canvases used. Those were tuned for one font
        # size, so a large plot font - which is exactly what a big
        # window produces - pushed the y-axis label off the edge of the
        # figure. Constrained layout measures the labels instead.
        self.figure = Figure(figsize=(width, height), dpi=dpi,
                             layout="constrained")
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = self.figure.add_subplot(111)
        self.ax2 = self.ax.twinx() if self.twin else None

        box = QtWidgets.QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(SPACING // 2)
        box.addWidget(self.canvas, 1)
        box.addWidget(self.toolbar, 0)

        # Keep the whole toolbar reachable: the pixel number under the
        # cursor is read off it, and it is the first thing a narrow
        # window hides.
        self.setMinimumSize(
            toolbar_min_width(self.toolbar), MIN_CANVAS_HEIGHT
        )

        # What was last handed in, so that a theme change can be drawn
        # rather than waiting for the next data file.
        self._data = None
        self._scale_linear = True
        self._fontsize = theme_manager().plot_font_size

        self._resize_timer = QtCore.QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(RESIZE_SETTLE_MS)
        self._resize_timer.timeout.connect(self._settled)

        theme_manager().changed.connect(self.refresh_theme)
        self.render()

    # -- the theme -----------------------------------------------------

    @property
    def theme(self):
        return theme_manager().theme

    @property
    def fontsize(self):
        return self._fontsize

    def rc(self):
        return theme_manager().mpl_rc(self._fontsize)

    def refresh_theme(self):
        """Redraw in the new theme, keeping whatever is on the plot."""
        self._fontsize = self._grown_fontsize()
        self.render()

    # -- drawing -------------------------------------------------------

    def set_data(self, data):
        """Hand in what to draw, and draw it."""
        self._data = data
        self.render()

    def clear(self):
        self._data = None
        self.render()

    def render(self):
        """Draw the stored data in the current theme.

        Everything is drawn inside one ``rc_context``: matplotlib reads
        the parameters when an artist is *created*, so styling has to
        wrap the drawing rather than follow it. The old code pushed
        values into the global ``plt.rcParams`` from inside each draw,
        which meant whichever canvas drew last decided how the others
        looked.

        """
        with matplotlib.rc_context(self.rc()):
            self.ax.clear()
            if self.ax2 is not None:
                self.ax2.clear()
                # 'clear' resets a twin's label back to the left-hand
                # side - the ticks stay on the right, but the words end
                # up on top of the primary axis's label. Only the label
                # needs putting back, and only after a clear.
                self.ax2.yaxis.set_label_position("right")
                self.ax2.yaxis.set_ticks_position("right")
            # Before the data, not after: changing the scale installs
            # that scale's default locator and formatter, so a scale set
            # afterwards throws away the scientific notation the draw
            # asked for - which is how a rate of 430000 came to be
            # labelled in full rather than as 4.3 against a '1e5'.
            self._apply_scale()
            if self._data is not None:
                self.draw_data(self._data)
            self.style_axes()
        self._paint_frame()
        self.canvas.draw_idle()

    def draw_data(self, data):
        """What this kind of plot draws. Overridden by every subclass."""
        raise NotImplementedError

    def style_axes(self):
        """Ticks, spines and labels, identical on every plot.

        Inward ticks on all four sides with a minor set between them:
        the convention the group's published figures use, and the reason
        a plot lifted straight out of the application needs no editing.

        """
        theme = self.theme
        axes = [self.ax] + ([self.ax2] if self.ax2 is not None else [])

        self.ax.set_xlabel(self.x_label)
        self.ax.set_ylabel(self.y_label)

        for ax in axes:
            ax.tick_params(which="both", width=1.6, direction="in",
                           colors=theme.axes_fg)
            ax.tick_params(which="major", length=7, direction="in",
                           labelsize=self._fontsize)
            ax.tick_params(which="minor", length=4, direction="in",
                           labelsize=self._fontsize)
            for side in ("top", "bottom", "left", "right"):
                ax.spines[side].set_linewidth(1.6)
                ax.spines[side].set_color(theme.axes_edge)
            ax.set_facecolor(theme.axes_bg)

        # Ticks on all four sides, but only on the primary axes: the
        # twin owns the right-hand side, and asking for both puts two
        # sets of ticks on top of each other.
        if self.ax2 is None:
            self.ax.yaxis.set_ticks_position("both")
        self.ax.xaxis.set_ticks_position("both")

        if theme.grid_on:
            self.ax.grid(True, color=theme.grid, alpha=0.45,
                         linestyle="--", linewidth=0.8)

    def glow(self, gradient=True):
        """The look the application is known for, when the theme wants it.

        Off by default in every theme but "Cyberpunk", because it is not
        free: each line is redrawn several times over, which is felt on
        a stream refreshing as fast as the files arrive.

        """
        if not self.theme.glow:
            return
        try:
            import mplcyberpunk

            mplcyberpunk.make_lines_glow(self.ax, diff_linewidth=1.1)
            if gradient:
                mplcyberpunk.add_gradient_fill(
                    self.ax, alpha_gradientglow=0.3
                )
        except Exception:
            # The glow is decoration. A version of mplcyberpunk that
            # cannot fill under a log axis, or cannot be imported at
            # all, must not stop the data being drawn.
            pass

    def scientific_y(self, *axes):
        """Label the y-axis as '4.3' against a '1e5', where that applies.

        Photon rates run to a few million, and an axis labelled in full
        needs more room beside the plot than the plot can spare.

        Silently skipped on a logarithmic axis: ``ticklabel_format``
        only understands the linear formatter and raises otherwise,
        which used to mean that new data arriving while the plot was on
        a log scale took the stream down with an ``AttributeError``.

        """
        if not self._scale_linear:
            return
        for ax in axes or (self.ax,):
            ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

    def _paint_frame(self):
        """Colour the parts of the figure no artist covers."""
        theme = self.theme
        self.figure.set_facecolor(theme.figure_bg)
        self.figure.set_edgecolor(theme.figure_bg)

    # -- scale ---------------------------------------------------------

    def set_scale_linear(self, linear):
        """Switch the left y-axis between linear and logarithmic."""
        self._scale_linear = bool(linear)
        self._apply_scale()
        self.canvas.draw_idle()

    def _apply_scale(self):
        scale = "linear" if self._scale_linear else "log"
        self.ax.set_yscale(scale)
        if self.ax2 is not None:
            self.ax2.set_yscale(scale)

    # -- size ----------------------------------------------------------

    def resizeEvent(self, event):
        """Grow the plot font with the plot, once the dragging stops.

        Each tab used to do this for itself, off the width of the whole
        window and with the same four magic numbers copied out five
        times. Off the canvas's own width it is both in one place and
        correct: adding a control column beside the plot no longer
        changes the font on it.

        """
        super().resizeEvent(event)
        self._resize_timer.start()

    def _settled(self):
        grown = self._grown_fontsize()
        if abs(grown - self._fontsize) < 0.5:
            return
        self._fontsize = grown
        self.render()

    def _grown_fontsize(self):
        base = theme_manager().plot_font_size
        low, high = FONT_WIDTH_RANGE
        width = max(low, min(high, self.canvas.width()))
        share = (width - low) / float(high - low)
        return base * (1 + share * (FONT_GROWTH - 1))
