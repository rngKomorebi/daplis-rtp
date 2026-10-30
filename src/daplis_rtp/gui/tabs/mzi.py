"""MZI: the photon rate in two pixels, against time.

The two arms of a Mach-Zehnder interferometer land on two pixels, and
what is being watched is how their counts move against each other as the
interferometer drifts or is driven. One point is added per data file, so
the trace grows at whatever rate the acquisition writes.

"""

import os

import numpy as np
from PyQt5 import QtWidgets

from daplis_rtp.functions.sen_pop import sen_pop
from daplis_rtp.gui.canvas import MziCanvas
from daplis_rtp.gui.tabs.base import PlotTab
from daplis_rtp.gui.widgets import (
    DirectoryPicker,
    LimitPair,
    ReadoutStrip,
    daughterboard_combo,
    firmware_combo,
    motherboard_combo,
    pixel_spin,
    timestamps_spin,
)

N_PIXELS = 256


class MZI(PlotTab):
    """Two pixels' photon rate against elapsed time."""

    hint_text = (
        "Photon rate in two pixels against time — one point per data "
        "file. Start the stream and the trace grows as files arrive."
    )
    canvas_class = MziCanvas
    session_scope = "mzi"

    def build(self):
        # The trace, kept here rather than only on the plot: it is what
        # a change of colour, of limits or of theme is redrawn from.
        self._t = []
        self._y1 = []
        self._y2 = []
        self._stream_start_time = 0

        self._build_header()
        self._build_footer()
        self._build_controls()
        self._build_actions()

    def bind_session(self):
        self.session.bind_all(
            {
                "folder": self.picker.lineEdit,
                "daughterboard": self.comboBox_mask_2,
                "motherboard": self.comboBox_mb_2,
                "firmware": self.comboBox_FW_2,
                "timestamps": self.spinBox_timestamps_2,
                "pix_add_fix": self.checkBox_pix_add_fix,
                "first_pixel": self.spinBox_FirstPixel,
                "second_pixel": self.spinBox_SecondPixel,
                "linear_scale": self.checkBox_linearScale_2,
                "x_low": self.xLimits.low,
                "x_high": self.xLimits.high,
                "y_low": self.yLimits.low,
                "y_high": self.yLimits.high,
            }
        )

    def on_waiting_for_data(self):
        self.readout.set("points", "waiting…")

    def watched_paths(self):
        return [self.picker.path()]

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def plotted_data(self):
        if not self._t:
            return None
        first = self.spinBox_FirstPixel.value()
        second = self.spinBox_SecondPixel.value()
        return {
            "stem": "mzi",
            "columns": {
                "time_s": np.asarray(self._t),
                "rate_pixel_{}_Hz".format(first): np.asarray(self._y1),
                "rate_pixel_{}_Hz".format(second): np.asarray(self._y2),
            },
            "notes": [
                "MZI - photon rate in two pixels against elapsed time",
                "one point per data file; time is measured from the "
                "first file of this run",
                "folder: {}".format(self.picker.path()),
                "daughterboard {}, motherboard {}, firmware {}".format(
                    self.comboBox_mask_2.currentText(),
                    self.comboBox_mb_2.currentText(),
                    self.comboBox_FW_2.currentText(),
                ),
                "timestamps {}, pixel addressing corrected: {}".format(
                    self.spinBox_timestamps_2.value(),
                    self.checkBox_pix_add_fix.isChecked(),
                ),
            ],
        }

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_header(self):
        self.picker = DirectoryPicker(
            self,
            caption="Data folder",
            title="Select Directory",
            tip="Folder the board writes its data files to. One point is "
                "added to the trace per new file.",
        )
        self.header_row(0).addWidget(self.picker)

        self.readout = ReadoutStrip(self)
        self.readout.add("rate1", "Pixel 1", width=90)
        self.readout.add("rate2", "Pixel 2", width=90)
        self.readout.add(
            "elapsed",
            "Elapsed",
            tip="Seconds since the first file of this run.",
            width=70,
        )
        self.readout.add("points", "Points", initial="0", width=50)
        self.readout.add_stretch()
        self.header_row(1).addWidget(self.readout)

    def _build_footer(self):
        row = self.footer_row()
        auto = (
            "Leave an edge empty to let it autoscale. Accepts decimals "
            "and scientific notation, e.g. 10e3."
        )
        self.xLimits = LimitPair(self, caption="x limits (s)", tip=auto)
        self.yLimits = LimitPair(self, caption="y limits (Hz)", tip=auto)
        for pair in (self.xLimits, self.yLimits):
            pair.changed.connect(self._redraw_current)
            row.addWidget(pair)
        row.addStretch(1)

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

        column.add_heading("Interferometer arms")
        self.spinBox_FirstPixel = column.add_row(
            "First pixel",
            pixel_spin(maximum=N_PIXELS - 1),
            tip="Pixel the first arm falls on; drawn on the left y-axis.",
        )
        self.spinBox_SecondPixel = column.add_row(
            "Second pixel",
            pixel_spin(maximum=N_PIXELS - 1),
            tip="Pixel the second arm falls on; drawn on the right "
                "y-axis, which always carries the same limits as the "
                "left one so the two can be compared.",
        )

        self.checkBox_linearScale_2 = column.add_wide_row(
            QtWidgets.QCheckBox("Linear scale"),
            tip="Clear for a logarithmic y-axis on both sides.",
        )
        self.checkBox_linearScale_2.setChecked(True)
        self.checkBox_linearScale_2.toggled.connect(
            self.widget_figure.set_scale_linear
        )

        column.add_stretch()

    def _build_actions(self):
        self.pushButton_refreshPlot = self.actions.add_button(
            "Refresh plot", tip="Read the newest file and add a point now."
        )
        self.pushButton_refreshPlot.clicked.connect(self.slot_refresh)

        self.pushButton_startStream = self.actions.add_button(
            "Start stream",
            tip="Follow the folder, adding a point whenever a newer file "
                "appears.",
            primary=True,
        )
        self.pushButton_startStream.clicked.connect(self.toggle_stream)

        self.pushButton_Reset = self.actions.add_button(
            "Reset",
            tip="Throw the trace away and start the clock again. The "
                "stream, if running, keeps running.",
        )
        self.pushButton_Reset.clicked.connect(self.resetPlot)

    # ------------------------------------------------------------------
    # Stream
    # ------------------------------------------------------------------

    def on_stream_start(self):
        # A run's elapsed time is measured from its own first file, so
        # starting the stream again starts the clock again - but the
        # trace is kept, since 'Reset' is what throws it away.
        self._stream_start_time = 0

    def resetPlot(self):
        self._t, self._y1, self._y2 = [], [], []
        self._stream_start_time = 0
        self.last_file_ctime = 0
        self.readout.set("points", 0)
        self.readout.set("rate1", "—")
        self.readout.set("rate2", "—")
        self.readout.set("elapsed", "—")
        self.widget_figure.clear()

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _redraw_current(self):
        if not self._t:
            return
        self.widget_figure.set_data(
            {
                "t": self._t,
                "y1": self._y1,
                "y2": self._y2,
                "x_lim": self.xLimits.values(),
                "y_lim": self.yLimits.values(),
                "labels": (
                    "Pixel {}".format(self.spinBox_FirstPixel.value()),
                    "Pixel {}".format(self.spinBox_SecondPixel.value()),
                ),
            }
        )

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def refresh(self):
        last_file = self.last_data_file(self.picker.path())
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

        if self._stream_start_time == 0:
            self._stream_start_time = new_ctime
        elapsed = new_ctime - self._stream_start_time

        try:
            rates = sen_pop(
                last_file,
                board_number=self.comboBox_mask_2.currentText(),
                fw_ver=self.comboBox_FW_2.currentText(),
                timestamps=self.spinBox_timestamps_2.value(),
                pix_add_fix=self.checkBox_pix_add_fix.isChecked(),
            )
        except (ValueError, IndexError, OSError) as err:
            self.report_error(
                "Cannot read data file — it may have been removed. "
                "Check the timestamp setting and the firmware version.",
                err,
            )
            return

        rate1 = float(rates[self.spinBox_FirstPixel.value()])
        rate2 = float(rates[self.spinBox_SecondPixel.value()])
        self._t.append(elapsed)
        self._y1.append(rate1)
        self._y2.append(rate2)

        self._redraw_current()
        self.readout.set("rate1", "{:.3g}".format(rate1))
        self.readout.set("rate2", "{:.3g}".format(rate2))
        self.readout.set("elapsed", "{:.1f} s".format(elapsed))
        self.readout.set("points", len(self._t))
