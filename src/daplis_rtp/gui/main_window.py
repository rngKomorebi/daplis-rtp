"""The window: five tabs, a menu bar, and the theme wired to both.

The old main window was a ``pyuic`` file that nobody could edit by hand
without losing the edit on the next export, and it carried a menu bar
that was built, shown, and left empty. Here the menu bar earns its
place - it is where the theme is chosen - and the window opens at a
deliberate size instead of at whatever minimum the tallest tab happened
to impose.

"""

import os

import numpy as np
from PyQt5 import QtCore, QtWidgets

from daplis_rtp import __version__
from daplis_rtp.gui.layout import WINDOW_DEFAULT_SIZE
from daplis_rtp.gui.preferences import PreferencesDialog
from daplis_rtp.gui.tabs import (
    LinoSPAD2Dual,
    LiveTimestamps,
    MZI,
    SinglePixelHistogram,
    Synchronization,
)
from daplis_rtp.gui.theme import PRESETS, preset_names, theme_manager

# How long a worker thread is given to finish on its own when the window
# closes, in milliseconds.
WORKER_WAIT_MS = 2000

# The tabs, in the order they are shown.
TABS = (
    (LiveTimestamps, "Online plot"),
    (SinglePixelHistogram, "Single Pixel Histogram"),
    (MZI, "MZI"),
    (LinoSPAD2Dual, "Full Sensor"),
    (Synchronization, "Synchronization"),
)


def write_plotted_data(path, data):
    """Write one tab's plotted numbers to ``path``.

    CSV or ``.npz``, by extension. The CSV carries the tab's notes as
    ``#`` comments above the header - which ``numpy.loadtxt`` and
    ``pandas.read_csv`` both skip by default - so that a file found on a
    disk six months later can still say which board, which firmware and
    which settings it came from. A plot whose provenance has to be
    remembered is a plot nobody trusts.

    """
    columns = data["columns"]
    headings = list(columns)
    table = np.column_stack([np.asarray(columns[h]) for h in headings])

    stamp = QtCore.QDateTime.currentDateTime().toString(
        "yyyy-MM-dd HH:mm:ss"
    )
    notes = ["daplis-rtp {} - exported {}".format(__version__, stamp)]
    notes += list(data.get("notes", []))

    if os.path.splitext(path)[1].lower() == ".npz":
        # A plain string array rather than an object one, so that
        # 'np.load' reads it back without 'allow_pickle'.
        np.savez_compressed(
            path,
            notes=np.array(notes),
            **{h: np.asarray(columns[h]) for h in headings}
        )
        return

    # Written by hand rather than with 'savetxt', which comments out
    # every header line it is given - including the column names, which
    # is what a spreadsheet needs left alone.
    with open(path, "w", newline="", encoding="utf-8") as handle:
        for line in notes:
            handle.write("# {}\n".format(line))
        handle.write(",".join(headings) + "\n")
        for row in table:
            handle.write(
                ",".join("{:.10g}".format(value) for value in row) + "\n"
            )


def quiesce(tab):
    """Stop whatever one tab left running.

    Everything here outlives the widget that started it unless it is
    stopped by hand, and each one is fatal in its own way: a QTimer
    fires into a deleted object, and a QThread destroyed while still
    running aborts the process outright.

    """
    # Every plotting tab starts a refresh timer when the stream starts,
    # and none of them stops it on the way out
    timer = getattr(tab, "timer", None)
    if timer is not None:
        timer.stop()

    # The pixel mask is a window of its own, so it does not necessarily
    # go when its tab does
    mask_window = getattr(tab, "mask_window", None)
    if mask_window is not None:
        mask_window.close()

    # 'Both boards in step' sweeps directories in a thread. Its own
    # 'stop' asks the sweep to finish and leaves a hung one muted and
    # referenced rather than killing it, which is the right thing here
    # too - so it is used as it stands.
    panel = getattr(tab, "fileSyncPanel", None)
    if panel is not None:
        panel.stop()

    # The Synchronization tab's acquisition thread has no flag to set:
    # it is a blocking socket conversation with two boards. So it is
    # given a moment to finish and then cut short - the one place the
    # package does that, and still better than destroying it running.
    worker = getattr(tab, "_worker", None)
    if worker is not None and worker.isRunning():
        if not worker.wait(WORKER_WAIT_MS):
            worker.terminate()
            worker.wait(WORKER_WAIT_MS)


class MainWindow(QtWidgets.QMainWindow):
    """The application window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DAPLIS - Real Time Plotting")

        self._manager = theme_manager()
        # Connected before the tabs are built, so that a theme change
        # restyles the application - and so sets the font the rows are
        # measured from - before any tab re-measures itself against it.
        self._manager.changed.connect(self._theme_changed)

        self._preferences = None

        self.tabWidget = QtWidgets.QTabWidget(self)
        self.tabWidget.setObjectName("tabWidget")
        for factory, title in TABS:
            self.tabWidget.addTab(factory(self), title)
        self.setCentralWidget(self.tabWidget)

        self._build_menu()
        self._build_status_bar()
        self.tabWidget.currentChanged.connect(self._sync_export_action)
        self._sync_export_action()

        # The old window had no 'resize' at all, so it opened at its own
        # minimum - which is why that minimum had been the subject of so
        # much attention. It opens at a comfortable size now, and the
        # minimum is only a floor.
        self.resize(*WINDOW_DEFAULT_SIZE)

    # ------------------------------------------------------------------
    # Menu and status bar
    # ------------------------------------------------------------------

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        self._export_action = file_menu.addAction("&Export plotted data…")
        self._export_action.setShortcut("Ctrl+E")
        self._export_action.setStatusTip(
            "Save the numbers behind the current plot, not a picture of "
            "them."
        )
        self._export_action.triggered.connect(self.export_current_tab)
        file_menu.addSeparator()
        quit_action = file_menu.addAction("&Quit")
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

        view = self.menuBar().addMenu("&View")

        theme_menu = view.addMenu("&Theme")
        # One group, so that exactly one preset is ticked at a time.
        self._theme_group = QtWidgets.QActionGroup(self)
        self._theme_group.setExclusive(True)
        self._theme_actions = {}
        # The presets are defined dark first, then light; a rule drawn
        # where the base changes saves reading ten names to find the
        # half of the list that suits the room.
        previous_base = None
        for key, name in preset_names():
            base = PRESETS[key].base
            if previous_base is not None and base != previous_base:
                theme_menu.addSeparator()
            previous_base = base
            action = theme_menu.addAction(name)
            action.setCheckable(True)
            action.setData(key)
            self._theme_group.addAction(action)
            self._theme_actions[key] = action
        self._theme_group.triggered.connect(
            lambda action: self._manager.set_preset(action.data())
        )

        view.addSeparator()
        preferences = view.addAction("&Preferences…")
        preferences.setShortcut("Ctrl+,")
        preferences.setStatusTip(
            "Colours, trace colours and font sizes, applied as they are "
            "chosen."
        )
        preferences.triggered.connect(self.open_preferences)

        help_menu = self.menuBar().addMenu("&Help")
        about = help_menu.addAction("&About")
        about.triggered.connect(self._about)

    def _build_status_bar(self):
        self._theme_label = QtWidgets.QLabel(self)
        self.statusBar().addPermanentWidget(self._theme_label)
        self._sync_theme_widgets()

    def open_preferences(self):
        # Built on first use: the dialog is a window of its own, and
        # most sessions never open it.
        if self._preferences is None:
            self._preferences = PreferencesDialog(self)
        self._preferences.open_beside()

    def _about(self):
        QtWidgets.QMessageBox.about(
            self,
            "DAPLIS - Real Time Plotting",
            "<b>DAPLIS - Real Time Plotting {}</b>"
            "<p>Live plotting for the LinoSPAD2 detector.</p>"
            "<p>Colours and font sizes are under "
            "<i>View &rarr; Preferences</i>, and are remembered per "
            "user.</p>".format(__version__),
        )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _current_tab(self):
        return self.tabWidget.currentWidget()

    def _sync_export_action(self):
        """Grey out the export when the tab in front has nothing to give.

        Checked when the tab changes rather than when the menu opens,
        because a greyed-out item with a keyboard shortcut also has to
        do nothing when the shortcut is pressed.

        """
        tab = self._current_tab()
        getter = getattr(tab, "plotted_data", None)
        self._export_action.setEnabled(
            getter is not None and getter() is not None
        )

    def export_current_tab(self):
        """Write the current plot's numbers to a file the user picks."""
        tab = self._current_tab()
        getter = getattr(tab, "plotted_data", None)
        data = getter() if getter is not None else None
        if data is None:
            QtWidgets.QMessageBox.information(
                self,
                "Export",
                "There is nothing plotted on this tab yet.",
            )
            return

        suggested = "{}-{}".format(
            data["stem"],
            QtCore.QDateTime.currentDateTime().toString("yyyyMMdd-HHmmss"),
        )
        path, selected = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export plotted data",
            suggested,
            "Comma-separated values (*.csv);;NumPy archive (*.npz)",
        )
        if not path:
            return
        if not os.path.splitext(path)[1]:
            path += ".npz" if "npz" in selected else ".csv"

        try:
            write_plotted_data(path, data)
        except OSError as err:
            QtWidgets.QMessageBox.warning(
                self, "Export", "Could not write the file.\n\n{}".format(err)
            )
            return
        self.statusBar().showMessage(
            "Exported to {}".format(os.path.basename(path)), 5000
        )

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _theme_changed(self):
        self._manager.apply_to_app()
        self._sync_theme_widgets()

    def _sync_theme_widgets(self):
        theme = self._manager.theme
        action = self._theme_actions.get(self._manager.preset_key)
        if action is not None and not action.isChecked():
            # Without blocking, ticking it here would fire 'triggered'
            # and set the preset the window is already showing - which
            # would drop the user's overrides as a side effect of
            # displaying them.
            blocked = self._theme_group.blockSignals(True)
            action.setChecked(True)
            self._theme_group.blockSignals(blocked)
        self._theme_label.setText("Theme: {}".format(theme.name))

    # ------------------------------------------------------------------
    # Closing
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        """Stop what the tabs left running, then close.

        This used to call ``QApplication.quit()``. Run from a terminal
        that made no difference - closing the last window ends the event
        loop anyway - but in an interpreter that outlives the call it
        tore down the QApplication the session was still holding, and
        the next run crashed the kernel.

        """
        for index in range(self.tabWidget.count()):
            quiesce(self.tabWidget.widget(index))
        if self._preferences is not None:
            self._preferences.close()
        event.accept()
