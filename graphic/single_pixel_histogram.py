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


class HistCanvas(QWidget):
    def __init__(self, height=4, width=4, dpi=100):
        super().__init__()

        # figure initialization
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axes = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)
        # self.figure.tight_layout()
        self.figure.subplots_adjust(left=0.17, bottom=0.154, right=0.990, top=0.917)

        # creating a Vertical Box layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

    def _plot_hist(self, pix):

        file = glob.glob("*.dat*")[0]

        data = unpk.unpack_calib(file, board_number="A5", timestamps=512)

        bins = np.arange(0, 4e9, 17.867 * 1e6)  # bin size of 17.867 us

        self.axes.cla()
        self.axes.hist(data[pix], bins=bins, color="teal")
        self.axes.set_xlabel("Time [ps]")
        self.axes.set_ylabel("# of timestamps [-]")
        self.axes.set_title("Pixel {} histogram".format(pix))
        self.axes.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        # self.figure.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()

        # try:
        #     os.chdir("results/single pixel histograms")
        # except Exception:
        #     os.mkdir("results/single pixel histograms")
        #     os.chdir("results/single pixel histograms")
        # plt.savefig("{file}, pixel {pixel}.png".format(file=file, pixel=pix))
        # os.chdir("../..")
