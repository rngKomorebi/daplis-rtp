"""Module for plotting single pixel histograms.

The main usage is checking the homogeneity of the LinoSPAD2 output. The
output graph should be flat top.

"""

import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from daplis_rtp.functions.unpack import unpack_bin


class HistCanvas(QWidget):
    def __init__(self, parent=None, width=7, height=4, dpi=100):
        """Figure widget initialization.

        The figure is initialized with the matplotlib navigation panel for
        more control over the plot.

        Parameters
        ----------
        width : int, optional
            Figure widget width, by default 7.
        height : int, optional
            Figure widget height, by default 4.
        dpi : int, optional
            Figure widget dpi, by default 100.
        """
        super(HistCanvas, self).__init__(parent)

        # figure initialization
        self.figure = Figure(figsize=(width, height), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)

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

        self._setplotparameters()

    def _setplotparameters(self, fontsize: int = 16):
        """Figure parameters manipulation.

        Set font size, axes labels. Set the width and orientation of the
        axes ticks.

        """
        plt.rcParams.update({"font.size": fontsize})
        self.ax.set_xlabel("Pixel (-)", fontsize=fontsize)
        self.ax.set_ylabel("# of timestamps (-)", fontsize=fontsize)

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

    def plot_hist(
        self,
        file: str,
        pixel: int,
        timestamps: int,
        board_number: str,
        fw_ver: str,
        cycle_length: float,
    ):
        """Plot histogram.

        Plots a histogram of timestamps for a single pixel. Bin size is
        set to 17.867 us.

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

        bin_rounder = cycle_length / (2500 / 140) / 250

        bins = np.arange(0, cycle_length, 2500 / 140 * bin_rounder)

        self.ax.cla()

        if fw_ver == "2208":
            self.ax.hist(data[pixel], bins=bins, color="teal")
        elif fw_ver[:-1] == "2212":
            if fw_ver == "2212s":
                pix_coor = np.arange(256).reshape(4, 64).T
            elif fw_ver == "2212b":
                pix_coor = np.arange(256).reshape(64, 4)
            tdc, pix = np.argwhere(pix_coor == pixel)[0]
            ind = np.where(data[tdc].T[0] == pix)[0]
            ind1 = np.where(data[tdc].T[1][ind] > 0)[0]
            data_to_plot = data[tdc].T[1][ind[ind1]]

            self.ax.hist(data_to_plot, bins=bins, color="teal")
        else:
            print("\nFirmware version is not recognized, exiting.")
            sys.exit()

        self.ax.set_xlabel("Time (ps)")
        self.ax.set_ylabel("# of timestamps (-)")
        # self.ax.set_title("Pixel {}, 17.867 us bin".format(pixel))
        self.ax.set_xlim(0, cycle_length + 100)
        # self.ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        self.canvas.draw()
        self.canvas.flush_events()
