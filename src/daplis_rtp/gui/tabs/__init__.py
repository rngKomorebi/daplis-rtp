"""The five tabs, in the order the window shows them."""

from daplis_rtp.gui.tabs.full_sensor import LinoSPAD2Dual
from daplis_rtp.gui.tabs.mzi import MZI
from daplis_rtp.gui.tabs.online_plot import LiveTimestamps
from daplis_rtp.gui.tabs.single_pixel_histogram import SinglePixelHistogram
from daplis_rtp.gui.tabs.synchronization import Synchronization

__all__ = [
    "LiveTimestamps",
    "LinoSPAD2Dual",
    "MZI",
    "SinglePixelHistogram",
    "Synchronization",
]
