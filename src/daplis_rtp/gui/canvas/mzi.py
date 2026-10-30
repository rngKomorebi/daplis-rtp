"""Two pixels' photon rate against time, on a shared pair of y-axes.

The two arms of a Mach-Zehnder interferometer land on two pixels, and
what is being watched is how their counts move against each other. Both
axes therefore always carry the same limits: two traces on
independently scaled axes cross wherever they like and say nothing.

The trace is kept here as three arrays and redrawn whole. The old canvas
instead added a fresh two-point line segment on every refresh, which
meant an hour's run ended as some thousands of ``Line2D`` objects that
matplotlib walked on every draw - and meant there was no record of the
trace to redraw, so a change of colour could only apply to the points
that came after it.

"""

import numpy as np

from daplis_rtp.gui.canvas.base import BaseCanvas


class MziCanvas(BaseCanvas):
    """Photon rate in two pixels against elapsed time."""

    x_label = "Time (s)"
    y_label = "Photon rate (Hz)"
    twin = True

    def draw_data(self, data):
        t = np.asarray(data["t"], dtype=float)
        y1 = np.asarray(data["y1"], dtype=float)
        y2 = np.asarray(data["y2"], dtype=float)
        if t.size == 0:
            return

        labels = data.get("labels", ("Pixel 1", "Pixel 2"))
        line1, = self.ax.plot(
            t, y1, "-o", color=self.theme.colour(0), label=labels[0]
        )
        line2, = self.ax2.plot(
            t, y2, "-o", color=self.theme.colour(1), label=labels[1]
        )
        # The twin's label sits on the right, where it would otherwise
        # be unlabelled; the legend says which trace is which without
        # the reader having to match colours to axes.
        self.ax2.set_ylabel(self.y_label)
        self.ax.legend(
            handles=[line1, line2],
            # 'best' rather than a corner: the trace fills the plot
            # and any fixed corner is sometimes the one with data in it.
            loc="best",
            framealpha=0.6,
            fontsize=self.fontsize * 0.8,
        )

        self._apply_limits(t, data.get("x_lim"), data.get("y_lim"))

        # After the limits: the glow is drawn to the size the axes have
        # when it is added, so it has to come last.
        self.glow(gradient=False)

        self.scientific_y(self.ax, self.ax2)

    def _apply_limits(self, t, x_lim, y_lim):
        """Apply whichever edges were given and autoscale the rest.

        An edge whose field was left empty - or cleared again - has to
        go back to fitting the data, so autoscaling is switched on and
        the autoscaled value read *before* anything is set: ``set_xlim``
        and ``set_ylim`` latch it off, and an edge set once would
        otherwise stay where it was put forever.

        """
        for ax in (self.ax, self.ax2):
            ax.autoscale(enable=True, axis="both")
            ax.relim()
            ax.autoscale_view()

        x_lo, x_hi = x_lim or (None, None)
        auto_x_lo, _ = self.ax.get_xlim()
        self.ax.set_xlim(
            auto_x_lo if x_lo is None else x_lo,
            # Two seconds of room past the newest point, so a running
            # stream draws into space rather than against the frame.
            t[-1] + 2 if x_hi is None else x_hi,
        )

        # Both axes are read before either is set: the shared limits
        # have to cover the data on both, so the extremes of the pair
        # are what an unset edge falls back to.
        bottom_1, top_1 = self.ax.get_ylim()
        bottom_2, top_2 = self.ax2.get_ylim()
        y_lo, y_hi = y_lim or (None, None)
        shared_bottom = (
            min(bottom_1, bottom_2) if y_lo is None else y_lo
        )
        shared_top = max(top_1, top_2, 1) if y_hi is None else y_hi
        self.ax.set_ylim(shared_bottom, shared_top)
        self.ax2.set_ylim(shared_bottom, shared_top)
