"""This script generates the tab for online photon count plotting.

Two pixels are chosen for which the photon count registered is plotted
side by side. Can be used in the Mach-Zehnder interferometer setup to
follow the changes of the photon counts in two pixels, or in other
setups for checking the stability.

"""

import glob
import os

from PyQt5 import QtCore, QtGui, QtWidgets, uic

from daplis_rtp.functions.sen_pop import sen_pop
from daplis_rtp.gui.plot_figure import reserve_toolbar_width
from daplis_rtp.gui.plot_figure_MZI import PltCanvas_MZI
from daplis_rtp.gui.ui.MZI_tab import Ui_Form


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
        file found are created. Four fields are provided for the axis
        limits - lower and upper for x and for y - each accepting a
        float in plain or scientific notation, or nothing at all, in
        which case that edge autoscales.

        """
        super().__init__(parent)
        # os.chdir(r"C:\Users\bruce\Documents\Python Scripts\daplis-rtp\src\daplis_rtp\gui\ui")
        # uic.loadUi(
        #     r"MZI_tab.ui",
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

        # Figure widget
        # The '.ui' file carries a 500x425 placeholder where the canvas
        # goes. The real canvas is added over it just below, but the
        # placeholder stays in the grid, and its minimum size alone
        # decided how tall and wide the application had to open.
        self.gridLayout.removeWidget(self.ui.widget_figure)
        self.ui.widget_figure.setParent(None)
        self.ui.widget_figure.deleteLater()

        self.widget_figure = PltCanvas_MZI()
        # self.widget_figure.setMinimumSize(500, 400)
        # self.widget_figure.setFixedSize(500, 425)
        self.widget_figure.setObjectName("widget")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 4, 3)
        reserve_toolbar_width(self.frame, self.widget_figure)

        # Refresh plot and start stream buttons
        self.pushButton_refreshPlot.clicked.connect(self.slot_refresh)

        self.pushButton_startStream.clicked.connect(self.slot_startstream)

        # Set directory if path was pasted instead of chosen with the
        # 'Browse' button
        self.lineEdit_browse.textChanged.connect(self.change_path)

        self.stream_start_time = 0
        self.last_elapsed = 0
        self.pix1 = 0
        self.pix2 = 0

        # Axis limits: one field per edge, all four independent. Empty means
        # "autoscale this edge", which is why these are line edits and not
        # spin boxes - a spin box has no way to say "unset".
        self.limit_fields = (
            self.lineEdit_leftXLim,
            self.lineEdit_rightXLim,
            self.lineEdit_lowerYLim,
            self.lineEdit_upperYLim,
        )
        # Accepts '-1.5', '2e-3', '10e3'. The range is deliberately the full
        # float range: a photon rate and a stream length have no common scale
        # worth capping.
        validator = QtGui.QDoubleValidator(self)
        validator.setNotation(QtGui.QDoubleValidator.ScientificNotation)
        for field in self.limit_fields:
            field.setValidator(validator)
            field.editingFinished.connect(self.slot_updateLimits)

        self.xLim = (None, None)
        self.yLim = (None, None)

        # Browse button
        self.pushButton_Reset.clicked.connect(self.resetPlot)

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
        self.stream_start_time = 0
        self.last_elapsed = 0

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

    @staticmethod
    def _limit_value(field):
        """Return a field's value as a float, or None when it is unset.

        A field left empty - or holding a fragment the validator tolerated
        while typing, such as a lone '-' or 'e' - means that edge should
        autoscale rather than break the plot.

        """
        text = field.text().strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def slot_updateLimits(self):
        """Called when any of the four axis-limit fields is committed.

        Re-reads all four and redraws, so a new limit takes effect without
        waiting for the next data file.

        """
        self.xLim = (
            self._limit_value(self.lineEdit_leftXLim),
            self._limit_value(self.lineEdit_rightXLim),
        )
        self.yLim = (
            self._limit_value(self.lineEdit_lowerYLim),
            self._limit_value(self.lineEdit_upperYLim),
        )
        self.apply_limits()

    def apply_limits(self):
        """Push the current limits onto the existing plot.

        Applied directly rather than by replotting: the MZI trace is built
        up point by point across refreshes, so there is no single data set
        to redraw from.

        """
        x_lo, x_hi = self.xLim
        y_lo, y_hi = self.yLim
        # Restore autoscaling first, so an edge whose field was just cleared
        # goes back to fitting the data instead of keeping its old value.
        for ax in (self.widget_figure.ax, self.widget_figure.ax2):
            ax.autoscale(enable=True, axis="both")
            ax.relim()
            ax.autoscale_view()
        auto_x = self.widget_figure.ax.get_xlim()
        self.widget_figure.ax.set_xlim(
            auto_x[0] if x_lo is None else x_lo,
            auto_x[1] if x_hi is None else x_hi,
        )
        b1, t1 = self.widget_figure.ax.get_ylim()
        b2, t2 = self.widget_figure.ax2.get_ylim()
        bottom = min(b1, b2) if y_lo is None else y_lo
        top = max(t1, t2, 1) if y_hi is None else y_hi
        self.widget_figure.ax.set_ylim(bottom, top)
        self.widget_figure.ax2.set_ylim(bottom, top)
        self.widget_figure.figure.canvas.draw()
        self.widget_figure.figure.canvas.flush_events()

    def resetPlot(self):
        self.widget_figure.ax.cla()
        self.widget_figure.ax2.cla()
        self.stream_start_time = 0
        self.last_elapsed = 0
        self.pix1 = 0
        self.pix2 = 0
        self.widget_figure.setplotparameters(self.canvas_fontsize)
        self.widget_figure.figure.canvas.draw()
        self.widget_figure.figure.canvas.flush_events()

    def update_time_stamp(self):
        """Called during the cycle of real-time plotting.

        Load data from the last data file found in the directory
        provided.

        """
        stopping = False
        DATA_FILES = glob.glob(os.path.join(self.pathtotimestamp, "*.dat*"))
        try:
            last_file = max(DATA_FILES, key=os.path.getctime)
            new_file_ctime = os.path.getctime(last_file)
        except (ValueError, FileNotFoundError):
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
                    if self.stream_start_time == 0:
                        self.stream_start_time = new_file_ctime
                    elapsed = new_file_ctime - self.stream_start_time
                    self.last_file_ctime = new_file_ctime

                    validtimestamps = sen_pop(
                        last_file,
                        board_number=self.comboBox_mask_2.currentText(),
                        fw_ver=self.comboBox_FW_2.currentText(),
                        timestamps=self.spinBox_timestamps_2.value(),
                        pix_add_fix=self.checkBox_pix_add_fix.isChecked(),
                    )

                    self.widget_figure.setPlotData_MZI(
                        [self.last_elapsed, elapsed],
                        [
                            self.pix1,
                            validtimestamps[self.spinBox_FirstPixel.value()],
                        ],
                        [
                            self.pix2,
                            validtimestamps[self.spinBox_SecondPixel.value()],
                        ],
                        self.xLim,
                        self.yLim,
                        self.canvas_fontsize,
                    )
                    self.last_elapsed = elapsed
                    self.pix1 = validtimestamps[
                        self.spinBox_FirstPixel.value()
                    ]
                    self.pix2 = validtimestamps[
                        self.spinBox_SecondPixel.value()
                    ]

            except (ValueError, FileNotFoundError, OSError):
                msg_window = QtWidgets.QMessageBox()
                msg_window.setText(
                    "Cannot read data file — it may have been removed. "
                    "Check the timestamp setting and firmware version."
                )
                msg_window.setWindowTitle("Error")
                msg_window.exec_()
                self.slot_stopstream()
                stopping = True
