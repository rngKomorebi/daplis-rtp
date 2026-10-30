"""Measure the tabs, rather than looking at them.

Every layout problem this package has had was found by measuring and
none by looking: a status box added to one control column made every
tab open 70 px taller, three tabs carried a 500x425 placeholder widget
that nothing drew, and the "Full Sensor" combo boxes had drifted to
80 px Expanding against everyone else's 100 px Fixed. Each of those was
invisible on screen until two tabs were put side by side.

So the geometry is asserted here. The numbers themselves move with the
font and the platform; what these tests hold is that the five tabs
agree with each other, and that the window's minimum stays inside a
budget.

"""

import os

import pytest

# Before anything imports QtWidgets: on a build machine there is no
# display, and Qt's offscreen platform is what makes a window
# measurable without one.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5")

from PyQt5 import QtWidgets  # noqa: E402

from daplis_rtp.gui import layout  # noqa: E402
from daplis_rtp.gui.main_window import TABS  # noqa: E402
from daplis_rtp.gui.theme import theme_manager  # noqa: E402

# The size every tab is measured at. Comfortably above the minimum, so
# that what is being compared is where things sit rather than how they
# collapse.
MEASURE_SIZE = (1500, 900)


@pytest.fixture(scope="module")
def app():
    """One QApplication for the module; a second in a process is fatal.

    Skipped rather than failed where Qt cannot start at all. A build
    machine without the libraries the offscreen platform plugin needs
    can say nothing useful about this application's geometry, and a red
    build that means "no graphics here" teaches nobody anything.

    """
    existing = QtWidgets.QApplication.instance()
    if existing is None:
        try:
            existing = QtWidgets.QApplication([])
        except Exception as err:  # noqa: BLE001 - whatever Qt raises
            pytest.skip("no Qt platform available: {}".format(err))
    application = existing
    theme_manager().apply_to_app(application)
    yield application


@pytest.fixture(scope="module")
def tabs(app):
    """Every tab, built once and laid out at the same size."""
    built = {}
    for factory, title in TABS:
        tab = factory()
        tab.resize(*MEASURE_SIZE)
        # A widget that was never shown has no laid-out geometry, and
        # 'activate' is what fills it in without needing a screen.
        tab.layout().activate()
        built[title] = tab
    yield built
    for tab in built.values():
        tab.deleteLater()


def _one_value(tabs, measure):
    """{value: [tab names]} - one key means the tabs agree."""
    grouped = {}
    for title, tab in tabs.items():
        grouped.setdefault(measure(tab), []).append(title)
    return grouped


def test_the_plot_is_in_the_same_place_on_every_tab(tabs):
    """The rectangle the canvas occupies, identical across the five.

    This is the whole point of 'gui.layout.TabShell'. The
    Synchronization tab has no plot, but its log sits in the same
    rectangle, so moving between tabs moves nothing under the hands.

    """
    grouped = _one_value(
        tabs, lambda tab: tab.canvas_area.geometry().getRect()
    )
    assert len(grouped) == 1, "the plot moves between tabs: {}".format(
        {str(rect): names for rect, names in grouped.items()}
    )


def test_the_control_column_is_the_same_width_on_every_tab(tabs):
    grouped = _one_value(tabs, lambda tab: tab.controls.width())
    assert len(grouped) == 1, grouped
    assert list(grouped)[0] == layout.control_column_width()


def test_the_action_bar_is_the_same_size_and_place_on_every_tab(tabs):
    grouped = _one_value(
        tabs, lambda tab: tab.actions.geometry().getRect()
    )
    assert len(grouped) == 1, grouped


def test_the_first_button_is_under_the_same_pixels_on_every_tab(tabs):
    """A tab with one button leaves the other two slots empty.

    Letting a lone button stretch across the bar would put "Refresh
    plot" somewhere different on every tab, which is exactly what the
    fixed slot count is for.

    """
    def first_button(tab):
        buttons = tab.actions.findChildren(QtWidgets.QPushButton)
        return buttons[0].geometry().getRect()

    grouped = _one_value(tabs, first_button)
    assert len(grouped) == 1, grouped


def test_every_control_box_is_the_standard_width(tabs):
    """No tab quietly sizes its own combo and spin boxes.

    The drift this catches is the real one: the hand-built tabs had
    theirs at 80 px Expanding while the generated ones were at 100 px
    Fixed, and nobody noticed for a year.

    """
    expected = layout.control_box_width()
    offenders = []
    for title, tab in tabs.items():
        for widget in tab.controls.findChildren(QtWidgets.QComboBox):
            if widget.width() != expected:
                offenders.append((title, widget.objectName(), widget.width()))
    assert not offenders, offenders


def test_the_window_minimum_stays_inside_its_budget(app):
    """The floor the window can be dragged down to, over all five tabs.

    Height comes from one tab and width may come from another, which is
    why this is measured on the window rather than per tab.

    """
    from daplis_rtp.gui.main_window import MainWindow

    window = MainWindow()
    window.layout = window.centralWidget().layout
    minimum = window.minimumSizeHint()
    budget_w, budget_h = layout.WINDOW_MIN_BUDGET
    try:
        assert minimum.width() <= budget_w, (
            "the window cannot be made narrower than {} px "
            "(budget {})".format(minimum.width(), budget_w)
        )
        assert minimum.height() <= budget_h, (
            "the window cannot be made shorter than {} px "
            "(budget {})".format(minimum.height(), budget_h)
        )
    finally:
        window.close()
        window.deleteLater()


def test_a_larger_interface_font_moves_the_rows_rather_than_clipping(app):
    """Turning the font up has to take the geometry with it.

    The sizes in 'gui.layout' are quoted at 10 pt and scaled; a row that
    stayed 26 px tall at 16 pt would cut the text in half.

    """
    manager = theme_manager()
    original = manager.ui_font_size
    try:
        manager.set_ui_font_size(10)
        manager.apply_to_app(app)
        small_row, small_column = layout.row_height(), (
            layout.control_column_width()
        )

        manager.set_ui_font_size(16)
        manager.apply_to_app(app)
        large_row, large_column = layout.row_height(), (
            layout.control_column_width()
        )

        assert large_row > small_row
        assert large_column > small_column
    finally:
        manager.set_ui_font_size(original)
        manager.apply_to_app(app)
