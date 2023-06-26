from PyQt5 import QtWidgets, QtCore, QtGui, uic
from graphic.single_pixel_histogram import HistCanvas
import os
import glob


class SinglePixelHistogram(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        os.chdir(r"graphic/ui")
        uic.loadUi(
            r"SinglePixelHistogram_tab_c.ui",
            self,
        )
        os.chdir("../..")
        self.show()

        # Browse button signal
        self.pushButton_browse.clicked.connect(self._get_dir)

        # Histogram widget
        self.widget_figure = HistCanvas()
        # self.widget_figure.setMinimumSize(500, 400)
        self.widget_figure.setFixedSize(500, 425)
        self.widget_figure.setObjectName("widget")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 4, 3)

        # Refresh plot button signal
        self.pushButton_refreshPlot.clicked.connect(self._refresh_plot)

        # Pixel number input
        # self.lineEdit_enterPixNumber.setMinimumSize(QtCore.QSize(0, 28))
        self.lineEdit_enterPixNumber.setValidator(QtGui.QIntValidator())
        self.lineEdit_enterPixNumber.setMaxLength(3)
        self.lineEdit_enterPixNumber.setAlignment(QtCore.Qt.AlignCenter)
        # self.lineEdit_enterPixNumber.setFont(QtGui.QFont("Arial", 20))

        # Pixel number input signal
        self.lineEdit_enterPixNumber.returnPressed.connect(lambda: self._pix_input())

        # Set directory if path was pasted instead of chosen with the 'Browse' button
        self.lineEdit_browse.textChanged.connect(self._change_path)

    def _get_dir(self):
        self.folder = str(
            QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        )
        self.lineEdit_browse.setText(self.folder)

    def _change_path(self):
        self.folder = self.lineEdit_browse.text()

    def _pix_input(self):

        self.pix = int(self.pixInput.text())
        os.chdir(self.folder)

        self.figureWidget._plot_hist(
            self.pix, timestamps=self.spinBox_timestamps.value()
        )

    def _refresh_plot(self):

        self.pix = int(self.lineEdit_enterPixNumber.text())
        board_number = self.comboBox_boardNumber.currentText()
        timestamps = self.spinBox_timestamps.value()
        os.chdir(self.folder)

        files = glob.glob("*.dat*")

        try:
            last_file = max(files, key=os.path.getctime)
            new_file_ctime = os.path.getctime(last_file)
        except ValueError:
            msg_window = QtWidgets.QMessageBox()
            msg_window.setText("No data files found, check the working directory.")
            msg_window.setWindowTitle("Error")
            msg_window.exec_()

        self.widget_figure._plot_hist(self.pix, timestamps, board_number, last_file, fw_ver=self.comboBox_FW.currentText())
