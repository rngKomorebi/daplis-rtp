""" Class for hooking the widgets to the main window for the LinoSPAD2 data
analysis and visualization application.

"""

from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from app.graphic.tab_livetimestamps import LiveTimestamps
from app.graphic.tab_single_pixel_histogram import SinglePixelHistogram
import matplotlib

matplotlib.use("Qt5Agg")


class TableWidget(QWidget):
    def __init__(self, parent):
        """
        Class initialization. Widgets 'LiveHistogram' and
        'SinglePixelHistogram' will be initialized.

        Parameters
        ----------
        parent : basestring
            Class being inherited from.

        Returns
        -------
        None.

        """
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()

        self.tab1 = LiveTimestamps(self)
        self.tab2 = SinglePixelHistogram()
        # self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab1, "Live timestamps")
        self.tabs.addTab(self.tab2, "Single pixel histogram")

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
