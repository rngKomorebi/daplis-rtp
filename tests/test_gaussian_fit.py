"""The fits behind the 'Gaussian fit' strip on the online plot.

Checked against lines whose widths are known in advance, with Poisson
noise on top, since a fit that only works on a perfect curve tells the
bench nothing.

"""

import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5")
pytest.importorskip("scipy")

from daplis_rtp.gui.widgets.gaussian_fit import (  # noqa: E402
    describe_fit,
    fit_peaks,
    gaussian,
)

N = 256


def spectrum(lines, background=50.0, seed=0):
    """Poisson-noisy counts for ``[(centre, sigma, height), ...]``."""
    x = np.arange(N, dtype=float)
    mean = np.full(N, background)
    for centre, sigma, height in lines:
        mean += gaussian(x, height, centre, sigma, 0.0)
    return np.random.default_rng(seed).poisson(mean).astype(float)


def test_every_line_above_threshold_is_fitted():
    rates = spectrum([(40.3, 1.8, 3000), (120.0, 2.5, 2000), (200.7, 3.0,
                                                               1500)])
    fits = fit_peaks(rates, threshold=500)
    assert len(fits) == 3
    for fit, (centre, sigma) in zip(fits, [(40.3, 1.8), (120.0, 2.5),
                                           (200.7, 3.0)]):
        assert "error" not in fit
        assert fit["centre"] == pytest.approx(centre, abs=0.1)
        assert fit["sigma"] == pytest.approx(sigma, rel=0.05)
        # The uncertainty is reported, and is honest about its size
        assert 0 < fit["sigma_err"] < 0.2
        assert abs(fit["sigma"] - sigma) < 5 * fit["sigma_err"]


def test_a_line_below_threshold_is_left_alone():
    rates = spectrum([(60.0, 2.0, 3000), (150.0, 2.0, 300)])
    fits = fit_peaks(rates, threshold=800)
    assert [round(f["centre"]) for f in fits] == [60]


def test_nothing_above_threshold_gives_no_fits():
    assert fit_peaks(spectrum([]), threshold=1e6) == []
    assert fit_peaks(spectrum([]), threshold=None) == []


def test_only_lines_within_the_x_limits_are_fitted():
    rates = spectrum([(40.0, 2.0, 3000), (200.0, 2.0, 3000)])
    fits = fit_peaks(rates, threshold=500, x_lim=(150, 255))
    assert len(fits) == 1
    assert fits[0]["centre"] == pytest.approx(200.0, abs=0.1)


def test_a_masked_pixel_inside_a_line_is_left_out_not_fitted_as_zero():
    rates = spectrum([(100.0, 3.0, 3000)])
    valid = np.ones(N, dtype=bool)
    valid[101] = False
    rates[101] = 0.0
    fit = fit_peaks(rates, threshold=500, valid=valid)[0]
    assert fit["sigma"] == pytest.approx(3.0, rel=0.05)


def test_close_lines_do_not_borrow_each_others_flanks():
    """Each window stops halfway to its neighbour."""
    rates = spectrum([(100.0, 2.0, 3000), (115.0, 2.0, 3000)])
    fits = fit_peaks(rates, threshold=500)
    assert len(fits) == 2
    assert fits[0]["high"] < fits[1]["low"]
    for fit in fits:
        assert fit["sigma"] == pytest.approx(2.0, rel=0.08)


def test_a_failed_fit_says_so_instead_of_raising():
    rates = np.zeros(N)
    rates[10] = 1000.0
    # Four pixels of view leave too few points to fit at all
    fits = fit_peaks(rates, threshold=100, x_lim=(9, 12))
    assert len(fits) == 1
    assert "error" in fits[0]
    assert "10" in describe_fit(fits[0])
