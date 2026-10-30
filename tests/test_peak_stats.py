"""The peak arithmetic behind the 'Peak in view' box.

Kept as a plain function precisely so that it can be checked against
shapes whose answers are known in advance rather than read off a plot.

"""

import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5")

from daplis_rtp.gui.widgets.peak_stats import peak_stats  # noqa: E402

# 2 * sqrt(2 * ln 2), the factor between a Gaussian's sigma and its
# full width at half maximum.
FWHM_PER_SIGMA = 2.3548200450309493


def gaussian(centre, sigma, n=256, height=1000.0):
    x = np.arange(n, dtype=float)
    return height * np.exp(-((x - centre) ** 2) / (2 * sigma**2))


def test_a_clean_peak_is_described_correctly():
    stats = peak_stats(gaussian(100.0, 4.0))
    assert stats["peak_pixel"] == 100
    assert stats["peak_rate"] == pytest.approx(1000.0)
    assert stats["centroid"] == pytest.approx(100.0, abs=1e-6)
    assert stats["fwhm"] == pytest.approx(4.0 * FWHM_PER_SIGMA, abs=0.05)


def test_the_centroid_finds_a_peak_between_two_pixels():
    """The point of the centroid: sub-pixel movement.

    A peak sitting halfway between two pixels has no single brightest
    pixel worth reporting - whichever of the two wins is noise - but its
    centre of mass is exactly where it should be.

    """
    stats = peak_stats(gaussian(100.5, 4.0))
    assert stats["centroid"] == pytest.approx(100.5, abs=1e-6)


def test_the_limits_decide_which_peak_is_described():
    trace = gaussian(60.0, 3.0) + 2 * gaussian(180.0, 3.0)

    assert peak_stats(trace)["peak_pixel"] == 180
    assert peak_stats(trace, (0, 120))["peak_pixel"] == 60


def test_the_sum_covers_only_what_is_in_view():
    trace = np.ones(256)
    assert peak_stats(trace, (0, 255))["total"] == pytest.approx(256.0)
    assert peak_stats(trace, (10, 19))["total"] == pytest.approx(10.0)


def test_nothing_in_view_is_reported_as_nothing():
    assert peak_stats(np.zeros(256)) is None
    assert peak_stats(np.array([])) is None
    # Every pixel in the window masked off to zero
    trace = gaussian(100.0, 4.0)
    trace[:50] = 0
    assert peak_stats(trace, (0, 40)) is None


def test_a_peak_running_off_the_edge_has_no_width():
    """Better no number than one that is wrong by the part cut off."""
    ramp = np.linspace(0, 1000, 256)
    stats = peak_stats(ramp)
    assert stats["peak_pixel"] == 255
    assert stats["fwhm"] is None


def test_limits_given_the_wrong_way_round_still_work():
    trace = gaussian(100.0, 4.0)
    assert peak_stats(trace, (150, 50)) == peak_stats(trace, (50, 150))


def test_limits_outside_the_array_are_clamped():
    trace = gaussian(100.0, 4.0)
    assert peak_stats(trace, (-50, 9999)) == peak_stats(trace)
