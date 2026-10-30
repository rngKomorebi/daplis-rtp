"""Timestamp histogram for one pixel.

Used to check that the output is homogeneous: the histogram of a healthy
pixel has a flat top.

The canvas takes the numbers already extracted. That is a change from
the old ``HistCanvas``, which opened and unpacked the data file itself -
a plot widget that could not be drawn without a LinoSPAD2 file on disk,
and a file reader that could not be tested without a window. The
unpacking now happens in the tab, which is where the firmware version
and the timestamp count are chosen anyway.

"""

import numpy as np

from daplis_rtp.gui.canvas.base import BaseCanvas


class HistogramCanvas(BaseCanvas):
    """Counts against time within the acquisition cycle."""

    x_label = "Time (ps)"
    y_label = "# of timestamps (-)"

    def draw_data(self, data):
        counts = np.asarray(data["counts"])
        edges = np.asarray(data["edges"])

        # 'stairs' rather than 'hist': the counting has already been
        # done by the tab, and re-binning the raw timestamps here would
        # mean the drawing and the export could disagree about what the
        # histogram was.
        if counts.size:
            self.ax.stairs(
                counts,
                edges,
                fill=True,
                color=self.theme.colour(2),
                linewidth=0.3,
            )
        self.glow(gradient=False)

        x_lim = data.get("x_lim")
        if x_lim is not None:
            self.ax.set_xlim(x_lim[0], x_lim[1])

        pixel = data.get("pixel")
        if pixel is not None:
            self.ax.set_title(
                "Pixel {} — {} timestamps".format(
                    pixel, data.get("recorded", int(counts.sum()))
                ),
                color=self.theme.axes_fg,
                fontsize=self.fontsize,
            )
