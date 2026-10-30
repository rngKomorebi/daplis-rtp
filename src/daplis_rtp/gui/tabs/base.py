"""What the four plotting tabs do the same way.

Finding the newest data file, noticing when a new one lands, reporting a
file that cannot be read, stopping cleanly when it goes wrong: each tab
had its own copy of all four, and they had drifted. Only one of them
guarded against the refresh firing again while one was still running,
only one closed over the case of the directory disappearing mid-stream,
and the three that showed an error box left the timer running behind it
- so a modal box, which spins an event loop of its own, stacked a new
box on top of itself every 100 ms until the stream was stopped by hand.

"""

import glob
import os

from PyQt5 import QtCore, QtWidgets

from daplis_rtp.gui.layout import TabShell
from daplis_rtp.gui.session import SessionStore

# A directory that has just changed is a directory something is still
# writing to, so the look is delayed by this much and restarted by every
# further change - one read per burst of activity rather than one per
# event.
SETTLE_MS = 150

# How often the folder is looked at even when the watcher has said
# nothing. QFileSystemWatcher is reliable on a local disk and decidedly
# not on a network share, which is exactly where a board GUI writes when
# the acquisition PC is not the analysis PC, so the poll stays as a
# backstop. Slow enough to cost nothing; fast enough that a missed
# notification is an inconvenience rather than a stalled plot.
FALLBACK_POLL_MS = 2000


class PlotTab(TabShell):
    """A tab with a plot, a folder of data files, and a live stream."""

    # Shown in the strip across the top of the tab.
    hint_text = ""
    # The canvas class this tab draws on.
    canvas_class = None
    # Names this tab's stored settings. Must not change once shipped.
    session_scope = ""

    def __init__(self, parent=None):
        super().__init__(parent, hint=self.hint_text)

        self.widget_figure = self.canvas_class(self)
        self.set_canvas(self.widget_figure)

        # 'timer' and 'mask_window' are read by 'main_window.quiesce'
        # when the window closes: a QTimer left running fires into a
        # deleted object, and the mask is a window of its own that would
        # otherwise outlive its tab.
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(FALLBACK_POLL_MS)
        self.timer.timeout.connect(self.update_time_stamp)
        self.timerRunning = False
        self._updating = False

        # The folders are watched rather than swept. The old stream ran
        # 'glob' plus a 'getctime' per entry ten times a second, which
        # on a run of several thousand files is several thousand stat
        # calls a second for the sake of noticing one new name.
        self._watcher = QtCore.QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._folder_changed)
        self._settle = QtCore.QTimer(self)
        self._settle.setSingleShot(True)
        self._settle.setInterval(SETTLE_MS)
        self._settle.timeout.connect(self.update_time_stamp)

        self.last_file_ctime = 0
        self.pushButton_startStream = None
        # Whether an empty folder is worth interrupting the user over.
        # Set only around an explicit 'Refresh plot'.
        self._announce_missing = False

        self.session = SessionStore(
            self.session_scope or type(self).__name__.lower()
        )

        self.build()

        # After 'build', so that every widget the tab wants remembered
        # exists, and before anything is plotted.
        self.bind_session()
        self.session.restore()
        self.on_session_restored()

    def build(self):
        """Fill the shell. Every tab writes this and nothing else."""
        raise NotImplementedError

    def bind_session(self):
        """Register the controls this tab should remember."""

    def on_session_restored(self):
        """Hook: derive whatever the restored controls imply.

        A control whose value the tab also keeps in a variable - a
        cycle length parsed out of a line edit - has to be re-read once
        the stored text is back in the widget.

        """

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    def watched_paths(self):
        """The folders a running stream should watch. Tabs override."""
        return []

    def toggle_stream(self):
        if self.timerRunning:
            self.stop_stream()
        else:
            self.start_stream()

    def start_stream(self):
        self.last_file_ctime = 0
        self.on_stream_start()
        self._watch(self.watched_paths())
        self.timer.start()
        self.timerRunning = True
        if self.pushButton_startStream is not None:
            self.pushButton_startStream.setText("Stop stream")
        # Draw what is already there rather than waiting for the next
        # file: starting a stream on a folder that is not being written
        # to used to show nothing at all until something arrived.
        self.update_time_stamp()

    def stop_stream(self):
        self.timer.stop()
        self._settle.stop()
        self._watch([])
        self.timerRunning = False
        self.last_file_ctime = 0
        if self.pushButton_startStream is not None:
            self.pushButton_startStream.setText("Start stream")
        self.on_stream_stop()

    def on_stream_start(self):
        """Hook: what this tab arms when a run starts."""

    def on_stream_stop(self):
        """Hook: what this tab stands down when a run ends."""

    def _watch(self, paths):
        """Watch exactly ``paths`` and nothing else."""
        current = self._watcher.directories()
        if current:
            self._watcher.removePaths(current)
        wanted = [p for p in paths if p and os.path.isdir(p)]
        if wanted:
            self._watcher.addPaths(wanted)

    def _folder_changed(self, path):
        """Something landed in a watched folder; look once it settles."""
        # A directory replaced wholesale - deleted and recreated by a
        # board GUI starting a new run - is silently dropped by the
        # watcher, so it is re-added on every notification.
        if os.path.isdir(path) and path not in self._watcher.directories():
            self._watcher.addPath(path)
        self._settle.start()

    def slot_refresh(self):
        """Look again now, whether or not a stream is running."""
        self.last_file_ctime = 0
        self.on_refresh_requested()
        self._announce_missing = True
        try:
            self.update_time_stamp()
        finally:
            self._announce_missing = False

    def on_refresh_requested(self):
        """Hook: what an explicit 'look again' re-arms."""

    def update_time_stamp(self):
        """One refresh, and never two at once.

        Both the canvas redraw and a message box spin the event loop, so
        another refresh can be asked for while this call is still
        running; without the guard those calls stack up.

        """
        if self._updating:
            return
        self._updating = True
        try:
            self.refresh()
        finally:
            self._updating = False

    def refresh(self):
        """Read the newest file and redraw. Written by every tab."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Data files
    # ------------------------------------------------------------------

    @staticmethod
    def last_data_file(path):
        """The newest '.dat' file in ``path``, or ``None``.

        ``None`` covers both a directory with no data files in it and
        the files - or the directory itself - going away while the
        stream runs: ``glob`` lists the directory first and
        ``getctime`` is called on the result afterwards, so a file that
        disappears in between raises ``OSError`` rather than simply
        dropping out of the list.

        """
        if not path:
            return None
        data_files = glob.glob(os.path.join(path, "*.dat*"))
        try:
            return max(data_files, key=os.path.getctime)
        except (ValueError, OSError):
            return None

    def no_data(self, message):
        """There is nothing to read in the folder.

        Silent while a stream is running, because that is the ordinary
        way a run begins: the stream is started first and the
        acquisition second, so the folder is empty for the first few
        seconds by design. Interrupting that with a message box - and
        stopping the stream to show it, as every error here must - meant
        the stream could not be armed before the data it was waiting
        for existed.

        An explicit 'Refresh plot' is a different question, and gets a
        different answer: nothing there is exactly what the user asked
        about.

        """
        if self._announce_missing:
            self.report_error(message)
        else:
            self.on_waiting_for_data()

    def on_waiting_for_data(self):
        """Hook: say, quietly, that the folder is still empty."""

    def report_error(self, text, details=None):
        """Stop the stream, then say what went wrong.

        In that order on purpose: a modal box runs an event loop of its
        own, so a stream left running would ask for ``refresh`` again
        behind it and stack a new box on top of this one for as long as
        it stayed open.

        """
        self.stop_stream()
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setWindowTitle("Error")
        box.setText(text)
        if details is not None:
            box.setDetailedText(str(details))
        box.exec_()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def plotted_data(self):
        """The numbers behind the plot, for *File -> Export*.

        Returns ``None`` when there is nothing to export, or a dict:

        ``stem``
            A suggested file name, without an extension.
        ``columns``
            Ordered ``{heading: 1-D array}``; every column the same
            length.
        ``notes``
            Lines describing where the numbers came from, written into
            the file as ``#`` comments so that a plot found on a disk
            six months later can still say what it was.

        """
        return None
