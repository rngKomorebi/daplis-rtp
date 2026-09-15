"""Synchronization tab — control two-board synchronized acquisition.

This tab drives two running instances of ``LinoSPAD_synchro.exe`` over TCP (one
per board): it enables the external clock, verifies both boards are locked, and
starts acquisition on both **simultaneously**. It is the GUI equivalent of the
``acquire.py`` command-line tool.

Saving is handled by each board's own GUI: when a board acquires, if its
``AutoSave`` is on it writes to the folder configured there (``SavePrefix``). This
tab therefore does not choose a save location — set it in each LinoSPAD_synchro
instance.

Prerequisite: both board apps must already be running and "Listening" on their
TCP ports (default 5555 / 5556) before using this tab. Use 25 MHz on the external
clock (20 MHz never programs the DCM).

The TCP calls run in a background :class:`AcquisitionWorker` (``RUNHISTOGRAMS``
blocks until the acquisition finishes, so it must not run on the GUI thread).
"""

import os
import socket
import subprocess
import threading

from PyQt5 import QtCore, QtGui, QtWidgets

from daplis_rtp.gui.file_sync_check import FileSyncPanel

# All instances are addressed on the local machine.
HOST = "localhost"

# Default location of the two-board GUI and the per-board settings files. These
# are remembered per user via QSettings once changed in the tab.
DEFAULT_EXE = (
    r"D:\ls2sw_synchro\release_2212\release_2212\shared_ver2"
    r"\LinoSPAD_synchro.exe"
)
DEFAULT_SETTINGS = {0: "settings_14.txt", 1: "settings_23.txt"}

# ── TCP protocol helpers (same wire protocol as acquire.py) ──────────────────
# "On external and locked" = bit0 (external selected) AND bit2 (PLL locked).
# bit31 (module clock valid) is true even on the internal oscillator, so it is
# NOT a lock indicator on its own.
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

    Emits signals for logging, per-board clock status, and completion; never
    touches widgets directly. Saving is left to each board's GUI (AutoSave).
    """

    log = QtCore.pyqtSignal(str)
    # board_id, status word (Python int, passed as object to avoid 32-bit
    # signal overflow), locked
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
            # 1. ensure the external clock before acquiring. "Check clocks" is a
            #    pure read and does not change the clock source.
            if not self.check_only:
                self.log.emit("Enabling external clock on both boards...")
                for bid, (host, port) in self.boards.items():
                    try:
                        st = int(
                            send_cmd(host, port, "SETCLOCKSTATE 1").split()[0]
                        )
                    except Exception as e:  # noqa: BLE001 - report to the user
                        self.clock_fail.emit(bid, str(e))
                        self.done.emit(
                            False,
                            f"Board {bid}: cannot reach LinoSPAD_synchro.exe "
                            f"on {host}:{port} ({e}). Is it running and "
                            "'Listening'?",
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
                except Exception as e:  # noqa: BLE001 - report to the user
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
                    "clock. Nothing acquired.\n\nCheck: 25 MHz square wave on "
                    "CLK_IN (J11) of both boards; the Ext MHz box reads 25 "
                    "(not ~50); 25 MHz, not 20.",
                )
                return

            if self.check_only:
                self.done.emit(True, "Both boards EXT LOCKED.")
                return

            # 3. acquire on both boards simultaneously. Each board saves to its
            #    own GUI 'Save' path (AutoSave) when the run finishes.
            self.log.emit("Starting acquisition on both boards...")
            errors = {}

            def _acquire_one(bid):
                host, port = self.boards[bid]
                try:
                    self.log.emit(f"[Board {bid}] RUNHISTOGRAMS sent")
                    send_cmd(host, port, "RUNHISTOGRAMS", timeout=self.acq_timeout)
                    self.log.emit(f"[Board {bid}] acquisition complete")
                except Exception as e:  # noqa: BLE001 - report to the user
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
                "Done. Both boards acquired. Each file was saved by its GUI "
                "to the configured Save path (AutoSave).",
            )

        except Exception as e:  # noqa: BLE001 - never let the thread die silently
            self.done.emit(False, f"Unexpected error: {e}")


class Synchronization(QtWidgets.QWidget):
    """Tab for controlling two-board synchronized acquisition over TCP."""

    # board_id -> (label text, default port)
    BOARD_INFO = {
        0: ("Board 0  (dev 0 / #33)", 5555),
        1: ("Board 1  (dev 1 / #21)", 5556),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._procs = {}  # board_id -> Popen of a launched GUI
        self._leds = {}
        self._status_labels = {}
        self._ports = {}
        self._settings_edits = {}
        self._qsettings = QtCore.QSettings("daplis-rtp", "synchronization_tab")
        self._build_ui()
        self._connect()

    # ── UI construction ──────────────────────────────────────────────────────
    def _build_ui(self):
        font_header = QtGui.QFont()  # group-box titles
        font_header.setPointSize(13)
        font_body = QtGui.QFont()  # widgets inside the boxes
        font_body.setPointSize(11)
        font_btn = QtGui.QFont()  # buttons
        font_btn.setPointSize(13)
        font_acq = QtGui.QFont()  # the Acquire button (bold)
        font_acq.setPointSize(13)
        font_acq.setBold(True)

        root = QtWidgets.QVBoxLayout(self)

        title = QtWidgets.QLabel("Two-board synchronized acquisition")
        tfont = QtGui.QFont()
        tfont.setPointSize(13)
        tfont.setBold(True)
        title.setFont(tfont)
        root.addWidget(title)

        hint = QtWidgets.QLabel(
            "Both LinoSPAD_synchro.exe instances must be running and "
            "'Listening' first. Use 25 MHz on the external clock. Files are "
            "saved by each board's own GUI to its configured Save path "
            "(AutoSave) — set the location there."
        )
        hint.setWordWrap(True)
        hfont = QtGui.QFont()
        hfont.setPointSize(10)
        hint.setFont(hfont)
        root.addWidget(hint)

        # ── Two columns ───────────────────────────────────────────
        # Setting up a run (left) and watching it (right). Stacked in
        # one column the six boxes came to some 830 px, which is the
        # tallest thing in the application and so decided how tall the
        # window had to open; side by side they come to about half that,
        # and the two halves read as what they are - what is set once
        # before a run, and what is looked at while it runs.
        columns = QtWidgets.QHBoxLayout()
        left = QtWidgets.QVBoxLayout()
        right = QtWidgets.QVBoxLayout()
        columns.addLayout(left, 1)
        columns.addLayout(right, 1)
        root.addLayout(columns)

        # ── Boards group: launch the two GUI instances from here ─────────────
        launch_group = QtWidgets.QGroupBox("Boards")
        launch_group.setFont(font_header)
        lg = QtWidgets.QGridLayout(launch_group)
        lg.setHorizontalSpacing(10)

        exe_lbl = QtWidgets.QLabel("LinoSPAD_synchro.exe:")
        exe_lbl.setFont(font_body)
        lg.addWidget(exe_lbl, 0, 0)
        self.lineEdit_exe = QtWidgets.QLineEdit(
            self._qsettings.value("exe", DEFAULT_EXE, type=str)
        )
        self.lineEdit_exe.setFont(font_body)
        lg.addWidget(self.lineEdit_exe, 0, 1)
        self.pushButton_browseExe = QtWidgets.QPushButton("Browse")
        self.pushButton_browseExe.setFont(font_body)
        lg.addWidget(self.pushButton_browseExe, 0, 2)

        for i, (bid, (label, _port)) in enumerate(
            self.BOARD_INFO.items(), start=1
        ):
            s_lbl = QtWidgets.QLabel(f"{label}  settings:")
            s_lbl.setFont(font_body)
            lg.addWidget(s_lbl, i, 0)
            edit = QtWidgets.QLineEdit(
                self._qsettings.value(
                    f"settings_{bid}", DEFAULT_SETTINGS[bid], type=str
                )
            )
            edit.setFont(font_body)
            self._settings_edits[bid] = edit
            lg.addWidget(edit, i, 1, 1, 2)

        self.pushButton_launch = QtWidgets.QPushButton("Launch both boards")
        self.pushButton_launch.setFont(font_btn)
        self.pushButton_launch.setMinimumHeight(32)
        lg.addWidget(self.pushButton_launch, len(self.BOARD_INFO) + 1, 0, 1, 3)
        lg.setColumnStretch(1, 1)
        left.addWidget(launch_group)

        # ── Connection group (host is always localhost) ──────────────────────
        conn_group = QtWidgets.QGroupBox("Connection  (host: localhost)")
        conn_group.setFont(font_header)
        conn = QtWidgets.QGridLayout(conn_group)
        conn.setHorizontalSpacing(10)
        for row, (bid, (label, port)) in enumerate(self.BOARD_INFO.items()):
            board_lbl = QtWidgets.QLabel(label)
            board_lbl.setFont(font_body)
            conn.addWidget(board_lbl, row, 0)
            port_lbl = QtWidgets.QLabel("Port:")
            port_lbl.setFont(font_body)
            conn.addWidget(port_lbl, row, 1)
            port_spin = QtWidgets.QSpinBox()
            port_spin.setRange(1, 65535)
            port_spin.setValue(port)
            port_spin.setMaximumWidth(90)
            port_spin.setFont(font_body)
            self._ports[bid] = port_spin
            conn.addWidget(port_spin, row, 2)
        conn.setColumnStretch(3, 1)  # trailing space keeps label+port on the left
        left.addWidget(conn_group)

        # ── Options group ────────────────────────────────────────────────────
        opt_group = QtWidgets.QGroupBox("Options")
        opt_group.setFont(font_header)
        opt = QtWidgets.QGridLayout(opt_group)
        opt.setHorizontalSpacing(10)
        timeout_lbl = QtWidgets.QLabel("Acq. timeout (s):")
        timeout_lbl.setFont(font_body)
        opt.addWidget(timeout_lbl, 0, 0)
        self.spinBox_timeout = QtWidgets.QSpinBox()
        self.spinBox_timeout.setRange(1, 3600)
        self.spinBox_timeout.setValue(300)
        self.spinBox_timeout.setMaximumWidth(90)
        self.spinBox_timeout.setFont(font_body)
        self.spinBox_timeout.setToolTip(
            "How long to wait for each board's RUNHISTOGRAMS to finish."
        )
        opt.addWidget(self.spinBox_timeout, 0, 1)
        opt.setColumnStretch(2, 1)
        left.addWidget(opt_group)

        # ── Both boards in step ──────────────────────────────────────────────
        # Each board's own GUI saves where its AutoSave points, so the
        # two folders have to be named here; the check then watches, in
        # the background and for as long as the acquisition runs, that
        # both boards keep writing the same number of files at the same
        # time. The folders are only read, never written to.
        self.fileSyncPanel = FileSyncPanel(
            self,
            font=font_body,
            labels=("Board 0", "Board 1"),
            with_paths=True,
        )
        self.fileSyncPanel.setFont(font_header)
        self.fileSyncPanel.set_paths(
            self._qsettings.value("folder_0", "", type=str),
            self._qsettings.value("folder_1", "", type=str),
        )
        right.addWidget(self.fileSyncPanel)

        # ── Clock status group ───────────────────────────────────────────────
        st_group = QtWidgets.QGroupBox("Clock status")
        st_group.setFont(font_header)
        st = QtWidgets.QGridLayout(st_group)
        for row, (bid, (label, _p)) in enumerate(self.BOARD_INFO.items()):
            led = QtWidgets.QLabel("●")  # ●
            led.setFixedWidth(18)
            self._set_led(led, "grey")
            self._leds[bid] = led
            st.addWidget(led, row, 0)
            board_lbl = QtWidgets.QLabel(label)
            board_lbl.setFont(font_body)
            st.addWidget(board_lbl, row, 1)
            status = QtWidgets.QLabel("—")  # em dash
            status.setFont(font_body)
            self._status_labels[bid] = status
            st.addWidget(status, row, 2)
        st.setColumnStretch(2, 1)
        right.addWidget(st_group)

        left.addStretch(1)
        right.addStretch(1)

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_row = QtWidgets.QHBoxLayout()
        self.pushButton_check = QtWidgets.QPushButton("Check clocks")
        self.pushButton_check.setFont(font_btn)
        self.pushButton_check.setMinimumHeight(36)
        self.pushButton_acquire = QtWidgets.QPushButton("Acquire")
        self.pushButton_acquire.setFont(font_acq)
        self.pushButton_acquire.setMinimumHeight(36)
        btn_row.addWidget(self.pushButton_check)
        btn_row.addWidget(self.pushButton_acquire)
        root.addLayout(btn_row)

        # ── Log ──────────────────────────────────────────────────────────────
        self.plainTextEdit_log = QtWidgets.QPlainTextEdit()
        self.plainTextEdit_log.setReadOnly(True)
        self.plainTextEdit_log.setFont(QtGui.QFont("Consolas", 9))
        root.addWidget(self.plainTextEdit_log, stretch=1)

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

    # ── launch the board GUIs ────────────────────────────────────────────────
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
                f"settings_{bid}", self._settings_edits[bid].text().strip()
            )
        for bid, folder in zip(self.BOARD_INFO, self.fileSyncPanel.paths()):
            self._qsettings.setValue(f"folder_{bid}", folder)

    def _launch(self):
        exe = self.lineEdit_exe.text().strip()
        if not exe or not os.path.isfile(exe):
            QtWidgets.QMessageBox.warning(
                self, "Launch boards",
                f"LinoSPAD_synchro.exe not found:\n{exe}",
            )
            return
        cwd = os.path.dirname(exe)
        self._save_paths()
        self._append("\n=== Launch boards ===")
        for bid in self.BOARD_INFO:
            proc = self._procs.get(bid)
            if proc is not None and proc.poll() is None:
                self._append(
                    f"[Board {bid}] already running (PID {proc.pid}); skipped."
                )
                continue
            settings = self._settings_edits[bid].text().strip()
            cmd = [exe, "-d", str(bid), "-s", settings]
            try:
                proc = subprocess.Popen(cmd, cwd=cwd)
            except Exception as e:  # noqa: BLE001 - report to the user
                self._append(f"[Board {bid}] launch failed: {e}")
                continue
            self._procs[bid] = proc
            self._append(
                f"[Board {bid}] launched (PID {proc.pid}): " + " ".join(cmd)
            )
        self._append(
            "In each board window: click 'Listen' (the port must match the "
            "Connection port above) and set 25 MHz External. Then Acquire."
        )

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _set_led(label, color):
        label.setStyleSheet(f"color: {color}; font-size: 16px;")

    def _append(self, msg):
        self.plainTextEdit_log.appendPlainText(msg)

    def _busy(self, busy):
        self.pushButton_check.setEnabled(not busy)
        self.pushButton_acquire.setEnabled(not busy)

    # ── run control ──────────────────────────────────────────────────────────
    def _start(self, check_only):
        if self._worker is not None and self._worker.isRunning():
            return

        boards = {}
        for bid in self.BOARD_INFO:
            boards[bid] = (HOST, int(self._ports[bid].value()))
            self._set_led(self._leds[bid], "grey")
            self._status_labels[bid].setText("…")  # …

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
                    "Note: no data folders set, so the two boards are NOT "
                    "checked for writing in step."
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

    # ── worker signal slots ──────────────────────────────────────────────────
    def _on_clock(self, bid, status, locked):
        self._set_led(self._leds[bid], "limegreen" if locked else "red")
        self._status_labels[bid].setText(
            ("EXT LOCKED" if locked else "NOT on external clock")
            + f"  (0x{status:08X})"
        )

    def _on_clock_fail(self, bid, err):
        self._set_led(self._leds[bid], "grey")
        self._status_labels[bid].setText(f"unreachable ({err})")

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
