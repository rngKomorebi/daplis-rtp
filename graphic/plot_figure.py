from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class PltCanvas(QWidget):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super(PltCanvas, self).__init__(parent)
        # a figure instance to plot on
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # creating a Vertical Box layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

        # Create initial plot with initial data set to 1
        plt.rcParams.update({"font.size": 18})
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        (self.plot,) = self.ax.plot([1 for i in range(256)], "-ok")
        self.setplotparameters()
        self.canvas.draw()
        self.figure.tight_layout()

    # def setplotion(self):
    #     self.figure.ion()

    def setplotparameters(self):
        plt.rcParams.update({"font.size": 18})
        self.ax.set_xlabel("Pixel [-]")
        self.ax.set_ylabel("Valid timestamps [-]")

        # plt.box(bool(1))
        # plt.grid(False)
        # plt.subplots_adjust(left=0.15)

        self.ax.tick_params(which="both", width=2, direction="in")
        self.ax.tick_params(which="major", length=7, direction="in")
        self.ax.tick_params(which="minor", length=4, direction="in")
        self.ax.yaxis.set_ticks_position("both")
        self.ax.xaxis.set_ticks_position("both")

        for axis in ["top", "bottom", "left", "right"]:
            self.ax.spines[axis].set_linewidth(2)

    def setPlotData(self, xdataplot, yplotdata, xLim):

        # self.plot.set_xdata(xdataplot)
        self.plot.set_ydata(yplotdata)
        self.ax.relim()
        self.ax.autoscale_view()
        self.setplotparameters()
        self.ax.set_xlim(xLim[0], xLim[1])
        self.figure.tight_layout()
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def setPlotScale(self, scaleLin=True):
        if scaleLin:
            self.ax.set_yscale("linear")
            self.canvas.draw()
            self.canvas.flush_events()
        else:
            self.ax.set_yscale("log")
            self.canvas.draw()
            self.canvas.flush_events()
