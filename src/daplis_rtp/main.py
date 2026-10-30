"""Application starter.

Run this file in the terminal to start the application.

Run it in an IPython kernel - the VS Code interactive window, a Spyder
console, a notebook - as often as you like: the session's QApplication
is reused rather than replaced, so a second run neither kills the kernel
nor opens a window that never paints. The call returns when the window
is closed.

"""

import sys

from PyQt5.QtWidgets import QApplication

from daplis_rtp.gui.app_icon import app_icon, claim_taskbar_identity
from daplis_rtp.gui.main_window import MainWindow
from daplis_rtp.gui.theme import theme_manager

# The QApplication and the window live here, not in 'main's locals, and
# the reason is the crash you get otherwise. In an interpreter that
# outlives the call, locals are dropped when 'main' returns, which
# destroys the QApplication and the window in an order Qt does not
# survive. The next run then dies inside Qt with an access violation:
# no traceback, no Python error, just "the kernel died". Module globals
# keep both alive until something replaces them.
_APP = None
_WINDOW = None


def _qt_loop_already_running():
    """True only when something else is already spinning a Qt loop.

    That is the one case where 'main' must not call 'exec', since doing
    so would block the caller's loop. An IPython kernel spins one only
    when Qt integration has been switched on with '%gui qt', which is
    not the default; without it nothing processes Qt events, so a
    window opened without 'exec' never paints.
    """
    try:
        from IPython import get_ipython
    except ImportError:
        # Not an IPython session at all
        return False
    ip = get_ipython()
    if ip is None:
        # IPython importable, but this is a plain interpreter
        return False
    # Set by '%gui qt' to 'qt' / 'qt5' / 'qt6'; empty or None when off
    return str(getattr(ip, "active_eventloop", "") or "").startswith("qt")


def main():
    """Open the window, and run the Qt event loop unless something is.

    Safe to call more than once in the same interpreter: the existing
    QApplication is reused - a second one in one process is fatal - and
    the previous window is closed properly rather than collected.
    """
    global _APP, _WINDOW

    # Before the QApplication, and so before any window exists: this is
    # what tells Windows which taskbar button the process owns, and it
    # is only read once, when that button is first created.
    claim_taskbar_identity()

    existing = QApplication.instance()
    _APP = existing if existing is not None else QApplication(sys.argv)
    # On the application rather than the window: every top-level window
    # inherits it, the pixel mask and the message boxes included
    _APP.setWindowIcon(app_icon())
    # Before the widgets it applies to, so that nothing is built in
    # the default palette and re-polished into the themed one. This
    # also sets the application font, which is what every row height
    # and column width in 'gui.layout' is measured from.
    theme_manager().apply_to_app(_APP)

    if _WINDOW is not None:
        # Through 'closeEvent', so that a run left over from a previous
        # call stops its timers and threads rather than being torn down
        # underneath them
        _WINDOW.close()

    _WINDOW = MainWindow()
    _WINDOW.show()

    if not _qt_loop_already_running():
        _APP.exec()

    return _WINDOW


if __name__ == "__main__":
    main()
