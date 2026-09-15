"""Module for plotting photon count from two chosen pixel in real time.

Unpacks the binary data, finds the two pixels requested and plots the
number of photons registered by the two pixels. x-axis limits are given
by the slider, upper y-axis limit is set as maximum of the two counts
plus 10 percent.

"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from daplis_rtp.gui.plot_figure import MIN_CANVAS_HEIGHT, toolbar_min_width


class PltCanvas_MZI(QWidget):
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
        super(PltCanvas_MZI, self).__init__(parent)

        # For 'dark_background' style
        plt.style.use("dark_background")

        # a figure instance to plot on
        self.figure = Figure(figsize=(width, height), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = self.figure.add_subplot(111)
        self.ax2 = self.ax.twinx()
        self.figure.subplots_adjust(
            left=0.15, right=0.9, top=0.945, bottom=0.12
        )

        # creating a Vertical Box layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

        # Keep the whole toolbar reachable: the coordinates under the
        # cursor are read off it, and they are the first thing a narrow
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
        self.ax.set_xlabel("Time (s)", fontsize=fontsize)
        # self.ax.set_ylabel("# of timestamps (-)", fontsize=fontsize)
        self.ax.set_ylabel("Photon rate (Hz)", fontsize=fontsize)

        self.ax.tick_params(which="both", width=2, direction="in")
        self.ax.tick_params(
            which="major", length=7, direction="in", labelsize=fontsize
        )
        self.ax.tick_params(
            which="minor", length=4, direction="in", labelsize=fontsize
        )
        self.ax2.tick_params(
            which="major", length=7, direction="in", labelsize=fontsize
        )
        self.ax2.tick_params(
            which="minor", length=4, direction="in", labelsize=fontsize
        )
        self.ax.yaxis.set_ticks_position("both")
        self.ax.xaxis.set_ticks_position("both")

        for axis in ["top", "bottom", "left", "right"]:
            self.ax.spines[axis].set_linewidth(2)

    def setPlotData_MZI(
        self, xdataplot, yplotdata1, yplotdata2, xLim, yLim, fontsize: int = 16
    ):
        """Plot data.

        Plot the provided data, applying whichever axis limits were given
        explicitly and autoscaling the rest.

        Parameters
        ----------
        xdataplot : array
            Data for the x-axis: elapsed time in seconds.
        yplotdata1 : array-like
            Data for the left y-axis: photon rate in the first pixel.
        yplotdata2 : array-like
            Data for the right y-axis: photon rate in the second pixel.
        xLim : tuple of (float or None, float or None)
            Lower and upper limits for the x-axis. 'None' for either edge
            leaves that edge autoscaled; the upper edge then sits two
            seconds past the newest point, as it did when only the lower
            edge was adjustable.
        yLim : tuple of (float or None, float or None)
            Lower and upper limits for the y-axis, 'None' for autoscale.
            Both y-axes always share the same limits so the two traces can
            be compared directly.
        fontsize : int, optional
            Font size for the axes, by default 16.
        """
        # self.ax.cla()
        self.ax.plot(xdataplot, yplotdata1, "-o", color="indianred")
        self.ax2.plot(xdataplot, yplotdata2, "-o", color="teal")
        # set_xlim/set_ylim below latch autoscaling off. Switch it back on
        # before measuring, or an edge whose field was cleared back to empty
        # would stay stuck at the last value it was given instead of
        # returning to autoscale.
        self.ax.autoscale(enable=True, axis="both")
        self.ax2.autoscale(enable=True, axis="both")
        self.ax.relim()
        self.ax.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()
        self.setplotparameters(fontsize)

        x_lo, x_hi = xLim
        auto_x_lo, _ = self.ax.get_xlim()
        self.ax.set_xlim(
            auto_x_lo if x_lo is None else x_lo,
            xdataplot[-1] + 2 if x_hi is None else x_hi,
        )

        # Read both axes before setting either: the shared limits have to
        # cover the data on both, so the autoscaled extremes of the pair are
        # what an unset edge falls back to.
        ax1_bottom, ax1_top = self.ax.get_ylim()
        ax2_bottom, ax2_top = self.ax2.get_ylim()
        y_lo, y_hi = yLim
        shared_bottom = (
            min(ax1_bottom, ax2_bottom) if y_lo is None else y_lo
        )
        shared_top = max(ax1_top, ax2_top, 1) if y_hi is None else y_hi
        self.ax.set_ylim(shared_bottom, shared_top)
        self.ax2.set_ylim(shared_bottom, shared_top)
        self.ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        self.ax2.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
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
