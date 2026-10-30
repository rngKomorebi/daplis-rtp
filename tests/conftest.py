"""Keep the test run out of the developer's own settings.

Several tests change the theme, and the tabs save every control they are
bound to the moment it changes. Against the real ``QSettings`` store
that means running the suite quietly rewrites the preferences of
whoever ran it - a different theme, someone else's data folder in the
browse box - which is both rude and a source of tests that pass only on
the machine that last ran them.

``QSettings`` is therefore pointed at a throwaway directory for the
session, before anything asks it for a value.

"""

import os

import pytest

# Before PyQt5 is imported anywhere: a build machine has no display, and
# Qt's offscreen platform is what lets a window be built without one.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5")

from PyQt5 import QtCore  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def isolated_settings(tmp_path_factory):
    """Send every ``QSettings`` written during the run to a temp folder.

    The INI format is forced because it is the only one ``setPath``
    redirects; on Windows the native format is the registry, which has
    no path to redirect.

    """
    folder = str(tmp_path_factory.mktemp("settings"))
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
    QtCore.QSettings.setPath(
        QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, folder
    )
    return folder
