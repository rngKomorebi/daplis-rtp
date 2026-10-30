"""The Preferences window: pick a theme, or build one.

Deliberately not modal. Every change is applied the moment it is made,
to the window and to every plot already drawn, so the way to choose a
colour is to put this window beside the plot and watch the plot change.
A modal dialog with an "Apply" button would mean choosing colours from
memory.

Nothing here computes a look. It reads and writes
:class:`~daplis_rtp.gui.theme.ThemeManager`, which is what everything
else reads too.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from daplis_rtp.gui.layout import MARGIN, SPACING
from daplis_rtp.gui.theme import (
    N_SERIES,
    PLOT_FONT_RANGE,
    UI_FONT_RANGE,
    preset_names,
    theme_manager,
)

# The theme fields offered as colour pickers, as (field, caption, tip).
INTERFACE_COLOURS = (
    (
        "accent",
        "Accent",
        "The selected tab, the group-box titles, and the outline round "
        "the button each tab is really for.",
    ),
)

PLOT_COLOURS = (
    ("figure_bg", "Figure background", "Behind the axes, and the margin."),
    (
        "axes_bg",
        "Plot background",
        "Inside the axes. Setting it apart from the figure background "
        "frames the data; setting it the same keeps the plot flat.",
    ),
    (
        "axes_fg",
        "Ticks and labels",
        "Everything on the axes that is read as text.",
    ),
    (
        "axes_edge",
        "Axes frame",
        "The box around the data. Set it to the same colour as the "
        "ticks and labels for a plot with one axis colour; a dimmer "
        "frame under brighter text puts the emphasis on the numbers.",
    ),
    ("grid", "Grid", "The grid lines, when the grid is switched on."),
    (
        "marker",
        "Markers",
        "The line marking the seam between the two sensor halves, and "
        "the group-of-64 lines.",
    ),
)

# Width of the colour buttons, and of the two spin boxes beside them.
# One number, so that the left edge of every field in the window lines
# up with the one above it.
FIELD_WIDTH = 84

# What each series colour is actually used for, so that picking one is
# not guesswork.
SERIES_USE = (
    "Sensor population, and the first MZI pixel",
    "The second MZI pixel",
    "The single-pixel histogram",
    "Spare",
    "Spare",
)


def _readable_on(colour):
    """Black or white, whichever can be read on ``colour``.

    The picker buttons carry their own hex code as a label, and a light
    grey code on a light grey button is no label at all.

    """
    shade = QtGui.QColor(colour)
    if not shade.isValid():
        return "#000000"
    # Rec. 601 luma: the eye weights green far above blue, so a plain
    # mean of the channels calls yellow dark and blue light.
    luma = (
        0.299 * shade.red() + 0.587 * shade.green() + 0.114 * shade.blue()
    )
    return "#000000" if luma > 140 else "#ffffff"


class ColourButton(QtWidgets.QPushButton):
    """A button that is the colour it stands for, and opens a picker."""

    picked = QtCore.pyqtSignal(str)

    def __init__(self, colour, parent=None, title="Choose a colour"):
        super().__init__(parent)
        self._title = title
        self._colour = colour
        self.setFixedWidth(FIELD_WIDTH)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.set_colour(colour)
        self.clicked.connect(self._choose)

    def set_colour(self, colour):
        self._colour = colour
        self.setText(colour)
        # An instance stylesheet beats the application one for this
        # widget, which is what keeps qdarkstyle from painting over it.
        self.setStyleSheet(
            "QPushButton {{"
            " background-color: {}; color: {};"
            " border: 1px solid #7a7a7a; padding: 3px;"
            "}}".format(colour, _readable_on(colour))
        )

    def colour(self):
        return self._colour

    def _choose(self):
        chosen = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(self._colour), self, self._title
        )
        if chosen.isValid():
            self.set_colour(chosen.name())
            self.picked.emit(chosen.name())


class PreferencesDialog(QtWidgets.QDialog):
    """Theme, colours and font sizes, applied as they are chosen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        # A window of its own rather than a sheet over the tab, so it
        # can be put beside the plot it is being used to colour.
        self.setWindowFlags(QtCore.Qt.Window)
        self.setModal(False)

        self._manager = theme_manager()
        self._colour_buttons = {}
        self._series_buttons = []
        # Set while the widgets are being written to from the theme, so
        # that doing so does not read back as the user changing them.
        self._loading = False

        self._build_ui()
        self.reload()
        self._manager.changed.connect(self.reload)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        outer.setSpacing(SPACING)

        preset_row = QtWidgets.QHBoxLayout()
        preset_row.addWidget(QtWidgets.QLabel("Theme", self))
        self.comboBox_preset = QtWidgets.QComboBox(self)
        for key, name in preset_names():
            self.comboBox_preset.addItem(name, key)
        self.comboBox_preset.setToolTip(
            "A starting point. Any colour below can be changed "
            "afterwards; picking a preset again clears those changes."
        )
        self.comboBox_preset.activated.connect(self._preset_chosen)
        preset_row.addWidget(self.comboBox_preset, 1)
        outer.addLayout(preset_row)

        outer.addWidget(self._interface_box())
        outer.addWidget(self._plot_box())
        outer.addWidget(self._series_box())

        outer.addStretch(1)

        buttons = QtWidgets.QHBoxLayout()
        self.pushButton_reset = QtWidgets.QPushButton(
            "Reset to defaults", self
        )
        self.pushButton_reset.setToolTip(
            "Back to the shipped theme and font sizes, throwing away "
            "every change made here."
        )
        self.pushButton_reset.clicked.connect(self._reset)
        buttons.addWidget(self.pushButton_reset)
        buttons.addStretch(1)
        close = QtWidgets.QPushButton("Close", self)
        close.clicked.connect(self.hide)
        buttons.addWidget(close)
        outer.addLayout(buttons)

    def _interface_box(self):
        box = QtWidgets.QGroupBox("Interface", self)
        form = QtWidgets.QFormLayout(box)
        form.setSpacing(SPACING)

        for field, caption, tip in INTERFACE_COLOURS:
            form.addRow(caption, self._colour_row(field, caption, tip, box))

        self.spinBox_uiFont = QtWidgets.QSpinBox(box)
        self.spinBox_uiFont.setRange(*UI_FONT_RANGE)
        self.spinBox_uiFont.setSuffix(" pt")
        # Held to the width of the colour buttons above it. A form
        # layout gives its field the whole row otherwise, and a spin box
        # holding two digits stretched across 400 px looks like a
        # mistake.
        self.spinBox_uiFont.setFixedWidth(FIELD_WIDTH)
        self.spinBox_uiFont.setToolTip(
            "Size of the text in the window. The rows, the control "
            "column and the buttons are measured from it, so they grow "
            "with it rather than clipping."
        )
        self.spinBox_uiFont.valueChanged.connect(self._ui_font_changed)
        form.addRow("Font size", self.spinBox_uiFont)
        return box

    def _plot_box(self):
        box = QtWidgets.QGroupBox("Plots", self)
        form = QtWidgets.QFormLayout(box)
        form.setSpacing(SPACING)

        for field, caption, tip in PLOT_COLOURS:
            form.addRow(caption, self._colour_row(field, caption, tip, box))

        self.spinBox_plotFont = QtWidgets.QSpinBox(box)
        self.spinBox_plotFont.setRange(*PLOT_FONT_RANGE)
        self.spinBox_plotFont.setSuffix(" pt")
        self.spinBox_plotFont.setFixedWidth(FIELD_WIDTH)
        self.spinBox_plotFont.setToolTip(
            "Size of the axis labels on a small window. The plots grow "
            "it from here as the window widens."
        )
        self.spinBox_plotFont.valueChanged.connect(self._plot_font_changed)
        form.addRow("Font size", self.spinBox_plotFont)

        switches = QtWidgets.QHBoxLayout()
        self.checkBox_glow = QtWidgets.QCheckBox("Glow", box)
        self.checkBox_glow.setToolTip(
            "The glow under the traces. Good-looking and not free: each "
            "line is drawn several times over, which is felt on a "
            "stream refreshing as fast as the files arrive."
        )
        self.checkBox_glow.toggled.connect(
            lambda on: self._override("glow", on)
        )
        switches.addWidget(self.checkBox_glow)

        self.checkBox_grid = QtWidgets.QCheckBox("Grid", box)
        self.checkBox_grid.setToolTip(
            "Grid lines behind the data, in the grid colour above."
        )
        self.checkBox_grid.toggled.connect(
            lambda on: self._override("grid_on", on)
        )
        switches.addWidget(self.checkBox_grid)
        switches.addStretch(1)
        form.addRow("", switches)
        return box

    def _series_box(self):
        box = QtWidgets.QGroupBox("Trace colours", self)
        form = QtWidgets.QFormLayout(box)
        form.setSpacing(SPACING)
        for index in range(N_SERIES):
            button = ColourButton(
                "#000000", box, "Trace {} colour".format(index + 1)
            )
            button.setToolTip(SERIES_USE[index])
            button.picked.connect(
                lambda colour, i=index: self._series_picked(i, colour)
            )
            self._series_buttons.append(button)
            row = QtWidgets.QHBoxLayout()
            row.addWidget(button)
            caption = QtWidgets.QLabel(SERIES_USE[index], box)
            caption.setObjectName("tabHint")
            row.addWidget(caption, 1)
            holder = QtWidgets.QWidget(box)
            holder.setLayout(row)
            row.setContentsMargins(0, 0, 0, 0)
            form.addRow("Trace {}".format(index + 1), holder)
        return box

    def _colour_row(self, field, caption, tip, parent):
        button = ColourButton(
            "#000000", parent, "{} colour".format(caption)
        )
        button.setToolTip(tip)
        button.picked.connect(
            lambda colour, name=field: self._override(name, colour)
        )
        self._colour_buttons[field] = button
        return button

    # ------------------------------------------------------------------
    # Reading the theme back into the widgets
    # ------------------------------------------------------------------

    def reload(self):
        """Show what the theme currently says.

        Connected to the theme as well as called at build time, so that
        a reset - or a preset chosen while this window is open - moves
        the controls rather than leaving them showing the old values.

        """
        self._loading = True
        try:
            theme = self._manager.theme
            index = self.comboBox_preset.findData(self._manager.preset_key)
            if index >= 0:
                self.comboBox_preset.setCurrentIndex(index)
            for field, button in self._colour_buttons.items():
                button.set_colour(getattr(theme, field))
            for index, button in enumerate(self._series_buttons):
                button.set_colour(theme.colour(index))
            self.spinBox_uiFont.setValue(self._manager.ui_font_size)
            self.spinBox_plotFont.setValue(self._manager.plot_font_size)
            self.checkBox_glow.setChecked(theme.glow)
            self.checkBox_grid.setChecked(theme.grid_on)
        finally:
            self._loading = False

    # ------------------------------------------------------------------
    # Writing the widgets back into the theme
    # ------------------------------------------------------------------

    def _preset_chosen(self, index):
        if self._loading:
            return
        self._manager.set_preset(self.comboBox_preset.itemData(index))

    def _override(self, field, value):
        if self._loading:
            return
        self._manager.set_override(field, value)

    def _series_picked(self, index, colour):
        if self._loading:
            return
        self._manager.set_series_colour(index, colour)

    def _ui_font_changed(self, value):
        if self._loading:
            return
        self._manager.set_ui_font_size(value)

    def _plot_font_changed(self, value):
        if self._loading:
            return
        self._manager.set_plot_font_size(value)

    def _reset(self):
        self._manager.reset()

    def open_beside(self):
        self.show()
        self.raise_()
        self.activateWindow()
