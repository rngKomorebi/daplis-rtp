"""Plot canvas for the full-sensor (dual-board) tab.

512 pixels on the x-axis. A dashed boundary line is always drawn at
x=255.5 to mark the split between the two sensor halves. When grouping
is enabled, vertical lines are drawn at 64, 128, 192, 320, 384, 448.

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

from daplis_rtp.gui.plot_figure import MIN_CANVAS_HEIGHT, toolbar_min_width


class PltCanvasDual(QWidget):
    def __init__(self, parent=None, width=7, height=4, dpi=100):
        super().__init__(parent)

        plt.style.use("dark_background")

        self.figure = Figure(figsize=(width, height), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(
            left=0.15, right=0.97, top=0.945, bottom=0.12
        )

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)
        self.setLayout(self.layout)

        # Keep the whole toolbar reachable: the pixel number under
        # the cursor is read off it, and it is the first thing a narrow
        # window hides.
        self.setMinimumSize(
            toolbar_min_width(self.toolbar), MIN_CANVAS_HEIGHT
        )

        self.setplotparameters()

    def setplotparameters(self, fontsize: int = 16):
        plt.rcParams.update({"font.size": fontsize})
        self.ax.set_xlabel("Pixel (-)", fontsize=fontsize)
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
        self.ax.cla()
        self.ax.plot(yplotdata, "-o", color="#f48383")

        # Board boundary
        self.ax.axvline(
            x=255.5, color="white", linestyle="--", linewidth=1, alpha=0.5
        )

        if grouping:
            self.ax.vlines(
                x=(64, 128, 192, 320, 384, 448),
                ymin=0,
                ymax=yplotdata.max(),
                color="teal",
            )

        mplcyberpunk.make_lines_glow(self.ax, diff_linewidth=1.1)
        mplcyberpunk.add_gradient_fill(self.ax, alpha_gradientglow=0.3)

        self.ax.relim()
        self.ax.autoscale_view()
        self.setplotparameters(fontsize)
        self.ax.set_xlim(xLim[0], xLim[1])
        self.ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def setPlotScale(self, scaleLin: bool):
        if scaleLin:
            self.ax.set_yscale("linear")
        else:
            self.ax.set_yscale("log")
        self.canvas.draw()
        self.canvas.flush_events()
