"""This script generates the tab for online sensor population plotting.

The tab can be used to introduce changes to the setup while following
the changes in real-time (depending on the actual data file size, the
plotting can take minutes).

"""

import glob
import os

import numpy as np
from daplis_rtp.functions.sen_pop import sen_pop
from daplis_rtp.gui.plot_figure import PltCanvas
from daplis_rtp.gui.ui.LiveTimestamps_tab_c import Ui_Form
from PyQt5 import QtCore, QtWidgets, uic


class LiveTimestamps(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """Creation of the tab.

        The tab is generated with a 'Browse' button along with a line
        edit field for choosing/inserting the address of the data
        file to plot. Combo boxes for LinoSPAD2 daughterboard number and
        the firmware version are generated. A check box for applying and
        a button for undoing the mask are generated. A spin box for
        the number of timestamps per pixel/TDC per cycle is provided. A
        widget with a grid of 4x64 of checkboxes with pixel numbers
        for masking single pixels is generated. A check box for switching
        between a linear and a logarithmic scale of the plot along with
        a check box for plotting vertical lines at positions 64, 128, and
        192 are provided (the latter can be used for firmware versions
        2208 and 2212s for setup alignment). Buttons 'Refresh plot' for
        refreshing the plot and 'Start stream' for plotting the
        last file found are created. Two sliders for the left and right
        limits for the x-axis are created.

        """
        super().__init__(parent)
        # os.chdir(r"C:\Users\bruce\Documents\Python Scripts\daplis-rtp\src\daplis_rtp\gui\ui")
        # uic.loadUi(
        #     r"LiveTimestamps_tab_c.ui",
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

        self.pathtotimestamp = ""

        # Browse button
        self.pushButton_browse.clicked.connect(self.get_dir)

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
        # self.widget_figure.setFixedSize(500, 425)
        self.widget_figure.setObjectName("widget")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 4, 3)

        # Sliders
        self.horizontalSlider_leftXLim.valueChanged.connect(
            self.slot_updateLeftSlider
        )
        self.horizontalSlider_rightXLim.valueChanged.connect(
            self.slot_updateRightSlider
        )

        self.horizontalSlider_leftXLim.setMinimum(0)
        self.horizontalSlider_leftXLim.setMaximum(255)
        self.horizontalSlider_rightXLim.setMinimum(0)
        self.horizontalSlider_rightXLim.setMaximum(255)
        self.horizontalSlider_rightXLim.setSliderPosition(255)
        self.leftPosition = 0
        self.rightPosition = 255

        # Pixel masking
        self.checkBox_presetMask_2.stateChanged.connect(self.presetmask_pixels)

        self.checkBox_linearScale_2.stateChanged.connect(
            self.slot_checkplotscale_2
        )

        self.pushButton_resetMask_2.clicked.connect(self.reset_pix_mask)

        self.path_to_main = os.getcwd()

        self.comboBox_mask_2.activated.connect(self.reset_pix_mask)

        # Refresh plot and start stream buttons
        self.pushButton_refreshPlot.clicked.connect(self.slot_refresh)

        self.pushButton_startStream.clicked.connect(self.slot_startstream)

        # Check box for plotting 3 vertical lines at position x=64,
        # 128, 192 (FW 2208)
        self.grouping = False
        self.checkBox_grouping_2.stateChanged.connect(
            self.slot_checkBox_grouping_2
        )

        # Set directory if path was pasted instead of chosen with the
        # 'Browse' button
        self.lineEdit_browse.textChanged.connect(self.change_path)

        # Timer preset
        self.timer = QtCore.QTimer()
        self.timerRunning = False
        self.last_file_ctime = 0
        self.timer.timeout.connect(self.update_time_stamp)

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

        self.widget_figure.setplotparameters(fontsize=new_font_size)

        super().resizeEvent(event)

    def get_dir(self):
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

    def change_path(self):
        """Called when address is inserted to the line edit.

        Sets the path variable to the address inserted.

        """
        self.pathtotimestamp = self.lineEdit_browse.text()

    def slot_startstream(self):
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

    def slot_stopstream(self):
        self.timer.stop()
        self.timerRunning = False
        self.pushButton_startStream.setText("Start stream")
        self.last_file_ctime = 0

    def slot_checkplotscale_2(self):
        """Called when state of the check box for scale is changed.

        Switches between logarithmic and linear scale of the plot.

        """
        if self.checkBox_linearScale_2.isChecked():
            self.widget_figure.setPlotScale(True)
        else:
            self.widget_figure.setPlotScale(False)

    def slot_refresh(self):
        """Called when the 'Refresh button' is pressed.

        Refreshes the plot, either the current one or updates with the
        new data if new data were taken.

        """
        self.update_time_stamp()
        self.last_file_ctime = 0

    def slot_updateLeftSlider(self):
        """Called when left slider state has changed.

        Updates the left x-axis limit based on the position of the
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

    def slot_updateRightSlider(self):
        """Called when right slider state has changed.

        Updates the right x-axis limit based on the position of the
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

    def update_time_stamp(self):
        """Called during the cycle of real-time plotting.

        Load data from the last data file found in the directory
        provided.

        """
        stopping = False
        self.mask_pixels()
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
            self.slot_stopstream()
            stopping = True
        if stopping is False:
            try:
                if new_file_ctime > self.last_file_ctime:
                    self.last_file_ctime = new_file_ctime

                    validtimestamps = sen_pop(
                        self.pathtotimestamp + "/" + last_file,
                        board_number=self.comboBox_mask_2.currentText(),
                        fw_ver=self.comboBox_FW_2.currentText(),
                        timestamps=self.spinBox_timestamps_2.value(),
                        pix_add_fix=self.checkBox_pix_add_fix.isChecked(),
                    )
                    validtimestamps = validtimestamps * self.maskValidPixels
                    self.widget_figure.setPlotData(
                        np.arange(0, 256, 1),
                        validtimestamps,
                        [self.leftPosition, self.rightPosition],
                        self.grouping,
                    )

                    copy_for_max = np.sort(np.copy(validtimestamps))

                    self.lcdTopMostPixel1.display(
                        np.argwhere(validtimestamps == copy_for_max[-1])[0][0]
                    )
                    self.lcdTopMostPixel2.display(
                        np.argwhere(validtimestamps == copy_for_max[-2])[0][0]
                    )

            except ValueError:
                msg_window = QtWidgets.QMessageBox()
                msg_window.setText(
                    "Cannot unpack data, check the timestamp setting and "
                    "the firmware version."
                )
                msg_window.setWindowTitle("Error")
                msg_window.exec_()
                self.slot_stopstream()
                stopping = True

    def mask_pixels(self):
        """
        Function for masking the chosen pixels.

        """
        for i in range(256):
            if self.checkBoxPixel[i].isChecked():
                self.maskValidPixels[i] = 0
            else:
                self.maskValidPixels[i] = 1

    def presetmask_pixels(self):
        """Called when the check box 'Preset mask' is checked.

        Uses the masking data provided in the 'params' folder for
        masking of the warm/hot pixels. Uses the LinoSPAD2 daughterboard
        number to load appropriate data.

        """

        if self.checkBox_presetMask_2.isChecked():
            try:
                if os.getcwd() != self.path_to_main + "/params/masks":
                    os.chdir(self.path_to_main + "/params/masks")
                file = glob.glob(
                    "*{}_{}*".format(
                        self.comboBox_mask_2.currentText(),
                        self.comboBox_mb_2.currentText(),
                    )
                )[0]
                mask = np.genfromtxt(file, delimiter=",", dtype="int")
                for i in mask:
                    self.maskValidPixels[i] = 0
                    cb = self.scrollAreaWidgetContentslayout.itemAt(i).widget()
                    cb.setChecked(True)
            except IndexError:
                self.checkBox_presetMask_2.setCheckState(0)
                msg_window = QtWidgets.QMessageBox()
                msg_window.setText(
                    "No mask data were found for the given daughterboard, "
                    "motherboard, and firmware combination."
                )
                msg_window.setWindowTitle("Error")
                msg_window.exec_()

        else:
            for i in range(256):
                # self.maskValidPixels[i] = 0
                cb = self.scrollAreaWidgetContentslayout.itemAt(i).widget()
                cb.setChecked(False)

    def reset_pix_mask(self):
        """
        Function for resetting the pixel masking by unchecking all pixel
        mask checkboxes.

        """
        for i in range(256):
            cb = self.scrollAreaWidgetContentslayout.itemAt(i).widget()
            cb.setChecked(False)
        self.checkBox_presetMask_2.setChecked(False)

    def slot_checkBox_grouping_2(self):
        """Called when check box for plotting lines state changed."""
        if self.checkBox_grouping_2.isChecked():
            self.grouping = True
        else:
            self.grouping = False
