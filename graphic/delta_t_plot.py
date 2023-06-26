from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from tools.calc_diff import calc_diff as cd
import os
from glob import glob
from tools.unpack_data import unpack_calib
import numpy as np
import matplotlib.pyplot as plt


class Delta_tCanvas(QWidget):
    def __init__(self, parent=None, width=7, height=4, dpi=100):
        super(Delta_tCanvas, self).__init__(parent)
        # a figure instance to plot on
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.axes = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=0.15, right=0.97, top=0.96, bottom=0.17)

        # creating a Vertical Box layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

        self._setplotparameters()

    def _setplotparameters(self):
        plt.rcParams.update({"font.size": 12})
        self.axes.set_xlabel("\u0394t [ps]")
        self.axes.set_ylabel("# of timestamps [-]")

        self.axes.tick_params(which="both", width=2, direction="in")
        self.axes.tick_params(which="major", length=7, direction="in")
        self.axes.tick_params(which="minor", length=4, direction="in")
        self.axes.yaxis.set_ticks_position("both")
        self.axes.xaxis.set_ticks_position("both")

        for axis in ["top", "bottom", "left", "right"]:
            self.axes.spines[axis].set_linewidth(2)

    def _plot_delta(
        self, pix1, pix2, timestamps, board_number, range_left, range_right
    ):

        files = glob("*.dat*")
        last_file = max(files, key=os.path.getctime)

        data = unpack_calib(last_file, board_number, timestamps)

        data_pair = np.vstack((data[pix1], data[pix2]))

        deltas = cd(data_pair, timestamps, range_left, range_right)

        bins = np.linspace(np.min(deltas), np.max(deltas), 100)

        self.axes.cla()
        self.axes.hist(deltas, bins=bins, color="salmon")
        self.axes.set_xlabel("\u0394t [ps]")
        self.axes.set_ylabel("# of timestamps [-]")
        self.axes.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        self.canvas.draw()
        self.canvas.flush_events()
