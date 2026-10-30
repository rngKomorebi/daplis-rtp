"""Plot canvases: one themed base class and one subclass per plot."""

from daplis_rtp.gui.canvas.base import BaseCanvas, toolbar_min_width
from daplis_rtp.gui.canvas.histogram import HistogramCanvas
from daplis_rtp.gui.canvas.mzi import MziCanvas
from daplis_rtp.gui.canvas.sensor import DualSensorCanvas, SensorCanvas

__all__ = [
    "BaseCanvas",
    "DualSensorCanvas",
    "HistogramCanvas",
    "MziCanvas",
    "SensorCanvas",
    "toolbar_min_width",
]
