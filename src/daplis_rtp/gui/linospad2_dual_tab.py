"""Tab for real-time plotting of the full LinoSPAD2 sensor (2 × 256 pixels).

Layout mirrors the single-board "Online plot" tab.  The left frame holds
two stacked browse rows (one per board), the plot, and the two spin boxes
holding the x-axis limits (0-511, spanning both halves).  The right frame
holds all controls: shared daughterboard/firmware/timestamps selectors,
two motherboard selectors, a shared preset-mask checkbox and reset
button, and the pixel-mask area split into two side-by-side scroll areas
(board 1 left, board 2 right) that together occupy the same space as the
single scroll area in the original tab.

Pixel-address correction is always applied to board 2 (never to board 1)
as required by the sensor geometry; no UI control is exposed for this.
The same holds for the absolute timestamps: full-sensor data are always
collected with them, as they are needed to synchronize the two boards,
so they are always unpacked here.

"""

import glob
import os
from importlib.resources import files

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from daplis_rtp.functions.sen_pop import sen_pop
from daplis_rtp.functions.tdc_occupancy import pixel_to_tdc_map
from daplis_rtp.gui.file_sync_check import FileSyncPanel
from daplis_rtp.gui.pixel_mask_window import PixelMaskWindow, mask_summary
from daplis_rtp.gui.plot_figure import reserve_toolbar_width
from daplis_rtp.gui.plot_figure_dual import PltCanvasDual
from daplis_rtp.gui.tdc_occupancy_panel import (
    BoardOccupancy,
    TdcOccupancyPanel,
    pixels_of_interest,
)


# Width of every combo and spin box in the control column. The tabs
# built from '.ui' files all give theirs a fixed 100 px, which is what
# makes them line up down the column and stay put as the window is
# resized - the label beside each one takes the slack instead. This tab
# builds its column in code, so it has to say the same thing out loud.
CONTROL_BOX_WIDTH = 100


def size_like_ui_tabs(widget, width=CONTROL_BOX_WIDTH):
    """Give a combo or spin box the size the '.ui' tabs give theirs."""
    policy = QtWidgets.QSizePolicy(
        QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
    )
    policy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
    widget.setSizePolicy(policy)
    widget.setMinimumSize(QtCore.QSize(width, 0))
    return widget


class LinoSPAD2Dual(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        font10 = QtGui.QFont()
        font10.setPointSize(10)
        font_bold = QtGui.QFont()
        font_bold.setPointSize(10)
        font_bold.setBold(True)
        font_bold.setWeight(75)

        # ------------------------------------------------------------------
        # Outer grid: frame (col 0, expanding) | frame_2 (col 1, fixed)
        # ------------------------------------------------------------------
        self.gridLayout_2 = QtWidgets.QGridLayout(self)
        self.gridLayout_2.setObjectName("gridLayout_2")

        # ==================================================================
        # RIGHT FRAME (frame_2) — all controls
        # ==================================================================
        self.frame_2 = QtWidgets.QFrame(self)
        sp_fixed = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred
        )
        self.frame_2.setSizePolicy(sp_fixed)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout.setObjectName("verticalLayout")

        # --- Daughterboard (shared) ---
        hl_db = QtWidgets.QHBoxLayout()
        hl_db.setObjectName("horizontalLayout_db")
        lbl_db = QtWidgets.QLabel("LinoSPAD2 daughterboard", self.frame_2)
        lbl_db.setFont(font10)
        lbl_db.setMinimumSize(QtCore.QSize(0, 26))
        hl_db.addWidget(lbl_db)
        self.comboBox_mask_2 = QtWidgets.QComboBox(self.frame_2)
        self.comboBox_mask_2.setFont(font10)
        size_like_ui_tabs(self.comboBox_mask_2)
        self.comboBox_mask_2.setEditable(True)
        self.comboBox_mask_2.setInsertPolicy(
            QtWidgets.QComboBox.InsertAtCurrent
        )
        for item in ["B7d", "NL11", "A5", "D2b"]:
            self.comboBox_mask_2.addItem(item)
        hl_db.addWidget(self.comboBox_mask_2)
        self.verticalLayout.addLayout(hl_db)

        # --- Motherboard Board 1 ---
        hl_mb1 = QtWidgets.QHBoxLayout()
        hl_mb1.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        hl_mb1.setContentsMargins(-1, 0, -1, 0)
        lbl_mb1 = QtWidgets.QLabel("Motherboard Board 1", self.frame_2)
        lbl_mb1.setFont(font10)
        lbl_mb1.setMinimumSize(QtCore.QSize(0, 26))
        hl_mb1.addWidget(lbl_mb1)
        self.comboBox_mb_1 = QtWidgets.QComboBox(self.frame_2)
        self.comboBox_mb_1.setFont(font10)
        size_like_ui_tabs(self.comboBox_mb_1)
        self.comboBox_mb_1.setEditable(True)
        self.comboBox_mb_1.setInsertPolicy(QtWidgets.QComboBox.InsertAtCurrent)
        for item in ["#28", "#33", "#21", "#36", "#37", "#4", "#29"]:
            self.comboBox_mb_1.addItem(item)
        hl_mb1.addWidget(self.comboBox_mb_1)
        self.verticalLayout.addLayout(hl_mb1)

        # --- Motherboard Board 2 ---
        hl_mb2 = QtWidgets.QHBoxLayout()
        hl_mb2.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        hl_mb2.setContentsMargins(-1, 0, -1, 0)
        lbl_mb2 = QtWidgets.QLabel("Motherboard Board 2", self.frame_2)
        lbl_mb2.setFont(font10)
        lbl_mb2.setMinimumSize(QtCore.QSize(0, 26))
        hl_mb2.addWidget(lbl_mb2)
        self.comboBox_mb_2 = QtWidgets.QComboBox(self.frame_2)
        self.comboBox_mb_2.setFont(font10)
        size_like_ui_tabs(self.comboBox_mb_2)
        self.comboBox_mb_2.setEditable(True)
        self.comboBox_mb_2.setInsertPolicy(QtWidgets.QComboBox.InsertAtCurrent)
        for item in ["#28", "#33", "#21", "#36", "#37", "#4", "#29"]:
            self.comboBox_mb_2.addItem(item)
        hl_mb2.addWidget(self.comboBox_mb_2)
        self.verticalLayout.addLayout(hl_mb2)

        # --- Firmware (shared) ---
        hl_fw = QtWidgets.QHBoxLayout()
        hl_fw.setContentsMargins(-1, -1, -1, 0)
        lbl_fw = QtWidgets.QLabel("Firmware version", self.frame_2)
        lbl_fw.setFont(font10)
        lbl_fw.setMinimumSize(QtCore.QSize(0, 26))
        hl_fw.addWidget(lbl_fw)
        self.comboBox_FW_2 = QtWidgets.QComboBox(self.frame_2)
        self.comboBox_FW_2.setFont(font10)
        size_like_ui_tabs(self.comboBox_FW_2)
        for item in ["2212b", "2212s"]:
            self.comboBox_FW_2.addItem(item)
        hl_fw.addWidget(self.comboBox_FW_2)
        self.verticalLayout.addLayout(hl_fw)

        # --- Timestamps (shared) ---
        hl_ts = QtWidgets.QHBoxLayout()
        lbl_ts = QtWidgets.QLabel("Timestamps", self.frame_2)
        lbl_ts.setFont(font10)
        lbl_ts.setMinimumSize(QtCore.QSize(0, 26))
        lbl_ts.setToolTip(
            "Number of timestamps per pixel per acquisition cycle."
        )
        hl_ts.addWidget(lbl_ts)
        self.spinBox_timestamps_2 = QtWidgets.QSpinBox(self.frame_2)
        self.spinBox_timestamps_2.setFont(font10)
        size_like_ui_tabs(self.spinBox_timestamps_2)
        self.spinBox_timestamps_2.setMaximum(1536)
        self.spinBox_timestamps_2.setValue(300)
        hl_ts.addWidget(self.spinBox_timestamps_2)
        self.verticalLayout.addLayout(hl_ts)

        # --- Preset mask + Reset (both boards) ---
        hl_pmask = QtWidgets.QHBoxLayout()
        hl_pmask.setContentsMargins(-1, 0, -1, 0)
        self.checkBox_presetMask_2 = QtWidgets.QCheckBox(
            "Preset mask", self.frame_2
        )
        self.checkBox_presetMask_2.setFont(font10)
        self.checkBox_presetMask_2.setMinimumSize(QtCore.QSize(0, 26))
        hl_pmask.addWidget(self.checkBox_presetMask_2)
        self.label_presetMaskInfo_2 = QtWidgets.QLabel("i", self.frame_2)
        self.label_presetMaskInfo_2.setMinimumSize(QtCore.QSize(20, 20))
        self.label_presetMaskInfo_2.setMaximumSize(QtCore.QSize(20, 20))
        self.label_presetMaskInfo_2.setFont(font10)
        self.label_presetMaskInfo_2.setFrameShape(QtWidgets.QFrame.Box)
        self.label_presetMaskInfo_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_presetMaskInfo_2.setToolTip(
            "Applies the warm-pixel mask for both boards using their "
            "respective motherboard numbers."
        )
        hl_pmask.addWidget(self.label_presetMaskInfo_2)
        hl_pmask.addItem(
            QtWidgets.QSpacerItem(
                5,
                20,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Minimum,
            )
        )
        self.pushButton_resetMask_2 = QtWidgets.QPushButton(
            "Reset Mask", self.frame_2
        )
        self.pushButton_resetMask_2.setFont(font10)
        self.pushButton_resetMask_2.setMinimumSize(QtCore.QSize(90, 21))
        hl_pmask.addWidget(self.pushButton_resetMask_2)
        self.verticalLayout.addLayout(hl_pmask)

        # --- Pixel mask: 256 check boxes per board, in a window ---
        # Side by side in the column they took 250 px and showed a
        # handful of the 128 rows at a time, while setting how tall the
        # whole application opened. In their own window they can be put
        # next to the plot and left there while the stream runs. The
        # boxes are the same objects as before, so 'checkBoxPixel',
        # 'checkBoxPixel_b2' and the two grid layouts still address
        # pixel i as item i.
        self.maskValidPixels = np.zeros(256)
        self.maskValidPixels_b2 = np.zeros(256)
        self.mask_window = PixelMaskWindow(
            self,
            boards=[("Board 1", 2, 128), ("Board 2", 2, 128)],
            font=font10,
            title="Pixel mask — Full Sensor",
        )
        self.checkBoxPixel = self.mask_window.boxes[0]
        self.checkBoxPixel_b2 = self.mask_window.boxes[1]
        self.scrollAreaWidgetContentslayout = self.mask_window.grids[0]
        self.scrollAreaWidgetContentslayout_b2 = self.mask_window.grids[1]
        self.mask_window.changed.connect(self.slot_mask_changed)
        self.mask_window.clear_requested.connect(self.reset_pix_mask)

        hl_mask = QtWidgets.QHBoxLayout()
        self.pushButton_editMask = QtWidgets.QPushButton(
            "Edit mask…", self.frame_2
        )
        self.pushButton_editMask.setFont(font10)
        self.pushButton_editMask.setMinimumSize(QtCore.QSize(0, 26))
        self.pushButton_editMask.setToolTip(
            "Open the pixel mask for both boards in a window of its "
            "own; it can be left open beside the plot while the stream "
            "runs."
        )
        self.pushButton_editMask.clicked.connect(
            self.mask_window.open_beside
        )
        hl_mask.addWidget(self.pushButton_editMask)
        self.label_maskCount = QtWidgets.QLabel("b1: 0, b2: 0", self.frame_2)
        self.label_maskCount.setFont(font10)
        hl_mask.addWidget(self.label_maskCount)
        hl_mask.addStretch(1)
        self.verticalLayout.addLayout(hl_mask)
        self.slot_mask_changed()

        # --- Linear scale + Grouping ---
        hl_opts = QtWidgets.QHBoxLayout()
        hl_opts.setContentsMargins(-1, -1, -1, 0)
        self.checkBox_linearScale_2 = QtWidgets.QCheckBox(
            "Linear scale", self.frame_2
        )
        self.checkBox_linearScale_2.setFont(font10)
        self.checkBox_linearScale_2.setChecked(True)
        hl_opts.addWidget(self.checkBox_linearScale_2)
        hl_opts.addItem(
            QtWidgets.QSpacerItem(
                40,
                20,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Minimum,
            )
        )
        self.checkBox_grouping_2 = QtWidgets.QCheckBox(
            "Group of 64", self.frame_2
        )
        self.checkBox_grouping_2.setFont(font10)
        self.checkBox_grouping_2.setToolTip(
            "Plot vertical lines at 64, 128, 192, 320, 384, 448."
        )
        hl_opts.addWidget(self.checkBox_grouping_2)
        self.verticalLayout.addLayout(hl_opts)

        # --- Both boards in step (background check) ---
        # Fed from the two browse rows on the left; started and stopped
        # together with the stream, which runs for as long as the
        # acquisition does.
        self.fileSyncPanel = FileSyncPanel(
            self.frame_2, font=font10, labels=("Board 1", "Board 2")
        )
        self.verticalLayout.addWidget(self.fileSyncPanel)

        # --- TDC slot occupancy ---
        # How close the readout is to saturation, in the same place as
        # on the "Online plot" tab: last panel of the control column,
        # just above the two buttons. The x-axis of this tab runs 0-511,
        # so the box is told to accept pixel numbers over that whole
        # range rather than a single half's 0-255.
        self.panel_occupancy = TdcOccupancyPanel(
            self.frame_2, font=font10, n_pixels=512
        )
        self.panel_occupancy.attach_timestamps_spinbox(
            self.spinBox_timestamps_2
        )
        self.verticalLayout.addWidget(self.panel_occupancy)

        # --- Refresh + Start stream ---
        self.pushButton_refreshPlot = QtWidgets.QPushButton(
            "Refresh plot", self.frame_2
        )
        self.pushButton_refreshPlot.setFont(font10)
        self.verticalLayout.addWidget(self.pushButton_refreshPlot)

        self.pushButton_startStream = QtWidgets.QPushButton(
            "Start stream", self.frame_2
        )
        self.pushButton_startStream.setFont(font_bold)
        self.pushButton_startStream.setMinimumSize(QtCore.QSize(0, 30))
        self.verticalLayout.addWidget(self.pushButton_startStream)

        self.gridLayout_2.addWidget(self.frame_2, 0, 1, 1, 1)

        # ==================================================================
        # LEFT FRAME (frame) — browse rows + plot + sliders
        # ==================================================================
        self.frame = QtWidgets.QFrame(self)
        sp_expand = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.frame.setSizePolicy(sp_expand)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout = QtWidgets.QGridLayout(self.frame)
        self.gridLayout.setObjectName("gridLayout")

        # Browse row — Board 1 (row 0)
        sp_btn = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.pushButton_browse_1 = QtWidgets.QPushButton("Board 1", self.frame)
        self.pushButton_browse_1.setSizePolicy(sp_btn)
        self.pushButton_browse_1.setMinimumSize(QtCore.QSize(100, 28))
        self.pushButton_browse_1.setFont(font10)
        self.gridLayout.addWidget(self.pushButton_browse_1, 0, 0, 1, 2)
        self.lineEdit_browse_1 = QtWidgets.QLineEdit(self.frame)
        self.lineEdit_browse_1.setMinimumSize(QtCore.QSize(0, 28))
        self.gridLayout.addWidget(self.lineEdit_browse_1, 0, 2, 1, 1)

        # Browse row — Board 2 (row 1)
        self.pushButton_browse_2 = QtWidgets.QPushButton("Board 2", self.frame)
        self.pushButton_browse_2.setSizePolicy(sp_btn)
        self.pushButton_browse_2.setMinimumSize(QtCore.QSize(100, 28))
        self.pushButton_browse_2.setFont(font10)
        self.gridLayout.addWidget(self.pushButton_browse_2, 1, 0, 1, 2)
        self.lineEdit_browse_2 = QtWidgets.QLineEdit(self.frame)
        self.lineEdit_browse_2.setMinimumSize(QtCore.QSize(0, 28))
        self.gridLayout.addWidget(self.lineEdit_browse_2, 1, 2, 1, 1)

        # Left x limit (row 6)
        lbl_lx = QtWidgets.QLabel("Left x limit", self.frame)
        lbl_lx.setFont(font10)
        lbl_lx.setMinimumSize(QtCore.QSize(0, 28))
        self.gridLayout.addWidget(lbl_lx, 6, 0, 1, 1)
        self.spinBox_leftXLim = QtWidgets.QSpinBox(self.frame)
        self.spinBox_leftXLim.setFont(font10)
        self.spinBox_leftXLim.setMinimumSize(QtCore.QSize(0, 28))
        self.spinBox_leftXLim.setMaximumSize(QtCore.QSize(120, 16777215))
        self.gridLayout.addWidget(self.spinBox_leftXLim, 6, 1, 1, 2)

        # Right x limit (row 8)
        lbl_rx = QtWidgets.QLabel("Right x limit", self.frame)
        lbl_rx.setFont(font10)
        lbl_rx.setMinimumSize(QtCore.QSize(0, 28))
        self.gridLayout.addWidget(lbl_rx, 8, 0, 1, 1)
        self.spinBox_rightXLim = QtWidgets.QSpinBox(self.frame)
        self.spinBox_rightXLim.setFont(font10)
        self.spinBox_rightXLim.setMinimumSize(QtCore.QSize(0, 28))
        self.spinBox_rightXLim.setMaximumSize(QtCore.QSize(120, 16777215))
        self.gridLayout.addWidget(self.spinBox_rightXLim, 8, 1, 1, 2)

        # Spacer between plot and sliders (row 5)
        self.gridLayout.addItem(
            QtWidgets.QSpacerItem(
                20,
                5,
                QtWidgets.QSizePolicy.Minimum,
                QtWidgets.QSizePolicy.Fixed,
            ),
            5,
            0,
            1,
            3,
        )

        self.gridLayout_2.addWidget(self.frame, 0, 0, 1, 1)

        self.show()

        # ------------------------------------------------------------------
        # State
        # ------------------------------------------------------------------
        self.pathtotimestamp_1 = ""
        self.pathtotimestamp_2 = ""
        self.leftPosition = 0
        self.rightPosition = 511
        self.grouping = False
        self.timerRunning = False
        self.last_file_ctime_1 = 0
        self.last_file_ctime_2 = 0
        self.canvas_fontsize = 16
        # Guard against 'update_time_stamp' re-entering itself, see there
        self._updating = False

        # ------------------------------------------------------------------
        # Plot widget — added programmatically (rows 2-5 of gridLayout)
        # ------------------------------------------------------------------
        self.widget_figure = PltCanvasDual()
        self.widget_figure.setObjectName("widget_figure_dual")
        self.gridLayout.addWidget(self.widget_figure, 2, 0, 3, 3)
        reserve_toolbar_width(self.frame, self.widget_figure)

        # ------------------------------------------------------------------
        # x-limit spin box configuration
        # ------------------------------------------------------------------
        # 0-511, not 0-255: this tab plots both sensor halves side by side,
        # so board 2 lives at pixels 256-511 and a 255 ceiling would put half
        # the sensor out of reach.
        self.spinBox_leftXLim.setRange(0, 511)
        self.spinBox_rightXLim.setRange(0, 511)
        self.spinBox_leftXLim.setValue(0)
        self.spinBox_rightXLim.setValue(511)
        # Commit on Enter/focus loss rather than on every keystroke, so a
        # part-typed number is not clamped against the other limit.
        self.spinBox_leftXLim.setKeyboardTracking(False)
        self.spinBox_rightXLim.setKeyboardTracking(False)

        # ------------------------------------------------------------------
        # Signal connections
        # ------------------------------------------------------------------
        self.pushButton_browse_1.clicked.connect(self.get_dir_1)
        self.pushButton_browse_2.clicked.connect(self.get_dir_2)
        self.lineEdit_browse_1.textChanged.connect(self.change_path_1)
        self.lineEdit_browse_2.textChanged.connect(self.change_path_2)

        self.spinBox_leftXLim.valueChanged.connect(self.slot_updateLeftXLim)
        self.spinBox_rightXLim.valueChanged.connect(self.slot_updateRightXLim)

        self.checkBox_presetMask_2.stateChanged.connect(self.presetmask_pixels)
        self.pushButton_resetMask_2.clicked.connect(self.reset_pix_mask)
        self.comboBox_mask_2.activated.connect(self.reset_pix_mask)

        self.checkBox_linearScale_2.stateChanged.connect(
            self.slot_checkplotscale_2
        )
        self.checkBox_grouping_2.stateChanged.connect(
            self.slot_checkBox_grouping_2
        )

        self.pushButton_refreshPlot.clicked.connect(self.slot_refresh)
        self.pushButton_startStream.clicked.connect(self.slot_startstream)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_time_stamp)

    # ------------------------------------------------------------------
    # Resize — adaptive font size
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        min_width, max_width = 908, 3810
        min_fs, max_fs = 16, 40
        cw = max(min_width, min(max_width, self.size().width()))
        self.canvas_fontsize = min_fs + (
            (cw - min_width) / (max_width - min_width)
        ) * (max_fs - min_fs)
        self.widget_figure.setplotparameters(fontsize=self.canvas_fontsize)
        super().resizeEvent(event)

    # ------------------------------------------------------------------
    # Browse / path
    # ------------------------------------------------------------------

    def get_dir_1(self):
        path = str(
            QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Directory — Board 1"
            )
        )
        self.lineEdit_browse_1.setText(path)
        self.pathtotimestamp_1 = path

    def get_dir_2(self):
        path = str(
            QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Directory — Board 2"
            )
        )
        self.lineEdit_browse_2.setText(path)
        self.pathtotimestamp_2 = path

    def change_path_1(self):
        self.pathtotimestamp_1 = self.lineEdit_browse_1.text()

    def change_path_2(self):
        self.pathtotimestamp_2 = self.lineEdit_browse_2.text()

    # ------------------------------------------------------------------
    # Stream / refresh
    # ------------------------------------------------------------------

    def slot_startstream(self):
        self.last_file_ctime_1 = 0
        self.last_file_ctime_2 = 0
        if self.timerRunning:
            self.timer.stop()
            self.timerRunning = False
            self.pushButton_startStream.setText("Start stream")
            self.fileSyncPanel.stop()
        else:
            self.pushButton_startStream.setText("Stop stream")
            # A new run gets a new saturation warning, even if the last
            # one was already dismissed
            self.panel_occupancy.reset()
            self.timer.start(100)
            self.timerRunning = True
            self.fileSyncPanel.set_paths(
                self.pathtotimestamp_1, self.pathtotimestamp_2
            )
            self.fileSyncPanel.start()

    def slot_stopstream(self):
        self.timer.stop()
        self.timerRunning = False
        self.pushButton_startStream.setText("Start stream")
        self.fileSyncPanel.stop()
        self.last_file_ctime_1 = 0
        self.last_file_ctime_2 = 0

    def slot_refresh(self):
        self.last_file_ctime_1 = 0
        self.last_file_ctime_2 = 0
        # An explicit look again asks for the saturation warning again
        # too - typically the 'Timestamps' setting has just been changed
        self.panel_occupancy.reset()
        self.update_time_stamp()

    # ------------------------------------------------------------------
    # x-axis limits
    # ------------------------------------------------------------------

    def slot_updateLeftXLim(self):
        if self.spinBox_leftXLim.value() >= self.spinBox_rightXLim.value():
            self.spinBox_leftXLim.setValue(self.spinBox_rightXLim.value() - 1)
        self.leftPosition = self.spinBox_leftXLim.value()

    def slot_updateRightXLim(self):
        if self.spinBox_rightXLim.value() <= self.spinBox_leftXLim.value():
            self.spinBox_rightXLim.setValue(self.spinBox_leftXLim.value() + 1)
        self.rightPosition = self.spinBox_rightXLim.value()

    # ------------------------------------------------------------------
    # Display options
    # ------------------------------------------------------------------

    def slot_checkplotscale_2(self):
        self.widget_figure.setPlotScale(
            self.checkBox_linearScale_2.isChecked()
        )

    def slot_checkBox_grouping_2(self):
        self.grouping = self.checkBox_grouping_2.isChecked()

    # ------------------------------------------------------------------
    # Data update
    # ------------------------------------------------------------------

    def _report_error(self, text, details=None):
        """Stop the stream and show an error message box.

        The stream is stopped *before* the box is shown on purpose: a
        modal box runs an event loop of its own, so a timer left running
        would fire `update_time_stamp` again every 100 ms and stack a
        new box on top of this one for as long as it stays open.

        """
        self.slot_stopstream()
        msg = QtWidgets.QMessageBox()
        msg.setText(text)
        if details is not None:
            msg.setDetailedText(str(details))
        msg.setWindowTitle("Error")
        msg.exec_()

    @staticmethod
    def _last_data_file(path):
        """Return the newest '.dat' file in 'path', or None if there is none.

        None is returned both when the directory holds no data files and
        when the files - or the directory itself - are removed while the
        stream is running: 'glob' lists the directory first and
        'getctime' is called on the result afterwards, so a file that
        disappears in between raises OSError instead of simply dropping
        out of the list.

        """
        data_files = glob.glob(os.path.join(path, "*.dat*"))
        try:
            return max(data_files, key=os.path.getctime)
        # ValueError: no data files at all; OSError (FileNotFoundError
        # among them): a file vanished between the listing and the call
        except (ValueError, OSError):
            return None

    def update_time_stamp(self):
        # Both the canvas 'flush_events' and the modal error box spin the
        # event loop, so the 100 ms timer can fire again while this call
        # is still running; without the guard those calls stack up.
        if self._updating:
            return
        self._updating = True
        try:
            self._update_plot()
        finally:
            self._updating = False

    def _update_plot(self):
        self.mask_pixels()

        last_file_1 = self._last_data_file(self.pathtotimestamp_1)
        last_file_2 = self._last_data_file(self.pathtotimestamp_2)

        if last_file_1 is None or last_file_2 is None:
            if last_file_1 is None and last_file_2 is None:
                where = "either working directory"
            elif last_file_1 is None:
                where = "the working directory of board 1"
            else:
                where = "the working directory of board 2"
            self._report_error(
                f"No data files found in {where} — they may have been "
                "removed. Check both working directories."
            )
            return

        try:
            new_ctime_1 = os.path.getctime(last_file_1)
            new_ctime_2 = os.path.getctime(last_file_2)

            if (
                new_ctime_1 > self.last_file_ctime_1
                or new_ctime_2 > self.last_file_ctime_2
            ):
                self.last_file_ctime_1 = new_ctime_1
                self.last_file_ctime_2 = new_ctime_2

                fw_ver = self.comboBox_FW_2.currentText()
                check_slots = self.panel_occupancy.enabled

                # Full-sensor data are always collected with the
                # absolute timestamps, needed to synchronize the two
                # boards, so no UI control is exposed for this.
                result_1 = sen_pop(
                    last_file_1,
                    board_number=self.comboBox_mask_2.currentText(),
                    fw_ver=fw_ver,
                    timestamps=self.spinBox_timestamps_2.value(),
                    pix_add_fix=False,
                    absolute_timestamps=True,
                    return_occupancy=check_slots,
                )
                # Pixel-address correction is always applied to board 2.
                result_2 = sen_pop(
                    last_file_2,
                    board_number=self.comboBox_mask_2.currentText(),
                    fw_ver=fw_ver,
                    timestamps=self.spinBox_timestamps_2.value(),
                    pix_add_fix=True,
                    absolute_timestamps=True,
                    return_occupancy=check_slots,
                )

                if check_slots:
                    rates_1, occupancy_1 = result_1
                    rates_2, occupancy_2 = result_2
                    self.report_occupancy(fw_ver, occupancy_1, occupancy_2)
                else:
                    rates_1, rates_2 = result_1, result_2
                    self.panel_occupancy.clear("switched off")

                rates_1 = rates_1 * self.maskValidPixels
                rates_2 = rates_2 * self.maskValidPixels_b2
                combined = np.concatenate([rates_1, rates_2])

                self.widget_figure.setPlotData(
                    np.arange(0, 512, 1),
                    combined,
                    [self.leftPosition, self.rightPosition],
                    self.grouping,
                    self.canvas_fontsize,
                )

        # A file removed while it is being read shows up here as
        # OSError; a truncated or half-written one as ValueError or
        # IndexError from the unpacking
        except (ValueError, IndexError, OSError) as err:
            self._report_error(
                "Cannot read data file — it may have been removed. "
                "Check the timestamp setting and the firmware "
                "version; full-sensor data must hold the absolute "
                "timestamps.",
                err,
            )

    # ------------------------------------------------------------------
    # TDC slot occupancy
    # ------------------------------------------------------------------

    def report_occupancy(self, fw_ver, occupancy_1, occupancy_2):
        """Hand one refresh's slot occupancy to the status box.

        The pixels of interest are given on the 0-511 x-axis of this
        tab, so each board takes the part of them that falls on its own
        half and maps it to TDCs with the 'pix_add_fix' its rates were
        built with - always off for board 1 and on for board 2.

        """
        try:
            explicit = self.panel_occupancy.explicit_pixels()
        except ValueError as err:
            # A half-typed pixel list should not blank the readout, and
            # it certainly should not raise into the plotting path
            self.panel_occupancy.clear("pixels of interest: {}".format(err))
            return

        x_lim = (self.leftPosition, self.rightPosition)
        boards = []
        for label, occupancy, mask, offset, pix_add_fix in (
            ("board 1", occupancy_1, self.maskValidPixels, 0, False),
            ("board 2", occupancy_2, self.maskValidPixels_b2, 256, True),
        ):
            pixels = pixels_of_interest(explicit, mask, x_lim, offset)
            boards.append(
                BoardOccupancy(
                    label,
                    occupancy,
                    pixel_to_tdc_map(fw_ver, pix_add_fix)[pixels],
                )
            )
        self.panel_occupancy.show_result(boards)

    # ------------------------------------------------------------------
    # Pixel masking
    # ------------------------------------------------------------------

    def slot_mask_changed(self):
        """Keep the count beside the button in step with the boxes.

        The mask arrays themselves are rebuilt by 'mask_pixels' on the
        next refresh, so ticking a box never races the plotting.

        """
        self.label_maskCount.setText(
            mask_summary(self.mask_window.masked_counts())
        )

    def mask_pixels(self):
        for i in range(256):
            self.maskValidPixels[i] = (
                0 if self.checkBoxPixel[i].isChecked() else 1
            )
            self.maskValidPixels_b2[i] = (
                0 if self.checkBoxPixel_b2[i].isChecked() else 1
            )

    def presetmask_pixels(self):
        """Load and apply preset masks for both boards.

        Each board uses the shared daughterboard and its own motherboard
        number to look up the mask file. Boards that have no mask file
        are silently skipped; an error is shown only if neither board has
        a mask.

        """
        if self.checkBox_presetMask_2.isChecked():
            any_loaded = False
            db = self.comboBox_mask_2.currentText()

            # Board 1
            try:
                f1 = files("daplis_rtp.params.masks").joinpath(
                    f"mask_{db}_{self.comboBox_mb_1.currentText()}.txt"
                )
                mask1 = np.genfromtxt(f1, delimiter=",", dtype="int")
                for i in mask1:
                    self.maskValidPixels[i] = 0
                    self.scrollAreaWidgetContentslayout.itemAt(
                        i
                    ).widget().setChecked(True)
                any_loaded = True
            except (IndexError, FileNotFoundError):
                pass

            # Board 2
            try:
                f2 = files("daplis_rtp.params.masks").joinpath(
                    f"mask_{db}_{self.comboBox_mb_2.currentText()}.txt"
                )
                mask2 = np.genfromtxt(f2, delimiter=",", dtype="int")
                for i in mask2:
                    self.maskValidPixels_b2[i] = 0
                    self.scrollAreaWidgetContentslayout_b2.itemAt(
                        i
                    ).widget().setChecked(True)
                any_loaded = True
            except (IndexError, FileNotFoundError):
                pass

            if not any_loaded:
                self.checkBox_presetMask_2.setCheckState(0)
                msg = QtWidgets.QMessageBox()
                msg.setText(
                    "No mask data found for the given daughterboard and "
                    "motherboard combination for either board."
                )
                msg.setWindowTitle("Error")
                msg.exec_()
        else:
            for i in range(256):
                self.scrollAreaWidgetContentslayout.itemAt(
                    i
                ).widget().setChecked(False)
                self.scrollAreaWidgetContentslayout_b2.itemAt(
                    i
                ).widget().setChecked(False)

    def reset_pix_mask(self):
        for i in range(256):
            self.scrollAreaWidgetContentslayout.itemAt(i).widget().setChecked(
                False
            )
            self.scrollAreaWidgetContentslayout_b2.itemAt(
                i
            ).widget().setChecked(False)
        self.checkBox_presetMask_2.setChecked(False)
