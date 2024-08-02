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
            left=0.15, right=0.93, top=0.96, bottom=0.17
        )

        # creating a Vertical Box layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

        self.setplotparameters()

        # Upper ylim for the plot
        self.upper_ylim = 0

    def setplotparameters(self):
        """Figure parameters manipulation.

        Set font size, axes labels. Set the width and orientation of the
        axes ticks.

        """
        plt.rcParams.update({"font.size": 12})
        self.ax.set_xlabel("Pixel [-]")
        self.ax.set_ylabel("# of timestamps [-]")

        self.ax.tick_params(which="both", width=2, direction="in")
        self.ax.tick_params(which="major", length=7, direction="in")
        self.ax.tick_params(which="minor", length=4, direction="in")
        self.ax.yaxis.set_ticks_position("both")
        self.ax.xaxis.set_ticks_position("both")

        for axis in ["top", "bottom", "left", "right"]:
            self.ax.spines[axis].set_linewidth(2)

    def setPlotData_MZI(self, xdataplot, yplotdata1, yplotdata2, xLim, yLim):
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
        # self.ax.cla()
        self.ax.plot(xdataplot, yplotdata1, "-o", color="indianred")
        self.ax2.plot(xdataplot, yplotdata2, "-o", color="teal")
        self.ax.relim()
        self.ax.autoscale_view()
        self.setplotparameters()
        self.ax.set_xlim(xLim, xdataplot[-1] + 2)

        new_ylim = np.max([yplotdata1[-1], yplotdata2[-1]]) * 1.1
        if new_ylim > self.upper_ylim:
            self.upper_ylim = new_ylim

        self.ax.set_ylim(yLim, self.upper_ylim)
        self.ax2.set_ylim(yLim, self.upper_ylim)
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
