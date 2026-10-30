"""Status box: how close the readout is to filling its TDC memory.

Each TDC holds 'Timestamps' slots per acquisition cycle, shared by its
four pixels. Once they are full the rest of the cycle is thrown away,
and the data file gives no sign of it - it is exactly the size it would
have been. This box puts that on screen while the stream runs, so the
setting can be chosen to fit the measurement instead of guessed, and so
that a long run cannot truncate unnoticed.

Two rows are shown, and both are needed:

* 'Signal' - the busiest TDC among the pixels being measured. This is
  the one that says whether *this* measurement is affected.
* 'Sensor' - the busiest TDC anywhere on the half. This is usually a
  hot pixel nobody is looking at, but it says whether the board is near
  the edge at all.

The pixels being measured are taken, by default, from what the tab
already knows: every pixel that is not masked and lies inside the
current x-limits. A TDC counts as "of interest" when it holds at least
one such pixel, and all of that TDC's traffic is counted - including
that of a hot pixel sharing it, which is exactly the case that eats the
memory the signal needs. Where the mask is not the whole story, the
pixels can be typed in instead.

'Both boards in step' is the model for the LED colours and the
once-per-run alert. Both tabs that have this box keep it in the same
place - last panel of the control column, above the two buttons - so
that what is read during a run is read in the same place on either.

That column's minimum height is the sum of the panels stacked in it,
and the tallest tab is what decides how tall the whole application
opens, so the rows here are counted. Hence the tick in the group-box
title rather than a check box of its own, and the heading sharing a row
with the first radio button.

"""

import numpy as np
from PyQt5 import QtCore, QtWidgets

from daplis_rtp.functions.tdc_occupancy import (
    SAT_WARN_FRACTION,
    OccupancySummary,
    parse_pixel_spec,
)

# TDCs listed in the "Show details" text of the alert box.
MAX_DETAIL_ROWS = 12


def pixels_of_interest(explicit, mask_valid, x_lim, offset=0, n_pixels=256):
    """Which of one board's pixels are worth watching.

    Parameters
    ----------
    explicit : ndarray or None
        Pixels typed in by hand, in the coordinates of the plot's
        x-axis. None to fall back on the mask and the x-limits.
    mask_valid : array-like
        The tab's mask array for this board, one entry per pixel,
        nonzero where the pixel is *not* masked.
    x_lim : tuple
        Current x-axis limits, in the coordinates of the plot.
    offset : int, optional
        Where this board starts on that x-axis: 0 for a single board or
        for board 1 of the full-sensor tab, 256 for board 2.
    n_pixels : int, optional
        Pixels on the board, by default 256.

    Returns
    -------
    ndarray
        Pixel indices local to the board, 0..n_pixels-1. Empty when the
        board lies wholly outside the x-limits, or when every pixel of
        it is masked.
    """
    if explicit is not None:
        local = explicit - offset
        return local[(local >= 0) & (local < n_pixels)]

    pixels = np.arange(n_pixels)
    inside = (pixels + offset >= min(x_lim)) & (pixels + offset <= max(x_lim))
    return pixels[inside & (np.asarray(mask_valid)[:n_pixels] != 0)]


class BoardOccupancy:
    """One board's occupancy, ready for the panel to render.

    'tdcs' holds the TDCs of interest - the ones carrying the pixels
    being measured - as read out by the board, so a caller using
    'pix_add_fix' must have mapped its pixels through
    'tdc_occupancy.pixel_to_tdc_map' with the same flag. Callers hand
    over one entry per pixel, four of which share a TDC, so the list is
    reduced to the TDCs themselves here.

    """

    def __init__(self, label, occupancy, tdcs):
        self.label = label
        self.occupancy = occupancy
        self.tdcs = np.unique(np.asarray(tdcs, dtype=int))


class TdcOccupancyPanel(QtWidgets.QGroupBox):
    """The status box, and the pixel selection that feeds it."""

    # Re-emitted for hosts that want to log the alert as well.
    problem = QtCore.pyqtSignal(str, str)

    LED_COLORS = {
        "idle": "grey",
        "waiting": "goldenrod",
        "ok": "limegreen",
        "warn": "orange",
        "bad": "red",
    }

    def __init__(self, parent=None, font=None, n_pixels=256):
        super().__init__("TDC memory", parent)
        # The whole box is the switch: a checkable group box puts the
        # tick in the title and greys the contents out when it is
        # cleared, which is a row of the control column saved over a
        # check box of its own. That column's minimum height is the sum
        # of its panels, so a row here is a row of the whole window.
        self.setCheckable(True)
        self.setChecked(True)
        self.setToolTip(
            "Count how many of the 'Timestamps' slots each TDC uses "
            "per acquisition cycle. A TDC that fills up drops the rest "
            "of the cycle without any sign of it in the data file."
        )
        self._n_pixels = n_pixels
        self._spin_timestamps = None
        self._suggestion = None
        self._alerted = False
        self._alert_box = None
        self._build_ui(font)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self, font):
        grid = QtWidgets.QGridLayout(self)
        # Top margin clears the group-box title, which is drawn over the
        # frame rather than above it.
        grid.setContentsMargins(8, 16, 8, 6)
        grid.setVerticalSpacing(4)
        row = 0

        # "Pixels:" heads the first radio button rather than sitting on
        # a row of its own. All three on one line would save another
        # row, but the box would then be some 250 px wider at its
        # minimum, and the control column is what sets how narrow the
        # window can be made - see 'plot_figure.toolbar_min_width'.
        lbl_which = QtWidgets.QLabel("Pixels:", self)
        grid.addWidget(lbl_which, row, 0)
        self.radioButton_auto = QtWidgets.QRadioButton(
            "unmasked, in view", self
        )
        self.radioButton_auto.setChecked(True)
        self.radioButton_auto.setToolTip(
            "Every pixel that is not masked and lies inside the current "
            "x-limits. Apply the preset mask, or zoom in on the signal, "
            "and this narrows down on its own."
        )
        grid.addWidget(self.radioButton_auto, row, 1, 1, 2)
        row += 1

        self.radioButton_explicit = QtWidgets.QRadioButton("these:", self)
        self.radioButton_explicit.setToolTip(
            "The pixels carrying the signal, when the mask is not the "
            "whole story. Single pixels and ranges, e.g. '143, 156-159'."
        )
        grid.addWidget(self.radioButton_explicit, row, 1)
        self.lineEdit_pixels = QtWidgets.QLineEdit(self)
        self.lineEdit_pixels.setPlaceholderText("143, 156-159")
        self.lineEdit_pixels.setEnabled(False)
        grid.addWidget(self.lineEdit_pixels, row, 2)
        row += 1

        self.label_led_signal = QtWidgets.QLabel("●", self)
        self.label_led_signal.setFixedWidth(18)
        grid.addWidget(self.label_led_signal, row, 0, QtCore.Qt.AlignTop)
        self.label_signal = QtWidgets.QLabel("not running", self)
        self.label_signal.setWordWrap(True)
        self.label_signal.setToolTip(
            "The busiest TDC carrying a pixel of interest: slots used "
            "per cycle, as a median over the cycles. All four pixels of "
            "that TDC share its slots, so a hot pixel next to the "
            "signal shows up here - which is the point."
        )
        grid.addWidget(self.label_signal, row, 1, 1, 2)
        row += 1

        self.label_led_sensor = QtWidgets.QLabel("●", self)
        self.label_led_sensor.setFixedWidth(18)
        grid.addWidget(self.label_led_sensor, row, 0, QtCore.Qt.AlignTop)
        self.label_sensor = QtWidgets.QLabel("", self)
        self.label_sensor.setWordWrap(True)
        self.label_sensor.setToolTip(
            "The busiest TDC anywhere on the sensor, whether or not it "
            "is being measured. Usually a hot pixel; it says how close "
            "to the edge the board is running."
        )
        grid.addWidget(self.label_sensor, row, 1, 1, 2)
        row += 1

        self.label_suggestion = QtWidgets.QLabel("", self)
        self.label_suggestion.setWordWrap(True)
        self.label_suggestion.setToolTip(
            "Slots needed per TDC per cycle, measured here, with room "
            "to spare:\n\n"
            "    4 x rate per pixel x timestamping window\n\n"
            "so 4 x 86 kHz x 4 ms is about 1380. A large 'Timestamps' "
            "costs file size and unpacking time; too small a one costs "
            "data, silently."
        )
        grid.addWidget(self.label_suggestion, row, 0, 1, 2)
        self.pushButton_apply = QtWidgets.QPushButton("Apply", self)
        self.pushButton_apply.setMaximumWidth(70)
        self.pushButton_apply.setEnabled(False)
        self.pushButton_apply.setToolTip(
            "Put the suggested value into the 'Timestamps' box. Takes "
            "effect on the next file."
        )
        grid.addWidget(self.pushButton_apply, row, 2)

        grid.setColumnStretch(1, 1)

        self.radioButton_explicit.toggled.connect(
            self.lineEdit_pixels.setEnabled
        )
        self.pushButton_apply.clicked.connect(self._apply_suggestion)

        if font is not None:
            self.setFont(font)
            for widget in self.findChildren(QtWidgets.QWidget):
                widget.setFont(font)

        self.clear()

    # ------------------------------------------------------------------
    # Host interface
    # ------------------------------------------------------------------

    @property
    def enabled(self):
        """Whether the host should ask for the occupancy at all."""
        return self.isChecked()

    def attach_timestamps_spinbox(self, spin_box):
        """Point 'Apply' at the tab's 'Timestamps' box."""
        self._spin_timestamps = spin_box

    def explicit_pixels(self):
        """The typed-in pixels, or None when the mask is to be used.

        Raises
        ------
        ValueError
            If the text cannot be read as pixels; the caller decides
            whether to report it or to carry on with the mask.
        """
        if not self.radioButton_explicit.isChecked():
            return None
        return parse_pixel_spec(self.lineEdit_pixels.text(), self._n_pixels)

    def reset(self):
        """Called when a stream starts: clear the once-per-run alert."""
        self._alerted = False
        if self._alert_box is not None:
            self._alert_box.close()
            self._alert_box = None

    def clear(self, text="not running"):
        """Blank the readout, e.g. when the check is switched off."""
        self._suggestion = None
        self.pushButton_apply.setEnabled(False)
        self._set_led(self.label_led_signal, "idle")
        self._set_led(self.label_led_sensor, "idle")
        self.label_signal.setText(text)
        self.label_sensor.setText("")
        self.label_suggestion.setText("")

    def show_result(self, boards):
        """Render one refresh.

        Parameters
        ----------
        boards : list of BoardOccupancy
            One entry per board plotted. The worst 'Signal' figure
            across the boards is the one shown, and likewise the worst
            'Sensor' one - a full-sensor run is only as good as its
            worse half.
        """
        if not boards:
            self.clear()
            return

        signal = [
            (board.label, OccupancySummary(board.occupancy, board.tdcs))
            for board in boards
        ]
        sensor = [
            (
                board.label,
                OccupancySummary(
                    board.occupancy, np.arange(board.occupancy.n_tdc)
                ),
            )
            for board in boards
        ]
        multi = len(boards) > 1

        signal_label, signal_worst = max(signal, key=_severity)
        sensor_label, sensor_worst = max(sensor, key=_severity)

        if signal_worst.tdc is None:
            self._set_led(self.label_led_signal, "waiting")
            self.label_signal.setText(
                "no pixels of interest - every pixel in view is masked"
                if self.radioButton_auto.isChecked()
                else "no pixels of interest - the list is empty"
            )
        else:
            self._set_led(self.label_led_signal, signal_worst.state)
            self.label_signal.setText(
                _describe(signal_worst, signal_label if multi else None)
                + _watching(signal_worst, boards)
            )

        self._set_led(self.label_led_sensor, sensor_worst.state)
        self.label_sensor.setText(
            "worst on sensor: "
            + _describe(sensor_worst, sensor_label if multi else None)
        )

        self._show_suggestion(signal_worst)

        # The alert is about the measurement, so it follows the 'Signal'
        # row: a hot TDC nobody is looking at turns the sensor row red
        # but does not interrupt.
        if (
            not self._alerted
            and signal_worst.tdc is not None
            and signal_worst.sat_fraction > SAT_WARN_FRACTION
        ):
            self._alerted = True
            self._alert(signal_label if multi else None, signal_worst, boards)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _set_led(self, led, state):
        led.setStyleSheet(
            "color: {}; font-size: 14px;".format(self.LED_COLORS[state])
        )

    def _show_suggestion(self, summary):
        self._suggestion = summary.suggested_timestamps
        if summary.tdc is None:
            self.label_suggestion.setText("")
            self.pushButton_apply.setEnabled(False)
            return

        if self._suggestion is None:
            self.pushButton_apply.setEnabled(False)
            self.label_suggestion.setText(
                "Timestamps needed: unknown - every cycle filled up, so "
                "the file shows neither the rate nor the window"
            )
            return

        ceiling = (
            self._spin_timestamps.maximum()
            if self._spin_timestamps is not None
            else None
        )
        if ceiling is not None and self._suggestion > ceiling:
            # The ceiling is the firmware's, not the spin box's: there
            # is no setting that would hold this rate, so the answer is
            # to send fewer photons or listen for less time
            self.pushButton_apply.setEnabled(False)
            self.label_suggestion.setText(
                "Timestamps needed: {}, more than the {} the hardware "
                "has - shorten the window or attenuate instead".format(
                    self._suggestion, ceiling
                )
            )
            return

        self.pushButton_apply.setEnabled(True)
        self.label_suggestion.setText(
            "Timestamps suggested: {} (now {})".format(
                self._suggestion, summary.timestamps
            )
        )

    def _apply_suggestion(self):
        if self._spin_timestamps is None or self._suggestion is None:
            return
        self._spin_timestamps.setValue(
            min(self._suggestion, self._spin_timestamps.maximum())
        )

    def _alert(self, label, summary, boards):
        where = "TDC {}".format(summary.tdc)
        if label:
            where = "{}, {}".format(label, where)

        text = (
            "{} filled all {} of its slots in {:.1f} % of the "
            "acquisition cycles.\n\n"
            "Everything after that point in the window is dropped, and "
            "the file gives no sign of it - it is the same size either "
            "way. The loss is rate-dependent, so the two halves of a "
            "full-sensor run truncate at different times and can no "
            "longer be compared.".format(
                where, summary.timestamps, 100 * summary.sat_fraction
            )
        )
        if summary.suggested_timestamps:
            text += "\n\nRaise 'Timestamps' to about {}.".format(
                summary.suggested_timestamps
            )
        else:
            text += (
                "\n\nEvery cycle filled up, so the file shows neither "
                "the true rate nor the length of the window: raise "
                "'Timestamps' well above {} and measure again.".format(
                    summary.timestamps
                )
            )

        self.problem.emit("Readout saturated", text)

        box = QtWidgets.QMessageBox(self)
        box.setWindowTitle("Readout saturated")
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setText(text)
        box.setDetailedText(_detail_text(boards))
        # Not modal: the stream keeps refreshing behind it, and the box
        # is shown at most once per run anyway.
        box.setWindowModality(QtCore.Qt.NonModal)
        box.finished.connect(lambda _: setattr(self, "_alert_box", None))
        self._alert_box = box
        box.show()


def _severity(entry):
    """Sort key putting the worst summary of a pair of boards last."""
    _, summary = entry
    return (summary.sat_fraction, summary.fraction)


def _watching(summary, boards):
    """' (N TDCs watched)', or a note that nothing was narrowed down.

    The comparison is against one board's worth of TDCs, not the sum
    over the boards: each summary covers a single half, so on the
    full-sensor tab a selection of all 64 is still "the whole sensor".

    """
    per_board = max(board.occupancy.n_tdc for board in boards)
    if summary.n_tdc >= per_board:
        return " (whole sensor - mask or zoom in to narrow it down)"
    if summary.n_tdc == 1:
        return " (1 TDC watched)"
    return " ({} TDCs watched)".format(summary.n_tdc)


def _describe(summary, label=None):
    """'TDC 36: 54/150 slots (36 %)', with the saturation if any."""
    where = "TDC {}".format(summary.tdc)
    if label:
        where = "{} {}".format(label, where)
    text = "{}: {:.0f}/{} slots ({:.0f} %)".format(
        where, summary.median_used, summary.timestamps, 100 * summary.fraction
    )
    if summary.sat_fraction > 0:
        text += ", full in {:.1f} % of cycles".format(
            100 * summary.sat_fraction
        )
    return text


def _detail_text(boards):
    """Every TDC that filled up, per board, for the alert's details."""
    lines = []
    for board in boards:
        occupancy = board.occupancy
        saturating = np.flatnonzero(occupancy.sat_fraction > 0)
        header = "{}: {} cycles of {} slots".format(
            board.label, occupancy.cycles, occupancy.timestamps
        )
        if np.isfinite(occupancy.window):
            header += ", window {:.2f} ms".format(occupancy.window * 1e-9)
        else:
            header += ", window unknown (every cycle filled up)"
        lines.append(header)

        if not len(saturating):
            lines.append("    no TDC filled up")
        else:
            of_interest = set(np.asarray(board.tdcs, dtype=int).tolist())
            # Worst first, so the truncated details still carry the
            # TDCs that matter
            order = saturating[
                np.argsort(-occupancy.sat_fraction[saturating])
            ]
            for tdc in order[:MAX_DETAIL_ROWS]:
                line = "    TDC {:2d}  full in {:5.1f} % of cycles".format(
                    tdc, 100 * occupancy.sat_fraction[tdc]
                )
                if np.isfinite(occupancy.fill_time[tdc]):
                    line += "  after {:.2f} ms".format(
                        occupancy.fill_time[tdc] * 1e-9
                    )
                if tdc in of_interest:
                    line += "   <- pixel of interest"
                lines.append(line)
            if len(order) > MAX_DETAIL_ROWS:
                lines.append(
                    "    ... and {} more".format(
                        len(order) - MAX_DETAIL_ROWS
                    )
                )
        lines.append("")
    return "\n".join(lines)
