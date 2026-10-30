"""One set of geometry rules for every tab.

Nothing in the old application decided how large it was. Five tabs each
decided for themselves, in two different ways - three generated from
``.ui`` files by ``pyuic``, two built by hand in Python - and the window
took the largest minimum of the five. A panel added to the tab nobody
was looking at set how tall the application opened, and a widget sized
differently from its counterpart on another tab was invisible until the
two were put side by side.

That cost real time. A status box added to one control column made
every tab open 70 px taller; three tabs carried a 500x425 placeholder
widget that nothing drew; the "Full Sensor" combo boxes had drifted to
80 px ``Expanding`` against everyone else's 100 px ``Fixed``. All three
were found by measuring, not by looking.

So the numbers live here, once, and the tabs are built from
:class:`TabShell` rather than each inventing its own skeleton. What that
buys is the thing the eye actually notices: the plot is the same size
and in the same place on every tab, and so is every button.

The rules that govern, none of them obvious and all of them learnt the
expensive way:

* **A control column's minimum height is the sum of the panels stacked
  in it.** Nothing in a ``QVBoxLayout`` gives height back. So every box
  added to a column used to be height the window could never lose, on
  every tab, forever. Hence :class:`ControlColumn`, which is a scroll
  area: a column too tall for the window scrolls instead of pushing the
  window taller. That is what stops one tab's panel from setting the
  size of all five.
* **The canvas is the only other thing that yields.**
  :data:`MIN_CANVAS_HEIGHT` is 240, tuned as the largest value that
  costs the window no height of its own.
* **The navigation toolbar does not push back.** Squeeze a ``QToolBar``
  below its contents and it hides them behind an overflow button rather
  than forcing its parent wider - and the cursor readout, which is how
  pixel numbers are read off the plot, is the first thing to go. See
  ``canvas.base.toolbar_min_width``.
* **The window's minimum is the worst tab, per axis.** Height can come
  from one tab and width from another, which is why
  ``tests/test_tab_geometry.py`` measures all five.

Sizes here are quoted at the default 10 pt interface font and scaled
with it, so that turning the font up in Preferences moves the rows and
the control column with it instead of clipping them.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from daplis_rtp.gui.theme import DEFAULT_UI_FONT_SIZE, theme_manager

# Width of every combo and spin box in a control column. The label
# beside it takes the slack instead, which is what makes a column line
# up down its whole length and stay put as the window is resized.
CONTROL_BOX_WIDTH = 100

# The whole right-hand column, scroll bar included. Wide enough for
# "Daughterboard" plus a 100 px box without eliding the label.
CONTROL_COLUMN_WIDTH = 288

# Room kept for the column's scroll bar whether or not it is showing.
# Without this the controls shift 16 px left the moment one panel too
# many is added - on that tab only - and the fixed-width boxes at the
# right-hand end are the ones that get clipped.
SCROLLBAR_WIDTH = 16

# One row height, replacing the 26/28 px mixture the old tabs carried
# with no rule behind which was which.
ROW_HEIGHT = 26

# The action buttons along the bottom of the control column.
ACTION_HEIGHT = 34

# Rows above the plot, on every tab. Two, because "Full Sensor" needs
# two browse rows and the plot has to start at the same height there as
# everywhere else; the tabs that need only one put a readout in the
# other.
HEADER_ROWS = 2

# The one row below the plot, which is where axis limits live.
FOOTER_ROWS = 1

# The hint line across the top of every tab.
HINT_HEIGHT = 20

# Below this the plot is not worth looking at. Kept at the largest value
# that costs the window no height of its own: above 240 the canvas,
# rather than the controls beside it, starts deciding how tall the
# application opens.
MIN_CANVAS_HEIGHT = 240

# Slots in the action bar. Fixing the count rather than the sizes is
# what puts "Refresh plot" in the same place on the tab that has one
# button and on the tab that has three.
ACTION_SLOTS = 3

MARGIN = 8
SPACING = 6

# What the window opens at, and the floor the geometry test holds it
# under. The old window had no 'resize' at all, so it opened at its
# minimum - which is why that minimum had been the subject of so much
# attention. It opens at a comfortable size now, and the minimum is
# only a floor.
WINDOW_DEFAULT_SIZE = (1500, 900)
WINDOW_MIN_BUDGET = (1320, 720)


def scale():
    """How far the interface font is from the size the numbers assume."""
    return theme_manager().ui_font_size / float(DEFAULT_UI_FONT_SIZE)


def _scaled(value):
    return int(round(value * scale()))


def row_height():
    """One control row, never shorter than the text it has to hold."""
    app = QtWidgets.QApplication.instance()
    text = QtGui.QFontMetrics(app.font()).height() if app else 0
    return max(_scaled(ROW_HEIGHT), text + 9)


def control_box_width():
    return _scaled(CONTROL_BOX_WIDTH)


def control_column_width():
    return _scaled(CONTROL_COLUMN_WIDTH)


def control_content_width():
    """The column's width less the room kept for its scroll bar.

    Everything in the column - the rows, the panels, the action buttons
    - is laid out to this, so that the contents sit in the same place
    on a tab whose column scrolls and one whose column does not.

    """
    return control_column_width() - _scaled(SCROLLBAR_WIDTH)


def action_height():
    return max(_scaled(ACTION_HEIGHT), row_height() + 6)


def hint_height():
    app = QtWidgets.QApplication.instance()
    text = QtGui.QFontMetrics(app.font()).height() if app else HINT_HEIGHT
    return max(_scaled(HINT_HEIGHT), text + 2)


def size_like_ui_tabs(widget, width=None):
    """Give one control the width and height every other control has.

    Named after what it was for: the two hand-built tabs had to be made
    to agree with the three generated ones. Now it is the only way any
    of them is sized.

    """
    widget.setFixedWidth(control_box_width() if width is None else width)
    widget.setFixedHeight(row_height())
    widget.setSizePolicy(
        QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
    )
    return widget


def fixed_row(parent=None, height=None):
    """A widget of exactly one row's height, holding a horizontal box.

    Used for the rows above and below the plot. Fixed rather than
    minimum, so that a tab which leaves one empty still starts its plot
    at the same height as the tab beside it.

    """
    row = QtWidgets.QWidget(parent)
    row.setFixedHeight(row_height() if height is None else height)
    box = QtWidgets.QHBoxLayout(row)
    box.setContentsMargins(0, 0, 0, 0)
    box.setSpacing(SPACING)
    return row, box


def label(text, parent=None, object_name=None):
    widget = QtWidgets.QLabel(text, parent)
    if object_name:
        widget.setObjectName(object_name)
    return widget


def allow_shrink(widget):
    """Let a widget be squeezed below the width of its own contents.

    A row of readings, or a status line, must not be what decides how
    narrow the window can be made: the plot is the thing being sized,
    and a reading that is clipped at 1300 px is a smaller loss than a
    window that cannot be made narrower than 1600. Qt's ``Ignored``
    policy is exactly this - the layout stops counting the widget's
    minimum, and it takes whatever space is left.

    """
    widget.setSizePolicy(
        QtWidgets.QSizePolicy.Ignored,
        widget.sizePolicy().verticalPolicy(),
    )
    widget.setMinimumWidth(0)
    return widget


class ElidedLabel(QtWidgets.QLabel):
    """A one-line label that shortens itself rather than widening the window.

    A plain ``QLabel`` reports a minimum width equal to the whole of its
    text, and a layout never goes below that - so the sentence of
    guidance across the top of each tab set the narrowest the whole
    application could be made, at well over 2000 px. This one reports
    almost no minimum and paints an ellipsis instead, keeping the full
    text in its tooltip so nothing is actually lost.

    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full = text
        self.setToolTip(text)
        # Horizontally the hint yields to everything; vertically it
        # keeps its one line.
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed
        )

    def setText(self, text):
        self._full = text
        self.setToolTip(text)
        super().setText(text)
        self.update()

    def minimumSizeHint(self):
        size = super().minimumSizeHint()
        size.setWidth(0)
        return size

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(
            self._full, QtCore.Qt.ElideRight, self.width()
        )
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.drawText(self.rect(), int(self.alignment()), elided)


def led(parent=None):
    """The round status lamp used by the panels and the sync tab.

    Its colour comes from the ``ledState`` property and the stylesheet
    rather than from a per-widget palette, so it follows the theme.

    """
    lamp = QtWidgets.QLabel("●", parent)
    lamp.setProperty("ledState", "idle")
    lamp.setFixedWidth(16)
    lamp.setAlignment(QtCore.Qt.AlignCenter)
    return lamp


def set_led(lamp, state):
    """Re-colour a lamp: 'idle', 'ok', 'warn' or 'error'.

    The property alone changes nothing on screen - Qt only re-reads the
    stylesheet when told to - so the widget is unpolished and polished
    again, which is the documented way of doing this.

    """
    lamp.setProperty("ledState", state)
    lamp.style().unpolish(lamp)
    lamp.style().polish(lamp)


class ControlColumn(QtWidgets.QScrollArea):
    """The right-hand column of controls, identical on every tab.

    A scroll area rather than a plain column, and that is the whole
    point: a column with one panel too many scrolls, where before it
    made every tab in the application open taller. The width is fixed,
    so the plot beside it starts at the same x on all five tabs.

    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._body = QtWidgets.QWidget(self)
        self._column = QtWidgets.QVBoxLayout(self._body)
        self._column.setContentsMargins(0, 0, SPACING, 0)
        self._column.setSpacing(SPACING)
        self.setWidget(self._body)
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        # Off, not 'as needed': a horizontal bar here would mean the
        # column is too narrow, and the fix for that is a wider column,
        # not a bar for the user to drag.
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        # Widgets whose size is a function of the interface font, kept
        # so that 'apply_metrics' can revisit them when it changes.
        self._rows = []
        self._boxes = []
        self.apply_metrics()

    # -- building it ---------------------------------------------------

    def add_row(self, text, widget, tip=None):
        """A label on the left, one fixed-width control on the right.

        Every control column is this row repeated a dozen times, which
        is why it is a function rather than four lines written out each
        time.

        """
        row, box = fixed_row(self._body)
        name = label(text, row)
        box.addWidget(name)
        box.addStretch(1)
        box.addWidget(widget)
        if tip:
            name.setToolTip(tip)
            widget.setToolTip(tip)
        size_like_ui_tabs(widget)
        self._rows.append(row)
        self._boxes.append(widget)
        self._column.addWidget(row)
        return widget

    def add_wide_row(self, widget, tip=None):
        """One control across the full width - a check box, a button."""
        row, box = fixed_row(self._body)
        box.addWidget(widget)
        if tip:
            widget.setToolTip(tip)
        self._rows.append(row)
        self._column.addWidget(row)
        return widget

    def add_pair_row(self, left, right):
        """Two controls side by side, sharing one row's height."""
        row, box = fixed_row(self._body)
        box.addWidget(left)
        box.addWidget(right)
        self._rows.append(row)
        self._column.addWidget(row)
        return row

    def add_widget(self, widget):
        """A panel that brings its own height - a group box, a readout."""
        self._column.addWidget(widget)
        return widget

    def add_group(self, title):
        """A titled box to put rows in, returned with its layout."""
        box = QtWidgets.QGroupBox(title, self._body)
        inner = QtWidgets.QVBoxLayout(box)
        inner.setContentsMargins(SPACING, SPACING, SPACING, SPACING)
        inner.setSpacing(4)
        self._column.addWidget(box)
        return box, inner

    def add_heading(self, text):
        """A small caption dividing one run of rows from the next."""
        caption = label(text, self._body, object_name="tabHint")
        self._column.addWidget(caption)
        return caption

    def add_stretch(self):
        """Push everything above it to the top of the column."""
        self._column.addStretch(1)

    # -- keeping it in step with the font -------------------------------

    def apply_metrics(self):
        self.setFixedWidth(control_column_width())
        # The body is held to the width the scroll bar leaves, whether
        # or not the bar is showing, so that adding one panel too many
        # to a column does not shift every control on that tab 16 px
        # left of where the same control sits on the tab beside it.
        content = control_content_width()
        self._body.setMinimumWidth(content)
        self._body.setMaximumWidth(content)
        height = row_height()
        for row in self._rows:
            row.setFixedHeight(height)
        for widget in self._boxes:
            size_like_ui_tabs(widget)


class ActionBar(QtWidgets.QWidget):
    """The buttons at the foot of the control column.

    Three slots, stacked, on every tab. A tab with one button leaves two
    empty rather than letting its button grow or the bar shrink - which
    is what puts "Refresh plot" under the same pixels whichever tab is
    in front.

    Stacked rather than side by side because the column is 272 px wide:
    three buttons across it get 85 px each, which is narrower than the
    words on them. Full width each, and they are all legible and all
    the same size.

    The slots mean something, and the tabs fill them the same way:

    ===== ===========================================================
    slot  what goes in it
    ===== ===========================================================
    1     look again now - "Refresh plot", "Check clocks"
    2     the thing the tab is for, and the one that runs - "Start
          stream", "Acquire". Marked ``primary``.
    3     the extra, if there is one - "Reset", "Launch boards"
    ===== ===========================================================

    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._grid = QtWidgets.QGridLayout(self)
        self._grid.setContentsMargins(0, 0, SPACING, 0)
        self._grid.setSpacing(SPACING)
        self._buttons = []
        self.apply_metrics()

    def add_button(self, text, tip=None, primary=False, slot=None):
        """Put a button in a slot - the next free one unless told.

        ``primary`` marks the one the tab is really for, which the
        stylesheet outlines in the accent colour.

        """
        index = len(self._buttons) if slot is None else slot
        if not 0 <= index < ACTION_SLOTS:
            raise ValueError(
                "an action bar holds {} buttons; a tab needing more "
                "wants a group box in the column instead".format(
                    ACTION_SLOTS
                )
            )
        button = QtWidgets.QPushButton(text, self)
        if primary:
            button.setObjectName("primaryAction")
        if tip:
            button.setToolTip(tip)
        button.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed
        )
        self._grid.addWidget(button, index, 0)
        self._buttons.append(button)
        self.apply_metrics()
        return button

    def apply_metrics(self):
        height = action_height()
        # Every slot keeps its height whether or not it holds a button,
        # so the bar is the same size on a tab with one and a tab with
        # three - and so the buttons of both line up.
        for slot in range(ACTION_SLOTS):
            self._grid.setRowMinimumHeight(slot, height)
            self._grid.setRowStretch(slot, 0)
        # The same width as the column's contents, so the buttons line
        # up with the rows above them rather than with the scroll bar.
        self.setFixedWidth(control_content_width())
        self.setFixedHeight(
            ACTION_SLOTS * height + (ACTION_SLOTS - 1) * SPACING
        )
        for button in self._buttons:
            button.setFixedHeight(height)


class TabShell(QtWidgets.QWidget):
    """The skeleton every tab is built in.

    ::

        +------------------------------------------------------------+
        | hint                                                       |
        +-------------------------------------------+----------------+
        | header row 0                              |                |
        | header row 1                              |  control       |
        |                                           |  column        |
        |            canvas area                    |  (scrolls)     |
        |                                           |                |
        | footer row                                +----------------+
        |                                           |  action bar    |
        +-------------------------------------------+----------------+

    Every one of those slots is the same height and width on all five
    tabs, whether or not the tab has anything to put in it. A tab that
    leaves the second header row empty still starts its plot at the
    same y as the tab that fills it.

    """

    def __init__(self, parent=None, hint=""):
        super().__init__(parent)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        root.setSpacing(SPACING)

        self.hint = ElidedLabel(hint, self)
        self.hint.setObjectName("tabHint")
        self.hint.setFixedHeight(hint_height())
        root.addWidget(self.hint)

        body = QtWidgets.QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(SPACING)
        root.addLayout(body, 1)

        # -- left: header rows, canvas, footer row --------------------
        left = QtWidgets.QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(SPACING)
        body.addLayout(left, 1)

        self._header_rows = []
        self._header_boxes = []
        for _ in range(HEADER_ROWS):
            row, box = fixed_row(self)
            self._header_rows.append(row)
            self._header_boxes.append(box)
            left.addWidget(row)

        self._canvas_holder = QtWidgets.QWidget(self)
        self._canvas_holder.setMinimumHeight(MIN_CANVAS_HEIGHT)
        self._canvas_holder.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        holder_box = QtWidgets.QVBoxLayout(self._canvas_holder)
        holder_box.setContentsMargins(0, 0, 0, 0)
        # Only felt on a tab with a strip above its plot; a lone canvas
        # has nothing to be spaced from.
        holder_box.setSpacing(SPACING)
        self._canvas_box = holder_box
        self._strip_rows = []
        left.addWidget(self._canvas_holder, 1)

        self._footer_rows = []
        self._footer_boxes = []
        for _ in range(FOOTER_ROWS):
            row, box = fixed_row(self)
            self._footer_rows.append(row)
            self._footer_boxes.append(box)
            left.addWidget(row)

        # -- right: the control column and its buttons ----------------
        right = QtWidgets.QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(SPACING)
        body.addLayout(right, 0)

        self.controls = ControlColumn(self)
        right.addWidget(self.controls, 1)
        self.actions = ActionBar(self)
        right.addWidget(self.actions, 0, QtCore.Qt.AlignLeft)

        self._canvas = None
        theme_manager().changed.connect(self.apply_metrics)

    # -- filling it ----------------------------------------------------

    @property
    def canvas_area(self):
        """The rectangle the plot occupies.

        Exposed so that ``tests/test_tab_geometry.py`` can assert it is
        the same rectangle on all five tabs, which is the one property
        of this module the eye actually notices.

        """
        return self._canvas_holder

    def header_row(self, index=0):
        """The horizontal box of header row ``index`` (0 or 1)."""
        return self._header_boxes[index]

    def footer_row(self, index=0):
        """The horizontal box of the row under the plot."""
        return self._footer_boxes[index]

    def add_canvas_strip(self, widget):
        """A row of controls across the top of the plot, on this tab only.

        Inside the canvas area rather than a third header row, so the
        area itself stays the same rectangle on every tab: the row is
        taken out of this tab's plot, and the tabs without one keep the
        height.

        """
        row, box = fixed_row(self._canvas_holder)
        box.addWidget(widget)
        self._canvas_box.insertWidget(len(self._strip_rows), row)
        self._strip_rows.append(row)
        return widget

    def set_canvas(self, widget):
        """Put the plot - or, on the Synchronization tab, the log - in.

        Named for the plot because that is what it holds on four tabs
        out of five, and because the point of the shell is that the
        fifth occupies exactly the same rectangle.

        """
        if self._canvas is not None:
            self._canvas_box.removeWidget(self._canvas)
            self._canvas.setParent(None)
        self._canvas = widget
        self._canvas_box.addWidget(widget)
        return widget

    def set_hint(self, text):
        self.hint.setText(text)

    # -- keeping it in step with the font -------------------------------

    def apply_metrics(self):
        """Re-apply every font-dependent size.

        Connected to the theme, so that changing the interface font in
        Preferences moves the rows rather than clipping their contents.

        """
        height = row_height()
        for row in self._header_rows + self._footer_rows + self._strip_rows:
            row.setFixedHeight(height)
        self.hint.setFixedHeight(hint_height())
        self.controls.apply_metrics()
        self.actions.apply_metrics()
