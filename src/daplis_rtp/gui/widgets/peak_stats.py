"""What the peak in view is doing, in numbers.

Aligning a setup means maximising something, and until now the only
figure on screen was which pixel was brightest. That tells you a peak
moved but not whether it got better: a peak that doubles in height while
doubling in width has gained nothing, and one that shifts by half a
pixel is invisible against the sample spacing.

So four numbers, over the x-limits currently shown - which is what makes
them useful, since narrowing the limits onto the signal is how you stop
a hot pixel elsewhere on the sensor dominating the answer:

* the brightest pixel and its rate - where the peak is,
* the centroid - where it is to better than a pixel,
* the FWHM - how tight it is,
* the sum over the view - how much light is getting through at all.

The arithmetic is a plain function so that it can be tested without a
window; the group box below only displays what it returns.

"""

import numpy as np
from PyQt5 import QtWidgets

from daplis_rtp.gui.layout import SPACING, allow_shrink


def peak_stats(rates, x_lim=None):
    """Describe the peak in ``rates`` between the given x-limits.

    Parameters
    ----------
    rates : array-like
        Photon rate per pixel, indexed by pixel number.
    x_lim : tuple, optional
        ``(low, high)`` pixel numbers, inclusive, as shown on the plot.
        The whole array when omitted.

    Returns
    -------
    dict or None
        ``None`` when the window holds nothing to describe - no pixels,
        or every one of them at zero. Otherwise ``peak_pixel``,
        ``peak_rate``, ``centroid``, ``fwhm`` and ``total``, any of
        which except the first two may be ``None`` where the window does
        not support the figure.

    """
    rates = np.asarray(rates, dtype=float)
    if rates.size == 0:
        return None

    low, high = (0, rates.size - 1) if x_lim is None else x_lim
    # Both ends are worked out before either is stored: writing 'low'
    # first and then taking 'max(low, high)' reads back the value just
    # written, so limits given the wrong way round collapsed to a
    # single pixel instead of being swapped.
    low, high = int(min(low, high)), int(max(low, high))
    low = max(0, low)
    high = min(rates.size - 1, high)
    if high < low:
        return None

    pixels = np.arange(low, high + 1)
    window = rates[low : high + 1]
    # A negative rate is not physical; it would only come from a masked
    # pixel multiplied by something odd, and it would poison both the
    # centroid and the sum.
    window = np.clip(window, 0, None)
    if not np.any(window > 0):
        return None

    peak_index = int(np.argmax(window))
    peak_rate = float(window[peak_index])
    total = float(window.sum())
    centroid = float((pixels * window).sum() / total)

    return {
        "peak_pixel": int(pixels[peak_index]),
        "peak_rate": peak_rate,
        "centroid": centroid,
        "fwhm": _fwhm(pixels, window, peak_index),
        "total": total,
    }


def _fwhm(pixels, window, peak_index):
    """Full width at half maximum, in pixels, or ``None``.

    Measured outwards from the peak to the first sample below half
    height on each side, with the crossing interpolated between that
    sample and its neighbour - so a peak a few pixels wide still gets a
    width to a fraction of a pixel rather than to the nearest one.

    ``None`` when the peak runs off either edge of the window, because
    a half-height crossing that is not in view cannot be located: the
    honest answer there is "widen the limits", not a number that is
    wrong by however much was cut off.

    """
    half = window[peak_index] / 2.0

    left = _crossing(pixels, window, peak_index, -1, half)
    right = _crossing(pixels, window, peak_index, +1, half)
    if left is None or right is None:
        return None
    return float(right - left)


def _crossing(pixels, window, peak_index, step, half):
    """Where the trace falls through ``half`` on one side of the peak."""
    index = peak_index
    while 0 <= index + step < window.size:
        index += step
        if window[index] <= half:
            # Linear interpolation between this sample and the one
            # before it, which is still above half.
            previous = index - step
            span = window[previous] - window[index]
            if span <= 0:
                return float(pixels[index])
            fraction = (window[previous] - half) / span
            return float(
                pixels[previous]
                + fraction * (pixels[index] - pixels[previous])
            )
    return None


class PeakStatsPanel(QtWidgets.QGroupBox):
    """The four figures, in the control column.

    Checkable, like the other two status boxes, and for the same reason:
    the tick is a row of the column saved over a check box of its own.
    Cleared, it stops the host asking for the arithmetic at all.

    """

    def __init__(self, parent=None):
        super().__init__("Peak in view", parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.setToolTip(
            "The peak between the current x-limits. Narrow the limits "
            "onto the signal to stop a hot pixel elsewhere on the "
            "sensor deciding these numbers."
        )
        self._values = {}
        self._build_ui()
        self.clear()

    def _build_ui(self):
        grid = QtWidgets.QGridLayout(self)
        # Top margin clears the group-box title, which is drawn over the
        # frame rather than above it.
        grid.setContentsMargins(SPACING + 2, 16, SPACING + 2, SPACING)
        grid.setVerticalSpacing(4)
        grid.setHorizontalSpacing(SPACING)

        rows = (
            (
                "peak",
                "Brightest",
                "The pixel with the highest rate in view, and that rate.",
            ),
            (
                "centroid",
                "Centroid",
                "The rate-weighted mean pixel: where the peak is to "
                "better than one pixel, which is what to watch while "
                "walking a mirror.",
            ),
            (
                "fwhm",
                "FWHM",
                "Full width at half maximum, in pixels. Blank when the "
                "peak runs off the edge of the view - widen the limits.",
            ),
            (
                "total",
                "Sum in view",
                "Every rate between the limits added up: how much light "
                "is getting through, independent of how tightly it is "
                "focused.",
            ),
        )
        for row, (key, caption, tip) in enumerate(rows):
            label = QtWidgets.QLabel(caption, self)
            label.setToolTip(tip)
            grid.addWidget(label, row, 0)
            value = QtWidgets.QLabel("—", self)
            value.setObjectName("readoutValue")
            value.setToolTip(tip)
            allow_shrink(value)
            grid.addWidget(value, row, 1)
            self._values[key] = value
        grid.setColumnStretch(1, 1)

    @property
    def enabled(self):
        return self.isChecked()

    def clear(self, text="—"):
        for value in self._values.values():
            value.setText(text)

    def show_stats(self, stats):
        """Render one refresh's figures, or blank them."""
        if stats is None:
            self.clear("nothing in view")
            return
        self._values["peak"].setText(
            "{}  ({})".format(
                stats["peak_pixel"], _hz(stats["peak_rate"])
            )
        )
        self._values["centroid"].setText(
            "{:.2f}".format(stats["centroid"])
        )
        self._values["fwhm"].setText(
            "—" if stats["fwhm"] is None else "{:.2f} px".format(
                stats["fwhm"]
            )
        )
        self._values["total"].setText(_hz(stats["total"]))


def _hz(value):
    """A rate at three significant figures, with a unit that fits."""
    for limit, suffix, scale in (
        (1e9, "G", 1e9),
        (1e6, "M", 1e6),
        (1e3, "k", 1e3),
    ):
        if abs(value) >= limit:
            return "{:.3g} {}Hz".format(value / scale, suffix)
    return "{:.3g} Hz".format(value)
