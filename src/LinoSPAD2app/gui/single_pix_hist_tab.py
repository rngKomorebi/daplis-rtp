"""This script generates the tab for single pixel histograms.

The tab itself could be used for checking the LinoSPAD2 output for
homogenity (the histogram should be more or less flattop).
"""

from PyQt5 import QtWidgets, QtCore, QtGui, uic
from LinoSPAD2app.gui.single_pixel_histogram import HistCanvas
import os
import glob


class SinglePixelHistogram(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """Tab creation.

        Tab is created with combo boxes for LinoSPAD2 daughterboard
        number and firmware version, a spin box for the number of
        timestamps per pixel/TDC per cycle, and a line edit for the
        pixel number input. A 'browse' button with a line edit for
        showing/inserting the file address are generated. A button for
        refreshing the plot is generated. The figure widget size is set
        constant across all tabs to achieve the same look for plots.
        An ui file generated with Qt5 designer is used.

        """
        super().__init__(parent)

        os.chdir(r"gui/ui")
        uic.loadUi(
            r"SinglePixelHistogram_tab_c.ui",
            self,
        )
        os.chdir("../..")
        self.show()

        # Browse button signal
        self.pushButton_browse.clicked.connect(self.get_dir)

        # Histogram widget
        self.widget_figure = HistCanvas()
        # self.widget_figure.setMinimumSize(500, 400)
        self.widget_figure.setFixedSize(500, 425)
        self.widget_figure.setObjectName("widget")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 4, 3)

        # Refresh plot button signal
        self.pushButton_refreshPlot.clicked.connect(self.refresh_plot)

        # Pixel number input
        # self.lineEdit_enterPixNumber.setMinimumSize(QtCore.QSize(0, 28))
        self.lineEdit_enterPixNumber.setValidator(QtGui.QIntValidator())
        self.lineEdit_enterPixNumber.setMaxLength(3)
        self.lineEdit_enterPixNumber.setAlignment(QtCore.Qt.AlignCenter)
        # self.lineEdit_enterPixNumber.setFont(QtGui.QFont("Arial", 20))

        # Pixel number input signal
        self.lineEdit_enterPixNumber.returnPressed.connect(
            lambda: self.pix_input()
        )

        # Set directory if path was pasted instead of chosen with the
        # 'Browse' button
        self.lineEdit_browse.textChanged.connect(self.change_path)

    def get_dir(self):
        """Called when "browse" button is pressed.

        Used for file searching and selecting. The file should be the
        '.dat' data file.
        """
        self.folder = str(
            QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Directory"
            )
        )
        self.lineEdit_browse.setText(self.folder)

    def change_path(self):
        """Called when text is inserted to the browse line edit.

        Used for updating the path variable when text is inserted to the
        line edit.

        """
        self.folder = self.lineEdit_browse.text()

    def pix_input(self):
        """Input for the pixel number."""

        self.pix = int(self.pixInput.text())
        os.chdir(self.folder)

        self.figureWidget.plot_hist(
            self.pix, timestamps=self.spinBox_timestamps.value()
        )

    def refresh_plot(self):
        """Button for refreshing the plot."""

        self.pix = int(self.lineEdit_enterPixNumber.text())
        board_number = self.comboBox_boardNumber.currentText()
        timestamps = self.spinBox_timestamps.value()
        os.chdir(self.folder)

        files = glob.glob("*.dat*")

        try:
            last_file = max(files, key=os.path.getctime)
            # new_file_ctime = os.path.getctime(last_file)
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
        )
