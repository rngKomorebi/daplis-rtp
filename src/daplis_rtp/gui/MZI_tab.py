"""This script generates the tab for online photon count plotting.

Two pixels are chosen for which the photon count registered is plotted
side by side. Can be used in the Mach-Zehnder interferometer setup to
follow the changes of the photon counts in two pixels, or in other
setups for checking the stability.

"""

import glob
import os

import numpy as np
from PyQt5 import QtCore, QtWidgets, uic

from daplis_rtp.functions.sen_pop import sen_pop
from daplis_rtp.gui.plot_figure_MZI import PltCanvas_MZI


class MZI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """Creation of the tab.

        The tab is generated with a 'Browse' button along with a line
        edit field for choosing/inserting the address of the data
        file to plot. Combo boxes for LinoSPAD2 daughterboard number and
        the firmware version are generated. A check box for applying and
        a button for undoing the mask are generated. A spin box for
        the number of timestamps per pixel/TDC per cycle is provided.
        A check box for switching between a linear and a logarithmic
        scale of the plot is also provided. Buttons 'Refresh plot' for
        refreshing the plot and 'Start stream' for plotting the last
        file found are created. Two sliders for the left x-axis left
        limit and lower y-axis limit are provided.

        """
        super().__init__(parent)
        os.chdir(r"gui/ui")
        uic.loadUi(
            r"MZI_tab.ui",
            self,
        )
        os.chdir("../..")

        self.show()

        self.pathtotimestamp = ""

        # Browse button
        self.pushButton_browse.clicked.connect(self.get_dir)

        # Figure widget
        self.widget_figure = PltCanvas_MZI()
        # self.widget_figure.setMinimumSize(500, 400)
        # self.widget_figure.setFixedSize(500, 425)
        self.widget_figure.setObjectName("widget")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 4, 3)

        # Refresh plot and start stream buttons
        self.pushButton_refreshPlot.clicked.connect(self.slot_refresh)

        self.pushButton_startStream.clicked.connect(self.slot_startstream)

        # Set directory if path was pasted instead of chosen with the
        # 'Browse' button
        self.lineEdit_browse.textChanged.connect(self.change_path)

        # Count of dataset for using as x axis; raised by 1 when
        # update_time_stamp is called
        self.dataset_count = 0
        self.pix1 = 0
        self.pix2 = 0

        # Sliders
        self.horizontalSlider_leftXLim.valueChanged.connect(
            self.slot_updateLeftSlider
        )
        self.horizontalSlider_lowerXLim.valueChanged.connect(
            self.slot_updateLowerSlider
        )

        self.horizontalSlider_leftXLim.setMinimum(0)
        self.horizontalSlider_leftXLim.setMaximum(self.dataset_count)
        self.horizontalSlider_lowerXLim.setMinimum(0)
        self.horizontalSlider_lowerXLim.setMaximum(0)

        self.leftPosition = 0
        self.bottomPosition = 0

        # Browse button
        self.pushButton_Reset.clicked.connect(self.resetPlot)

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
        if self.checkBox_presetMask_2.isChecked():
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
        self.leftPosition = self.horizontalSlider_leftXLim.value()

    def slot_updateLowerSlider(self):
        """Called when left slider state has changed.

        Updates the left x-axis limit based on the position of the
        slider.

        """
        self.bottomPosition = self.horizontalSlider_lowerXLim.value()

    def resetPlot(self):
        self.widget_figure.ax.cla()
        self.widget_figure.ax2.cla()
        self.dataset_count = 0
        self.widget_figure.figure.canvas.draw()
        self.widget_figure.figure.canvas.flush_events()

    def update_time_stamp(self):
        """Called during the cycle of real-time plotting.

        Load data from the last data file found in the directory
        provided.

        """
        stopping = False
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
                    self.dataset_count += 1
                    self.horizontalSlider_leftXLim.setMaximum(
                        self.dataset_count
                    )
                    self.last_file_ctime = new_file_ctime

                    validtimestamps = sen_pop(
                        self.pathtotimestamp + "/" + last_file,
                        board_number=self.comboBox_mask_2.currentText(),
                        fw_ver=self.comboBox_FW_2.currentText(),
                        timestamps=self.spinBox_timestamps_2.value(),
                        pix_add_fix=self.checkBox_pix_add_fix.isChecked(),
                    )

                    self.widget_figure.setPlotData_MZI(
                        [self.dataset_count - 1, self.dataset_count],
                        [
                            self.pix1,
                            validtimestamps[self.spinBox_FirstPixel.value()],
                        ],
                        [
                            self.pix2,
                            validtimestamps[self.spinBox_SecondPixel.value()],
                        ],
                        self.leftPosition,
                        self.bottomPosition,
                    )
                    self.pix1 = validtimestamps[
                        self.spinBox_FirstPixel.value()
                    ]
                    self.pix2 = validtimestamps[
                        self.spinBox_SecondPixel.value()
                    ]
                    self.horizontalSlider_lowerXLim.setMaximum(
                        int(np.max([self.pix1, self.pix2]))
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
