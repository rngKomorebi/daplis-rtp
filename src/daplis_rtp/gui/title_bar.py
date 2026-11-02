"""A dark title bar on every window, whatever the theme.

The title bar, the frame and the three buttons in its corner are drawn
by Windows, not by Qt, so the stylesheet that themes everything inside
the window never reaches them: left alone, the bar stays the light
system default over a dark application. Windows 10 (20H1 and later) and
Windows 11 let a program ask for the dark version of the bar, one
window at a time, through the desktop window manager.

The bar is dark on every theme, light ones included. It is part of the
window rather than of the content, and one bar that never changes is
calmer than one that flips with the colours below it.

Every top-level window is caught as it is shown, through one event
filter on the application: the main window, Preferences, the user
guide, the pixel mask, and the message boxes Qt builds on the fly. A
window added later needs nothing doing. The show event arrives before
Windows first draws the frame, so the bar never flashes light.

The native file dialogs ("Browse") are drawn by Windows itself and
follow the system setting instead. Elsewhere than Windows this does
nothing, and the desktop decides.

"""

import sys

from PyQt5 import QtCore

# Window attribute that asks for the dark title bar. Windows 10 builds
# before 20H1 (19041) knew it as 19; asked for by the new number, they
# answer with an error and the old one is tried.
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19

# Kept here so that a second run of 'main' in the same interpreter, which
# reuses the QApplication, does not stack a second filter on it.
_FILTER = None


def dark_title_bar(window):
    """Ask Windows for a dark title bar on one top-level window.

    Returns True when Windows accepted it, and False when it did not or
    could not be asked: another platform, a Windows too old to know the
    attribute, or a window without a real native handle (Qt's offscreen
    platform, in the tests).

    """
    if sys.platform != "win32":
        return False
    import ctypes

    try:
        dwmapi = ctypes.windll.dwmapi
    except OSError:
        return False
    # 'winId' creates the native window if it does not exist yet, which
    # is fine here: it is about to be shown anyway.
    hwnd = ctypes.c_void_p(int(window.winId()))
    value = ctypes.c_int(1)
    for attribute in (
        DWMWA_USE_IMMERSIVE_DARK_MODE,
        DWMWA_USE_IMMERSIVE_DARK_MODE_OLD,
    ):
        result = dwmapi.DwmSetWindowAttribute(
            hwnd,
            attribute,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
        if result == 0:
            return True
    return False


class _DarkTitleBars(QtCore.QObject):
    """Darken each window's title bar the first time it is shown."""

    def eventFilter(self, obj, event):
        if (
            event.type() == QtCore.QEvent.Show
            and obj.isWidgetType()
            and obj.isWindow()
            # A window is shown many times - the mask and Preferences
            # are hidden and shown again - but its bar only needs
            # darkening once.
            and not obj.property("darkTitleBar")
        ):
            obj.setProperty("darkTitleBar", True)
            dark_title_bar(obj)
        return False


def install_dark_title_bars(app):
    """Give every window of ``app`` a dark title bar from now on.

    Safe to call more than once: the filter is installed the first time
    and left alone after that, as long as the application is the same.

    """
    global _FILTER
    if _FILTER is not None and _FILTER.parent() is app:
        return _FILTER
    _FILTER = _DarkTitleBars(app)
    app.installEventFilter(_FILTER)
    return _FILTER
