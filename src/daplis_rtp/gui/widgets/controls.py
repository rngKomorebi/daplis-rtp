"""The controls the tabs are made of, built once and used by all of them.

Four tabs choose a daughterboard, a motherboard, a firmware version and
a number of timestamps. Before this module each of them built those
four itself, which is how the "Full Sensor" combo boxes came to be 80 px
``Expanding`` while everyone else's were 100 px ``Fixed``, and how one
tab came to offer a motherboard the others did not. A control that
exists once cannot drift.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from daplis_rtp.gui.layout import (
    SPACING,
    allow_shrink,
    control_box_width,
    row_height,
    size_like_ui_tabs,
)

# The hardware the group has. Editable combo boxes, because a board that
# is not on the list is a board that arrived after the last release and
# still has to be usable.
DAUGHTERBOARDS = ("B7d", "NL11", "A5", "D2b")
MOTHERBOARDS = ("#28", "#33", "#21", "#36", "#37", "#4", "#29")
FIRMWARE_VERSIONS = ("2212b", "2212s")

# Slots a TDC has per acquisition cycle, and what the tabs open at.
MAX_TIMESTAMPS = 1536
DEFAULT_TIMESTAMPS = 300

PIXELS_PER_BOARD = 256


def _editable(combo, items):
    combo.setEditable(True)
    combo.setInsertPolicy(QtWidgets.QComboBox.InsertAtCurrent)
    for item in items:
        combo.addItem(item)
    return combo


def daughterboard_combo(parent=None):
    return _editable(QtWidgets.QComboBox(parent), DAUGHTERBOARDS)


def motherboard_combo(parent=None):
    return _editable(QtWidgets.QComboBox(parent), MOTHERBOARDS)


def firmware_combo(parent=None):
    """Not editable: the unpacking only knows these two."""
    combo = QtWidgets.QComboBox(parent)
    for item in FIRMWARE_VERSIONS:
        combo.addItem(item)
    return combo


def timestamps_spin(parent=None):
    spin = QtWidgets.QSpinBox(parent)
    spin.setRange(1, MAX_TIMESTAMPS)
    spin.setValue(DEFAULT_TIMESTAMPS)
    return spin


def pixel_spin(parent=None, maximum=PIXELS_PER_BOARD - 1):
    spin = QtWidgets.QSpinBox(parent)
    spin.setRange(0, maximum)
    # Without this, 'valueChanged' fires on every keystroke, so typing a
    # smaller number gets clamped against its neighbour halfway through.
    # The value is committed on Enter or focus loss instead, and the
    # arrows still work as before.
    spin.setKeyboardTracking(False)
    return spin


def float_field(parent=None, placeholder="auto"):
    """A field for one axis limit, or nothing at all.

    A line edit rather than a spin box because a spin box has no way to
    say "unset", and an edge left unset is one that autoscales. Accepts
    '-1.5', '2e-3', '10e3'; the range is deliberately the whole of
    float, since a photon rate and a stream length share no scale worth
    capping.

    """
    field = QtWidgets.QLineEdit(parent)
    field.setPlaceholderText(placeholder)
    validator = QtGui.QDoubleValidator(field)
    validator.setNotation(QtGui.QDoubleValidator.ScientificNotation)
    field.setValidator(validator)
    return field


def float_value(field):
    """A field's value as a float, or ``None`` when it is unset.

    A field left empty - or holding a fragment the validator tolerated
    while typing, such as a lone '-' or 'e' - means that edge should
    autoscale rather than break the plot.

    """
    text = field.text().strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def info_badge(tooltip, parent=None):
    """The small boxed 'i' that carries an explanation beside a control."""
    badge = QtWidgets.QLabel("i", parent)
    side = row_height() - 8
    badge.setFixedSize(QtCore.QSize(side, side))
    badge.setFrameShape(QtWidgets.QFrame.Box)
    badge.setAlignment(QtCore.Qt.AlignCenter)
    badge.setToolTip(tooltip)
    return badge


class DirectoryPicker(QtWidgets.QWidget):
    """A caption, a path, and a Browse button - one header row's worth.

    Every tab that reads data files has one of these, and on the full
    sensor tab there are two, which is why the shell reserves two header
    rows on every tab: the plot has to start at the same height whether
    a tab fills both or one.

    """

    changed = QtCore.pyqtSignal(str)

    def __init__(
        self,
        parent=None,
        caption="Data folder",
        title="Select Directory",
        tip=None,
    ):
        super().__init__(parent)
        self._title = title

        box = QtWidgets.QHBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(SPACING)

        self.label = QtWidgets.QLabel(caption, self)
        box.addWidget(self.label)

        self.lineEdit = QtWidgets.QLineEdit(self)
        self.lineEdit.setPlaceholderText(
            "folder the board writes its .dat files to"
        )
        box.addWidget(self.lineEdit, 1)

        self.pushButton = QtWidgets.QPushButton("Browse", self)
        self.pushButton.setFixedWidth(control_box_width())
        box.addWidget(self.pushButton)

        if tip:
            self.setToolTip(tip)

        self.pushButton.clicked.connect(self._browse)
        # 'textChanged', not 'editingFinished': a path pasted into the
        # field has to work exactly as one chosen with the button, and
        # pasting never moves the focus.
        self.lineEdit.textChanged.connect(self.changed.emit)

    def _browse(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, self._title, self.path()
        )
        if path:
            self.lineEdit.setText(path)

    def path(self):
        return self.lineEdit.text().strip()

    def set_path(self, path):
        self.lineEdit.setText(path)


class ReadoutStrip(QtWidgets.QWidget):
    """A row of 'name: value' readings, for the second header row.

    The tabs that need only one browse row put a reading here instead of
    leaving the row empty - which is how the top-most pixels came out of
    the control column, where they were costing every tab in the
    application a row of height.

    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._box = QtWidgets.QHBoxLayout(self)
        self._box.setContentsMargins(0, 0, 0, 0)
        self._box.setSpacing(SPACING)
        self._values = {}
        # A row of readings must not decide how narrow the window can be
        # made; the plot is what is being sized here.
        allow_shrink(self)

    def add(self, key, caption, initial="—", tip=None, width=None):
        name = QtWidgets.QLabel("{}:".format(caption), self)
        value = QtWidgets.QLabel(initial, self)
        value.setObjectName("readoutValue")
        if width is not None:
            value.setMinimumWidth(width)
        if tip:
            name.setToolTip(tip)
            value.setToolTip(tip)
        self._box.addWidget(name)
        self._box.addWidget(value)
        self._box.addSpacing(SPACING * 2)
        self._values[key] = value
        return value

    def add_stretch(self):
        self._box.addStretch(1)

    def set(self, key, text):
        widget = self._values.get(key)
        if widget is not None:
            widget.setText(str(text))


class LimitPair(QtWidgets.QWidget):
    """Two edges of one axis, side by side under the plot.

    ``spin`` builds the integer pair the pixel axes use, where every
    value is a pixel and both edges always have one; the float pair is
    for the axes where an edge can simply be left to autoscale.

    """

    changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, caption="x limits", spin=False,
                 maximum=255, values=(0, 255), tip=None):
        super().__init__(parent)
        self._spin = spin

        box = QtWidgets.QHBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(SPACING)
        label = QtWidgets.QLabel(caption, self)
        box.addWidget(label)

        if spin:
            self.low = pixel_spin(self, maximum)
            self.high = pixel_spin(self, maximum)
            self.low.setValue(values[0])
            self.high.setValue(values[1])
            self.low.valueChanged.connect(self._keep_ordered)
            self.high.valueChanged.connect(self._keep_ordered)
        else:
            self.low = float_field(self)
            self.high = float_field(self)
            self.low.editingFinished.connect(self.changed.emit)
            self.high.editingFinished.connect(self.changed.emit)

        for widget in (self.low, self.high):
            size_like_ui_tabs(widget)
            box.addWidget(widget)
        if tip:
            label.setToolTip(tip)
            self.low.setToolTip(tip)
            self.high.setToolTip(tip)

    def _keep_ordered(self):
        """Stop the two edges from crossing, then report the change."""
        if self.low.value() >= self.high.value():
            sender = self.sender()
            if sender is self.low:
                self.low.setValue(self.high.value() - 1)
            else:
                self.high.setValue(self.low.value() + 1)
        self.changed.emit()

    def values(self):
        if self._spin:
            return self.low.value(), self.high.value()
        return float_value(self.low), float_value(self.high)
