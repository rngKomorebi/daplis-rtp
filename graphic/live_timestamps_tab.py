from PyQt5 import QtCore, QtWidgets, uic
from graphic.plot_figure import PltCanvas
import glob
import os
from tools import timestamp_computation
import numpy as np

# from app.graphic.ui.LiveTimestamps_tab_ui import Ui_LiveTimestamps


# class LiveTimestamps(QtWidgets.QWidget, Ui_LiveTimestamps):
#     def __init__(self, parent=None):

#         super().__init__(parent)

#         self.setupUi(self)


class LiveTimestamps(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(r"C:/Users/bruce/Documents/Python Scripts/LinoSPAD2_app/"
                   "app/graphic/ui/LiveTimestamps_tab_c.ui", self)

        self.show()

        self.pathtotimestamp = ""

        # Browse button
        self.pushButton_browse.clicked.connect(self._slot_loadpath)

        # Scroll area with check boxes
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 383, 346))
        self.checkBoxPixel = []
        self.scrollAreaWidgetContentslayout = QtWidgets.QGridLayout(
            self.scrollAreaWidgetContents
        )
        self.maskValidPixels = np.zeros(256)
        for col in range(4):
            for row in range(64):
                self.checkBoxPixel.append(
                    QtWidgets.QCheckBox(
                        str(row + col * 64), self.scrollAreaWidgetContents
                    )
                )
                self.scrollAreaWidgetContentslayout.addWidget(
                    self.checkBoxPixel[row + col * 64], row, col, 1, 1
                )
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        # Figure widget

        self.widget_figure = PltCanvas()
        self.widget_figure.setMinimumSize(500, 400)
        self.widget_figure.setObjectName("widget")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 4, 3)

        # Sliders
        self.horizontalSlider_leftXLim.valueChanged.connect(self._slot_updateLeftSlider)
        self.horizontalSlider_rightXLim.valueChanged.connect(
            self._slot_updateRightSlider
        )

        self.horizontalSlider_leftXLim.setMinimum(0)
        self.horizontalSlider_leftXLim.setMaximum(255)
        self.horizontalSlider_rightXLim.setMinimum(0)
        self.horizontalSlider_rightXLim.setMaximum(255)
        self.horizontalSlider_rightXLim.setSliderPosition(255)
        self.leftPosition = 0
        self.rightPosition = 255

        # Pixel masking

        self.checkBox_presetMask.stateChanged.connect(self._preset_mask_pixels)

        self.checkBox_linearScale.stateChanged.connect(self._slot_checkplotscale)

        self.pushButton_resetMask.clicked.connect(self._reset_pix_mask)

        # Refresh plot and start stream buttons

        self.pushButton_refreshPlot.clicked.connect(self._slot_refresh)

        self.pushButton_startStream.clicked.connect(self._slot_startstream)

        # Timer preset
        self.timer = QtCore.QTimer()
        self.timerRunning = False
        self.last_file_ctime = 0
        self.timer.timeout.connect(self._update_time_stamp)

    def _slot_loadpath(self):
        file = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.lineEdit_browse.setText(file)
        self.pathtotimestamp = file

    def _slot_startstream(self):
        self.last_file_ctime = 0

        if self.timerRunning is True:
            self.timer.stop()
            self.timerRunning = False
            self.pushButton_startStream.setText("Start stream")
        else:
            self.pushButton_startStream.setText("Stop stream")
            self.timer.start(100)
            self.timerRunning = True

    def _slot_checkplotscale(self):
        if self.checkBox_linearScale.isChecked():
            self.widget_figure.setPlotScale(True)
        else:
            self.widget_figure.setPlotScale(False)

    def _slot_refresh(self):
        self._update_time_stamp()
        self.last_file_ctime = 0

    def _slot_updateLeftSlider(self):
        if (
            self.horizontalSlider_leftXLim.value()
            >= self.horizontalSlider_rightXLim.value()
        ):
            self.horizontalSlider_leftXLim.setValue(
                self.horizontalSlider_rightXLim.value() - 1
            )
        self.leftPosition = self.horizontalSlider_leftXLim.value()

    def _slot_updateRightSlider(self):
        if (
            self.horizontalSlider_rightXLim.value()
            <= self.horizontalSlider_leftXLim.value()
        ):
            self.horizontalSlider_rightXLim.setValue(
                self.horizontalSlider_leftXLim.value() + 1
            )
        self.rightPosition = self.horizontalSlider_rightXLim.value()

    def _update_time_stamp(self):
        self._mask_pixels()
        os.chdir(self.pathtotimestamp)
        DATA_FILES = glob.glob("*.dat*")
        print("_update_time_stamp: timer running")
        try:
            last_file = max(DATA_FILES, key=os.path.getctime)
            new_file_ctime = os.path.getctime(last_file)

            if new_file_ctime > self.last_file_ctime:

                self.last_file_ctime = new_file_ctime

                validtimestemps, peak = timestamp_computation.get_nmr_validtimestamps(
                    self.pathtotimestamp + "/" + last_file, np.arange(145, 155, 1), 512
                )
                validtimestemps = validtimestemps * self.maskValidPixels
                self.widget_figure.setPlotData(
                    np.arange(0, 256, 1),
                    validtimestemps,
                    peak,
                    [self.leftPosition, self.rightPosition],
                )
        except ValueError:
            print("_update_time_stamp:  waiting for a file")

    def _mask_pixels(self):
        """
        Function for masking the chosen pixels.

        Returns
        -------
        None.

        """
        for i in range(256):
            if self.checkBoxPixel[i].isChecked():
                self.maskValidPixels[i] = 0
            else:
                self.maskValidPixels[i] = 1

    def _preset_mask_pixels(self):
        mask = [
            15,
            16,
            29,
            39,
            40,
            50,
            52,
            66,
            73,
            93,
            95,
            96,
            98,
            101,
            109,
            122,
            127,
            196,
            210,
            231,
            236,
            238,
        ]
        if self.checkBox_presetMask.isChecked():
            for i in mask:
                self.maskValidPixels[i] = 0
                cb = self.scrollAreaWidgetContentslayout.itemAt(i).widget()
                cb.setChecked(True)
        else:
            for i in mask:
                self.maskValidPixels[i] = 0
                cb = self.scrollAreaWidgetContentslayout.itemAt(i).widget()
                cb.setChecked(False)

    def _reset_pix_mask(self):
        """
        Function for resetting the pixel masking by unchecking all pixel
        mask check boxes.

        Returns
        -------
        None.

        """
        for i in range(256):
            cb = self.scrollAreaWidgetContentslayout.itemAt(i).widget()
            cb.setChecked(False)
        self.checkBox_presetMask.setChecked(False)
