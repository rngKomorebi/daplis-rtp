"""This script generates the tab for online sensor population plotting.

The tab can be used to introduce changes into the setup while following
the changes in real-time (dependning on the actual data file size, the
plottign can take minutes).

"""

from PyQt5 import QtCore, QtWidgets, uic
from gui.plot_figure import PltCanvas
import glob
import os
import sys
import numpy as np

sys.path.append("..")
from functions.sen_pop import sen_pop


class LiveTimestamps(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """Creation of the tab.

        The tab is generated with a 'Browse' button along with a line
        edit field for looking for/inserting the address of the data
        file to plot. Combo boxes for LinoSPAD2 daughterboard number and
        the firmware version are generated. A check box for applying and
        a button for resetting the mask are generated. A spin box for
        number of timestamps per pixel/TDC per cycle is provided. A
        widget with a grid of 4x64 of check boxes with pixel numbers
        for masking single pixels is generated. A check box for swtiching
        between a linear and a logarithmic scale of the plot along with
        a check box for plotting vertical lines at positiong 64, 128, and
        192 are provided (the latter can be used for firmware versions
        2208 and 2212s for setup alignment). Buttons 'Refresh plot' for
        refreshing the current plot and 'Start stream' for plotting the
        last file found are created. Two sliders for left and right
        limit for the x axis are created.

        """
        super().__init__(parent)
        os.chdir(r"graphic/ui")
        uic.loadUi(
            r"LiveTimestamps_tab_c.ui",
            self,
        )
        os.chdir("../..")

        self.show()

        self.pathtotimestamp = ""

        # Browse button
        self.pushButton_browse.clicked.connect(self._get_dir)

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
        # self.widget_figure.setMinimumSize(500, 400)
        self.widget_figure.setFixedSize(500, 425)
        self.widget_figure.setObjectName("widget")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 4, 3)

        # Sliders
        self.horizontalSlider_leftXLim.valueChanged.connect(
            self._slot_updateLeftSlider
        )
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

        self.checkBox_linearScale.stateChanged.connect(
            self._slot_checkplotscale
        )

        self.pushButton_resetMask.clicked.connect(self._reset_pix_mask)

        self.path_to_main = os.getcwd()

        self.comboBox_mask.activated.connect(self._reset_pix_mask)

        # Refresh plot and start stream buttons

        self.pushButton_refreshPlot.clicked.connect(self._slot_refresh)

        self.pushButton_startStream.clicked.connect(self._slot_startstream)

        # Check box for plotting 3 vertical lines at position x=64,
        # 128, 192 (FW 2208)
        self.grouping = False
        self.checkBox_grouping.stateChanged.connect(
            self._slot_checkBox_grouping
        )

        # Set directory if path was pasted instead of chosen with the
        # 'Browse' button
        self.lineEdit_browse.textChanged.connect(self._change_path)

        # Timer preset
        self.timer = QtCore.QTimer()
        self.timerRunning = False
        self.last_file_ctime = 0
        self.timer.timeout.connect(self._update_time_stamp)

    def _get_dir(self):
        """Called when the 'browse' button is pressed.

        Sets the path variable to the address chosen.

        """
        file = str(
            QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Directory"
            )
        )
        self.lineEdit_browse.setText(file)
        self.pathtotimestamp = file

    def _change_path(self):
        """Called when address is inserted to the line edit.

        Sets the path variable to the address inserted.

        """
        self.pathtotimestamp = self.lineEdit_browse.text()

    def _slot_startstream(self):
        """Called when the 'Start stream' button is pressed.

        Starts an infinite cycle of refreshing the plot when new files
        are found in the folder.

        """
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
        """Called when state of the check box for scale is changed.

        Switches between logarithmic and linear scale of the plot.

        """
        if self.checkBox_linearScale.isChecked():
            self.widget_figure.setPlotScale(True)
        else:
            self.widget_figure.setPlotScale(False)

    def _slot_refresh(self):
        """Called when the 'Refresh button' is pressed."""
        self._update_time_stamp()
        self.last_file_ctime = 0

    def _slot_updateLeftSlider(self):
        """Called when left slider state has changed.

        Updates the left x axis limit based on the position of the
        slider.

        """
        if (
            self.horizontalSlider_leftXLim.value()
            >= self.horizontalSlider_rightXLim.value()
        ):
            self.horizontalSlider_leftXLim.setValue(
                self.horizontalSlider_rightXLim.value() - 1
            )
        self.leftPosition = self.horizontalSlider_leftXLim.value()

    def _slot_updateRightSlider(self):
        """Called when right slider state has changed.

        Updates the right x axis limit based on the position of the
        slider.

        """
        if (
            self.horizontalSlider_rightXLim.value()
            <= self.horizontalSlider_leftXLim.value()
        ):
            self.horizontalSlider_rightXLim.setValue(
                self.horizontalSlider_leftXLim.value() + 1
            )
        self.rightPosition = self.horizontalSlider_rightXLim.value()

    def _update_time_stamp(self):
        """Called during the cycle of real-time plotting.

        Load data from the last data file found in the directory
        provided.

        """
        self._mask_pixels()
        os.chdir(self.pathtotimestamp)
        DATA_FILES = glob.glob("*.dat*")
        try:
            last_file = max(DATA_FILES, key=os.path.getctime)
            new_file_ctime = os.path.getctime(last_file)
        except ValueError:
            msg_window = QtWidgets.QMessageBox()
            msg_window.setText(
                "No data files found, check the working directory."
            )
            msg_window.setWindowTitle("Error")
            msg_window.exec_()

        try:
            if new_file_ctime > self.last_file_ctime:
                self.last_file_ctime = new_file_ctime

                validtimestamps = sen_pop(
                    self.pathtotimestamp + "/" + last_file,
                    board_number=self.comboBox_mask.currentText(),
                    fw_ver=self.comboBox_FW.currentText(),
                    timestamps=self.spinBox_timestamps.value(),
                )
                validtimestamps = validtimestamps * self.maskValidPixels
                self.widget_figure.setPlotData(
                    np.arange(0, 256, 1),
                    validtimestamps,
                    [self.leftPosition, self.rightPosition],
                    self.grouping,
                )
        except ValueError:
            msg_window = QtWidgets.QMessageBox()
            msg_window.setText(
                "Cannot unpack data, check the timestamp setting."
            )
            msg_window.setWindowTitle("Error")
            msg_window.exec_()

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
        """Called when the check box 'Preset mask' is checked.

        Uses the masking data provided in the 'params' folder for
        masking of the warm/hot pixels. Uses the LinoSPAD2 daughterboard
        number to load appropriate data.

        """
        if os.getcwd() != self.path_to_main + "/masks":
            os.chdir(self.path_to_main + "/masks")
        file = glob.glob("*{}*".format(self.comboBox_mask.currentText()))[0]
        mask = np.genfromtxt(file, delimiter=",", dtype="int")

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

    def _slot_checkBox_grouping(self):
        """Called when check box for plotting lines state changed."""
        if self.checkBox_grouping.isChecked():
            self.grouping = True
        else:
            self.grouping = False
