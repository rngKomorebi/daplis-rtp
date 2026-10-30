"""Synchronization: drive a two-board acquisition over TCP.

This tab talks to two running instances of ``LinoSPAD_synchro.exe``, one
per board: it enables the external clock, verifies both boards are
locked to it, and starts acquisition on both **simultaneously**. It is
the GUI equivalent of the ``acquire.py`` command-line tool.

Saving is handled by each board's own GUI: when a board acquires, if its
``AutoSave`` is on it writes to the folder configured there
(``SavePrefix``). This tab therefore does not choose a save location -
set it in each LinoSPAD_synchro instance.

Prerequisite: both board apps must already be running and "Listening" on
their TCP ports (default 5555 / 5556) before this tab is used. Use
25 MHz on the external clock; 20 MHz never programs the DCM.

The TCP calls run in a background :class:`AcquisitionWorker`, because
``RUNHISTOGRAMS`` blocks until the acquisition finishes and so must not
run on the GUI thread.

The tab has no plot, but it is built in the same shell as the four that
do: the log sits where their canvas sits, the clock status sits where
their axis limits sit, and the three buttons sit in the same three
slots. Moving between tabs then moves nothing under the hands.

"""

import os
import socket
import subprocess
import threading

from PyQt5 import QtCore, QtWidgets

from daplis_rtp.gui.layout import (
    SPACING,
    ElidedLabel,
    TabShell,
    led,
    set_led,
)
from daplis_rtp.gui.session import SessionStore
from daplis_rtp.gui.widgets import FileSyncPanel

# All instances are addressed on the local machine.
HOST = "localhost"

# Default location of the two-board GUI and the per-board settings
# files. These are remembered per user via QSettings once changed here.
DEFAULT_EXE = (
    r"D:\ls2sw_synchro\release_2212\release_2212\shared_ver2"
    r"\LinoSPAD_synchro.exe"
)
DEFAULT_SETTINGS = {0: "settings_14.txt", 1: "settings_23.txt"}

# -- TCP protocol helpers (same wire protocol as acquire.py) -----------
# "On external and locked" = bit0 (external selected) AND bit2 (PLL
# locked). bit31 (module clock valid) is true even on the internal
# oscillator, so it is NOT a lock indicator on its own.
LOCK_MASK = 0x5
CONNECT_TIMEOUT = 5


def send_cmd(host, port, cmd, timeout=CONNECT_TIMEOUT):
    """Send one newline-terminated command; return the response up to DONE."""
    with socket.socket() as s:
        s.settimeout(CONNECT_TIMEOUT)
        s.connect((host, port))
        s.sendall((cmd + "\n").encode())
        s.settimeout(timeout)
        data = b""
        while b"DONE" not in data:
            chunk = s.recv(256)
            if not chunk:
                break
            data += chunk
        return data.decode().strip()


def is_locked(status):
    return (status & LOCK_MASK) == LOCK_MASK


class AcquisitionWorker(QtCore.QThread):
    """Run enable -> check -> acquire off the GUI thread.

    Emits signals for logging, per-board clock status, and completion;
    never touches widgets directly. Saving is left to each board's GUI
    (AutoSave).

    """

    log = QtCore.pyqtSignal(str)
    # board_id, status word (Python int, passed as object to avoid
    # 32-bit signal overflow), locked
    clock = QtCore.pyqtSignal(int, object, bool)
    clock_fail = QtCore.pyqtSignal(int, str)
    done = QtCore.pyqtSignal(bool, str)

    def __init__(self, boards, check_only, acq_timeout, parent=None):
        super().__init__(parent)
        self.boards = boards  # {0: (host, port), 1: (host, port)}
        self.check_only = check_only
        self.acq_timeout = acq_timeout

    def run(self):
        try:
            # 1. ensure the external clock before acquiring. "Check
            #    clocks" is a pure read and does not change the source.
            if not self.check_only:
                self.log.emit("Enabling external clock on both boards...")
                for bid, (host, port) in self.boards.items():
                    try:
                        st = int(
                            send_cmd(host, port, "SETCLOCKSTATE 1").split()[0]
                        )
                    except Exception as e:  # noqa: BLE001 - report it
                        self.clock_fail.emit(bid, str(e))
                        self.done.emit(
                            False,
                            f"Board {bid}: cannot reach "
                            f"LinoSPAD_synchro.exe on {host}:{port} ({e}). "
                            "Is it running and 'Listening'?",
                        )
                        return
                    self.clock.emit(bid, st, is_locked(st))
                    self.log.emit(
                        f"  Board {bid}: 0x{st:08X}  "
                        + (
                            "EXT LOCKED"
                            if is_locked(st)
                            else "fell back to internal -- check CLK_IN (J11)"
                        )
                    )

            # 2. verify both boards are locked to the external clock
            self.log.emit("Checking clock status...")
            all_locked = True
            for bid, (host, port) in self.boards.items():
                try:
                    st = int(
                        send_cmd(host, port, "GETCLOCKSTATE").split()[0]
                    )
                except Exception as e:  # noqa: BLE001 - report it
                    self.clock_fail.emit(bid, str(e))
                    self.done.emit(
                        False, f"Board {bid}: connection failed ({e})."
                    )
                    return
                locked = is_locked(st)
                self.clock.emit(bid, st, locked)
                self.log.emit(
                    f"  Board {bid}: 0x{st:08X}  ->  "
                    + ("EXT LOCKED" if locked else "NOT ON EXTERNAL CLOCK")
                )
                if not locked:
                    all_locked = False

            if not all_locked:
                self.done.emit(
                    False,
                    "One or both boards are NOT locked to the external "
                    "clock. Nothing acquired.\n\nCheck: 25 MHz square "
                    "wave on CLK_IN (J11) of both boards; the Ext MHz "
                    "box reads 25 (not ~50); 25 MHz, not 20.",
                )
                return

            if self.check_only:
                self.done.emit(True, "Both boards EXT LOCKED.")
                return

            # 3. acquire on both boards simultaneously. Each board saves
            #    to its own GUI 'Save' path (AutoSave) when it finishes.
            self.log.emit("Starting acquisition on both boards...")
            errors = {}

            def _acquire_one(bid):
                host, port = self.boards[bid]
                try:
                    self.log.emit(f"[Board {bid}] RUNHISTOGRAMS sent")
                    send_cmd(
                        host, port, "RUNHISTOGRAMS", timeout=self.acq_timeout
                    )
                    self.log.emit(f"[Board {bid}] acquisition complete")
                except Exception as e:  # noqa: BLE001 - report it
                    errors[bid] = str(e)
                    self.log.emit(f"[Board {bid}] ERROR: {e}")

            threads = [
                threading.Thread(target=_acquire_one, args=(bid,))
                for bid in self.boards
            ]
            for t in threads:
                t.start()  # both start within microseconds of each other
            for t in threads:
                t.join()

            if errors:
                self.done.emit(False, f"Errors during acquisition: {errors}")
                return

            self.done.emit(
                True,
                "Done. Both boards acquired. Each file was saved by its "
                "GUI to the configured Save path (AutoSave).",
            )

        except Exception as e:  # noqa: BLE001 - never die silently
            self.done.emit(False, f"Unexpected error: {e}")


class Synchronization(TabShell):
    """Tab for controlling two-board synchronized acquisition over TCP."""

    # board_id -> (label text, default port)
    BOARD_INFO = {
        0: ("Board 0  (dev 0 / #33)", 5555),
        1: ("Board 1  (dev 1 / #21)", 5556),
    }

    HINT = (
        "Both LinoSPAD_synchro.exe instances must be running and "
        "'Listening' first. Use 25 MHz on the external clock. Each "
        "board saves to its own GUI's AutoSave path."
    )

    def __init__(self, parent=None):
        super().__init__(parent, hint=self.HINT)
        # '_worker' is read by 'main._quiesce' when the window closes: a
        # QThread destroyed while still running aborts the process.
        self._worker = None
        self._procs = {}  # board_id -> Popen of a launched GUI
        self._leds = {}
        self._status_labels = {}
        self._ports = {}
        self._settings_edits = {}
        # Left as it was so that an existing user keeps the paths they
        # had; the theme's settings live under their own keys.
        self._qsettings = QtCore.QSettings(
            "daplis-rtp", "synchronization_tab"
        )
        self._build_header()
        self._build_log()
        self._build_footer()
        self._build_controls()
        self._build_actions()
        self._connect()

        # The executable, the settings files and the two data folders
        # are remembered by '_qsettings' above, under the keys they have
        # always used. The ports and the timeout were not remembered at
        # all, and they are the two most likely to be wrong on a fresh
        # start, so they go in the session store with everything else's.
        self.session = SessionStore("synchronization")
        self.session.bind_all(
            [("port_{}".format(bid), spin)
             for bid, spin in self._ports.items()]
        )
        self.session.bind("acq_timeout", self.spinBox_timeout)
        self.session.bind("boards_in_step", self.fileSyncPanel)
        self.session.restore()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_header(self):
        row = self.header_row(0)
        row.addWidget(QtWidgets.QLabel("LinoSPAD_synchro.exe", self))
        self.lineEdit_exe = QtWidgets.QLineEdit(
            self._qsettings.value("exe", DEFAULT_EXE, type=str), self
        )
        self.lineEdit_exe.setToolTip(
            "The two-board GUI. 'Launch boards' starts one instance of "
            "it per board, each with its own settings file."
        )
        row.addWidget(self.lineEdit_exe, 1)
        self.pushButton_browseExe = QtWidgets.QPushButton("Browse", self)
        row.addWidget(self.pushButton_browseExe)

        # One settings file per board, side by side: the second header
        # row is two browse rows' worth of space on the full-sensor tab,
        # so it is two fields' worth here. The captions are the short
        # names - the full ones, with the device and motherboard
        # numbers, are in the Connection box beside them, and spelling
        # them out here was setting how narrow the window could be made.
        row = self.header_row(1)
        for bid in self.BOARD_INFO:
            row.addWidget(
                QtWidgets.QLabel("Board {} settings".format(bid), self)
            )
            edit = QtWidgets.QLineEdit(
                self._qsettings.value(
                    "settings_{}".format(bid), DEFAULT_SETTINGS[bid], type=str
                ),
                self,
            )
            edit.setToolTip(
                "Settings file this board's instance is started with, "
                "relative to the executable."
            )
            self._settings_edits[bid] = edit
            row.addWidget(edit, 1)

    def _build_log(self):
        """The log goes where the other tabs put their plot."""
        self.plainTextEdit_log = QtWidgets.QPlainTextEdit(self)
        self.plainTextEdit_log.setObjectName("logView")
        self.plainTextEdit_log.setReadOnly(True)
        self.plainTextEdit_log.setPlaceholderText(
            "What the two boards say, as they say it."
        )
        self.set_canvas(self.plainTextEdit_log)

    def _build_footer(self):
        """Clock status, where the other tabs put their axis limits."""
        row = self.footer_row()
        for bid, (label, _port) in self.BOARD_INFO.items():
            lamp = led(self)
            self._leds[bid] = lamp
            row.addWidget(lamp)
            caption = QtWidgets.QLabel("Board {}".format(bid), self)
            caption.setToolTip(label)
            row.addWidget(caption)
            status = ElidedLabel("—", self)
            status.setToolTip(
                "Whether this board is locked to the external clock, "
                "and the raw status word it reported."
            )
            self._status_labels[bid] = status
            row.addWidget(status, 1)
            row.addSpacing(SPACING * 3)

    def _build_controls(self):
        column = self.controls

        box, inner = column.add_group("Connection")
        box.setToolTip(
            "Both instances run on this machine, so the host is "
            "always localhost; only the ports are settable."
        )
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(SPACING)
        for row, (bid, (label, port)) in enumerate(self.BOARD_INFO.items()):
            grid.addWidget(QtWidgets.QLabel(label.split("  ")[0], box), row, 0)
            grid.addWidget(QtWidgets.QLabel("Port", box), row, 1)
            spin = QtWidgets.QSpinBox(box)
            spin.setRange(1, 65535)
            spin.setValue(port)
            spin.setToolTip(
                "The port this board's instance is listening on. It "
                "must match the one set in that window."
            )
            self._ports[bid] = spin
            grid.addWidget(spin, row, 2)
        grid.setColumnStretch(0, 1)
        inner.addLayout(grid)

        self.spinBox_timeout = column.add_row(
            "Acq. timeout (s)",
            QtWidgets.QSpinBox(),
            tip="How long to wait for each board's RUNHISTOGRAMS to "
                "finish.",
        )
        self.spinBox_timeout.setRange(1, 3600)
        self.spinBox_timeout.setValue(300)

        # Each board's own GUI saves where its AutoSave points, so the
        # two folders have to be named here; the check then watches, in
        # the background and for as long as the acquisition runs, that
        # both boards keep writing the same number of files at the same
        # time. The folders are only read, never written to.
        self.fileSyncPanel = FileSyncPanel(
            self, labels=("Board 0", "Board 1"), with_paths=True
        )
        self.fileSyncPanel.set_paths(
            self._qsettings.value("folder_0", "", type=str),
            self._qsettings.value("folder_1", "", type=str),
        )
        column.add_widget(self.fileSyncPanel)
        column.add_stretch()

    def _build_actions(self):
        # In the slots the shell reserves for them: look again, then the
        # thing the tab is for, then the extra. Launching the two board
        # windows comes first in the workflow but last in the bar, so
        # that "Acquire" sits under the same pixels as "Start stream"
        # does on every plotting tab.
        self.pushButton_check = self.actions.add_button(
            "Check clocks",
            tip="Read both boards' clock status without changing "
                "anything.",
        )
        self.pushButton_acquire = self.actions.add_button(
            "Acquire",
            tip="Put both boards on the external clock, verify both are "
                "locked, and start both acquisitions together.",
            primary=True,
        )
        self.pushButton_launch = self.actions.add_button(
            "Launch boards",
            tip="Start one LinoSPAD_synchro.exe per board, each with "
                "its own settings file. Do this first, then set each "
                "window to Listen and 25 MHz External.",
        )

    def _connect(self):
        self.pushButton_browseExe.clicked.connect(self._browse_exe)
        self.pushButton_launch.clicked.connect(self._launch)
        self.pushButton_check.clicked.connect(
            lambda: self._start(check_only=True)
        )
        self.pushButton_acquire.clicked.connect(
            lambda: self._start(check_only=False)
        )
        self.fileSyncPanel.problem.connect(self._on_sync_problem)

    # ------------------------------------------------------------------
    # Launching the board GUIs
    # ------------------------------------------------------------------

    def _browse_exe(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select LinoSPAD_synchro.exe", "", "Executables (*.exe)"
        )
        if path:
            self.lineEdit_exe.setText(path)

    def _save_paths(self):
        self._qsettings.setValue("exe", self.lineEdit_exe.text().strip())
        for bid in self.BOARD_INFO:
            self._qsettings.setValue(
                "settings_{}".format(bid),
                self._settings_edits[bid].text().strip(),
            )
        for bid, folder in zip(self.BOARD_INFO, self.fileSyncPanel.paths()):
            self._qsettings.setValue("folder_{}".format(bid), folder)

    def _launch(self):
        exe = self.lineEdit_exe.text().strip()
        if not exe or not os.path.isfile(exe):
            QtWidgets.QMessageBox.warning(
                self,
                "Launch boards",
                "LinoSPAD_synchro.exe not found:\n{}".format(exe),
            )
            return
        cwd = os.path.dirname(exe)
        self._save_paths()
        self._append("\n=== Launch boards ===")
        for bid in self.BOARD_INFO:
            proc = self._procs.get(bid)
            if proc is not None and proc.poll() is None:
                self._append(
                    "[Board {}] already running (PID {}); skipped.".format(
                        bid, proc.pid
                    )
                )
                continue
            settings = self._settings_edits[bid].text().strip()
            cmd = [exe, "-d", str(bid), "-s", settings]
            try:
                proc = subprocess.Popen(cmd, cwd=cwd)
            except Exception as e:  # noqa: BLE001 - report to the user
                self._append("[Board {}] launch failed: {}".format(bid, e))
                continue
            self._procs[bid] = proc
            self._append(
                "[Board {}] launched (PID {}): {}".format(
                    bid, proc.pid, " ".join(cmd)
                )
            )
        self._append(
            "In each board window: click 'Listen' (the port must match "
            "the Connection port) and set 25 MHz External. Then Acquire."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _append(self, msg):
        self.plainTextEdit_log.appendPlainText(msg)

    def _busy(self, busy):
        self.pushButton_check.setEnabled(not busy)
        self.pushButton_acquire.setEnabled(not busy)

    # ------------------------------------------------------------------
    # Run control
    # ------------------------------------------------------------------

    def _start(self, check_only):
        if self._worker is not None and self._worker.isRunning():
            return

        boards = {}
        for bid in self.BOARD_INFO:
            boards[bid] = (HOST, int(self._ports[bid].value()))
            set_led(self._leds[bid], "idle")
            self._status_labels[bid].setText("…")

        self._append(
            "\n=== "
            + ("Check clocks" if check_only else "Acquire")
            + " ==="
        )
        self._busy(True)

        # The file check only makes sense while data are being written.
        if not check_only:
            self._save_paths()
            self.fileSyncPanel.start()
            if not all(self.fileSyncPanel.paths()):
                self._append(
                    "Note: no data folders set, so the two boards are "
                    "NOT checked for writing in step."
                )

        self._worker = AcquisitionWorker(
            boards=boards,
            check_only=check_only,
            acq_timeout=int(self.spinBox_timeout.value()),
        )
        self._worker.log.connect(self._append)
        self._worker.clock.connect(self._on_clock)
        self._worker.clock_fail.connect(self._on_clock_fail)
        self._worker.done.connect(self._on_done)
        self._worker.start()

    # ------------------------------------------------------------------
    # Worker signal slots
    # ------------------------------------------------------------------

    def _on_clock(self, bid, status, locked):
        set_led(self._leds[bid], "ok" if locked else "error")
        self._status_labels[bid].setText(
            ("EXT LOCKED" if locked else "NOT on external clock")
            + "  (0x{:08X})".format(status)
        )

    def _on_clock_fail(self, bid, err):
        set_led(self._leds[bid], "warn")
        self._status_labels[bid].setText("unreachable ({})".format(err))

    def _on_sync_problem(self, summary, details):
        """Keep the out-of-step alert in the log after the box is closed."""
        self._append("\n!!! " + summary + "\n\n" + details)

    def _on_done(self, success, message):
        self._busy(False)
        self.fileSyncPanel.stop()
        self._append(message)
        if not success:
            box = QtWidgets.QMessageBox(self)
            box.setIcon(QtWidgets.QMessageBox.Warning)
            box.setWindowTitle("Acquisition stopped")
            box.setText(message)
            box.exec_()
