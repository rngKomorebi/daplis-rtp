"""This script generates the tab for single-pixel histograms.

The tab itself could be used for checking the LinoSPAD2 output for
homogeneity (the histogram should be more or less flat top).
"""

import glob
import os

from daplis_rtp.gui.single_pixel_histogram import HistCanvas
from daplis_rtp.gui.ui.SinglePixelHistogram_tab_c import Ui_Form
from PyQt5 import QtCore, QtGui, QtWidgets, uic


class SinglePixelHistogram(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """Tab creation.

        The tab is created with combo boxes for LinoSPAD2 daughterboard
        number and firmware version, a spin box for the number of
        timestamps per pixel/TDC per cycle, and a spin box for the
        pixel number input. A 'browse' button with a line edit for
        choosing/inserting the file address is generated. A button for
        refreshing the plot is generated. The figure widget size is set
        constant across all tabs to achieve the same look for plots.
        An 'ui' file generated with Qt5 designer is used.

        """
        super().__init__(parent)

        # os.chdir(r"C:\Users\bruce\Documents\Python Scripts\daplis-rtp\src\daplis_rtp\gui\ui")
        # uic.loadUi(
        #     r"SinglePixelHistogram_tab_c.ui",
        #     self,
        # )
        # os.chdir("../..")

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Dynamically bind all child widgets to `self`
        for attr_name in dir(self.ui):
            if not attr_name.startswith("__"):  # Skip dunder methods
                attr = getattr(self.ui, attr_name)
                setattr(self, attr_name, attr)

        self.show()

        # Browse button signal
        self.pushButton_browse.clicked.connect(self.get_dir)

        # Histogram widget
        self.widget_figure = HistCanvas()
        # self.widget_figure.setFixedSize(500, 425)
        # self.widget_figure.setObjectName("widget")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 4, 3)

        # Refresh plot button signal
        self.pushButton_refreshPlot.clicked.connect(self.refresh_plot)

        # Set directory if path was pasted instead of chosen with the
        # 'Browse' button
        self.lineEdit_browse.textChanged.connect(self.change_path)

        # Standard cycle length is 4 ms
        self.cycle_length = 4e9

        self.lineEdit_cycleLength.editingFinished.connect(
            self.cycle_length_change
        )

    def get_dir(self):
        """Called when "browse" button is pressed.

        Path to where data files are saved to. Used for file searching and
        selecting.
        """
        self.folder = str(
            QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Directory"
            )
        )
        self.lineEdit_browse.setText(self.folder)

    def change_path(self):
        """Called when text is inserted to the browse line edit.

        Used for updating the path variable when text is inserted into
        the line edit.

        """
        self.folder = self.lineEdit_browse.text()

    def refresh_plot(self):
        """Button for refreshing the plot.

        Either refreshes the current plot or plots a new graph if new
        data were taken.

        """

        self.pix = self.spinBox_enterPixNumber.value()
        board_number = self.comboBox_boardNumber.currentText()
        timestamps = self.spinBox_timestamps.value()
        os.chdir(self.folder)

        files = glob.glob("*.dat*")

        try:
            last_file = max(files, key=os.path.getctime)
        except ValueError:
            msg_window = QtWidgets.QMessageBox()
            msg_window.setText(
                "No data files found, check the working directory."
            )
            msg_window.setWindowTitle("Error")
            msg_window.exec_()

        self.widget_figure.plot_hist(
            last_file,
            self.pix,
            timestamps,
            board_number,
            fw_ver=self.comboBox_FW.currentText(),
            cycle_length=self.cycle_length,
        )

    # Testing adaptive fontsize
    def resizeEvent(self, event):

        # Define minimum and maximum width and corresponding font sizes
        min_width = 908
        max_width = 3810
        min_fontsize = 16
        max_fontsize = 40

        # Get the current window width
        current_width = self.size().width()

        # Ensure the current width stays within the bounds
        current_width = max(min_width, min(max_width, current_width))

        # Calculate the new font size using linear interpolation
        new_font_size = min_fontsize + (
            (current_width - min_width) / (max_width - min_width)
        ) * (max_fontsize - min_fontsize)

        self.widget_figure._setplotparameters(fontsize=new_font_size)

        super().resizeEvent(event)

    def cycle_length_change(self):

        try:
            self.cycle_length = float(self.lineEdit_cycleLength.text())
        except ValueError:
            msg_window = QtWidgets.QMessageBox()
            msg_window.setText(
                "Cycle length should be a float, i.e., 4e9. Resetting "
                "to the default value."
            )
            msg_window.setWindowTitle("Error")
            msg_window.exec_()
            self.lineEdit_cycleLength.setText("4e9")
            self.cycle_length = 4e9
