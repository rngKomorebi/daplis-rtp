"""What the tabs remember between runs.

A tab is opened, a folder is chosen, the daughterboard and the firmware
and the timestamp count are set - and until now all of it was thrown
away when the window closed, so the next session began by typing the
same six things again. The Synchronization tab already remembered its
executable and its two folders; nothing else remembered anything.

A widget is bound to a key here, and from then on it saves itself
whenever it changes and restores itself when the tab is next built.
Storage is ``QSettings``, the same per-user store the theme uses, under
a ``session/<tab>`` group.

Only *inputs* are bound. A readout, a status lamp or a plot is a
statement about the data in front of you, and restoring one of those on
a fresh start would be a statement about nothing.

"""

from PyQt5 import QtCore, QtWidgets

from daplis_rtp.gui.theme import APPLICATION, ORGANISATION


def _combo_accessors(widget):
    def read():
        return widget.currentText()

    def write(value):
        index = widget.findText(value)
        if index >= 0:
            widget.setCurrentIndex(index)
        elif widget.isEditable():
            # An editable combo is editable because the list is not
            # exhaustive - a board that arrived after the last release
            # still has to be usable, and still has to be remembered.
            widget.setCurrentText(value)

    return read, write, widget.currentTextChanged, str


def _spin_accessors(widget):
    return (
        widget.value,
        widget.setValue,
        widget.valueChanged,
        float if isinstance(widget, QtWidgets.QDoubleSpinBox) else int,
    )


def _line_accessors(widget):
    return widget.text, widget.setText, widget.textChanged, str


def _check_accessors(widget):
    return widget.isChecked, widget.setChecked, widget.toggled, bool


def _accessors(widget):
    """How to read, write and watch one widget.

    Returns ``(read, write, changed_signal, type)``. The type is what
    ``QSettings.value`` is asked to hand back: it stores everything as
    text on some platforms, so a bool read without it comes back as the
    string "false", which is true.

    """
    if isinstance(widget, QtWidgets.QComboBox):
        return _combo_accessors(widget)
    if isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
        return _spin_accessors(widget)
    if isinstance(widget, QtWidgets.QLineEdit):
        return _line_accessors(widget)
    if isinstance(widget, QtWidgets.QCheckBox):
        return _check_accessors(widget)
    if isinstance(widget, QtWidgets.QGroupBox) and widget.isCheckable():
        return _check_accessors(widget)
    raise TypeError(
        "no idea how to remember a {}".format(type(widget).__name__)
    )


class SessionStore:
    """The settings one tab remembers, and the widgets they belong to.

    Parameters
    ----------
    scope : str
        Names the tab. Becomes the ``QSettings`` group, so it must not
        change once a version has shipped or everyone's settings are
        silently forgotten.

    """

    def __init__(self, scope):
        self._settings = QtCore.QSettings(ORGANISATION, APPLICATION)
        self._scope = "session/{}".format(scope)
        self._bound = []
        self._restoring = False

    def bind(self, key, widget):
        """Remember one widget under ``key``.

        The key is given rather than taken from the widget's name: an
        object name is a layout detail that gets renamed in a tidy-up,
        and renaming one here would quietly lose what it stored.

        """
        read, write, changed, kind = _accessors(widget)
        entry = (key, read, write, kind)
        self._bound.append(entry)
        changed.connect(lambda *_, e=entry: self._save_one(e))
        return widget

    def bind_all(self, pairs):
        """``bind`` for a dict or a sequence of ``(key, widget)``."""
        items = pairs.items() if isinstance(pairs, dict) else pairs
        for key, widget in items:
            self.bind(key, widget)

    def restore(self):
        """Put back what was stored, for every bound widget.

        Saving is suppressed while this runs. Writing a widget makes it
        emit its change signal, and without the guard the first widget
        restored would save the *unrestored* value of the ones after it
        - which is only not a bug because they are about to be
        overwritten anyway, and is exactly the kind of thing that stops
        being true later.

        """
        self._restoring = True
        try:
            self._settings.beginGroup(self._scope)
            for key, _read, write, kind in self._bound:
                if not self._settings.contains(key):
                    continue
                try:
                    write(self._settings.value(key, type=kind))
                except (TypeError, ValueError):
                    # A stored value that no longer fits the widget - a
                    # spin box whose range has narrowed since - is
                    # skipped rather than raised. Settings are not
                    # something a user can easily repair, so they must
                    # never stop a tab being built.
                    continue
            self._settings.endGroup()
        finally:
            self._restoring = False

    def save(self):
        """Write every bound widget. Rarely needed; binding autosaves."""
        for entry in self._bound:
            self._save_one(entry)

    def _save_one(self, entry):
        if self._restoring:
            return
        key, read, _write, _kind = entry
        self._settings.beginGroup(self._scope)
        self._settings.setValue(key, read())
        self._settings.endGroup()

    def forget(self):
        """Drop everything stored for this tab."""
        self._settings.remove(self._scope)
