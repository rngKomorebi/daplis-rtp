"""Module for plotting the data in the real-time plotting tab.

Plots the data provided as number of timestamps vs pixel number. Options
for changing the plot scale (linear or logarithmic) and plotting of 
vertical lines at positions 64, 128, and 192 are provided. The figure
widget is generated with the matplotlib navigation bar for additional
control over the plot.

"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar,
)
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class PltCanvas(QWidget):
    def __init__(self, parent=None, width=7, height=4, dpi=100):
        """Creation of the figure widget.

        The widget is created along with the bar with options.

        Parameters
        ----------
        width : int, optional
            Figure widget width, by default 7
        height : int, optional
            Figure widget height, by default 4
        dpi : int, optional
            Figure widget dpi, by default 100
        """
        super(PltCanvas, self).__init__(parent)
        # a figure instance to plot on
        self.figure = Figure(figsize=(width, height), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(
            left=0.15, right=0.97, top=0.96, bottom=0.17
        )

        # creating a Vertical Box layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

        self.setplotparameters()

    def setplotparameters(self):
        """Figure parameters manipulation.

        Set font size, axes labels. Set width and orientation of axes
        ticks.

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

    def setPlotData(self, xdataplot, yplotdata, xLim, grouping: bool = False):
        """_summary_

        Parameters
        ----------
        xdataplot : array
            Data for the x axis: pixel numbers.
        yplotdata : array-like
            Data for the y axis: number of timestamps.
        xLim : list
            Limits for the x axis.
        grouping : bool, optional
            Switch for plotting vertical lines at positiong 64, 128, and
            192, by default False.
        """
        self.ax.cla()
        self.ax.plot(yplotdata, "-o", color="indianred")
        if grouping is True:
            self.ax.vlines(
                x=(64, 128, 192), ymin=0, ymax=yplotdata.max(), color="teal"
            )
        self.ax.relim()
        self.ax.autoscale_view()
        self.setplotparameters()
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
