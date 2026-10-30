"""Module for plotting data in the real-time plotting tab.

Plots the data provided as number of timestamps vs. pixel number. Options
for changing the plot scale (linear or logarithmic) and plotting of
vertical lines at positions 64, 128, and 192 are provided. The figure
widget is generated with the matplotlib navigation bar for additional
control over the plot.

"""

import matplotlib.pyplot as plt
import mplcyberpunk
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout, QWidget

# The readout the navigation toolbar writes while the cursor is over the
# axes: the pixel number under the mouse, which is the quickest way to
# tell which pixel a peak belongs to. matplotlib writes it as two lines,
# the coordinates and the colour beneath them.
TOOLBAR_READOUT_SAMPLE = (
    "(x, y) = (255.0, 2000.0)\n[0.957, 0.514, 0.514, 0.0857]"
)

# Below this the plot is not worth looking at. Kept at the largest
# value that costs the window no height of its own: above 240 the
# canvas, rather than the controls beside it, starts deciding how tall
# the application opens.
MIN_CANVAS_HEIGHT = 240


def toolbar_min_width(toolbar, sample=TOOLBAR_READOUT_SAMPLE):
    """Width at which every toolbar button and the readout still fit.

    A QToolBar squeezed below its contents hides them behind a '>>'
    overflow button rather than forcing its parent wider - its own
    'minimumSizeHint' is barely wider than that button - and the
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
        if not isinstance(child, QWidget) or child is label:
            continue
        # The overflow button is the thing we are sizing to avoid
        if child.objectName() == "qt_toolbar_ext_button":
            continue
        buttons += child.sizeHint().width()

    # Layout margins, the spacing between the buttons, and the frame
    return buttons + readout + 32


def reserve_toolbar_width(frame, canvas):
    """Make the plot's frame wide enough to keep the whole toolbar.

    The canvas carries its own minimum width, but between it and the
    window sit two frames whose layouts do not pass that minimum all the
    way up, so the plot is squeezed and the toolbar folds its readout
    away regardless. An explicit minimum on the frame is respected, and
    is what actually reaches the window.

    """
    margins = frame.layout().contentsMargins()
    frame.setMinimumWidth(
        canvas.minimumWidth() + margins.left() + margins.right() + 2
    )


class PltCanvas(QWidget):
    def __init__(self, parent=None, width=7, height=4, dpi=100):
        """Creation of the figure widget.

        The widget is created with the bar with options.

        Parameters
        ----------
        width : int, optional
            Figure widget width, by default 7.
        height : int, optional
            Figure widget height, by default 4.
        dpi : int, optional
            Figure widget dpi, by default 100.
        """
        super(PltCanvas, self).__init__(parent)

        # For 'dark_background' style
        plt.style.use("dark_background")

        # a figure instance to plot on
        self.figure = Figure(figsize=(width, height), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(
            left=0.15, right=0.97, top=0.945, bottom=0.12
        )

        # creating a Vertical Box layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

        # Keep the whole toolbar reachable: the pixel number under the
        # cursor is read off it, and it is the first thing a narrow
        # window hides.
        self.setMinimumSize(
            toolbar_min_width(self.toolbar), MIN_CANVAS_HEIGHT
        )

        self.setplotparameters()

    def setplotparameters(self, fontsize: int = 16):
        """Figure parameters manipulation.

        Set font size, axes labels. Set the width and orientation of the
        axes ticks.

        """
        plt.rcParams.update({"font.size": fontsize})
        self.ax.set_xlabel("Pixel (-)", fontsize=fontsize)
        # self.ax.set_ylabel("# of timestamps (-)", fontsize=fontsize)
        self.ax.set_ylabel("Photon rate (Hz)", fontsize=fontsize)

        self.ax.tick_params(which="both", width=2, direction="in")
        self.ax.tick_params(
            which="major", length=7, direction="in", labelsize=fontsize
        )
        self.ax.tick_params(
            which="minor", length=4, direction="in", labelsize=fontsize
        )
        self.ax.yaxis.set_ticks_position("both")
        self.ax.xaxis.set_ticks_position("both")

        for axis in ["top", "bottom", "left", "right"]:
            self.ax.spines[axis].set_linewidth(2)

    def setPlotData(
        self,
        xdataplot,
        yplotdata,
        xLim,
        grouping: bool = False,
        fontsize: int = 16,
    ):
        """Plot data.

        Plot the provided data while following the state of the axis
        limits and the switch for plotting vertical lines at positions
        64, 128, and 192.

        Parameters
        ----------
        xdataplot : array
            Data for the x-axis: pixel numbers.
        yplotdata : array-like
            Data for the y-axis: number of timestamps.
        xLim : list
            Limits for the x-axis.
        grouping : bool, optional
            Switch for plotting vertical lines at positiong 64, 128, and
            192, by default False.
        """
        self.ax.cla()
        # self.ax.plot(yplotdata, "-o", color="indianred")
        # self.ax.plot(yplotdata, "-o", color="#F5D300")
        self.ax.plot(yplotdata, "-o", color="#f48383")
        if grouping is True:
            self.ax.vlines(
                x=(64, 128, 192), ymin=0, ymax=yplotdata.max(), color="teal"
            )

        # <><><><><><><><><><><><><><><>
        mplcyberpunk.make_lines_glow(self.ax, diff_linewidth=1.1)
        # mplcyberpunk.add_underglow(self.ax)
        # mplcyberpunk.add_glow_effects(self.ax, gradient_fill=True)
        mplcyberpunk.add_gradient_fill(self.ax, alpha_gradientglow=0.3)

        # <><><><><><><><><><><><><><><>

        self.ax.relim()
        self.ax.autoscale_view()
        self.setplotparameters(fontsize)
        self.ax.set_xlim(xLim[0], xLim[1])
        self.ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def setPlotScale(self, scaleLin):
        """Switches plot scale between logarithmic and linear."""
        if scaleLin:
            self.ax.set_yscale("linear")
            self.canvas.draw()
            self.canvas.flush_events()
        else:
            self.ax.set_yscale("log")
            self.canvas.draw()
            self.canvas.flush_events()
