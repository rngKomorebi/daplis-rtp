"""Full Sensor: both halves of the LinoSPAD2 sensor, 512 pixels at once.

Two boards, each writing into a directory of its own, plotted end to end
with a dashed line marking the seam. Pixel-address correction is always
applied to board 2 and never to board 1, as the sensor geometry
requires, so no switch is offered for it; the same holds for the
absolute timestamps, which full-sensor data are always collected with
because they are what synchronizes the two halves.

Both browse rows are used here, which is why every other tab reserves
two as well: the plot has to begin at the same height on all five.

"""

import os

import numpy as np
from PyQt5 import QtWidgets

from daplis_rtp._compat import files
from daplis_rtp.functions.sen_pop import sen_pop
from daplis_rtp.functions.tdc_occupancy import pixel_to_tdc_map
from daplis_rtp.gui.canvas import DualSensorCanvas
from daplis_rtp.gui.tabs.base import PlotTab
from daplis_rtp.gui.widgets import (
    BoardOccupancy,
    DirectoryPicker,
    FileSyncPanel,
    LimitPair,
    PeakStatsPanel,
    PixelMaskWindow,
    TdcOccupancyPanel,
    daughterboard_combo,
    firmware_combo,
    info_badge,
    mask_summary,
    masked_array,
    motherboard_combo,
    peak_stats,
    pixels_of_interest,
    timestamps_spin,
)

N_PIXELS = 256
N_PIXELS_TOTAL = 2 * N_PIXELS


class LinoSPAD2Dual(PlotTab):
    """Photon rate across both sensor halves, from two boards at once."""

    hint_text = (
        "Both sensor halves end to end, from two boards writing in "
        "step. Board 2 is always address-corrected; Ctrl+click a pixel "
        "to mask it."
    )
    canvas_class = DualSensorCanvas
    session_scope = "full_sensor"

    def build(self):
        self.maskValidPixels = np.ones(N_PIXELS)
        self.maskValidPixels_b2 = np.ones(N_PIXELS)
        # Unmasked, as read. The mask is applied when the plot is drawn,
        # so that ticking a pixel off changes the trace at once rather
        # than at the next pair of files.
        self._last_rates = None
        self._last_files = (None, None)
        self.last_file_ctime_1 = 0
        self.last_file_ctime_2 = 0

        self._build_header()
        self._build_footer()
        self._build_controls()
        self._build_actions()

        self.widget_figure.pixel_ctrl_clicked.connect(self.toggle_pixel_mask)
        self.slot_mask_changed()

    def bind_session(self):
        self.session.bind_all(
            {
                "folder_1": self.picker_1.lineEdit,
                "folder_2": self.picker_2.lineEdit,
                "daughterboard": self.comboBox_mask_2,
                "motherboard_1": self.comboBox_mb_1,
                "motherboard_2": self.comboBox_mb_2,
                "firmware": self.comboBox_FW_2,
                "timestamps": self.spinBox_timestamps_2,
                "linear_scale": self.checkBox_linearScale_2,
                "grouping": self.checkBox_grouping_2,
                "x_low": self.xLimits.low,
                "x_high": self.xLimits.high,
                "boards_in_step": self.fileSyncPanel,
                "tdc_memory": self.panel_occupancy,
                "peak_stats": self.panel_peak,
            }
        )

    def watched_paths(self):
        return [self.picker_1.path(), self.picker_2.path()]

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_header(self):
        self.picker_1 = DirectoryPicker(
            self,
            caption="Board 1 folder",
            title="Select Directory — Board 1",
            tip="Folder board 1 writes its data files to. Pixels 0-255 "
                "of the plot come from here.",
        )
        self.header_row(0).addWidget(self.picker_1)

        self.picker_2 = DirectoryPicker(
            self,
            caption="Board 2 folder",
            title="Select Directory — Board 2",
            tip="Folder board 2 writes its data files to. Pixels "
                "256-511 of the plot come from here, always with the "
                "pixel-address correction applied.",
        )
        self.header_row(1).addWidget(self.picker_2)

    def _build_footer(self):
        self.xLimits = LimitPair(
            self,
            caption="x limits (pixel)",
            spin=True,
            maximum=N_PIXELS_TOTAL - 1,
            values=(0, N_PIXELS_TOTAL - 1),
            tip="The range of pixels shown, spanning both halves. Also "
                "narrows the pixels the TDC memory check watches.",
        )
        self.xLimits.changed.connect(self._redraw_current)
        self.footer_row().addWidget(self.xLimits)
        self.footer_row().addStretch(1)

    def _build_controls(self):
        column = self.controls

        self.comboBox_mask_2 = column.add_row(
            "Daughterboard",
            daughterboard_combo(),
            tip="Shared by both boards: one daughterboard carries the "
                "whole sensor.",
        )
        self.comboBox_mb_1 = column.add_row(
            "Motherboard 1",
            motherboard_combo(),
            tip="Motherboard of board 1, which carries pixels 0-255.",
        )
        self.comboBox_mb_2 = column.add_row(
            "Motherboard 2",
            motherboard_combo(),
            tip="Motherboard of board 2, which carries pixels 256-511.",
        )
        self.comboBox_FW_2 = column.add_row(
            "Firmware version", firmware_combo()
        )
        self.spinBox_timestamps_2 = column.add_row(
            "Timestamps",
            timestamps_spin(),
            tip="Number of timestamps per pixel per acquisition cycle, "
                "the same on both boards.",
        )

        self._build_mask_controls(column)

        self.checkBox_linearScale_2 = column.add_wide_row(
            QtWidgets.QCheckBox("Linear scale"),
            tip="Clear for a logarithmic y-axis.",
        )
        self.checkBox_linearScale_2.setChecked(True)
        self.checkBox_linearScale_2.toggled.connect(
            self.widget_figure.set_scale_linear
        )

        self.checkBox_grouping_2 = column.add_wide_row(
            QtWidgets.QCheckBox("Group of 64"),
            tip="Draw vertical lines at every group boundary on both "
                "halves.",
        )
        self.checkBox_grouping_2.toggled.connect(self._redraw_current)

        # 'Both boards in step' and 'TDC memory', in that order and in
        # the same place they hold on the tabs that also carry them.
        self.fileSyncPanel = FileSyncPanel(
            self, labels=("Board 1", "Board 2")
        )
        column.add_widget(self.fileSyncPanel)

        self.panel_peak = PeakStatsPanel(self)
        self.panel_peak.toggled.connect(self._redraw_current)
        column.add_widget(self.panel_peak)

        self.panel_occupancy = TdcOccupancyPanel(self)
        self.panel_occupancy.attach_timestamps_spinbox(
            self.spinBox_timestamps_2
        )
        column.add_widget(self.panel_occupancy)
        column.add_stretch()

    def _build_mask_controls(self, column):
        box, inner = column.add_group("Pixel mask")

        preset_row = QtWidgets.QHBoxLayout()
        self.checkBox_presetMask_2 = QtWidgets.QCheckBox("Preset mask", box)
        self.checkBox_presetMask_2.stateChanged.connect(
            self.presetmask_pixels
        )
        preset_row.addWidget(self.checkBox_presetMask_2)
        preset_row.addWidget(
            info_badge(
                "The warm-pixel mask of each board, looked up from the "
                "shared daughterboard and that board's motherboard.",
                box,
            )
        )
        preset_row.addStretch(1)
        inner.addLayout(preset_row)

        self.mask_window = PixelMaskWindow(
            self,
            boards=[("Board 1", 4, 64), ("Board 2", 4, 64)],
            title="Pixel mask — Full Sensor",
        )
        self.checkBoxPixel = self.mask_window.boxes[0]
        self.checkBoxPixel_b2 = self.mask_window.boxes[1]
        self.mask_window.changed.connect(self.slot_mask_changed)
        self.mask_window.clear_requested.connect(self.reset_pix_mask)

        button_row = QtWidgets.QHBoxLayout()
        self.pushButton_editMask = QtWidgets.QPushButton("Edit mask…", box)
        self.pushButton_editMask.setToolTip(
            "Open both boards' pixel masks in a window of their own; it "
            "can be left open beside the plot while the stream runs."
        )
        self.pushButton_editMask.clicked.connect(self.mask_window.open_beside)
        button_row.addWidget(self.pushButton_editMask)
        self.pushButton_resetMask_2 = QtWidgets.QPushButton("Reset", box)
        self.pushButton_resetMask_2.clicked.connect(self.reset_pix_mask)
        button_row.addWidget(self.pushButton_resetMask_2)
        inner.addLayout(button_row)

        self.label_maskCount = QtWidgets.QLabel("", box)
        self.label_maskCount.setObjectName("tabHint")
        inner.addWidget(self.label_maskCount)

    def _build_actions(self):
        self.pushButton_refreshPlot = self.actions.add_button(
            "Refresh plot", tip="Read the newest file of each board again."
        )
        self.pushButton_refreshPlot.clicked.connect(self.slot_refresh)
        self.pushButton_startStream = self.actions.add_button(
            "Start stream",
            tip="Follow both folders, redrawing whenever either gets a "
                "newer file. Also starts the check that the two boards "
                "keep writing in step.",
            primary=True,
        )
        self.pushButton_startStream.clicked.connect(self.toggle_stream)

    # ------------------------------------------------------------------
    # Stream
    # ------------------------------------------------------------------

    def on_stream_start(self):
        self.last_file_ctime_1 = 0
        self.last_file_ctime_2 = 0
        self.panel_occupancy.reset()
        self.fileSyncPanel.set_paths(
            self.picker_1.path(), self.picker_2.path()
        )
        self.fileSyncPanel.start()

    def on_stream_stop(self):
        self.last_file_ctime_1 = 0
        self.last_file_ctime_2 = 0
        self.fileSyncPanel.stop()

    def on_refresh_requested(self):
        self.last_file_ctime_1 = 0
        self.last_file_ctime_2 = 0
        self.panel_occupancy.reset()

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _redraw_current(self):
        if self._last_rates is None:
            return
        self._plot(self._last_rates)

    def _plot(self, rates):
        low, high = self.xLimits.values()
        masked = rates * self.combined_mask()
        self.widget_figure.set_data(
            {
                "rates": masked,
                "x_lim": (low, high),
                "grouping": self.checkBox_grouping_2.isChecked(),
            }
        )
        if self.panel_peak.enabled:
            self.panel_peak.show_stats(peak_stats(masked, (low, high)))
        else:
            self.panel_peak.clear("switched off")

    def combined_mask(self):
        """Both boards' masks laid end to end on the 0-511 axis."""
        return np.concatenate(
            [self.maskValidPixels, self.maskValidPixels_b2]
        )

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def refresh(self):
        self.mask_pixels()

        path_1 = self.picker_1.path()
        path_2 = self.picker_2.path()
        last_file_1 = self.last_data_file(path_1)
        last_file_2 = self.last_data_file(path_2)

        if last_file_1 is None or last_file_2 is None:
            if last_file_1 is None and last_file_2 is None:
                where = "either working directory"
            elif last_file_1 is None:
                where = "the working directory of board 1"
            else:
                where = "the working directory of board 2"
            self.no_data(
                "No data files found in {} — they may have been "
                "removed. Check both working directories.".format(where)
            )
            return

        try:
            new_ctime_1 = os.path.getctime(last_file_1)
            new_ctime_2 = os.path.getctime(last_file_2)
        except OSError:
            # A file went away between the listing and the question
            return

        if (
            new_ctime_1 <= self.last_file_ctime_1
            and new_ctime_2 <= self.last_file_ctime_2
        ):
            return
        self.last_file_ctime_1 = new_ctime_1
        self.last_file_ctime_2 = new_ctime_2

        fw_ver = self.comboBox_FW_2.currentText()
        timestamps = self.spinBox_timestamps_2.value()
        board = self.comboBox_mask_2.currentText()
        check_slots = self.panel_occupancy.enabled

        try:
            # Full-sensor data are always collected with the absolute
            # timestamps, which are what synchronizes the two boards, so
            # no control is offered for them. Pixel-address correction
            # is always applied to board 2 and never to board 1.
            result_1 = sen_pop(
                last_file_1,
                board_number=board,
                fw_ver=fw_ver,
                timestamps=timestamps,
                pix_add_fix=False,
                absolute_timestamps=True,
                return_occupancy=check_slots,
            )
            result_2 = sen_pop(
                last_file_2,
                board_number=board,
                fw_ver=fw_ver,
                timestamps=timestamps,
                pix_add_fix=True,
                absolute_timestamps=True,
                return_occupancy=check_slots,
            )
        # A file removed while it is being read shows up as OSError; a
        # truncated or half-written one as ValueError or IndexError
        # from the unpacking.
        except (ValueError, IndexError, OSError) as err:
            self.report_error(
                "Cannot read data file — it may have been removed. "
                "Check the timestamp setting and the firmware version; "
                "full-sensor data must hold the absolute timestamps.",
                err,
            )
            return

        if check_slots:
            rates_1, occupancy_1 = result_1
            rates_2, occupancy_2 = result_2
            self.report_occupancy(fw_ver, occupancy_1, occupancy_2)
        else:
            rates_1, rates_2 = result_1, result_2
            self.panel_occupancy.clear("switched off")

        combined = np.concatenate([rates_1, rates_2])
        self._last_rates = combined
        self._last_files = (last_file_1, last_file_2)
        self._plot(combined)

    def report_occupancy(self, fw_ver, occupancy_1, occupancy_2):
        """Hand one refresh's slot occupancy to the status box.

        The pixels of interest are given on the 0-511 x-axis of this
        tab, so each board takes the part of them that falls on its own
        half and maps it to TDCs with the ``pix_add_fix`` its rates were
        built with - always off for board 1 and on for board 2.

        """
        try:
            explicit = self.panel_occupancy.explicit_pixels()
        except ValueError as err:
            # A half-typed pixel list should not blank the readout, and
            # it certainly should not raise into the plotting path
            self.panel_occupancy.clear("pixels of interest: {}".format(err))
            return

        x_lim = self.xLimits.values()
        boards = []
        for label, occupancy, mask, offset, pix_add_fix in (
            ("board 1", occupancy_1, self.maskValidPixels, 0, False),
            ("board 2", occupancy_2, self.maskValidPixels_b2, N_PIXELS, True),
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
    # Export
    # ------------------------------------------------------------------

    def plotted_data(self):
        if self._last_rates is None:
            return None
        mask = self.combined_mask()
        return {
            "stem": "full-sensor",
            "columns": {
                "pixel": np.arange(N_PIXELS_TOTAL),
                "board": np.arange(N_PIXELS_TOTAL) // N_PIXELS + 1,
                "rate_Hz": self._last_rates * mask,
                "masked": 1 - mask.astype(int),
            },
            "notes": [
                "Full Sensor - photon rate across both halves",
                "board 1 file: {}".format(self._last_files[0]),
                "board 2 file: {}".format(self._last_files[1]),
                "daughterboard {}, motherboards {} and {}, firmware "
                "{}".format(
                    self.comboBox_mask_2.currentText(),
                    self.comboBox_mb_1.currentText(),
                    self.comboBox_mb_2.currentText(),
                    self.comboBox_FW_2.currentText(),
                ),
                "timestamps {}; board 2 address-corrected, absolute "
                "timestamps assumed".format(
                    self.spinBox_timestamps_2.value()
                ),
                "x limits shown: {} to {}".format(*self.xLimits.values()),
                "'masked' is 1 where the pixel was masked, and its rate "
                "was forced to zero",
            ],
        }

    # ------------------------------------------------------------------
    # Pixel mask
    # ------------------------------------------------------------------

    def toggle_pixel_mask(self, pixel):
        """Ctrl+click on the plot: mask this pixel, or unmask it.

        The plot's x-axis runs 0-511 across both halves, so which board
        the click landed on is the half it fell in.

        """
        board, local = divmod(int(pixel), N_PIXELS)
        boxes = self.mask_window.boxes[board]
        boxes[local].setChecked(not boxes[local].isChecked())

    def slot_mask_changed(self):
        """Rebuild both masks, update the count, and redraw."""
        self.label_maskCount.setText(
            mask_summary(self.mask_window.masked_counts())
        )
        self.mask_pixels()
        self._redraw_current()

    def mask_pixels(self):
        self.maskValidPixels = masked_array(self.checkBoxPixel, N_PIXELS)
        self.maskValidPixels_b2 = masked_array(
            self.checkBoxPixel_b2, N_PIXELS
        )

    def presetmask_pixels(self):
        """Apply each board's recorded warm-pixel mask, or lift them.

        Each board uses the shared daughterboard and its own motherboard
        to look up its file. A board with no mask recorded is skipped
        silently; the warning comes only when neither has one, since one
        board masked and the other not is a perfectly ordinary state.

        """
        if not self.checkBox_presetMask_2.isChecked():
            self.mask_window.set_all(False)
            return

        board = self.comboBox_mask_2.currentText()
        loaded = False
        for index, combo in (
            (0, self.comboBox_mb_1),
            (1, self.comboBox_mb_2),
        ):
            try:
                path = files("daplis_rtp.params.masks").joinpath(
                    "mask_{}_{}.txt".format(board, combo.currentText())
                )
                mask = np.genfromtxt(path, delimiter=",", dtype="int")
            except (IndexError, FileNotFoundError, OSError):
                continue
            self.mask_window.set_pixels(index, np.atleast_1d(mask), True)
            loaded = True

        if not loaded:
            self.checkBox_presetMask_2.setChecked(False)
            QtWidgets.QMessageBox.warning(
                self,
                "Preset mask",
                "No mask data were found for this daughterboard and "
                "motherboard combination, for either board.",
            )

    def reset_pix_mask(self):
        self.mask_window.set_all(False)
        self.checkBox_presetMask_2.setChecked(False)
