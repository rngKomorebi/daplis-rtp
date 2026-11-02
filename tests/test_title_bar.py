"""The dark title bar: asked for once per window, and only on Windows.

Whether Windows really draws the bar dark cannot be seen from a test -
Qt's offscreen platform has no real window handle to ask about - so
what is held here is the plumbing: the filter goes on once, it marks
each window it darkens, and elsewhere than Windows nothing is asked.

"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5")

from PyQt5 import QtWidgets  # noqa: E402

from daplis_rtp.gui import title_bar  # noqa: E402


@pytest.fixture(scope="module")
def app():
    """One QApplication for the module, skipped where Qt cannot start."""
    existing = QtWidgets.QApplication.instance()
    if existing is None:
        try:
            existing = QtWidgets.QApplication([])
        except Exception as err:  # noqa: BLE001 - whatever Qt raises
            pytest.skip("no Qt platform available: {}".format(err))
    yield existing


def test_nothing_is_asked_outside_windows(app, monkeypatch):
    monkeypatch.setattr(title_bar.sys, "platform", "linux")
    assert title_bar.dark_title_bar(QtWidgets.QWidget()) is False


def test_the_filter_is_installed_once(app):
    first = title_bar.install_dark_title_bars(app)
    assert title_bar.install_dark_title_bars(app) is first


def test_each_window_is_darkened_when_first_shown(app, monkeypatch):
    calls = []
    monkeypatch.setattr(title_bar, "dark_title_bar", calls.append)
    title_bar.install_dark_title_bars(app)

    window = QtWidgets.QDialog()
    child = QtWidgets.QPushButton("not a window", window)
    window.show()
    app.processEvents()
    window.hide()
    window.show()
    app.processEvents()
    window.close()

    assert calls == [window]
    assert window.property("darkTitleBar") is True
    assert child.property("darkTitleBar") is None
