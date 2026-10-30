"""Single-pixel histogram: when in the cycle one pixel's photons arrive.

Used to check that the output is homogeneous. A healthy pixel fires at a
steady rate through the acquisition window, so its histogram has a flat
top; a sloping or truncated one says the readout is filling up, or that
the light is not steady.

The unpacking lives here rather than in the canvas, which is where it
used to be. A plot widget that cannot be drawn without a LinoSPAD2 file
on disk is one that cannot be tested, and the firmware version and the
timestamp count it needs are chosen on this tab anyway.

"""

import os

import numpy as np
from PyQt5 import QtWidgets

from daplis_rtp.functions.unpack import unpack_bin
from daplis_rtp.gui.canvas import HistogramCanvas
from daplis_rtp.gui.tabs.base import PlotTab
from daplis_rtp.gui.widgets import (
    DirectoryPicker,
    ReadoutStrip,
    daughterboard_combo,
    firmware_combo,
    motherboard_combo,
    pixel_spin,
    timestamps_spin,
)
from daplis_rtp.gui.widgets.controls import float_field

# The acquisition cycle, in picoseconds, and how many bars the histogram
# is drawn with. 250 over a 4 ms cycle is a bin of about 16 us, which is
# fine enough to show the shape and coarse enough to stay smooth.
DEFAULT_CYCLE_LENGTH = 4e9
N_BINS = 250

N_PIXELS = 256


class SinglePixelHistogram(PlotTab):
    """Histogram of one pixel's timestamps within the acquisition cycle."""

    hint_text = (
        "Arrival times of one pixel's photons within the acquisition "
        "cycle. A healthy pixel gives a flat top."
    )
    canvas_class = HistogramCanvas
    session_scope = "single_pixel_histogram"

    def build(self):
        self.cycle_length = DEFAULT_CYCLE_LENGTH
        self._last_histogram = None
        self._last_file = None

        self._build_header()
        self._build_footer()
        self._build_controls()
        self._build_actions()

    def bind_session(self):
        self.session.bind_all(
            {
                "folder": self.picker.lineEdit,
                "daughterboard": self.comboBox_boardNumber,
                "motherboard": self.comboBox_mb_2,
                "firmware": self.comboBox_FW,
                "timestamps": self.spinBox_timestamps,
                "pixel": self.spinBox_enterPixNumber,
                "linear_scale": self.checkBox_linearScale_2,
                "cycle_length": self.lineEdit_cycleLength,
            }
        )

    def on_session_restored(self):
        """Re-read the cycle length out of its restored field.

        Silently, unlike 'cycle_length_change': this runs while the tab
        is still being built, and a warning box here would come up
        before the window it belongs to.

        """
        try:
            value = float(self.lineEdit_cycleLength.text())
        except ValueError:
            value = 0
        if value > 0:
            self.cycle_length = value
        else:
            self.lineEdit_cycleLength.setText("4e9")
            self.cycle_length = DEFAULT_CYCLE_LENGTH

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def plotted_data(self):
        if self._last_histogram is None:
            return None
        counts, edges = self._last_histogram
        centres = (edges[:-1] + edges[1:]) / 2
        return {
            "stem": "single-pixel-histogram",
            "columns": {
                "time_ps": centres,
                "bin_low_ps": edges[:-1],
                "bin_high_ps": edges[1:],
                "counts": counts,
            },
            "notes": [
                "Single pixel histogram - arrival times within the "
                "acquisition cycle",
                "pixel {}".format(self.spinBox_enterPixNumber.value()),
                "source file: {}".format(self._last_file),
                "daughterboard {}, motherboard {}, firmware {}".format(
                    self.comboBox_boardNumber.currentText(),
                    self.comboBox_mb_2.currentText(),
                    self.comboBox_FW.currentText(),
                ),
                "timestamps {}, cycle length {:g} ps in {} bins".format(
                    self.spinBox_timestamps.value(),
                    self.cycle_length,
                    N_BINS,
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
            tip="Folder the board writes its data files to. The newest "
                "'.dat' file in it is the one read.",
        )
        self.header_row(0).addWidget(self.picker)

        self.readout = ReadoutStrip(self)
        self.readout.add(
            "count",
            "Timestamps",
            tip="How many timestamps this pixel contributed to the "
                "histogram. A pixel with none is either masked off, "
                "dead, or in the dark.",
            width=80,
        )
        self.readout.add(
            "file", "File", tip="The data file the histogram was built from."
        )
        self.readout.add_stretch()
        self.header_row(1).addWidget(self.readout)

    def _build_footer(self):
        row = self.footer_row()
        row.addWidget(QtWidgets.QLabel("Cycle length (ps)", self))
        self.lineEdit_cycleLength = float_field(self, placeholder="4e9")
        self.lineEdit_cycleLength.setText("4e9")
        self.lineEdit_cycleLength.setToolTip(
            "Length of one acquisition cycle, which is the width of the "
            "histogram. Accepts scientific notation, e.g. 4e9."
        )
        self.lineEdit_cycleLength.setFixedWidth(120)
        self.lineEdit_cycleLength.editingFinished.connect(
            self.cycle_length_change
        )
        row.addWidget(self.lineEdit_cycleLength)
        row.addStretch(1)

    def _build_controls(self):
        column = self.controls

        self.comboBox_boardNumber = column.add_row(
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
        self.comboBox_FW = column.add_row(
            "Firmware version", firmware_combo()
        )
        self.spinBox_timestamps = column.add_row(
            "Timestamps",
            timestamps_spin(),
            tip="Number of timestamps per pixel per acquisition cycle.",
        )
        self.spinBox_enterPixNumber = column.add_row(
            "Pixel",
            pixel_spin(maximum=N_PIXELS - 1),
            tip="The pixel to build the histogram for.",
        )

        self.checkBox_linearScale_2 = column.add_wide_row(
            QtWidgets.QCheckBox("Linear scale"),
            tip="Clear for a logarithmic y-axis.",
        )
        self.checkBox_linearScale_2.setChecked(True)
        self.checkBox_linearScale_2.toggled.connect(
            self.widget_figure.set_scale_linear
        )

        column.add_stretch()

    def _build_actions(self):
        self.pushButton_refreshPlot = self.actions.add_button(
            "Refresh plot",
            tip="Read the newest file again and rebuild the histogram.",
            primary=True,
        )
        self.pushButton_refreshPlot.clicked.connect(self.slot_refresh)

    # ------------------------------------------------------------------
    # Cycle length
    # ------------------------------------------------------------------

    def cycle_length_change(self):
        text = self.lineEdit_cycleLength.text().strip()
        try:
            value = float(text)
            if value <= 0:
                raise ValueError("the cycle length must be positive")
        except ValueError:
            QtWidgets.QMessageBox.warning(
                self,
                "Cycle length",
                "The cycle length should be a positive number, e.g. 4e9. "
                "Resetting it to the default.",
            )
            self.lineEdit_cycleLength.setText("4e9")
            self.cycle_length = DEFAULT_CYCLE_LENGTH
            return
        self.cycle_length = value

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def refresh(self):
        """Read the newest file and rebuild the histogram.

        There is no stream on this tab: a histogram is something to look
        at, not something to watch move. The button reads the newest
        file every time it is pressed, so a run in progress is followed
        by pressing it again.

        """
        last_file = self.last_data_file(self.picker.path())
        if last_file is None:
            # Always announced: this tab has no stream, so every look is
            # one the user asked for.
            self.report_error(
                "No data files found — check the working directory."
            )
            return

        pixel = self.spinBox_enterPixNumber.value()
        fw_ver = self.comboBox_FW.currentText()

        try:
            data = unpack_bin(
                last_file,
                self.comboBox_boardNumber.currentText(),
                fw_ver,
                self.spinBox_timestamps.value(),
            )
            values = self._pixel_timestamps(data, pixel, fw_ver)
        # ValueError: the firmware version or the timestamp count does
        # not match the file - this used to call 'sys.exit()' deep in
        # the plotting and take the whole application down with it;
        # IndexError: a truncated file; OSError: the file went away
        # between the listing and the read.
        except (ValueError, IndexError, OSError) as err:
            self.report_error(
                "Cannot read data file — it may have been removed. "
                "Check the timestamp setting and the firmware version.",
                err,
            )
            return

        # 250 bars across the cycle, which is the same width the old
        # three-step 'bin_rounder' arithmetic came out at. Binned here
        # rather than inside the canvas so that 'File -> Export' hands
        # over the bars that were drawn, not a second histogram built
        # from the same numbers with whatever defaults it happened to
        # pick.
        edges = np.linspace(0, self.cycle_length, N_BINS + 1)
        counts, edges = np.histogram(values, bins=edges)
        self._last_histogram = (counts, edges)
        self._last_file = last_file

        self.widget_figure.set_data(
            {
                "counts": counts,
                "edges": edges,
                "x_lim": (0, self.cycle_length + 100),
                "pixel": pixel,
                "recorded": int(values.size),
            }
        )
        self.readout.set("count", values.size)
        self.readout.set("file", os.path.basename(last_file))

    @staticmethod
    def _pixel_timestamps(data, pixel, fw_ver):
        """One pixel's positive timestamps, out of its TDC's block.

        The firmware decides how the 256 pixels are laid out across the
        64 TDCs: 2212s groups them column-wise, 2212b row-wise. A
        timestamp of -1 is an empty slot, not a photon.

        """
        pix_coor = (
            np.arange(N_PIXELS).reshape(4, 64).T
            if fw_ver == "2212s"
            else np.arange(N_PIXELS).reshape(64, 4)
        )
        tdc, pix = np.argwhere(pix_coor == pixel)[0]
        block = data[tdc].T
        in_pixel = np.where(block[0] == pix)[0]
        recorded = np.where(block[1][in_pixel] > 0)[0]
        return block[1][in_pixel[recorded]]
