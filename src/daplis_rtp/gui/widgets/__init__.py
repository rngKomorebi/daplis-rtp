"""Widgets the tabs share: the controls, the two status boxes, the mask."""

from daplis_rtp.gui.widgets.controls import (
    DirectoryPicker,
    LimitPair,
    ReadoutStrip,
    daughterboard_combo,
    firmware_combo,
    float_value,
    info_badge,
    motherboard_combo,
    pixel_spin,
    timestamps_spin,
)
from daplis_rtp.gui.widgets.file_sync import FileSyncPanel
from daplis_rtp.gui.widgets.gaussian_fit import (
    GaussianFitStrip,
    describe_fit,
    fit_peaks,
)
from daplis_rtp.gui.widgets.peak_stats import PeakStatsPanel, peak_stats
from daplis_rtp.gui.widgets.pixel_mask import (
    PixelMaskWindow,
    mask_summary,
    masked_array,
)
from daplis_rtp.gui.widgets.tdc_occupancy import (
    BoardOccupancy,
    TdcOccupancyPanel,
    pixels_of_interest,
)

__all__ = [
    "BoardOccupancy",
    "DirectoryPicker",
    "FileSyncPanel",
    "GaussianFitStrip",
    "LimitPair",
    "PeakStatsPanel",
    "PixelMaskWindow",
    "ReadoutStrip",
    "TdcOccupancyPanel",
    "daughterboard_combo",
    "describe_fit",
    "firmware_combo",
    "fit_peaks",
    "float_value",
    "info_badge",
    "mask_summary",
    "masked_array",
    "motherboard_combo",
    "pixel_spin",
    "peak_stats",
    "pixels_of_interest",
    "timestamps_spin",
]
