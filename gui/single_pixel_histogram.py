"""Module for plotting single pixel histograms.

Main usage is checking the homogenit of the LinoSPAD2 output.

"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar,
)
import numpy as np
from functions.unpack import unpack_bin
import matplotlib.pyplot as plt
import sys


class HistCanvas(QWidget):
    def __init__(self, width=7, height=4, dpi=100):
        """Figure widget initialization.

        Figure is intialized with the matplotlib navigation panel for
        more control over the plot.

        Parameters
        ----------
        width : int, optional
            Figure widget width, by default 7
        height : int, optional
            Figure widget height, by default 4
        dpi : int, optional
            Figure widget dpi, by default 100
        """
        super().__init__()

        # figure initialization
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axes = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.figure.subplots_adjust(
            left=0.085, right=0.995, top=0.935, bottom=0.125
        )

        # creating a Vertical Box layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

        self._setplotparameters()

    def _setplotparameters(self):
        """Figure parameters manipulation.

        Sets font size, axes labels, width and orientation of axes ticks.

        """
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

    def _plot_hist(self, file, pixel, timestamps, board_number, fw_ver):
        """Plot histogram.

        Parameters
        ----------
        file : str
            Data file address.
        pixel : int
            Pixel number to plot a histogram for.
        timestamps : int
            Number of timestamps per pixel/TDC per acquisition cycle.
        board_number : str
            LinoSPAD2 daughterboard number.
        fw_ver : str
            LinoSPAD2 firmware version.
        """
        data = unpack_bin(file, board_number, fw_ver, timestamps)

        bins = np.arange(0, 4e9, 17.867 * 1e6)  # bin size of 17.867 us

        self.axes.cla()

        if fw_ver == "2208":
            self.axes.hist(data[pixel], bins=bins, color="teal")
        elif fw_ver[:-1] == "2212":
            if fw_ver == "2212s":
                pix_coor = np.arange(256).reshape(4, 64).T
            elif fw_ver == "2212b":
                pix_coor = np.arange(256).reshape(64, 4)
            tdc, pix = np.argwhere(pix_coor == pixel)[0]
            ind = np.where(data[tdc].T[0] == pix)[0]
            ind1 = np.where(data[tdc].T[1][ind] > 0)[0]
            data_to_plot = data[tdc].T[1][ind[ind1]]

            self.axes.hist(data_to_plot, bins=bins, color="teal")
        else:
            print("\nFirmware version is not recognized, exiting.")
            sys.exit()

        self.axes.set_xlabel("Time [ps]")
        self.axes.set_ylabel("# of timestamps [-]")
        self.axes.set_title("Pixel {}, 17.867 us bin".format(pixel))
        self.axes.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        self.canvas.draw()
        self.canvas.flush_events()
