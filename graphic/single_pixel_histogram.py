""" Script for calculating a histogram of a single pixel

"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import glob
import numpy as np
import tools.unpack_data as unpk
import matplotlib.pyplot as plt


class HistCanvas(QWidget):
    def __init__(self, width=7, height=4, dpi=100):
        super().__init__()

        # figure initialization
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axes = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.figure.subplots_adjust(left=0.15, right=0.97, top=0.98, bottom=0.17)

        # creating a Vertical Box layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

        self._setplotparameters()


    def _setplotparameters(self):
        plt.rcParams.update({"font.size": 12})
        self.axes.set_xlabel("Time [ps]")
        self.axes.set_ylabel("# of timestamps [-]")

        self.axes.tick_params(which="both", width=2, direction="in")
        self.axes.tick_params(which="major", length=7, direction="in")
        self.axes.tick_params(which="minor", length=4, direction="in")
        self.axes.yaxis.set_ticks_position("both")
        self.axes.xaxis.set_ticks_position("both")

        for axis in ["top", "bottom", "left", "right"]:
            self.axes.spines[axis].set_linewidth(2)

    def _plot_hist(self, pix, timestamps, board_number):

        file = glob.glob("*.dat*")[0]

        data = unpk.unpack_calib(file, board_number, timestamps)

        bins = np.arange(0, 4e9, 17.867 * 1e6)  # bin size of 17.867 us

        self.axes.cla()
        self.axes.hist(data[pix], bins=bins, color="teal")
        self.axes.set_xlabel("Time [ps]")
        self.axes.set_ylabel("# of timestamps [-]")
        self.axes.set_title("Pixel {} histogram".format(pix))
        self.axes.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        self.canvas.draw()
        self.canvas.flush_events()
