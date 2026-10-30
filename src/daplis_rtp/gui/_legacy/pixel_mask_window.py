"""The per-pixel mask, in a window of its own.

The mask is 256 check boxes per board. Kept inside the tab they need a
scroll area about 250 px tall, which is both too small to work in - a
few rows of pixels visible at a time, out of 64 - and large enough to
set the minimum height of the whole application, since the control
column's minimum is the sum of everything stacked in it.

So they live here instead. The tab keeps a button and a count, and the
boxes open in a window that can be dragged next to the plot and left
there: it is not modal, so the stream keeps running and the plot keeps
refreshing while pixels are ticked off, which is the way masking is
actually done - look at the peak, mask it, watch what is left.

The check boxes are created here but belong to the host tab, which
reads them through 'boxes' and 'grids' exactly as it did when they sat
in the scroll area; 'grids[b].itemAt(i).widget()' is still the box for
pixel i, so the preset-mask and reset paths are unchanged.

"""

import numpy as np
from PyQt5 import QtCore, QtWidgets

from daplis_rtp.functions.tdc_occupancy import parse_pixel_spec


class PixelMaskWindow(QtWidgets.QDialog):
    """Non-modal window holding one grid of check boxes per board.

    Parameters
    ----------
    parent : QWidget
        The host tab. The window is a top-level one all the same, so it
        can be moved away from the application and left beside it.
    boards : sequence
        One '(label, columns, rows)' per board; 'columns * rows' must
        come to 'n_pixels'. The boxes are created column by column, the
        order the tabs have always used.
    font : QFont, optional
        Applied to every child, to match the tab it was opened from.
    title : str, optional
        Window title.
    n_pixels : int, optional
        Pixels per board, by default 256.
    """

    # Any check box toggled, or a quick-entry applied.
    changed = QtCore.pyqtSignal()
    # 'Clear all' pressed - the host owns what clearing means, since it
    # also has to clear the 'Preset mask' tick.
    clear_requested = QtCore.pyqtSignal()

    def __init__(
        self,
        parent=None,
        boards=(("", 4, 64),),
        font=None,
        title="Pixel mask",
        n_pixels=256,
    ):
        super().__init__(parent)
        # A plain QDialog would sit on top of the tab it came from;
        # 'Qt.Window' gives it a title bar of its own, so it can be put
        # beside the plot and minimised like any other window.
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(title)
        self.setModal(False)

        self._n_pixels = n_pixels
        self.boxes = []
        self.grids = []
        self._counts = []

        outer = QtWidgets.QVBoxLayout(self)
        columns_row = QtWidgets.QHBoxLayout()
        for index, (label, columns, rows) in enumerate(boards):
            columns_row.addWidget(
                self._board_column(index, label, columns, rows)
            )
        outer.addLayout(columns_row)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.pushButton_clear = QtWidgets.QPushButton("Clear all", self)
        self.pushButton_clear.setToolTip(
            "Unmask every pixel on every board, and release the preset "
            "mask."
        )
        self.pushButton_clear.clicked.connect(self.clear_requested.emit)
        buttons.addWidget(self.pushButton_clear)
        self.pushButton_close = QtWidgets.QPushButton("Close", self)
        self.pushButton_close.clicked.connect(self.hide)
        buttons.addWidget(self.pushButton_close)
        outer.addLayout(buttons)

        if font is not None:
            self.setFont(font)
            for widget in self.findChildren(QtWidgets.QWidget):
                widget.setFont(font)

        self.resize(460 if len(boards) == 1 else 720, 620)
        self.refresh_counts()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _board_column(self, index, label, columns, rows):
        """One board: quick entry, the grid of boxes, and a count."""
        box = QtWidgets.QGroupBox(label or "Pixels", self)
        layout = QtWidgets.QVBoxLayout(box)

        entry_row = QtWidgets.QHBoxLayout()
        entry = QtWidgets.QLineEdit(box)
        entry.setPlaceholderText("12, 40-43")
        entry.setToolTip(
            "Pixels to mask or unmask in one go, as single numbers and "
            "ranges. Faster than hunting for them in the grid when the "
            "hot ones are already known."
        )
        entry_row.addWidget(entry)
        mask_button = QtWidgets.QPushButton("Mask", box)
        mask_button.setMaximumWidth(70)
        unmask_button = QtWidgets.QPushButton("Unmask", box)
        unmask_button.setMaximumWidth(70)
        entry_row.addWidget(mask_button)
        entry_row.addWidget(unmask_button)
        layout.addLayout(entry_row)

        area = QtWidgets.QScrollArea(box)
        area.setWidgetResizable(True)
        contents = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(contents)
        boxes = []
        for col in range(columns):
            for row in range(rows):
                pixel = row + col * rows
                check = QtWidgets.QCheckBox(str(pixel), contents)
                check.stateChanged.connect(self._on_toggled)
                boxes.append(check)
                grid.addWidget(check, row, col, 1, 1)
        area.setWidget(contents)
        layout.addWidget(area)

        count = QtWidgets.QLabel("", box)
        layout.addWidget(count)

        self.boxes.append(boxes)
        self.grids.append(grid)
        self._counts.append(count)

        mask_button.clicked.connect(
            lambda _, i=index, e=entry: self._apply_entry(i, e, True)
        )
        unmask_button.clicked.connect(
            lambda _, i=index, e=entry: self._apply_entry(i, e, False)
        )
        entry.returnPressed.connect(
            lambda i=index, e=entry: self._apply_entry(i, e, True)
        )
        return box

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------

    def _on_toggled(self, _state):
        self.refresh_counts()
        self.changed.emit()

    def _apply_entry(self, index, entry, mask):
        """Tick or untick the pixels named in one board's quick entry."""
        try:
            pixels = parse_pixel_spec(entry.text(), self._n_pixels)
        except ValueError as err:
            QtWidgets.QMessageBox.warning(
                self, "Pixel mask", "{}.".format(err)
            )
            return
        if not len(pixels):
            return
        # One signal for the lot, rather than one per box
        for pixel in pixels:
            self.boxes[index][pixel].blockSignals(True)
            self.boxes[index][pixel].setChecked(mask)
            self.boxes[index][pixel].blockSignals(False)
        entry.clear()
        self.refresh_counts()
        self.changed.emit()

    def refresh_counts(self):
        """Update the 'n masked' line under each board's grid."""
        for boxes, label in zip(self.boxes, self._counts):
            masked = sum(1 for box in boxes if box.isChecked())
            label.setText(
                "{} of {} pixels masked".format(masked, len(boxes))
            )

    def masked_counts(self):
        """Masked pixels per board, for the host's summary label."""
        return [
            sum(1 for box in boxes if box.isChecked()) for boxes in self.boxes
        ]

    def open_beside(self):
        """Show the window, raising it if it is already open."""
        self.show()
        self.raise_()
        self.activateWindow()


def mask_summary(counts):
    """'18 pixels masked', or 'board 1: 18, board 2: 0' for two boards."""
    if len(counts) == 1:
        return "{} masked".format(counts[0])
    return ", ".join(
        "b{}: {}".format(i + 1, n) for i, n in enumerate(counts)
    )


def masked_array(boxes, n_pixels=256):
    """1 where the pixel is *not* masked, as the tabs' mask arrays are."""
    mask = np.ones(n_pixels)
    for pixel, box in enumerate(boxes):
        if box.isChecked():
            mask[pixel] = 0
    return mask
