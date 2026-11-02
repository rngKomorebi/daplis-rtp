"""The user guide window: contents on the left, the page on the right.

Not modal, like Preferences and the pixel mask: the guide is read with
the tab it describes still in front of you, and a stream keeps running
behind it. F1 opens it at the page of whatever tab is current, which is
nearly always the question being asked.

The words live in :mod:`daplis_rtp.gui.help_content`; this module only
shows them. The search box narrows the contents to the pages that
mention a word and marks every place it occurs on the page shown -
there is no index to keep up to date, so it cannot drift from the text.

"""

import html
import re

from PyQt5 import QtCore, QtGui, QtWidgets

from daplis_rtp.gui.help_content import SECTIONS, section
from daplis_rtp.gui.layout import MARGIN, SPACING, scale
from daplis_rtp.gui.theme import theme_manager

# Width of the contents list, at the default interface font.
CONTENTS_WIDTH = 220

_TAG = re.compile(r"<[^>]+>")


def plain_text(markup):
    """The words of a page, without its tags, for searching."""
    return " ".join(html.unescape(_TAG.sub(" ", markup)).split())


class UserGuide(QtWidgets.QDialog):
    """The guide, one section at a time, with contents and search."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User guide - DAPLIS - Real Time Plotting")
        # A window of its own rather than a sheet over the tab, so it
        # can be put beside the plot it explains.
        self.setWindowFlags(QtCore.Qt.Window)
        self.setModal(False)

        self._items = {}
        self._words = {
            item.key: plain_text(item.html).lower() for item in SECTIONS
        }
        self._current = None

        self._build_ui()
        self._fill_contents()
        self._apply_style()
        theme_manager().changed.connect(self._apply_style)

        factor = scale()
        self.resize(int(900 * factor), int(640 * factor))
        self.show_section(SECTIONS[0].key)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        outer.setSpacing(SPACING)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)

        left = QtWidgets.QWidget(splitter)
        left_box = QtWidgets.QVBoxLayout(left)
        left_box.setContentsMargins(0, 0, 0, 0)
        left_box.setSpacing(SPACING)
        self.lineEdit_search = QtWidgets.QLineEdit(left)
        self.lineEdit_search.setPlaceholderText("Search the guide…")
        self.lineEdit_search.setClearButtonEnabled(True)
        self.lineEdit_search.setToolTip(
            "Show only the pages that mention these words, and mark them "
            "on the page."
        )
        self.lineEdit_search.textChanged.connect(self._search)
        left_box.addWidget(self.lineEdit_search)

        self.treeWidget_contents = QtWidgets.QTreeWidget(left)
        self.treeWidget_contents.setHeaderHidden(True)
        self.treeWidget_contents.setRootIsDecorated(True)
        self.treeWidget_contents.currentItemChanged.connect(
            self._item_chosen
        )
        left_box.addWidget(self.treeWidget_contents, 1)

        self.label_matches = QtWidgets.QLabel("", left)
        self.label_matches.setObjectName("tabHint")
        left_box.addWidget(self.label_matches)

        self.textBrowser_page = QtWidgets.QTextBrowser(splitter)
        # Links are handled here: a link to another section is a jump to
        # that page, which QTextBrowser's own handling would treat as an
        # anchor on the page already shown.
        self.textBrowser_page.setOpenLinks(False)
        self.textBrowser_page.anchorClicked.connect(self._link_clicked)

        splitter.addWidget(left)
        splitter.addWidget(self.textBrowser_page)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([int(CONTENTS_WIDTH * scale()), 1])
        outer.addWidget(splitter, 1)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        close = QtWidgets.QPushButton("Close", self)
        close.clicked.connect(self.hide)
        buttons.addWidget(close)
        outer.addLayout(buttons)

    def _fill_contents(self):
        for item in SECTIONS:
            parent = self._items.get(item.parent)
            node = QtWidgets.QTreeWidgetItem(
                parent if parent is not None else self.treeWidget_contents,
                [item.title],
            )
            node.setData(0, QtCore.Qt.UserRole, item.key)
            self._items[item.key] = node
        self.treeWidget_contents.expandAll()

    def _apply_style(self):
        """Table rules that suit the theme.

        Qt's rich text draws table borders in a fixed grey, too strong
        on some themes. The rule is taken from the palette, and nothing
        is filled in: the dark themes paint the page with a stylesheet
        and leave the palette light, so a palette background - tried
        for the header row - came out white on a dark page. The header
        is told apart by its bold type instead. Rebuilt on every theme
        change.

        """
        rule = self.textBrowser_page.palette().color(QtGui.QPalette.Mid)
        self.textBrowser_page.document().setDefaultStyleSheet(
            "table {{ border-collapse: collapse; margin-top: 4px;"
            " margin-bottom: 8px; }}"
            "th, td {{ border: 1px solid {rule}; }}"
            "h2 {{ margin-top: 0; }}"
            "code {{ font-family: monospace; }}".format(rule=rule.name())
        )
        if self._current is not None:
            self._render(self._current)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def current_section(self):
        """The key of the page on show."""
        return self._current

    def show_section(self, key):
        """Show one page, and select it in the contents."""
        if section(key) is None:
            return
        node = self._items[key]
        if node.isHidden():
            # A page asked for by name - by F1 or by a link - is shown
            # even when the search has hidden it, so the search goes.
            self.lineEdit_search.clear()
        if self.treeWidget_contents.currentItem() is not node:
            # Selecting it calls '_item_chosen', which renders it.
            self.treeWidget_contents.setCurrentItem(node)
        else:
            self._render(key)

    def open_at(self, key):
        """Show a page and bring the window forward."""
        self.show_section(key)
        self.show()
        self.raise_()
        self.activateWindow()

    def _item_chosen(self, node, _previous=None):
        if node is None:
            return
        self._render(node.data(0, QtCore.Qt.UserRole))

    def _render(self, key):
        self._current = key
        self.textBrowser_page.setHtml(section(key).html)
        self.textBrowser_page.verticalScrollBar().setValue(0)
        self._mark_matches()

    def _link_clicked(self, url):
        target = url.toString()
        if target.startswith("#"):
            self.show_section(target[1:])
        else:
            QtGui.QDesktopServices.openUrl(url)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _terms(self):
        return self.lineEdit_search.text().lower().split()

    def matching_sections(self, terms=None):
        """Keys of the pages holding every one of the search words."""
        terms = self._terms() if terms is None else terms
        return [
            item.key
            for item in SECTIONS
            if all(
                t in self._words[item.key] or t in item.title.lower()
                for t in terms
            )
        ]

    def _search(self):
        terms = self._terms()
        if not terms:
            for node in self._items.values():
                node.setHidden(False)
            self.label_matches.setText("")
            self._mark_matches()
            return

        found = set(self.matching_sections(terms))
        for item in SECTIONS:
            node = self._items[item.key]
            # A heading stays visible while any page under it matches,
            # or there would be no way to reach that page.
            under = [s.key for s in SECTIONS if s.parent == item.key]
            node.setHidden(
                item.key not in found and not any(k in found for k in under)
            )

        count = len(found)
        self.label_matches.setText(
            "no page mentions that" if not count
            else "{} page{}".format(count, "" if count == 1 else "s")
        )
        if self._current in found:
            self._mark_matches()
        elif found:
            first = next(item.key for item in SECTIONS if item.key in found)
            self.treeWidget_contents.setCurrentItem(self._items[first])
        else:
            self._mark_matches()

    def _mark_matches(self):
        """Highlight every occurrence of the search words on the page."""
        browser = self.textBrowser_page
        marks = []
        terms = self._terms()
        if terms:
            fmt = QtGui.QTextCharFormat()
            fmt.setBackground(self.palette().color(QtGui.QPalette.Highlight))
            fmt.setForeground(
                self.palette().color(QtGui.QPalette.HighlightedText)
            )
            document = browser.document()
            for term in terms:
                cursor = QtGui.QTextCursor(document)
                while True:
                    cursor = document.find(term, cursor)
                    if cursor.isNull():
                        break
                    mark = QtWidgets.QTextEdit.ExtraSelection()
                    mark.cursor = cursor
                    mark.format = fmt
                    marks.append(mark)
        browser.setExtraSelections(marks)
        if marks:
            # Scroll to the first match without selecting it: the mark
            # is the highlight, and a selection on top would hide it.
            cursor = QtGui.QTextCursor(marks[0].cursor)
            cursor.clearSelection()
            browser.setTextCursor(cursor)
            browser.ensureCursorVisible()
