"""Online plot: sensor population of one board, refreshed as files land.

The tab the application is mostly used through. A folder is chosen, the
stream is started, and the plot follows the newest file in it - which is
how the setup is aligned, since a change to the optics shows up on the
plot within a file or two.

"""

import os
from importlib.resources import files

import numpy as np
from PyQt5 import QtWidgets

from daplis_rtp.functions.sen_pop import sen_pop
from daplis_rtp.functions.tdc_occupancy import pixel_to_tdc_map
from daplis_rtp.gui.canvas import SensorCanvas
from daplis_rtp.gui.tabs.base import PlotTab
from daplis_rtp.gui.widgets import (
    BoardOccupancy,
    DirectoryPicker,
    GaussianFitStrip,
    LimitPair,
    PeakStatsPanel,
    PixelMaskWindow,
    ReadoutStrip,
    TdcOccupancyPanel,
    daughterboard_combo,
    describe_fit,
    firmware_combo,
    fit_peaks,
    info_badge,
    mask_summary,
    masked_array,
    motherboard_combo,
    peak_stats,
    pixels_of_interest,
    timestamps_spin,
)

N_PIXELS = 256


class LiveTimestamps(PlotTab):
    """Photon rate per pixel, for a single LinoSPAD2 board."""

    hint_text = (
        "Photon rate per pixel, from the newest file in the folder. "
        "Start the stream to follow it as files arrive; Ctrl+click a "
        "pixel to mask it."
    )
    canvas_class = SensorCanvas
    session_scope = "online_plot"

    def build(self):
        self._build_header()
        self._build_footer()
        self._build_controls()
        self._build_actions()

        self.maskValidPixels = np.ones(N_PIXELS)
        # The rates as they were read, before the mask. Masking is
        # applied when the plot is drawn rather than here, so that
        # ticking a pixel off changes the trace at once instead of at
        # the next data file - which is the whole point of being able to
        # Ctrl+click one.
        self._last_rates = None
        self._last_file = None
        self._last_fits = []
        self.widget_figure.pixel_ctrl_clicked.connect(self.toggle_pixel_mask)
        self.slot_mask_changed()

    def bind_session(self):
        self.session.bind_all(
            {
                "folder": self.picker.lineEdit,
                "daughterboard": self.comboBox_mask_2,
                "motherboard": self.comboBox_mb_2,
                "firmware": self.comboBox_FW_2,
                "timestamps": self.spinBox_timestamps_2,
                "pix_add_fix": self.checkBox_pix_add_fix,
                "absolute_timestamps": self.checkBox_abs_timestamps,
                "linear_scale": self.checkBox_linearScale_2,
                "grouping": self.checkBox_grouping_2,
                "x_low": self.xLimits.low,
                "x_high": self.xLimits.high,
                "tdc_memory": self.panel_occupancy,
                "peak_stats": self.panel_peak,
                "gaussian_fit": self.fit_strip.checkBox,
                "fit_threshold": self.fit_strip.thresholdEdit,
            }
        )

    def on_waiting_for_data(self):
        self.readout.set("file", "waiting…")

    def watched_paths(self):
        return [self.picker.path()]

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_header(self):
        self.picker = DirectoryPicker(
            self,
            caption="Data folder",
            title="Select Directory",
            tip="Folder the board writes its data files to. The newest "
                "'.dat' file in it is the one plotted.",
        )
        self.header_row(0).addWidget(self.picker)

        # The two brightest pixels, which used to be a pair of LCD
        # displays in the control column - where they cost every tab in
        # the application a row of height, since the window's minimum is
        # the tallest column of the five.
        self.readout = ReadoutStrip(self)
        self.readout.add(
            "top1",
            "Brightest pixel",
            tip="Pixel with the highest rate in the last file plotted.",
            width=48,
        )
        self.readout.add("top2", "Second", width=48)
        self.readout.add("masked", "Masked", initial="0 masked", width=80)
        self.readout.add(
            "file", "File", tip="The data file the plot was drawn from."
        )
        self.readout.add_stretch()
        self.header_row(1).addWidget(self.readout)

        # Under the brightest pixels: the widths of the lines, read in
        # the same glance as where the peaks are.
        self.fit_strip = self.add_canvas_strip(GaussianFitStrip(self))
        self.fit_strip.changed.connect(self._redraw_current)

    def _build_footer(self):
        self.xLimits = LimitPair(
            self,
            caption="x limits (pixel)",
            spin=True,
            maximum=N_PIXELS - 1,
            values=(0, N_PIXELS - 1),
            tip="The range of pixels shown. Also narrows the pixels the "
                "TDC memory check watches.",
        )
        self.xLimits.changed.connect(self._limits_changed)
        self.footer_row().addWidget(self.xLimits)
        self.footer_row().addStretch(1)

    def _build_controls(self):
        column = self.controls

        self.comboBox_mask_2 = column.add_row(
            "Daughterboard",
            daughterboard_combo(),
            tip="The LinoSPAD2 daughterboard the data came from. "
                "Used, with the motherboard, to pick the preset "
                "mask.",
        )
        self.comboBox_mb_2 = column.add_row(
            "Motherboard",
            motherboard_combo(),
            tip="The LinoSPAD2 motherboard the data came from. "
                "Used to pick the preset mask.",
        )
        self.comboBox_FW_2 = column.add_row(
            "Firmware version", firmware_combo()
        )
        self.spinBox_timestamps_2 = column.add_row(
            "Timestamps",
            timestamps_spin(),
            tip="Number of timestamps per pixel per acquisition cycle.",
        )

        self.checkBox_pix_add_fix = column.add_wide_row(
            QtWidgets.QCheckBox("Correct pixel addressing"),
            tip="Undo the address scrambling of the sensor's second "
                "half, for data that need it.",
        )
        self.checkBox_abs_timestamps = column.add_wide_row(
            QtWidgets.QCheckBox("Absolute timestamps"),
            tip="Tick if the files were collected with absolute "
                "timestamps: two extra 32-bit words at the start of "
                "each acquisition cycle.",
        )

        self._build_mask_controls(column)

        self.checkBox_linearScale_2 = column.add_wide_row(
            QtWidgets.QCheckBox("Linear scale"),
            tip="Clear for a logarithmic y-axis, which is the one to "
                "use when a few bright pixels flatten everything else.",
        )
        self.checkBox_linearScale_2.setChecked(True)
        self.checkBox_linearScale_2.toggled.connect(
            self.widget_figure.set_scale_linear
        )

        self.checkBox_grouping_2 = column.add_wide_row(
            QtWidgets.QCheckBox("Group of 64"),
            tip="Draw vertical lines at pixels 64, 128 and 192, to help "
                "align the peaks within one group of 64.",
        )
        self.checkBox_grouping_2.toggled.connect(self._redraw_current)

        self.panel_peak = PeakStatsPanel(self)
        self.panel_peak.toggled.connect(self._redraw_current)
        column.add_widget(self.panel_peak)

        # Last panel of the column, above the two buttons - the same
        # place it sits on the full-sensor tab, so that what is watched
        # during a run is watched in the same place on either.
        self.panel_occupancy = TdcOccupancyPanel(self)
        self.panel_occupancy.attach_timestamps_spinbox(
            self.spinBox_timestamps_2
        )
        column.add_widget(self.panel_occupancy)
        column.add_stretch()

    def _build_mask_controls(self, column):
        """The preset mask, the count, and the button that opens the grid."""
        box, inner = column.add_group("Pixel mask")

        preset_row = QtWidgets.QHBoxLayout()
        self.checkBox_presetMask_2 = QtWidgets.QCheckBox("Preset mask", box)
        self.checkBox_presetMask_2.stateChanged.connect(
            self.presetmask_pixels
        )
        preset_row.addWidget(self.checkBox_presetMask_2)
        preset_row.addWidget(
            info_badge(
                "The warm-pixel mask recorded for this daughterboard "
                "and motherboard combination.",
                box,
            )
        )
        preset_row.addStretch(1)
        inner.addLayout(preset_row)

        # 256 check boxes, in a window of their own. In the column they
        # took 250 px, which both set how tall the application opened
        # and showed a handful of the 64 rows at a time; here they can
        # be dragged next to the plot and left there while the stream
        # runs.
        self.mask_window = PixelMaskWindow(
            self,
            boards=[("Pixels", 4, 64)],
            title="Pixel mask — Online plot",
        )
        self.checkBoxPixel = self.mask_window.boxes[0]
        self.mask_window.changed.connect(self.slot_mask_changed)
        self.mask_window.clear_requested.connect(self.reset_pix_mask)

        button_row = QtWidgets.QHBoxLayout()
        self.pushButton_editMask = QtWidgets.QPushButton("Edit mask…", box)
        self.pushButton_editMask.setToolTip(
            "Open the pixel mask in a window of its own; it can be left "
            "open beside the plot while the stream runs."
        )
        self.pushButton_editMask.clicked.connect(self.mask_window.open_beside)
        button_row.addWidget(self.pushButton_editMask)
        self.pushButton_resetMask_2 = QtWidgets.QPushButton("Reset", box)
        self.pushButton_resetMask_2.clicked.connect(self.reset_pix_mask)
        button_row.addWidget(self.pushButton_resetMask_2)
        inner.addLayout(button_row)

    def _build_actions(self):
        self.pushButton_refreshPlot = self.actions.add_button(
            "Refresh plot", tip="Read the newest file again and redraw."
        )
        self.pushButton_refreshPlot.clicked.connect(self.slot_refresh)
        self.pushButton_startStream = self.actions.add_button(
            "Start stream",
            tip="Follow the folder, redrawing whenever a newer file "
                "appears in it.",
            primary=True,
        )
        self.pushButton_startStream.clicked.connect(self.toggle_stream)

    # ------------------------------------------------------------------
    # Stream
    # ------------------------------------------------------------------

    def on_stream_start(self):
        # A new run gets a new saturation warning, even if the last one
        # was already dismissed
        self.panel_occupancy.reset()

    def on_refresh_requested(self):
        # An explicit look again asks for the saturation warning again
        # too - typically the 'Timestamps' setting has just been changed
        self.panel_occupancy.reset()

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _limits_changed(self):
        self._redraw_current()

    def _redraw_current(self):
        """Re-apply the display switches without re-reading the file."""
        if self._last_rates is None:
            return
        self._plot(self._last_rates)

    def _plot(self, rates):
        low, high = self.xLimits.values()
        masked = rates * self.maskValidPixels
        threshold, fits = self._fit_lines(masked, (low, high))
        self.widget_figure.set_data(
            {
                "rates": masked,
                "x_lim": (low, high),
                "grouping": self.checkBox_grouping_2.isChecked(),
                "fit_threshold": threshold,
                "fits": fits,
            }
        )
        self._report_peak(masked, (low, high))

    def _fit_lines(self, rates, x_lim):
        """The threshold to draw and the fits above it, or ``None, []``."""
        self._last_fits = []
        if not self.fit_strip.enabled:
            self.fit_strip.clear()
            return None, []
        threshold = self.fit_strip.threshold()
        if threshold is None:
            self.fit_strip.clear("set a threshold to fit")
            return None, []
        self._last_fits = fit_peaks(
            rates, threshold, x_lim, valid=self.maskValidPixels > 0
        )
        self.fit_strip.show_fits(self._last_fits)
        return threshold, self._last_fits

    def _report_peak(self, rates, x_lim):
        if not self.panel_peak.enabled:
            self.panel_peak.clear("switched off")
            return
        self.panel_peak.show_stats(peak_stats(rates, x_lim))

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def refresh(self):
        self.mask_pixels()

        path = self.picker.path()
        last_file = self.last_data_file(path)
        if last_file is None:
            self.no_data(
                "No data files found — check the working directory."
            )
            return

        try:
            new_ctime = os.path.getctime(last_file)
        except OSError:
            # The file went away between the listing and the question
            return
        if new_ctime <= self.last_file_ctime:
            return
        self.last_file_ctime = new_ctime

        fw_ver = self.comboBox_FW_2.currentText()
        pix_add_fix = self.checkBox_pix_add_fix.isChecked()
        check_slots = self.panel_occupancy.enabled

        try:
            result = sen_pop(
                last_file,
                board_number=self.comboBox_mask_2.currentText(),
                fw_ver=fw_ver,
                timestamps=self.spinBox_timestamps_2.value(),
                pix_add_fix=pix_add_fix,
                absolute_timestamps=(
                    self.checkBox_abs_timestamps.isChecked()
                ),
                return_occupancy=check_slots,
            )
        # ValueError: the firmware version or the timestamp count does
        # not match the file; IndexError: a truncated or half-written
        # one; OSError: the file went away while it was being read.
        except (ValueError, IndexError, OSError) as err:
            self.report_error(
                "Cannot read data file — it may have been removed. "
                "Check the timestamp setting, the firmware version, "
                "and whether the data hold absolute timestamps.",
                err,
            )
            return

        if check_slots:
            rates, occupancy = result
            self.report_occupancy(occupancy, fw_ver, pix_add_fix)
        else:
            rates = result
            self.panel_occupancy.clear("switched off")

        self._last_rates = rates
        self._last_file = last_file
        self._plot(rates)
        self._update_readout(rates * self.maskValidPixels, last_file)

    def _update_readout(self, rates, last_file):
        order = np.argsort(rates)
        self.readout.set("top1", int(order[-1]))
        self.readout.set("top2", int(order[-2]))
        self.readout.set("file", os.path.basename(last_file))

    def report_occupancy(self, occupancy, fw_ver, pix_add_fix):
        """Hand one refresh's slot occupancy to the status box.

        The pixels of interest come either from the box's own field or
        from the mask and the x-limits; they are pixel numbers as
        plotted, so they are mapped to TDCs with the same
        ``pix_add_fix`` the rates were built with.

        """
        try:
            explicit = self.panel_occupancy.explicit_pixels()
        except ValueError as err:
            # A half-typed pixel list should not blank the readout, and
            # it certainly should not raise into the plotting path
            self.panel_occupancy.clear("pixels of interest: {}".format(err))
            return

        pixels = pixels_of_interest(
            explicit, self.maskValidPixels, self.xLimits.values()
        )
        tdcs = pixel_to_tdc_map(fw_ver, pix_add_fix)[pixels]
        self.panel_occupancy.show_result([BoardOccupancy("", occupancy, tdcs)])

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def plotted_data(self):
        if self._last_rates is None:
            return None
        return {
            "stem": "online-plot",
            "columns": {
                "pixel": np.arange(N_PIXELS),
                "rate_Hz": self._last_rates * self.maskValidPixels,
                "masked": 1 - self.maskValidPixels.astype(int),
            },
            "notes": [
                "Online plot - photon rate per pixel",
                "source file: {}".format(self._last_file),
                "daughterboard {}, motherboard {}, firmware {}".format(
                    self.comboBox_mask_2.currentText(),
                    self.comboBox_mb_2.currentText(),
                    self.comboBox_FW_2.currentText(),
                ),
                "timestamps {}, pixel addressing corrected: {}".format(
                    self.spinBox_timestamps_2.value(),
                    self.checkBox_pix_add_fix.isChecked(),
                ),
                "x limits shown: {} to {}".format(*self.xLimits.values()),
                "'masked' is 1 where the pixel was masked, and its rate "
                "was forced to zero",
            ]
            + self._fit_notes(),
        }

    def _fit_notes(self):
        if not self._last_fits:
            return []
        return [
            "Gaussian fits above {} Hz (sigma in pixels):".format(
                self.fit_strip.threshold()
            )
        ] + ["  " + describe_fit(f, short=False) for f in self._last_fits]

    # ------------------------------------------------------------------
    # Pixel mask
    # ------------------------------------------------------------------

    def toggle_pixel_mask(self, pixel):
        """Ctrl+click on the plot: mask this pixel, or unmask it."""
        box = self.checkBoxPixel[pixel]
        box.setChecked(not box.isChecked())

    def slot_mask_changed(self):
        """Rebuild the mask, update the count, and redraw.

        Redrawing here is what makes a tick visible at once: the rates
        are kept unmasked, so re-applying the mask to them is the whole
        of the work, and it costs one redraw rather than a re-read of
        the file.

        """
        self.readout.set(
            "masked", mask_summary(self.mask_window.masked_counts())
        )
        self.mask_pixels()
        self._redraw_current()

    def mask_pixels(self):
        self.maskValidPixels = masked_array(self.checkBoxPixel, N_PIXELS)

    def presetmask_pixels(self):
        """Apply the recorded warm-pixel mask, or lift it again.

        The file is looked up from the daughterboard and motherboard
        chosen above; a combination that has no mask recorded says so
        and clears the tick rather than leaving it set over nothing.

        """
        if not self.checkBox_presetMask_2.isChecked():
            self.mask_window.set_all(False)
            return

        try:
            path = files("daplis_rtp.params.masks").joinpath(
                "mask_{}_{}.txt".format(
                    self.comboBox_mask_2.currentText(),
                    self.comboBox_mb_2.currentText(),
                )
            )
            mask = np.genfromtxt(path, delimiter=",", dtype="int")
        except (IndexError, FileNotFoundError, OSError):
            self.checkBox_presetMask_2.setChecked(False)
            QtWidgets.QMessageBox.warning(
                self,
                "Preset mask",
                "No mask data were found for this daughterboard and "
                "motherboard combination.",
            )
            return

        self.mask_window.set_pixels(0, np.atleast_1d(mask), True)

    def reset_pix_mask(self):
        self.mask_window.set_all(False)
        self.checkBox_presetMask_2.setChecked(False)
