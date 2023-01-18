from PyQt5 import QtCore, QtWidgets, uic, QtGui
from graphic.delta_t_plot import Delta_tCanvas
import glob
import os
import numpy as np


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

        self.pathtotimestamp = ""

        # Browse button
        self.pushButton_browse.clicked.connect(self._slot_loadpath)

        # Figure widget

        self.widget_figure = Delta_tCanvas()
        self.widget_figure.setMinimumSize(500, 400)
        self.widget_figure.setObjectName("widget")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 4, 3)

        # Refresh plot and start stream buttons

        self.pushButton_refreshPlot.clicked.connect(self._slot_refresh)

    def _slot_loadpath(self):
        file = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.lineEdit_browse.setText(file)
        self.pathtotimestamp = file

    def _slot_refresh(self):
        self._update_time_stamp()
        self.last_file_ctime = 0
