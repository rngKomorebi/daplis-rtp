"""Background check that both boards keep writing their files in step.

A good two-board run drops one file per board into each working
directory per acquisition cycle: the same number of files on both
sides, every pair created within a couple of seconds of the other. When
one board stalls, drops cycles, or stops writing altogether, the two
directories run off from each other - a different number of files, or a
growing offset between the pairs - and the two halves can no longer be
matched up afterwards, which makes the whole run useless. That can go
unnoticed for hours, since the live plot of either half looks perfectly
healthy on its own; hence this check.

The check runs in a thread of its own ('FileSyncWorker') so that
listing the two directories never blocks the GUI, and reports through
'FileSyncPanel', a compact status box that both the full-sensor and the
synchronization tab embed.

Two things are watched:

* the file counts, which may differ - one board always creates its file
  a moment before the other - but only briefly, so a difference is
  reported only once it outlives the grace period;
* the pairwise creation times: files are paired by their position in
  the time-sorted listing of each directory, so a single dropped cycle
  shifts every later pair and shows up at once.

Only files created after the monitoring starts are looked at: leftovers
from an earlier run in the same directory would otherwise be paired
with the new ones and throw every pair off.

'st_ctime' is the creation time on Windows, which is the platform the
acquisition runs on.

"""

import os
import threading
import time

from PyQt5 import QtCore, QtWidgets

# Same set of files the plotting tabs read: '*.dat' plus the numbered
# variants ('*.dat0', '*.dat1', ...) the board GUI writes.
DATA_SUFFIX = ".dat"

# 2 s is the pair spread of a healthy run; 5 s between sweeps keeps the
# directory listing cheap even for a run of many thousand files. A
# count difference is normal while one board is ahead of the other, so
# it is only reported once it has lasted GRACE seconds.
DEFAULT_TOLERANCE = 2.0
DEFAULT_INTERVAL = 5.0
DEFAULT_GRACE = 30.0

# Pairs listed in the "Show details" text of the alert box.
MAX_DETAIL_ROWS = 20


def _data_files(path):
    """Return {file name: creation time} for the data files in 'path'.

    None is returned when the directory cannot be listed at all - it
    was never set, was mistyped, or vanished mid-run - so that the
    caller can tell "no directory" from "directory with no files yet".
    Files removed between the listing and the 'stat' are skipped; the
    next sweep sees the directory as it is by then.

    """
    files = {}
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if DATA_SUFFIX not in entry.name:
                    continue
                try:
                    if not entry.is_file():
                        continue
                    files[entry.name] = entry.stat().st_ctime
                except OSError:
                    continue
    except OSError:
        return None
    return files


def baseline(path_1, path_2):
    """List what is already in both directories, as two sets of names.

    Taken by the caller before the sweeping thread is started, not by
    the thread itself: between 'QThread.start' and the thread actually
    being scheduled, the acquisition can already have written its first
    file. A file landing in that window would be taken for a leftover
    on one board and for new data on the other, which is exactly the
    permanent count difference this check is meant to report.

    """
    return (
        set(_data_files(path_1) or {}),
        set(_data_files(path_2) or {}),
    )


def _clock(ctime):
    """Format a creation time as 'HH:MM:SS.s'."""
    return "{}.{}".format(
        time.strftime("%H:%M:%S", time.localtime(ctime)),
        int(ctime % 1 * 10),
    )


class SyncStatus:
    """Outcome of one sweep, handed to the GUI thread for display.

    'state' is one of 'idle', 'waiting' (nothing to compare yet, or a
    directory is missing), 'ok', 'pending' (the counts differ but the
    grace period has not run out) and 'bad'.

    """

    def __init__(self, state, text, count_1=0, count_2=0, spread=0.0):
        self.state = state
        self.text = text
        self.count_1 = count_1
        self.count_2 = count_2
        self.spread = spread


class FileSyncWorker(QtCore.QThread):
    """Sweep both working directories until asked to stop.

    Emits 'status' after every sweep and 'problem' at most once per
    run: the first mismatch already means the run has to be repeated,
    and repeating the alert every few seconds would only bury the GUI
    under message boxes while nobody is at the desk.

    """

    status = QtCore.pyqtSignal(object)
    problem = QtCore.pyqtSignal(str, str)

    def __init__(
        self,
        path_1,
        path_2,
        labels,
        baseline,
        tolerance=DEFAULT_TOLERANCE,
        interval=DEFAULT_INTERVAL,
        grace=DEFAULT_GRACE,
        parent=None,
    ):
        super().__init__(parent)
        self.path_1 = path_1
        self.path_2 = path_2
        self.labels = labels
        # Files of earlier runs, listed before the thread starts: see
        # 'baseline'.
        self.base_1, self.base_2 = baseline
        self.tolerance = tolerance
        self.interval = interval
        self.grace = grace

        self._stop = threading.Event()
        self._mismatch_since = None
        self._alerted = False

    def stop(self):
        """Ask the sweep loop to end; returns without waiting for it."""
        self._stop.set()

    def run(self):
        while not self._stop.is_set():
            try:
                self.status.emit(self._sweep(self.base_1, self.base_2))
            except Exception as err:  # noqa: BLE001 - never kill the thread
                self.status.emit(
                    SyncStatus("waiting", "check failed: {}".format(err))
                )
            if self._stop.wait(self.interval):
                break

    # ------------------------------------------------------------------
    # One sweep
    # ------------------------------------------------------------------

    def _sweep(self, base_1, base_2):
        files_1 = _data_files(self.path_1)
        files_2 = _data_files(self.path_2)

        missing = [
            label
            for label, files in (
                (self.labels[0], files_1),
                (self.labels[1], files_2),
            )
            if files is None
        ]
        if missing:
            return SyncStatus(
                "waiting",
                "cannot read the directory of {}".format(
                    " and ".join(missing)
                ),
            )

        # Sorted by creation time, so index i on one board pairs with
        # index i on the other.
        new_1 = sorted(
            (t, name) for name, t in files_1.items() if name not in base_1
        )
        new_2 = sorted(
            (t, name) for name, t in files_2.items() if name not in base_2
        )
        n_1, n_2 = len(new_1), len(new_2)

        if not n_1 and not n_2:
            return SyncStatus("waiting", "waiting for the first files")

        # Creation times of every complete pair.
        off = [
            (abs(new_1[i][0] - new_2[i][0]), i) for i in range(min(n_1, n_2))
        ]
        spread, worst = max(off) if off else (0.0, None)

        counts = "{}: {} files, {}: {} files".format(
            self.labels[0], n_1, self.labels[1], n_2
        )
        summary = "{}, worst pair {:.1f} s apart".format(counts, spread)

        if spread > self.tolerance:
            self._alert(
                "The two boards are no longer writing in step.\n\n"
                "File pair {} was written {:.1f} s apart, over the {:.1f} s "
                "limit:\n"
                "    {}:  {}  at {}\n"
                "    {}:  {}  at {}\n\n"
                "{}\n\n"
                "The halves of this run can no longer be matched up - stop "
                "the acquisition and start the measurement again.".format(
                    worst + 1,
                    spread,
                    self.tolerance,
                    self.labels[0],
                    new_1[worst][1],
                    _clock(new_1[worst][0]),
                    self.labels[1],
                    new_2[worst][1],
                    _clock(new_2[worst][0]),
                    counts,
                ),
                self._details(new_1, new_2, off),
            )
            return SyncStatus("bad", summary, n_1, n_2, spread)

        now = time.time()
        if n_1 != n_2:
            if self._mismatch_since is None:
                self._mismatch_since = now
            age = now - self._mismatch_since
            if age > self.grace:
                self._alert(
                    "The two boards are no longer writing in step.\n\n"
                    "{}\n"
                    "A difference of {} file(s) has lasted {:.0f} s.\n\n"
                    "One of the boards is not saving its files - stop the "
                    "acquisition and start the measurement again.".format(
                        counts, abs(n_1 - n_2), age
                    ),
                    self._details(new_1, new_2, off),
                )
                return SyncStatus("bad", summary, n_1, n_2, spread)
            return SyncStatus(
                "pending",
                "{} ({:.0f} s out of step)".format(summary, age),
                n_1,
                n_2,
                spread,
            )

        self._mismatch_since = None
        return SyncStatus(
            "bad" if self._alerted else "ok", summary, n_1, n_2, spread
        )

    def _alert(self, summary, details):
        if self._alerted:
            return
        self._alerted = True
        self.problem.emit(summary, details)

    def _details(self, new_1, new_2, off):
        """Text for the 'Show details' pane: the pairs that are off."""
        lines = [
            "{}: {} files in {}".format(
                self.labels[0], len(new_1), self.path_1
            ),
            "{}: {} files in {}".format(
                self.labels[1], len(new_2), self.path_2
            ),
            "",
            "Pairs more than {:.1f} s apart:".format(self.tolerance),
        ]
        bad = [item for item in off if item[0] > self.tolerance]
        if not bad:
            lines.append("    none")
        for delta, i in bad[:MAX_DETAIL_ROWS]:
            lines.append(
                "    pair {:>5}   {:>6.1f} s   {} ({})  vs  {} ({})".format(
                    i + 1,
                    delta,
                    new_1[i][1],
                    _clock(new_1[i][0]),
                    new_2[i][1],
                    _clock(new_2[i][0]),
                )
            )
        if len(bad) > MAX_DETAIL_ROWS:
            lines.append(
                "    ... and {} more".format(len(bad) - MAX_DETAIL_ROWS)
            )

        # The unpaired tail: the files one board wrote and the other did
        # not, which is what a count difference comes down to.
        extra = new_1[len(new_2) :] or new_2[len(new_1) :]
        if extra:
            side = (
                self.labels[0] if len(new_1) > len(new_2) else self.labels[1]
            )
            lines += ["", "Files only {} has:".format(side)]
            for ctime, name in extra[:MAX_DETAIL_ROWS]:
                lines.append("    {}  at {}".format(name, _clock(ctime)))
            if len(extra) > MAX_DETAIL_ROWS:
                lines.append(
                    "    ... and {} more".format(len(extra) - MAX_DETAIL_ROWS)
                )
        return "\n".join(lines)


class FileSyncPanel(QtWidgets.QGroupBox):
    """Status box for the check, with the sweeping thread behind it.

    The host tab calls 'start' when the acquisition starts and 'stop'
    when it ends; with 'with_paths' the box also carries its own pair
    of directory selectors, for tabs that do not have them already.

    """

    # Re-emitted for hosts that want to log the alert as well.
    problem = QtCore.pyqtSignal(str, str)

    LED_COLORS = {
        "idle": "grey",
        "waiting": "goldenrod",
        "ok": "limegreen",
        "pending": "orange",
        "bad": "red",
    }

    def __init__(
        self,
        parent=None,
        font=None,
        labels=("Board 1", "Board 2"),
        with_paths=False,
    ):
        super().__init__("Both boards in step", parent)
        self._labels = labels
        self._with_paths = with_paths
        self._worker = None
        self._retired = []
        self._state = "idle"
        self._path_1 = ""
        self._path_2 = ""
        self._alert_box = None

        self._build_ui(font)

        # A running QThread outliving the application prints "QThread:
        # Destroyed while thread is still running" and can take the
        # process down with it, so the sweep always ends with the app.
        app = QtCore.QCoreApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.stop)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self, font):
        grid = QtWidgets.QGridLayout(self)
        # Top margin clears the group-box title, which is drawn over
        # the frame rather than above it.
        grid.setContentsMargins(8, 16, 8, 6)
        grid.setVerticalSpacing(4)
        row = 0

        self.checkBox_enabled = QtWidgets.QCheckBox(
            "Check both boards write in step", self
        )
        self.checkBox_enabled.setChecked(True)
        self.checkBox_enabled.setToolTip(
            "While the acquisition runs, compare the two working "
            "directories in the background: both boards must write the "
            "same number of files, each pair within the tolerance below. "
            "A run that drifts apart cannot be synchronized afterwards."
        )
        grid.addWidget(self.checkBox_enabled, row, 0, 1, 3)
        row += 1

        self.lineEdit_path_1 = None
        self.lineEdit_path_2 = None
        if self._with_paths:
            self.lineEdit_path_1, self.pushButton_path_1 = self._path_row(
                grid, row, self._labels[0]
            )
            row += 1
            self.lineEdit_path_2, self.pushButton_path_2 = self._path_row(
                grid, row, self._labels[1]
            )
            row += 1

        lbl_tol = QtWidgets.QLabel("Pair tolerance (s)", self)
        lbl_tol.setToolTip(
            "How far apart the two files of one acquisition cycle may be "
            "created. Good runs stay within about 2 s."
        )
        grid.addWidget(lbl_tol, row, 0)
        self.doubleSpinBox_tolerance = QtWidgets.QDoubleSpinBox(self)
        self.doubleSpinBox_tolerance.setRange(0.1, 600.0)
        self.doubleSpinBox_tolerance.setSingleStep(0.5)
        self.doubleSpinBox_tolerance.setDecimals(1)
        self.doubleSpinBox_tolerance.setValue(DEFAULT_TOLERANCE)
        # The stretch of column 1 belongs to the path fields, not to a
        # box holding two digits.
        self.doubleSpinBox_tolerance.setMaximumWidth(90)
        grid.addWidget(self.doubleSpinBox_tolerance, row, 1)
        row += 1

        lbl_int = QtWidgets.QLabel("Check every (s)", self)
        lbl_int.setToolTip("How often the two directories are compared.")
        grid.addWidget(lbl_int, row, 0)
        self.spinBox_interval = QtWidgets.QSpinBox(self)
        self.spinBox_interval.setRange(1, 600)
        self.spinBox_interval.setValue(int(DEFAULT_INTERVAL))
        self.spinBox_interval.setMaximumWidth(90)
        grid.addWidget(self.spinBox_interval, row, 1)
        row += 1

        self.label_led = QtWidgets.QLabel("●", self)
        self.label_led.setFixedWidth(18)
        grid.addWidget(self.label_led, row, 0, QtCore.Qt.AlignTop)
        self.label_status = QtWidgets.QLabel("not running", self)
        self.label_status.setWordWrap(True)
        grid.addWidget(self.label_status, row, 1, 1, 2)

        grid.setColumnStretch(1, 1)

        if font is not None:
            self.setFont(font)
            for widget in self.findChildren(QtWidgets.QWidget):
                widget.setFont(font)
        self._set_state("idle")

    def _path_row(self, grid, row, label):
        lbl = QtWidgets.QLabel("{} files".format(label), self)
        grid.addWidget(lbl, row, 0)
        edit = QtWidgets.QLineEdit(self)
        edit.setToolTip(
            "Folder this board's own GUI saves to (its 'Save' path). "
            "Only read by the check, never written to."
        )
        grid.addWidget(edit, row, 1)
        button = QtWidgets.QPushButton("Browse", self)
        button.clicked.connect(
            lambda _checked, e=edit, name=label: self._browse(e, name)
        )
        grid.addWidget(button, row, 2)
        return edit, button

    def _browse(self, edit, label):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select the working directory of {}".format(label)
        )
        if path:
            edit.setText(path)

    # ------------------------------------------------------------------
    # Host interface
    # ------------------------------------------------------------------

    def paths(self):
        """The pair of directories the check compares."""
        if self._with_paths:
            return (
                self.lineEdit_path_1.text().strip(),
                self.lineEdit_path_2.text().strip(),
            )
        return self._path_1, self._path_2

    def set_paths(self, path_1, path_2):
        """Point the check at the two working directories."""
        self._path_1, self._path_2 = path_1, path_2
        if self._with_paths:
            self.lineEdit_path_1.setText(path_1)
            self.lineEdit_path_2.setText(path_2)

    def is_enabled(self):
        return self.checkBox_enabled.isChecked()

    def start(self):
        """Begin sweeping; re-arms the alert of a previous run."""
        self.stop()
        if not self.is_enabled():
            self._set_state("idle", "check switched off")
            return

        path_1, path_2 = self.paths()
        if not path_1 or not path_2:
            self._set_state(
                "waiting", "no working directory set - not checking"
            )
            return
        if os.path.normcase(os.path.abspath(path_1)) == os.path.normcase(
            os.path.abspath(path_2)
        ):
            # One directory for both boards makes every count equal and
            # every pair simultaneous: the check would always pass.
            self._set_state(
                "waiting",
                "both boards point at the same directory - not checking",
            )
            return

        self._worker = FileSyncWorker(
            path_1=path_1,
            path_2=path_2,
            labels=self._labels,
            baseline=baseline(path_1, path_2),
            tolerance=self.doubleSpinBox_tolerance.value(),
            interval=float(self.spinBox_interval.value()),
        )
        self._worker.status.connect(self._on_status)
        self._worker.problem.connect(self._on_problem)
        self._worker.start()
        self._set_settings_enabled(False)
        self._set_state("waiting", "starting")

    def stop(self):
        """End the sweep; the last verdict stays on display."""
        self._retired = [w for w in self._retired if w.isRunning()]
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.stop()
            # 'stop' only sets a flag the loop checks between sweeps,
            # so the thread is normally back within milliseconds. A
            # directory listing that hangs - a network drive gone away
            # - is left to finish on its own rather than killed:
            # 'terminate' can cut the thread in the middle of Python
            # code and take the interpreter down with it. It stays
            # referenced and muted until it returns, since deleting a
            # running QThread crashes just as surely.
            if not worker.wait(5000):
                worker.status.disconnect(self._on_status)
                worker.problem.disconnect(self._on_problem)
                self._retired.append(worker)
        self._set_settings_enabled(True)

        if self._state == "bad":
            # A run that went wrong stays flagged until the next start.
            return
        text = self.label_status.text()
        if text == "starting":
            text = "not running"
        elif not text.endswith("(stopped)"):
            text = "{} (stopped)".format(text)
        self._set_state("idle", text)

    def _set_settings_enabled(self, enabled):
        self.checkBox_enabled.setEnabled(enabled)
        self.doubleSpinBox_tolerance.setEnabled(enabled)
        self.spinBox_interval.setEnabled(enabled)
        if self._with_paths:
            for widget in (
                self.lineEdit_path_1,
                self.lineEdit_path_2,
                self.pushButton_path_1,
                self.pushButton_path_2,
            ):
                widget.setEnabled(enabled)

    # ------------------------------------------------------------------
    # Worker signals
    # ------------------------------------------------------------------

    def _set_state(self, state, text=None):
        self._state = state
        self.label_led.setStyleSheet(
            "color: {}; font-size: 16px;".format(
                self.LED_COLORS.get(state, "grey")
            )
        )
        if text is not None:
            self.label_status.setText(text)

    def _on_status(self, status):
        self._set_state(status.state, status.text)

    def _on_problem(self, summary, details):
        self.problem.emit(summary, details)
        self._set_state("bad")
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Critical)
        box.setWindowTitle("Boards out of step")
        box.setText(summary)
        box.setDetailedText(details)
        # Not modal: the acquisition and the live plot must keep going
        # while the box waits to be noticed - the run is spoiled, but
        # freezing the GUI on top of that helps nobody.
        box.setWindowModality(QtCore.Qt.NonModal)
        box.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        box.destroyed.connect(self._forget_alert_box)
        self._alert_box = box
        box.show()
        box.raise_()
        # Nobody is necessarily at the desk when a run falls apart, so
        # put the box in front of whatever else is on screen.
        box.activateWindow()

    def _forget_alert_box(self):
        self._alert_box = None
