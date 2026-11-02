"""The user guide: every tab has a page, every link lands, F1 finds it.

The words themselves are not tested - a test cannot tell whether an
explanation is right - but what would break silently is: a tab added
without a page, a renamed section leaving links pointing nowhere, and
F1 opening the wrong page.

"""

import os
import re

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5")

from PyQt5 import QtCore, QtWidgets  # noqa: E402

from daplis_rtp.gui.help_content import (  # noqa: E402
    SECTIONS,
    TAB_SECTIONS,
    section,
)
from daplis_rtp.gui.main_window import TABS, MainWindow  # noqa: E402
from daplis_rtp.gui.user_guide import UserGuide, plain_text  # noqa: E402

LINK = re.compile(r'href="#([^"]+)"')


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


# ----------------------------------------------------------------------
# The content
# ----------------------------------------------------------------------


def test_section_keys_are_unique():
    keys = [item.key for item in SECTIONS]
    assert len(keys) == len(set(keys))


def test_every_parent_is_a_section_listed_before_its_children():
    seen = set()
    for item in SECTIONS:
        if item.parent is not None:
            assert item.parent in seen, item.key
        seen.add(item.key)


def test_every_tab_has_a_page():
    for _factory, title in TABS:
        assert title in TAB_SECTIONS, title
        assert section(TAB_SECTIONS[title]) is not None, title


def test_every_link_lands_on_a_section():
    for item in SECTIONS:
        for target in LINK.findall(item.html):
            assert section(target) is not None, (item.key, target)


def test_every_page_starts_with_its_title():
    for item in SECTIONS:
        assert plain_text(item.html).startswith(item.title), item.key


# ----------------------------------------------------------------------
# The window
# ----------------------------------------------------------------------


def test_contents_list_every_section(app):
    guide = UserGuide()
    # Walked item by item rather than with a QTreeWidgetItemIterator:
    # the iterator is a C++ object watching the tree, and if Python
    # frees the guide before it when the test returns, its destructor
    # reads the deleted tree and crashes the run (seen on Linux, on
    # Python 3.9-3.11, depending on what ran before).
    titles = []

    def walk(item):
        titles.append(item.text(0))
        for index in range(item.childCount()):
            walk(item.child(index))

    tree = guide.treeWidget_contents
    for index in range(tree.topLevelItemCount()):
        walk(tree.topLevelItem(index))
    assert titles == [item.title for item in SECTIONS]


def test_showing_a_section_renders_it(app):
    guide = UserGuide()
    guide.show_section("tdc")
    assert guide.current_section() == "tdc"
    assert "TDC memory" in guide.textBrowser_page.toPlainText()


def test_a_link_to_another_section_jumps_to_it(app):
    guide = UserGuide()
    guide.show_section("online")
    guide._link_clicked(QtCore.QUrl("#mask"))
    assert guide.current_section() == "mask"


def test_search_narrows_the_contents_and_marks_the_words(app):
    guide = UserGuide()
    guide.lineEdit_search.setText("RUNHISTOGRAMS saturated")
    assert guide.matching_sections() == []

    guide.lineEdit_search.setText("ctrl+click")
    found = guide.matching_sections()
    assert "mask" in found and "keys" in found
    assert guide.current_section() in found
    assert guide.textBrowser_page.extraSelections()
    # A page that does not mention it is hidden; its heading is not,
    # while a page under it still matches
    assert guide._items["sync"].isHidden()
    assert not guide._items["panels"].isHidden()


def test_asking_for_a_hidden_page_clears_the_search(app):
    guide = UserGuide()
    guide.lineEdit_search.setText("interferometer")
    assert guide._items["trouble"].isHidden()
    guide.show_section("trouble")
    assert guide.lineEdit_search.text() == ""
    assert guide.current_section() == "trouble"


def test_f1_opens_the_page_of_the_tab_in_front(app):
    window = MainWindow()
    try:
        for index, (_factory, title) in enumerate(TABS):
            window.tabWidget.setCurrentIndex(index)
            window.open_user_guide()
            assert window._guide.current_section() == TAB_SECTIONS[title]
    finally:
        window.close()
