from PyQt5 import QtWidgets, uic
from graphic.delta_t_plot import Delta_tCanvas
import os


class Delta_t(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        os.chdir(r"graphic/ui")
        uic.loadUi(
            r"DeltaT_tab_c.ui",
            self,
        )
        os.chdir("../..")

        self.show()

        # # Pixel number
        # self.pix1 = None
        # self.pix2 = None

        # Browse button
        self.pushButton_browse.clicked.connect(self._get_dir)

        # Figure widget
        self.widget_figure = Delta_tCanvas()
        self.widget_figure.setMinimumSize(500, 400)
        self.widget_figure.setObjectName("widget")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 4, 3)

        # Refresh plot and start stream buttons
        self.pushButton_refreshPlot.clicked.connect(self._plot_refresh)

    def _get_dir(self):
        self.folder = str(
            QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        )
        self.lineEdit_browse.setText(self.folder)

    def _plot_refresh(self):

        self.pix1 = self.spinBox_pix1.value()
        self.pix2 = self.spinBox_pix2.value()
        self.board_number = self.comboBox_boardNumber.currentText()
        self.range_left = self.spinBox_rangeLeft.value()
        self.range_right = self.spinBox_rangeRight.value()
        timestamps = self.spinBox_timestamps.value()

        os.chdir(self.folder)

        self.widget_figure._plot_delta(
            self.pix1,
            self.pix2,
            timestamps,
            self.board_number,
            self.range_left,
            self.range_right,
        )
