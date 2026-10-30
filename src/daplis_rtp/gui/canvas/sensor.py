"""Sensor population: photon rate against pixel number.

Two plots, one class. The single-board tab draws 256 pixels; the
full-sensor tab draws 512, with a dashed line marking the seam between
the two halves and the grouping lines repeated on the second half. That
is the whole of the difference, so it is three class attributes rather
than a second copy of the module.

"""

import numpy as np
from matplotlib.text import Annotation
from PyQt5 import QtCore, QtWidgets

from daplis_rtp.gui.canvas.base import BaseCanvas
from daplis_rtp.gui.widgets.gaussian_fit import gaussian

# Half width at half maximum, in sigmas: where a fitted line is half as
# tall as its peak, which is where a label beside it goes.
HWHM_PER_SIGMA = 1.1774100225154747


class FitLabel(Annotation):
    """A fitted sigma that keeps itself inside the frame.

    Centred over its peak where there is room, which is the ordinary
    case. A line near either x-limit has its label slid inwards rather
    than cut in half by the frame; a line too tall to leave room above
    it has its label beside it, at half height, where the line is narrow
    and the space either side is empty.

    Placed when it is drawn rather than when it is made. Only then are
    the frame's size and the text's size known, and only then does the
    placement survive what happens to the plot afterwards - a toolbar
    zoom, a pan, a resized window, a larger font - none of which hands
    the data in again.

    """

    # Gap between the label and the line, and between it and the frame,
    # in points.
    GAP = 4

    def __init__(self, text, fit, **kwargs):
        peak = (fit["centre"], fit["amplitude"] + fit["background"])
        super().__init__(
            text,
            peak,
            xytext=(0, 0),
            textcoords="offset pixels",
            ha="left",
            va="bottom",
            # Matplotlib's own clip would hide the label whenever the
            # top of the peak is out of view - which is exactly what
            # zooming onto one line's shape does, and exactly when its
            # width is wanted. 'draw' decides instead.
            annotation_clip=False,
            **kwargs,
        )
        self._fit = fit

    def draw(self, renderer):
        if not self.get_visible() or self.axes is None:
            return
        # Shown while the line's centre is in view; a line panned out of
        # the window takes its label with it rather than leaving it
        # pinned to the frame.
        low, high = sorted(self.axes.get_xlim())
        if not low <= self._fit["centre"] <= high:
            return
        self._place(renderer)
        super().draw(renderer)

    def _place(self, renderer):
        frame = self.axes.bbox
        to_pixels = self.axes.transData.transform
        gap = renderer.points_to_pixels(self.GAP)
        fit = self._fit

        peak_x, peak_y = to_pixels(self.xy)
        extent = self.get_window_extent(renderer)
        width, height = extent.width, extent.height

        if peak_y + gap + height <= frame.y1 - gap:
            # Above the peak, centred, slid in from either edge.
            left = peak_x - width / 2.0
            bottom = peak_y + gap
        else:
            # Beside it, at half height: right of the line if it fits,
            # left of it otherwise.
            half = fit["background"] + fit["amplitude"] / 2.0
            reach = HWHM_PER_SIGMA * fit["sigma"]
            right_x, half_y = to_pixels((fit["centre"] + reach, half))
            left_x, _ = to_pixels((fit["centre"] - reach, half))
            left = right_x + gap
            if left + width > frame.x1 - gap:
                left = left_x - gap - width
            bottom = half_y - height / 2.0

        left = min(max(left, frame.x0 + gap), frame.x1 - gap - width)
        bottom = min(max(bottom, frame.y0 + gap), frame.y1 - gap - height)
        self.xyann = (left - peak_x, bottom - peak_y)


class SensorCanvas(BaseCanvas):
    """Photon rate per pixel, for one LinoSPAD2 board."""

    # Ctrl+click on a pixel, carrying the pixel number. The tab decides
    # what that means; here it is only a click turned into a pixel.
    pixel_ctrl_clicked = QtCore.pyqtSignal(int)

    x_label = "Pixel (-)"
    y_label = "Photon rate (Hz)"

    # Where the firmware's four-TDC groups fall. Drawn on request, for
    # aligning a setup on firmware 2212s.
    group_lines = (64, 128, 192)
    # x of the seam between two boards, or None when there is only one.
    boundary = None
    n_pixels = 256

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas.mpl_connect("button_press_event", self._on_click)
        self.canvas.setToolTip(
            "Ctrl+click a pixel to mask or unmask it."
        )

    def _on_click(self, event):
        """Turn a Ctrl+click on the axes into a pixel number.

        The modifier is read from Qt rather than from
        ``event.key``. matplotlib tracks modifiers through its own key
        events, which only reach the canvas once it has keyboard focus,
        so the first Ctrl+click after clicking anywhere else in the
        window would report no modifier at all - masking on a plain
        click, which is precisely what this is meant to avoid.

        """
        if event.inaxes is not self.ax or event.button != 1:
            return
        if event.xdata is None:
            return
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if not modifiers & QtCore.Qt.ControlModifier:
            return
        pixel = int(round(event.xdata))
        if 0 <= pixel < self.n_pixels:
            self.pixel_ctrl_clicked.emit(pixel)

    def draw_data(self, data):
        rates = np.asarray(data["rates"])
        self.ax.plot(rates, "-o", color=self.theme.colour(0))

        if self.boundary is not None:
            self.ax.axvline(
                x=self.boundary,
                color=self.theme.marker,
                linestyle="--",
                linewidth=1.2,
                alpha=0.7,
            )

        if data.get("grouping"):
            for x in self.group_lines:
                self.ax.axvline(
                    x=x,
                    color=self.theme.marker,
                    linewidth=1.0,
                    alpha=0.6,
                )

        x_lim = data.get("x_lim")
        if x_lim is not None:
            self.ax.set_xlim(x_lim[0], x_lim[1])

        # After the limits, not before: the gradient under the trace is
        # drawn as an image sized to the current axes, so a glow added
        # first is stretched by the 'set_xlim' that follows it.
        self.glow()
        self._draw_fits(data)
        self.scientific_y()

    def _draw_fits(self, data):
        """The threshold and the fitted lines, over the data.

        After the glow, so that neither is glowed or filled under, and
        with autoscaling off, so that a threshold set above every pixel
        cannot stretch the axes the glow's gradient was sized to.

        """
        threshold = data.get("fit_threshold")
        fits = data.get("fits") or ()
        if threshold is None and not fits:
            return
        self.ax.set_autoscale_on(False)
        colour = self.theme.colour(1)
        if threshold is not None:
            self.ax.axhline(
                y=threshold,
                color=self.theme.marker,
                linestyle="--",
                linewidth=1.0,
                alpha=0.8,
            )
        for fit in fits:
            if "error" in fit:
                continue
            x = np.linspace(fit["low"], fit["high"], 200)
            self.ax.plot(
                x,
                gaussian(x, fit["amplitude"], fit["centre"], fit["sigma"],
                         fit["background"]),
                color=colour,
                linewidth=1.6,
            )
            # 'add_artist' clips it to the axes as a backstop: a peak
            # zoomed half out of view must not leave its label over the
            # tick labels.
            self.ax.add_artist(
                FitLabel(
                    "σ = {:.2f}".format(fit["sigma"]),
                    fit,
                    color=colour,
                    fontsize=self.fontsize * 0.8,
                )
            )


class DualSensorCanvas(SensorCanvas):
    """Photon rate across both halves of the full sensor, 512 pixels."""

    group_lines = (64, 128, 192, 320, 384, 448)
    boundary = 255.5
    n_pixels = 512
