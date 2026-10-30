"""Gaussian fits of the lines in view, refreshed with every file.

The "Peak in view" box describes one peak, the brightest, by its shape
alone. Aligning a spectrometer on a neon lamp wants more than that: every
line on the sensor at once, and a width that is a fitted parameter with
an uncertainty, so that a change in focus can be told apart from noise
while the mirror is still being turned.

What counts as a line is decided by a threshold set by hand. Hot pixels
and lines both stand above the dark floor, and nothing in one trace
tells them apart reliably, but the person at the bench can see which is
which - so the threshold is theirs to set, and the plot shows it as a
dashed line to set it against.

A line is a run of neighbouring pixels above the threshold. Each run is
fitted with a Gaussian on a constant background, over a window wide
enough to see the background on either side, then fitted again over
four sigmas of what the first fit found. Two lines close enough that
the trace never drops below the threshold between them are one run and
one fit: raise the threshold to split them.

The arithmetic is a plain function, like ``peak_stats``, so that it can
be tested on shapes whose answers are known; the strip below only
displays what it returns.

"""

import numpy as np
from PyQt5 import QtCore, QtWidgets
from scipy.optimize import curve_fit

from daplis_rtp.gui.layout import ElidedLabel, SPACING, size_like_ui_tabs
from daplis_rtp.gui.widgets.controls import float_field, float_value

# Below this many usable pixels a four-parameter fit has no degrees of
# freedom left to estimate its own uncertainties from.
MIN_POINTS = 5

# The window refitted around the first result, in sigmas either side.
WINDOW_SIGMAS = 4.0


def gaussian(x, amplitude, centre, sigma, background):
    """The model every line is fitted with."""
    return (
        amplitude * np.exp(-((x - centre) ** 2) / (2.0 * sigma**2))
        + background
    )


def fit_peaks(rates, threshold, x_lim=None, valid=None):
    """Fit a Gaussian to every line above ``threshold`` in view.

    Parameters
    ----------
    rates : array-like
        Photon rate per pixel, indexed by pixel number.
    threshold : float
        Rate a pixel must exceed to belong to a line.
    x_lim : tuple, optional
        ``(low, high)`` pixel numbers, inclusive, as shown on the plot.
        The whole array when omitted.
    valid : array-like, optional
        Truthy for the pixels that may be used. Masked pixels read zero,
        and a zero inside a line would drag its fit down, so they are
        left out of the fit rather than fitted as data.

    Returns
    -------
    list of dict
        One per line, left to right. Each has ``peak_pixel``, ``low``
        and ``high`` (the window fitted). A successful fit adds
        ``amplitude``, ``centre``, ``sigma`` and ``background``, and
        ``centre_err`` and ``sigma_err`` - ``None`` where the fit could
        not say. A failed one has ``error`` instead, saying why.

    """
    rates = np.asarray(rates, dtype=float)
    if rates.size == 0 or threshold is None:
        return []
    usable = (
        np.ones(rates.size, dtype=bool)
        if valid is None
        else np.asarray(valid).astype(bool)
    )

    low, high = (0, rates.size - 1) if x_lim is None else x_lim
    low, high = int(min(low, high)), int(max(low, high))
    low = max(0, low)
    high = min(rates.size - 1, high)
    if high < low:
        return []

    runs = _runs_above(rates, usable, threshold, low, high)
    results = []
    for index, (start, stop) in enumerate(runs):
        # A window may reach out to halfway to the next line and no
        # further, so one line's flank is never fitted as another's
        # background.
        left = low if index == 0 else (runs[index - 1][1] + start + 1) // 2
        right = (
            high if index == len(runs) - 1
            else (stop + runs[index + 1][0]) // 2
        )
        results.append(
            _fit_one(rates, usable, start, stop, left, right)
        )
    return results


def _runs_above(rates, usable, threshold, low, high):
    """``(start, stop)`` of each run of usable pixels above threshold."""
    above = np.zeros(rates.size, dtype=bool)
    above[low : high + 1] = (rates[low : high + 1] > threshold) & usable[
        low : high + 1
    ]
    runs = []
    start = None
    for pixel in range(low, high + 2):
        inside = pixel <= high and above[pixel]
        if inside and start is None:
            start = pixel
        elif not inside and start is not None:
            runs.append((start, pixel - 1))
            start = None
    return runs


def _fit_one(rates, usable, start, stop, left, right):
    peak = start + int(np.argmax(rates[start : stop + 1]))
    result = {"peak_pixel": peak}

    # First guess: the run's own width stands for the line's, and a
    # window three times as wide sees the floor on both sides.
    width = stop - start + 1
    sigma0 = max(0.5, width / 2.355)
    margin = max(3, width)
    window = (max(left, start - margin), min(right, stop + margin))

    params = None
    for attempt in range(2):
        result["low"], result["high"] = window
        pixels = np.arange(window[0], window[1] + 1)
        keep = usable[pixels]
        x = pixels[keep].astype(float)
        y = rates[pixels][keep]
        if x.size < MIN_POINTS:
            if params is None:
                result["error"] = "too few pixels"
                return result
            # The refit window was too tight to use; the first fit
            # stands.
            break

        background0 = float(np.min(y))
        guess = (
            [rates[peak] - background0, float(peak), sigma0, background0]
            if params is None
            else params
        )
        try:
            fitted, cov = curve_fit(
                gaussian,
                x,
                y,
                p0=guess,
                bounds=(
                    [0.0, window[0], 0.05, -np.inf],
                    [np.inf, window[1], float(window[1] - window[0] + 1),
                     np.inf],
                ),
                maxfev=2000,
            )
        except (RuntimeError, ValueError) as err:
            if params is None:
                result["error"] = "fit failed"
                result["detail"] = str(err)
                return result
            break
        params, covariance = list(fitted), cov

        if attempt == 0:
            reach = int(np.ceil(WINDOW_SIGMAS * params[2]))
            centre = int(round(params[1]))
            window = (
                max(left, centre - max(3, reach)),
                min(right, centre + max(3, reach)),
            )

    errors = np.sqrt(np.diag(covariance))
    amplitude, centre, sigma, background = (float(p) for p in params)
    result.update(
        amplitude=amplitude,
        centre=centre,
        sigma=sigma,
        background=background,
        centre_err=_finite(errors[1]),
        sigma_err=_finite(errors[2]),
    )
    return result


def _finite(value):
    value = float(value)
    return value if np.isfinite(value) else None


def describe_fit(fit, short=True):
    """One line for one fit, as the strip and the export show it."""
    if "error" in fit:
        return "px {}: {}".format(fit["peak_pixel"], fit["error"])
    sigma = _with_error(fit["sigma"], fit["sigma_err"])
    if short:
        return "px {:.1f}: σ = {}".format(fit["centre"], sigma)
    return (
        "centre {} px, sigma {} px, FWHM {:.2f} px, "
        "amplitude {:.4g} Hz, background {:.4g} Hz".format(
            _with_error(fit["centre"], fit["centre_err"]),
            sigma,
            fit["sigma"] * 2.3548200450309493,
            fit["amplitude"],
            fit["background"],
        )
    )


def _with_error(value, error):
    """``value ± error``, to as many decimals as the error deserves.

    Two significant figures of the error, between two and four
    decimals: a bright line's sigma is known to a few thousandths of a
    pixel, and printing that as '± 0.00' hides exactly the figure being
    watched. An error larger than the value - a hot pixel fitted as a
    line - is left in scientific notation, where it is unmissable.

    """
    if error is None:
        return "{:.2f} ± ?".format(value)
    if error >= 10:
        return "{:.2f} ± {:.1e}".format(value, error)
    decimals = 2
    if error > 0:
        decimals = int(min(4, max(2, 1 - np.floor(np.log10(error)))))
    return "{:.{d}f} ± {:.{d}f}".format(value, error, d=decimals)


class GaussianFitStrip(QtWidgets.QWidget):
    """The switch, the threshold, and one sigma per line, in one row.

    Sits directly above the plot, under the row naming the brightest
    pixels, so that the widths being watched are read in the same glance
    as the peaks they belong to.

    """

    changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        box = QtWidgets.QHBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(SPACING)

        tip = (
            "Fit a Gaussian on a constant background to every line "
            "above the threshold within the x-limits, on every refresh. "
            "Sigma is in pixels."
        )
        self.checkBox = QtWidgets.QCheckBox("Gaussian fit", self)
        self.checkBox.setToolTip(tip)
        box.addWidget(self.checkBox)

        threshold_tip = (
            "Photon rate a pixel must exceed to count as part of a "
            "line, in Hz. Set it above the hot pixels and below the "
            "lines; it is drawn on the plot as a dashed line. "
            "Accepts '2e5'."
        )
        label = QtWidgets.QLabel("Threshold (Hz)", self)
        label.setToolTip(threshold_tip)
        box.addWidget(label)
        self.thresholdEdit = float_field(self, placeholder="set")
        self.thresholdEdit.setToolTip(threshold_tip)
        size_like_ui_tabs(self.thresholdEdit)
        box.addWidget(self.thresholdEdit)

        box.addSpacing(SPACING)
        self.result = ElidedLabel("", self)
        self.result.setObjectName("readoutValue")
        box.addWidget(self.result, 1)

        self.checkBox.toggled.connect(self.changed.emit)
        self.thresholdEdit.editingFinished.connect(self.changed.emit)

    @property
    def enabled(self):
        return self.checkBox.isChecked()

    def threshold(self):
        return float_value(self.thresholdEdit)

    def clear(self, text=""):
        self.result.setText(text)

    def show_fits(self, fits):
        """Render one refresh's fits, sigma first, in the result line."""
        if not fits:
            self.clear("no lines above threshold")
            return
        self.result.setText("    ".join(describe_fit(f) for f in fits))
        # The full account goes in the tooltip, where the line itself
        # only has room for the width.
        self.result.setToolTip(
            "\n".join(describe_fit(f, short=False) for f in fits)
        )
