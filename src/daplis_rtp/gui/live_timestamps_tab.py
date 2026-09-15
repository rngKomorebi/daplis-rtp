"""This script generates the tab for online sensor population plotting.

The tab can be used to introduce changes to the setup while following
the changes in real-time (depending on the actual data file size, the
plotting can take minutes).

"""

import glob
import os
from importlib.resources import files

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets, uic

from daplis_rtp.functions.sen_pop import sen_pop
from daplis_rtp.functions.tdc_occupancy import pixel_to_tdc_map
from daplis_rtp.gui.pixel_mask_window import PixelMaskWindow, mask_summary
from daplis_rtp.gui.plot_figure import PltCanvas, reserve_toolbar_width
from daplis_rtp.gui.tdc_occupancy_panel import (
    BoardOccupancy,
    TdcOccupancyPanel,
    pixels_of_interest,
)
from daplis_rtp.gui.ui.LiveTimestamps_tab_c import Ui_Form


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
        192 are provided (the latter can be used for firmware version
        2212s for setup alignment). A check box for data files
        collected with absolute timestamps is provided. Buttons
        'Refresh plot' for
        refreshing the plot and 'Start stream' for plotting the
        last file found are created. Two spin boxes for the left and
        right limits for the x-axis, in pixels, are created.

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

        # Pixel mask — 256 check boxes, in a window of their own.
        # In the column they took 250 px, which both set how tall the
        # application opened and showed a few of the 64 rows at a time;
        # here they can be dragged next to the plot while the stream
        # runs. The boxes themselves are unchanged, so everything that
        # reads 'checkBoxPixel' or 'scrollAreaWidgetContentslayout'
        # works as before.
        font10 = QtGui.QFont()
        font10.setPointSize(10)
        self.maskValidPixels = np.zeros(256)
        self.mask_window = PixelMaskWindow(
            self,
            boards=[("Pixels", 4, 64)],
            font=font10,
            title="Pixel mask — Online plot",
        )
        self.checkBoxPixel = self.mask_window.boxes[0]
        self.scrollAreaWidgetContentslayout = self.mask_window.grids[0]
        self.mask_window.changed.connect(self.slot_mask_changed)
        self.mask_window.clear_requested.connect(self.reset_pix_mask)

        # The '.ui' scroll area it replaces, and the row of controls
        # that takes its place in the column
        mask_row = QtWidgets.QHBoxLayout()
        self.pushButton_editMask = QtWidgets.QPushButton(
            "Edit mask…", self.frame_2
        )
        self.pushButton_editMask.setFont(font10)
        self.pushButton_editMask.setMinimumSize(QtCore.QSize(0, 26))
        self.pushButton_editMask.setToolTip(
            "Open the pixel mask in a window of its own; it can be left "
            "open beside the plot while the stream runs."
        )
        self.pushButton_editMask.clicked.connect(
            self.mask_window.open_beside
        )
        mask_row.addWidget(self.pushButton_editMask)
        self.label_maskCount = QtWidgets.QLabel("0 masked", self.frame_2)
        self.label_maskCount.setFont(font10)
        mask_row.addWidget(self.label_maskCount)
        mask_row.addStretch(1)

        index = self.verticalLayout.indexOf(self.scrollArea)
        self.verticalLayout.removeWidget(self.scrollArea)
        self.scrollArea.setParent(None)
        self.scrollArea.deleteLater()
        self.verticalLayout.insertLayout(index, mask_row)
        self.slot_mask_changed()

        # The '.ui' file carries a 500x425 placeholder where the canvas
        # goes. The real canvas is added over it just below, but the
        # placeholder stays in the grid, and its minimum size alone
        # decided how tall and wide the application had to open.
        self.gridLayout.removeWidget(self.ui.widget_figure)
        self.ui.widget_figure.setParent(None)
        self.ui.widget_figure.deleteLater()

        # Figure widget
        self.widget_figure = PltCanvas()
        # self.widget_figure.setMinimumSize(500, 400)
        # self.widget_figure.setFixedSize(500, 425)
        self.widget_figure.setObjectName("widget")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 4, 3)
        reserve_toolbar_width(self.frame, self.widget_figure)

        # x-axis limits: one spin box per edge, over the pixel range
        self.spinBox_leftXLim.setRange(0, 255)
        self.spinBox_rightXLim.setRange(0, 255)
        self.spinBox_leftXLim.setValue(0)
        self.spinBox_rightXLim.setValue(255)
        # Without this, valueChanged fires on every keystroke, so typing a
        # smaller right limit gets clamped against the old left one halfway
        # through the number. Now the value is committed on Enter or focus
        # loss, and the arrows still work as before.
        self.spinBox_leftXLim.setKeyboardTracking(False)
        self.spinBox_rightXLim.setKeyboardTracking(False)

        self.spinBox_leftXLim.valueChanged.connect(self.slot_updateLeftXLim)
        self.spinBox_rightXLim.valueChanged.connect(self.slot_updateRightXLim)

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

        # TDC slot occupancy — how close the readout is to saturation.
        # Placed just above the two buttons; the '.ui' file has already
        # filled the column, so the widget is inserted rather than
        # appended.
        self.panel_occupancy = TdcOccupancyPanel(self.frame_2, font=font10)
        self.verticalLayout.insertWidget(
            self.verticalLayout.indexOf(self.pushButton_refreshPlot),
            self.panel_occupancy,
        )
        self.panel_occupancy.attach_timestamps_spinbox(
            self.spinBox_timestamps_2
        )

        # Refresh plot and start stream buttons
        self.pushButton_refreshPlot.clicked.connect(self.slot_refresh)

        self.pushButton_startStream.clicked.connect(self.slot_startstream)

        # Check box for plotting 3 vertical lines at position x=64,
        # 128, 192 (FW 2212s)
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

        # Initial fontsize for the canvas
        self.canvas_fontsize = 16

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

        self.canvas_fontsize = new_font_size

        self.widget_figure.setplotparameters(fontsize=self.canvas_fontsize)

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
            # A new run gets a new saturation warning, even if the last
            # one was already dismissed
            self.panel_occupancy.reset()
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
        # An explicit look again asks for the saturation warning again
        # too - typically the 'Timestamps' setting has just been changed
        self.panel_occupancy.reset()
        self.update_time_stamp()
        self.last_file_ctime = 0

    def slot_updateLeftXLim(self):
        """Called when the left x-limit spin box has changed.

        Updates the left x-axis limit, keeping it below the right one.

        """
        if self.spinBox_leftXLim.value() >= self.spinBox_rightXLim.value():
            self.spinBox_leftXLim.setValue(
                self.spinBox_rightXLim.value() - 1
            )
        self.leftPosition = self.spinBox_leftXLim.value()

    def slot_updateRightXLim(self):
        """Called when the right x-limit spin box has changed.

        Updates the right x-axis limit, keeping it above the left one.

        """
        if self.spinBox_rightXLim.value() <= self.spinBox_leftXLim.value():
            self.spinBox_rightXLim.setValue(
                self.spinBox_leftXLim.value() + 1
            )
        self.rightPosition = self.spinBox_rightXLim.value()

    def update_time_stamp(self):
        """Called during the cycle of real-time plotting.

        Load data from the last data file found in the directory
        provided.

        """
        stopping = False
        self.mask_pixels()
        DATA_FILES = glob.glob(os.path.join(self.pathtotimestamp, "*.dat*"))
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

                    fw_ver = self.comboBox_FW_2.currentText()
                    pix_add_fix = self.checkBox_pix_add_fix.isChecked()
                    timestamps = self.spinBox_timestamps_2.value()
                    check_slots = self.panel_occupancy.enabled

                    result = sen_pop(
                        last_file,
                        board_number=self.comboBox_mask_2.currentText(),
                        fw_ver=fw_ver,
                        timestamps=timestamps,
                        pix_add_fix=pix_add_fix,
                        absolute_timestamps=(
                            self.checkBox_abs_timestamps.isChecked()
                        ),
                        return_occupancy=check_slots,
                    )
                    if check_slots:
                        validtimestamps, occupancy = result
                        self.report_occupancy(occupancy, fw_ver, pix_add_fix)
                    else:
                        validtimestamps = result
                        self.panel_occupancy.clear("switched off")

                    validtimestamps = validtimestamps * self.maskValidPixels
                    self.widget_figure.setPlotData(
                        np.arange(0, 256, 1),
                        validtimestamps,
                        [self.leftPosition, self.rightPosition],
                        self.grouping,
                        self.canvas_fontsize,
                    )

                    copy_for_max = np.sort(np.copy(validtimestamps))

                    self.lcdTopMostPixel1.display(
                        np.argwhere(validtimestamps == copy_for_max[-1])[0][0]
                    )
                    self.lcdTopMostPixel2.display(
                        np.argwhere(validtimestamps == copy_for_max[-2])[0][0]
                    )

            except (ValueError, FileNotFoundError, OSError) as err:
                msg_window = QtWidgets.QMessageBox()
                msg_window.setText(
                    "Cannot read data file — it may have been removed. "
                    "Check the timestamp setting, the firmware version, "
                    "and whether the data hold absolute timestamps."
                )
                msg_window.setDetailedText(str(err))
                msg_window.setWindowTitle("Error")
                msg_window.exec_()
                self.slot_stopstream()
                stopping = True

    def report_occupancy(self, occupancy, fw_ver, pix_add_fix):
        """Hand one refresh's slot occupancy to the status box.

        The pixels of interest come either from the box's own field or
        from the mask and the x-limits; they are pixel numbers as
        plotted, so they are mapped to TDCs with the same
        'pix_add_fix' the rates were built with.

        """
        try:
            explicit = self.panel_occupancy.explicit_pixels()
        except ValueError as err:
            # A half-typed pixel list should not blank the readout, and
            # it certainly should not raise into the plotting path
            self.panel_occupancy.clear("pixels of interest: {}".format(err))
            return

        pixels = pixels_of_interest(
            explicit,
            self.maskValidPixels,
            (self.leftPosition, self.rightPosition),
        )
        tdcs = pixel_to_tdc_map(fw_ver, pix_add_fix)[pixels]
        self.panel_occupancy.show_result([BoardOccupancy("", occupancy, tdcs)])

    def slot_mask_changed(self):
        """Called whenever a box in the mask window is ticked.

        Only refreshes the count beside the button; the mask array
        itself is rebuilt by 'mask_pixels' on the next refresh, so
        ticking a box never races the plotting.

        """
        self.label_maskCount.setText(
            mask_summary(self.mask_window.masked_counts())
        )

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
                # if os.getcwd() != self.path_to_main + "/params/masks":
                #     os.chdir(self.path_to_main + "/params/masks")
                # file = glob.glob(
                #     "*{}_{}*".format(
                #         self.comboBox_mask_2.currentText(),
                #         self.comboBox_mb_2.currentText(),
                #     )
                # )[0]
                file_w_mask = files("daplis_rtp.params.masks").joinpath(
                    f"mask_{self.comboBox_mask_2.currentText()}_"
                    f"{self.comboBox_mb_2.currentText()}.txt"
                )
                # file = glob.glob(path_to_file_mask)[0]
                mask = np.genfromtxt(file_w_mask, delimiter=",", dtype="int")
                for i in mask:
                    self.maskValidPixels[i] = 0
                    cb = self.scrollAreaWidgetContentslayout.itemAt(i).widget()
                    cb.setChecked(True)
            except (IndexError, FileNotFoundError):
                self.checkBox_presetMask_2.setCheckState(0)
                msg_window = QtWidgets.QMessageBox()
                msg_window.setText(
                    "No mask data were found for the given daughterboard, "
                    "and motherboard combination."
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
