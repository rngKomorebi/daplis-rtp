"""The text of the user guide, one section per page.

Kept apart from the window that shows it, and free of Qt, so that the
words can be edited - and tested - without touching a widget. Each
section is a small piece of HTML in the subset Qt's rich text renders:
headings, paragraphs, lists, simple tables, bold and links. No colours
are set here, so the guide follows the theme like the rest of the
window.

A link to another section is written ``<a href="#key">``; the window
turns it into a jump to that section rather than a scroll within the
page.

The control names below are quoted exactly as they appear on screen.
When a label changes in a tab, change it here too - the tests check
that every tab has a section, not that the words still match.

"""

from collections import namedtuple

Section = namedtuple("Section", "key title parent html")


def _table(rows, head=("Control", "What it does")):
    """A two-column table of control names and what they do."""
    cells = "".join(
        "<tr><td><b>{}</b></td><td>{}</td></tr>".format(name, text)
        for name, text in rows
    )
    return (
        '<table cellspacing="0" cellpadding="4" border="1" width="100%">'
        "<tr><th align=\"left\">{}</th><th align=\"left\">{}</th></tr>"
        "{}</table>".format(head[0], head[1], cells)
    )


# ----------------------------------------------------------------------
# Rows shared by several tabs, so that they are described once
# ----------------------------------------------------------------------

_BOARD_ROWS = [
    (
        "Daughterboard",
        "The LinoSPAD2 daughterboard the data came from (B7d, NL11, A5, "
        "D2b). The list is editable: type the name of a board that is "
        "not on it. Used, with the motherboard, to look up the preset "
        "mask.",
    ),
    (
        "Motherboard",
        "The motherboard the data came from (#28, #33, #21, #36, #37, "
        "#4, #29), also editable. Used to look up the preset mask.",
    ),
    (
        "Firmware version",
        "<b>2212b</b> or <b>2212s</b>. It decides how the 256 pixels are "
        "shared among the 64 TDCs, so a wrong choice gives a wrong "
        "plot or an unreadable file.",
    ),
    (
        "Timestamps",
        "Timestamps per pixel per acquisition cycle, 1 to 1536 "
        "(300 when first opened). It must match the setting the data "
        "were taken with. The <a href=\"#tdc\">TDC memory</a> box "
        "suggests a value.",
    ),
]

_ADDRESS_ROW = (
    "Correct pixel addressing",
    "Undo the address scrambling of the sensor's second half, for data "
    "that need it.",
)

_ABSOLUTE_ROW = (
    "Absolute timestamps",
    "Tick when the files were taken with absolute timestamps: two extra "
    "32-bit words at the start of each acquisition cycle. Reading such "
    "a file without the tick (or the other way round) fails.",
)

_LINEAR_ROW = (
    "Linear scale",
    "Clear it for a logarithmic y-axis - the one to use when a few "
    "bright pixels flatten everything else.",
)


SECTIONS = [
    # ------------------------------------------------------------------
    Section(
        "start",
        "Getting started",
        None,
        """
<h2>Getting started</h2>
<p>DAPLIS - Real Time Plotting shows what a LinoSPAD2 detector is
recording while it records: the photon rate on every pixel, the arrival
times on one pixel, two pixels against time, and both halves of the
sensor at once. It reads the data files the board's own software
writes; it does not control the camera, except on the
<a href="#sync">Synchronization</a> tab.</p>

<h3>The five tabs</h3>
<table cellspacing="0" cellpadding="4" border="1" width="100%">
<tr><th align="left">Tab</th><th align="left">Use it to</th></tr>
<tr><td><a href="#online"><b>Online plot</b></a></td>
<td>align the optics: photon rate per pixel of one board, redrawn as
files arrive.</td></tr>
<tr><td><a href="#histogram"><b>Single Pixel Histogram</b></a></td>
<td>check that one pixel fires steadily through the acquisition
cycle.</td></tr>
<tr><td><a href="#mzi"><b>MZI</b></a></td>
<td>follow the two arms of an interferometer: two pixels' rates
against time.</td></tr>
<tr><td><a href="#full"><b>Full Sensor</b></a></td>
<td>see all 512 pixels from two boards side by side.</td></tr>
<tr><td><a href="#sync"><b>Synchronization</b></a></td>
<td>start a two-board acquisition on both boards at the same
moment.</td></tr>
</table>

<h3>A first plot in five steps</h3>
<ol>
<li>Open the <b>Online plot</b> tab.</li>
<li>Under <b>Data folder</b>, click <b>Browse</b> (or paste a path) and
choose the folder the board writes its <code>.dat</code> files to.</li>
<li>In the column on the right, set <b>Daughterboard</b>,
<b>Motherboard</b>, <b>Firmware version</b> and <b>Timestamps</b> to
match the acquisition.</li>
<li>Click <b>Start stream</b>. The plot shows the newest file and
redraws each time a new one lands. <b>Refresh plot</b> takes a single
look instead.</li>
<li>Hold <b>Ctrl</b> and click a hot pixel on the plot to mask it, then
narrow the <b>x limits</b> under the plot onto the signal.</li>
</ol>
<p>To keep the numbers behind a plot, use
<a href="#export">File &rarr; Export plotted data</a>. Every setting
you make is <a href="#remembered">remembered</a> for the next time.</p>
<p>Hovering over any control shows a short explanation of it. Press
<b>F1</b> on any tab to open this guide at that tab's page.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "window",
        "The window at a glance",
        None,
        """
<h2>The window at a glance</h2>
<p>Every tab is laid out the same way, so a control is in the same
place whichever tab is open:</p>
<table cellspacing="0" cellpadding="4" border="1" width="100%">
<tr><th align="left">Where</th><th align="left">What is there</th></tr>
<tr><td><b>Top strip</b></td><td>A one-line reminder of what the tab
shows.</td></tr>
<tr><td><b>Two rows under it</b></td><td>The data folder (two on
<a href="#full">Full Sensor</a>) and a row of readings about the last
file plotted.</td></tr>
<tr><td><b>Middle</b></td><td>The plot, with its toolbar beneath it
(on Synchronization, a log of what the boards say).</td></tr>
<tr><td><b>Under the plot</b></td><td>The axis limits (on
Synchronization, the clock lamps).</td></tr>
<tr><td><b>Right-hand column</b></td><td>The settings and status boxes.
It scrolls when it is taller than the window.</td></tr>
<tr><td><b>Bottom of the column</b></td><td>The action buttons. The one
the tab is mainly for is outlined.</td></tr>
<tr><td><b>Status bar</b></td><td>Messages such as "Exported to ...", and
the current theme on the right.</td></tr>
</table>

<h3>The plot toolbar</h3>
<p>The toolbar under each plot is matplotlib's standard one:</p>
<ul>
<li><b>Home</b>, <b>Back</b>, <b>Forward</b> - return to the full view,
or step through earlier zooms.</li>
<li><b>Pan</b> - drag the plot; right-drag to stretch an axis.</li>
<li><b>Zoom</b> - draw a rectangle to zoom into it.</li>
<li><b>Subplots</b> and <b>Customize</b> - adjust margins, axis ranges
and line styles by hand.</li>
<li><b>Save</b> - save the plot as a picture (PNG, PDF, SVG). To save
the numbers instead, use <a href="#export">File &rarr; Export</a>.</li>
</ul>
<p>While the mouse is over the plot, the right end of the toolbar shows
the coordinates under it - the quickest way to read off which pixel a
peak is on.</p>
<p>A new file redraws the plot with the limits set under it, which
undoes a toolbar zoom. To keep a zoom while streaming, set the axis
limits instead.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "data",
        "Data files and common settings",
        None,
        """
<h2>Data files and common settings</h2>
<h3>Which file is plotted</h3>
<p>The plotting tabs read the <b>newest</b> data file in the chosen
folder: the one with the latest creation time whose name contains
<code>.dat</code> (so <code>.dat0</code>, <code>.dat1</code> and so on
count too). Older files are not read.</p>

<h3>Streaming</h3>
<p><b>Start stream</b> watches the folder and redraws whenever a newer
file appears; the button then reads <b>Stop stream</b>. A burst of
changes is read once, a moment after it settles. On a network drive,
where change notices can go missing, the folder is also checked every
2 seconds.</p>
<p>It is fine to start the stream before the acquisition: an empty
folder is waited on quietly ("waiting..." in the readings row).
<b>Refresh plot</b> on an empty folder, on the other hand, says so in a
message.</p>
<p>When a file cannot be read, the stream stops and a message explains
why; <b>Show Details...</b> in that message gives the exact error.</p>

<h3>Settings found on most tabs</h3>
"""
        + _table(_BOARD_ROWS + [_ADDRESS_ROW, _ABSOLUTE_ROW, _LINEAR_ROW])
        + """
<p>Pixels are numbered 0 to 255 on each board (0 to 511 across both
halves on <a href="#full">Full Sensor</a>). Number fields under the
plots accept decimals and scientific notation, such as
<code>4e9</code> or <code>10e3</code>.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "tabs",
        "The tabs",
        None,
        """
<h2>The tabs</h2>
<ul>
<li><a href="#online">Online plot</a> - photon rate per pixel of one
board, live.</li>
<li><a href="#histogram">Single Pixel Histogram</a> - arrival times of
one pixel within the cycle.</li>
<li><a href="#mzi">MZI</a> - two pixels' rates against time.</li>
<li><a href="#full">Full Sensor</a> - both sensor halves from two
boards.</li>
<li><a href="#sync">Synchronization</a> - start a two-board
acquisition.</li>
</ul>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "online",
        "Online plot",
        "tabs",
        """
<h2>Online plot</h2>
<p>The photon rate on every pixel of one board, from the newest file in
the folder. This is the tab for aligning a setup: a change to the
optics shows up on the plot within a file or two.</p>

<h3>Above the plot</h3>
"""
        + _table(
            [
                (
                    "Data folder",
                    "The folder the board writes its data files to. "
                    "<b>Browse</b> picks one; a pasted path works as "
                    "well.",
                ),
                (
                    "Brightest pixel, Second",
                    "The two pixels with the highest rate in the last "
                    "file, after masking.",
                ),
                ("Masked", "How many pixels are masked."),
                ("File", "The file the plot was drawn from."),
                (
                    "Gaussian fit",
                    "Fits every spectral line above a threshold - see "
                    "<a href=\"#fit\">Gaussian fit</a>.",
                ),
            ],
            head=("Item", "What it shows"),
        )
        + """
<h3>Under the plot</h3>
"""
        + _table(
            [
                (
                    "x limits (pixel)",
                    "The range of pixels shown, 0 to 255. It also sets "
                    "which pixels <a href=\"#peak\">Peak in view</a>, "
                    "the <a href=\"#fit\">Gaussian fit</a> and the "
                    "<a href=\"#tdc\">TDC memory</a> check look at, so "
                    "narrowing it onto the signal keeps a hot pixel "
                    "elsewhere out of the numbers.",
                ),
            ]
        )
        + """
<h3>The column on the right</h3>
"""
        + _table(
            _BOARD_ROWS
            + [
                _ADDRESS_ROW,
                _ABSOLUTE_ROW,
                (
                    "Pixel mask",
                    "<b>Preset mask</b>, <b>Edit mask...</b> and "
                    "<b>Reset</b> - see "
                    "<a href=\"#mask\">Pixel mask</a>.",
                ),
                _LINEAR_ROW,
                (
                    "Group of 64",
                    "Vertical lines at pixels 64, 128 and 192, to help "
                    "line the peaks up within one group of 64.",
                ),
                (
                    "Peak in view",
                    "Position, width and brightness of the peak in "
                    "view - see <a href=\"#peak\">Peak in view</a>.",
                ),
                (
                    "TDC memory",
                    "Warns when the readout is close to dropping data - "
                    "see <a href=\"#tdc\">TDC memory</a>.",
                ),
            ]
        )
        + """
<h3>Buttons</h3>
"""
        + _table(
            [
                ("Refresh plot", "Read the newest file now and redraw."),
                (
                    "Start stream / Stop stream",
                    "Follow the folder, redrawing whenever a newer file "
                    "appears.",
                ),
            ],
            head=("Button", "What it does"),
        )
        + """
<h3>Tips</h3>
<ul>
<li><b>Ctrl+click</b> a point on the plot to mask that pixel, and
again to unmask it. The plot changes at once, without waiting for the
next file.</li>
<li>Switch off the boxes you do not need (untick <b>Peak in view</b>,
<b>TDC memory</b>) to make each refresh a little faster.</li>
<li>Exported columns: <code>pixel</code>, <code>rate_Hz</code> and
<code>masked</code> (1 where the pixel was masked and its rate set to
zero). The fits, if any, are listed in the file's notes.</li>
</ul>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "histogram",
        "Single Pixel Histogram",
        "tabs",
        """
<h2>Single Pixel Histogram</h2>
<p>When, within the acquisition cycle, one pixel's photons arrive. A
healthy pixel under steady light fires at a steady rate through the
whole cycle, so its histogram has a <b>flat top</b>. A top that slopes
down or stops early means the readout is filling up (see
<a href="#tdc">TDC memory</a>) or that the light is not steady.</p>
<p>This tab has no stream: a histogram is something to look at rather
than watch. Click <b>Refresh plot</b> each time you want the newest
file read again.</p>

<h3>Above the plot</h3>
"""
        + _table(
            [
                ("Data folder", "The folder the board writes to."),
                (
                    "Timestamps",
                    "How many timestamps this pixel contributed. None "
                    "means the pixel is masked off in the hardware, "
                    "dead, or in the dark.",
                ),
                ("File", "The file the histogram was built from."),
            ],
            head=("Item", "What it shows"),
        )
        + """
<h3>Under the plot</h3>
"""
        + _table(
            [
                (
                    "Cycle length (ps)",
                    "Length of one acquisition cycle, in picoseconds - "
                    "the width of the histogram. The default "
                    "<code>4e9</code> is 4 ms. The cycle is always cut "
                    "into 250 bins. Applied on the next "
                    "<b>Refresh plot</b>.",
                ),
            ]
        )
        + """
<h3>The column on the right</h3>
"""
        + _table(
            _BOARD_ROWS
            + [
                (
                    "Pixel",
                    "The pixel to build the histogram for, 0 to 255.",
                ),
                _LINEAR_ROW,
            ]
        )
        + """
<p>Exported columns: <code>time_ps</code> (bin centre),
<code>bin_low_ps</code>, <code>bin_high_ps</code> and
<code>counts</code>.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "mzi",
        "MZI",
        "tabs",
        """
<h2>MZI</h2>
<p>The photon rate on two pixels against time, for the two arms of a
Mach-Zehnder interferometer. Each new data file adds one point to each
trace, so the trace grows at whatever rate the acquisition writes.
Time is counted from the first file read after the stream was
started.</p>

<h3>Above the plot</h3>
"""
        + _table(
            [
                ("Data folder", "The folder the board writes to."),
                ("Pixel 1, Pixel 2", "The latest rate on each pixel."),
                ("Elapsed", "Seconds since the first file of this run."),
                ("Points", "How many points each trace has."),
            ],
            head=("Item", "What it shows"),
        )
        + """
<h3>Under the plot</h3>
"""
        + _table(
            [
                (
                    "x limits (s), y limits (Hz)",
                    "The edges of the plot. Leave an edge empty to let "
                    "it follow the data. The right-hand y-axis always "
                    "has the same limits as the left one, so the two "
                    "arms can be compared directly.",
                ),
            ]
        )
        + """
<h3>The column on the right</h3>
"""
        + _table(
            _BOARD_ROWS
            + [
                _ADDRESS_ROW,
                (
                    "First pixel",
                    "The pixel the first arm falls on; drawn against "
                    "the left y-axis.",
                ),
                (
                    "Second pixel",
                    "The pixel the second arm falls on; drawn against "
                    "the right y-axis.",
                ),
                (
                    "Linear scale",
                    "Clear it for logarithmic y-axes on both sides.",
                ),
            ]
        )
        + """
<h3>Buttons</h3>
"""
        + _table(
            [
                ("Refresh plot", "Read the newest file and add a point now."),
                (
                    "Start stream / Stop stream",
                    "Follow the folder, adding a point whenever a newer "
                    "file appears.",
                ),
                (
                    "Reset",
                    "Throw the traces away and start the clock again. A "
                    "running stream keeps running.",
                ),
            ],
            head=("Button", "What it does"),
        )
        + """
<p>Stopping and starting the stream starts the clock again but keeps
the points already drawn, so the time axis restarts in the middle of
the trace. Click <b>Reset</b> for a clean trace.</p>
<p>Exported columns: <code>time_s</code> and one
<code>rate_pixel_N_Hz</code> column per pixel.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "full",
        "Full Sensor",
        "tabs",
        """
<h2>Full Sensor</h2>
<p>Both halves of the LinoSPAD2 sensor, 512 pixels, from two boards
each writing to a folder of its own. Board 1 gives pixels 0-255 and
board 2 pixels 256-511; a dashed line marks the seam between them.</p>
<p>Two things are fixed on this tab, as the sensor requires: board 2 is
always address-corrected (board 1 never is), and the data are always
read as having <b>absolute timestamps</b>, since those are what
synchronize the two halves. There are no switches for either.</p>

<h3>Above the plot</h3>
"""
        + _table(
            [
                (
                    "Board 1 folder",
                    "Where board 1 writes its files (pixels 0-255).",
                ),
                (
                    "Board 2 folder",
                    "Where board 2 writes its files (pixels 256-511).",
                ),
                (
                    "Gaussian fit",
                    "Fits every spectral line above a threshold, across "
                    "both halves - see <a href=\"#fit\">Gaussian "
                    "fit</a>.",
                ),
            ],
            head=("Item", "What it is"),
        )
        + """
<h3>Under the plot</h3>
"""
        + _table(
            [
                (
                    "x limits (pixel)",
                    "The range shown, 0 to 511 across both halves. It "
                    "also sets what <a href=\"#peak\">Peak in view</a>, "
                    "the <a href=\"#fit\">Gaussian fit</a> and "
                    "<a href=\"#tdc\">TDC memory</a> look at.",
                ),
            ]
        )
        + """
<h3>The column on the right</h3>
"""
        + _table(
            [
                (
                    "Daughterboard",
                    "Shared by both boards: one daughterboard carries "
                    "the whole sensor.",
                ),
                ("Motherboard 1", "Motherboard of board 1."),
                ("Motherboard 2", "Motherboard of board 2."),
                _BOARD_ROWS[2],
                (
                    "Timestamps",
                    "Timestamps per pixel per cycle, the same on both "
                    "boards.",
                ),
                (
                    "Pixel mask",
                    "As on the other tabs, but with one grid per board; "
                    "the line under the buttons counts the masked pixels "
                    "of each (<code>b1: 3, b2: 0</code>). See "
                    "<a href=\"#mask\">Pixel mask</a>.",
                ),
                _LINEAR_ROW,
                (
                    "Group of 64",
                    "Vertical lines at every group boundary on both "
                    "halves.",
                ),
                (
                    "Both boards in step",
                    "Checks in the background that both boards keep "
                    "writing files together - see "
                    "<a href=\"#insync\">Both boards in step</a>.",
                ),
                (
                    "Peak in view",
                    "See <a href=\"#peak\">Peak in view</a>.",
                ),
                (
                    "TDC memory",
                    "See <a href=\"#tdc\">TDC memory</a>. With two "
                    "boards, the worse of the two is shown.",
                ),
            ]
        )
        + """
<h3>Buttons</h3>
"""
        + _table(
            [
                (
                    "Refresh plot",
                    "Read the newest file of each board now.",
                ),
                (
                    "Start stream / Stop stream",
                    "Follow both folders, redrawing whenever either "
                    "gets a newer file. Also starts the "
                    "<b>Both boards in step</b> check.",
                ),
            ],
            head=("Button", "What it does"),
        )
        + """
<p><b>Ctrl+click</b> a pixel on either half to mask it; the half it
falls on decides which board's mask it goes to.</p>
<p>Exported columns: <code>pixel</code> (0-511), <code>board</code>
(1 or 2), <code>rate_Hz</code> and <code>masked</code>.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "sync",
        "Synchronization",
        "tabs",
        """
<h2>Synchronization</h2>
<p>This tab starts an acquisition on two boards at the same moment. It
talks to two running copies of <code>LinoSPAD_synchro.exe</code>, one
per board, over the network on this computer: it switches both to the
external clock, checks that both are locked to it, then starts both
acquisitions together.</p>
<p>It does not save any data itself. Each board's own window saves its
files, when its <b>AutoSave</b> is on, to the folder set there.</p>

<h3>Before you start</h3>
<ul>
<li>Feed a <b>25 MHz</b> square wave into <b>CLK_IN (J11)</b> of both
boards. 20 MHz does not work.</li>
<li>In each board's window, the <b>Ext MHz</b> box should read 25
(not about 50).</li>
</ul>

<h3>Step by step</h3>
<ol>
<li>Check the path to <b>LinoSPAD_synchro.exe</b> and the two settings
files, then click <b>Launch boards</b>. One window opens per board; a
board already launched from here is skipped.</li>
<li>In each board's window, click <b>Listen</b> (its port must match
the one under <b>Connection</b>) and set <b>25 MHz External</b>.</li>
<li>Click <b>Check clocks</b>. Both lamps under the log should turn to
<b>EXT LOCKED</b>. This only reads the boards; it changes nothing.</li>
<li>Under <b>Both boards in step</b>, set each board's folder to the
folder that board's window saves to, so that the run is watched (see
<a href="#insync">Both boards in step</a>).</li>
<li>Click <b>Acquire</b>. The tab puts both boards on the external
clock, checks both are locked, and starts both acquisitions at once.
If either board is not locked, nothing is acquired. The log says when
both have finished.</li>
</ol>

<h3>Above the log</h3>
"""
        + _table(
            [
                (
                    "LinoSPAD_synchro.exe",
                    "The board program. <b>Browse</b> finds it.",
                ),
                (
                    "Board 0 settings, Board 1 settings",
                    "The settings file each board's window is started "
                    "with, given relative to the folder of the "
                    "program.",
                ),
            ],
            head=("Item", "What it is"),
        )
        + """
<h3>Under the log</h3>
<p>One lamp per board: green with <b>EXT LOCKED</b> when the board is
locked to the external clock, red with <b>NOT on external clock</b>
when it is not, and amber with <b>unreachable</b> when the board's
window could not be contacted. The number in brackets is the raw status
word the board returned.</p>

<h3>The column on the right</h3>
"""
        + _table(
            [
                (
                    "Connection: Board 0 / Board 1 Port",
                    "The port each board's window listens on (5555 and "
                    "5556 to start with). Both run on this computer.",
                ),
                (
                    "Acq. timeout (s)",
                    "How long to wait for each board to finish its "
                    "acquisition, 1 to 3600 s (300 to start with). Set "
                    "it longer than the acquisition.",
                ),
                (
                    "Both boards in step",
                    "The two folders to watch during <b>Acquire</b>, "
                    "with the check's settings - see "
                    "<a href=\"#insync\">Both boards in step</a>.",
                ),
            ]
        )
        + """
<h3>Buttons</h3>
"""
        + _table(
            [
                (
                    "Check clocks",
                    "Read both boards' clock status without changing "
                    "anything.",
                ),
                (
                    "Acquire",
                    "External clock on, check the lock, and start both "
                    "acquisitions together.",
                ),
                (
                    "Launch boards",
                    "Start one copy of the board program per board, "
                    "each with its own settings file.",
                ),
            ],
            head=("Button", "What it does"),
        )
        + """
<p>The boards are named Board 0 and Board 1 here, as the board program
numbers them; <a href="#full">Full Sensor</a> calls the two halves
Board 1 and Board 2.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "panels",
        "Shared panels",
        None,
        """
<h2>Shared panels</h2>
<p>Some boxes appear on more than one tab and work the same way on
each:</p>
<ul>
<li><a href="#mask">Pixel mask</a> - Online plot, Full Sensor.</li>
<li><a href="#peak">Peak in view</a> - Online plot, Full Sensor.</li>
<li><a href="#fit">Gaussian fit</a> - Online plot, Full Sensor.</li>
<li><a href="#tdc">TDC memory</a> - Online plot, Full Sensor.</li>
<li><a href="#insync">Both boards in step</a> - Full Sensor,
Synchronization.</li>
</ul>
<p>The boxes with a tick in their title can be switched off with it;
a switched-off box costs nothing on each refresh.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "mask",
        "Pixel mask",
        "panels",
        """
<h2>Pixel mask</h2>
<p>A masked pixel is drawn at zero and left out of the readings,
<a href="#peak">Peak in view</a>, the <a href="#fit">fits</a> and the
"unmasked, in view" choice of <a href="#tdc">TDC memory</a>. Masking
takes effect on the plot at once, without waiting for the next
file.</p>

<h3>Three ways to mask</h3>
<ul>
<li><b>Ctrl+click</b> a pixel on the plot. Ctrl+click it again to
unmask it.</li>
<li><b>Preset mask</b>: the warm pixels recorded for the chosen
daughterboard and motherboard. If none is recorded for that pair, a
message says so and the tick is cleared. On Full Sensor each board
uses its own motherboard, and a board with nothing recorded is
skipped.</li>
<li><b>Edit mask...</b>: a window with one check box per pixel (one grid
per board on Full Sensor). It can stay open beside the plot while the
stream runs.</li>
</ul>

<h3>The mask window</h3>
"""
        + _table(
            [
                (
                    "Quick entry",
                    "Type pixels such as <code>12, 40-43</code> and "
                    "click <b>Mask</b> or <b>Unmask</b>; Enter means "
                    "Mask.",
                ),
                (
                    "The grid",
                    "Four pixels per row, numbered across: the first row "
                    "is 0-3. On firmware 2212b a row is exactly the "
                    "four pixels that share one TDC.",
                ),
                (
                    "n of 256 pixels masked",
                    "The count under each grid.",
                ),
                (
                    "Clear all",
                    "Unmask everything on every board, and clear "
                    "<b>Preset mask</b>.",
                ),
                ("Close", "Hide the window; the mask stays."),
            ]
        )
        + """
<p><b>Reset</b> on the tab does the same as <b>Clear all</b>.</p>
<p>Pixel lists, here and in <a href="#tdc">TDC memory</a>, are single
numbers and inclusive ranges separated by commas, spaces or
semicolons: <code>36, 40-43; 100</code>. A range can also be written
<code>40:43</code>.</p>
<p>The mask is not remembered when the application closes; tick
<b>Preset mask</b> again next time.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "peak",
        "Peak in view",
        "panels",
        """
<h2>Peak in view</h2>
<p>Four numbers about the peak between the current x limits, updated
with every file. They tell you whether an adjustment made the peak
better, not only whether it moved.</p>
"""
        + _table(
            [
                (
                    "Brightest",
                    "The pixel with the highest rate in view, and that "
                    "rate.",
                ),
                (
                    "Centroid",
                    "The rate-weighted mean pixel: where the peak is, to "
                    "better than one pixel. The one to watch while "
                    "turning a mirror.",
                ),
                (
                    "FWHM",
                    "Full width at half maximum, in pixels, measured "
                    "out from the brightest pixel. Blank when the peak "
                    "runs off the edge of the view - widen the limits.",
                ),
                (
                    "Sum in view",
                    "All the rates in view added up: how much light gets "
                    "through, however tightly it is focused.",
                ),
            ],
            head=("Reading", "What it means"),
        )
        + """
<p>Narrow the x limits onto the signal: otherwise a hot pixel elsewhere
on the sensor can be the brightest and decide every number. "nothing in
view" means every pixel between the limits reads zero.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "fit",
        "Gaussian fit",
        "panels",
        """
<h2>Gaussian fit</h2>
<p>On the Online plot and the Full Sensor tab, the strip just above
the plot fits a Gaussian to
every spectral line in view - for example while focusing a spectrometer
on a neon lamp - and shows each line's width with its uncertainty, on
every refresh.</p>
<ol>
<li>Tick <b>Gaussian fit</b>.</li>
<li>Type a <b>Threshold (Hz)</b>, such as <code>2e5</code>, and press
Enter. It is drawn on the plot as a dashed line. Put it above the
hot pixels and the dark floor, and below the lines.</li>
</ol>
<p>Each run of neighbouring, unmasked pixels above the threshold, within
the x limits, counts as one line. It is fitted with a Gaussian on a
constant background, then fitted again over four sigmas either side of
the first result.</p>
<p>The strip shows one entry per line, such as
<code>px 131.4: &sigma; = 1.82 &plusmn; 0.03</code> (centre and sigma,
both in pixels; sigma and its error to two decimals). On the Full
Sensor tab the centre is on the 0-511 axis. Each line's sigma is also written on the plot. Hover
over the strip for the full result: centre, sigma, FWHM, amplitude and
background.</p>
"""
        + _table(
            [
                (
                    "set a threshold to fit",
                    "The fit is ticked but no threshold is set.",
                ),
                (
                    "no lines above threshold",
                    "Nothing in view rises above the threshold.",
                ),
                (
                    "too few pixels",
                    "The line has fewer than 5 usable pixels - widen "
                    "the limits or lower the threshold.",
                ),
                ("fit failed", "The fit did not converge on this line."),
                (
                    "a huge uncertainty",
                    "Shown in scientific notation. Usually a hot pixel "
                    "fitted as a line: raise the threshold or mask it.",
                ),
            ],
            head=("Message", "What it means"),
        )
        + """
<p>Two lines close enough that the trace never drops below the
threshold between them are fitted as one; raise the threshold to split
them. The fits are written into the notes of an
<a href="#export">exported</a> file.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "tdc",
        "TDC memory",
        "panels",
        """
<h2>TDC memory</h2>
<p>Each TDC records the photons of four pixels, and has room for
<b>Timestamps</b> of them per acquisition cycle. When that room is used
up, the rest of the cycle is thrown away - and the data file gives no
sign of it, since it is the same size either way. This box watches for
that while the stream runs, and suggests a <b>Timestamps</b> setting
that fits the measurement.</p>

<h3>Which pixels are watched</h3>
"""
        + _table(
            [
                (
                    "unmasked, in view",
                    "Every pixel that is not masked and lies between the "
                    "x limits. Apply the preset mask or zoom onto the "
                    "signal and this narrows down on its own.",
                ),
                (
                    "these:",
                    "The pixels you type, such as "
                    "<code>143, 156-159</code>, when the mask is not the "
                    "whole story.",
                ),
            ],
            head=("Choice", "What it watches"),
        )
        + """
<p>All the traffic of a TDC holding a watched pixel counts, including
that of a hot pixel sharing it - that is exactly the case that uses up
the room the signal needs.</p>

<h3>The two readings</h3>
"""
        + _table(
            [
                (
                    "First line",
                    "The busiest TDC among the watched pixels, such as "
                    "<code>TDC 36: 54/150 slots (36 %)</code>: the "
                    "median number of slots used per cycle. This is the "
                    "one that says whether <i>your</i> measurement is "
                    "affected.",
                ),
                (
                    "worst on sensor",
                    "The busiest TDC anywhere on the board, watched or "
                    "not. Usually a hot pixel; it shows how close to the "
                    "edge the board is running.",
                ),
            ],
            head=("Reading", "What it means"),
        )
        + """
<p>The lamps: <b>green</b> - plenty of room; <b>amber</b> - more than
70 % of the slots used, or full in some cycles; <b>red</b> - full in
more than 1 % of cycles, so data are being lost. The text says
"full in x % of cycles" whenever a TDC filled up.</p>

<h3>The suggestion</h3>
<p><b>Timestamps suggested: N (now M)</b> is the setting that would
hold the watched pixels with about 30 % to spare, rounded up to a
multiple of 50. <b>Apply</b> puts it into the <b>Timestamps</b> box;
it takes effect on the next file, so the acquisition must be set to the
same value. As a rule of thumb, the slots needed are about 4 &times;
rate per pixel &times; the timestamping window: 4 &times; 86 kHz
&times; 4 ms is about 1380.</p>
<p>If more than the 1536 slots the hardware has would be needed, no
setting is enough: shorten the window or attenuate the light. If every
cycle filled up, the file shows neither the true rate nor the window,
so no suggestion can be made: raise <b>Timestamps</b> well above its
current value and measure again.</p>

<h3>The warning</h3>
<p>The first time a watched TDC is full in more than 1 % of cycles, a
<b>Readout saturated</b> message appears, once per run. It does not
stop the stream. <b>Show Details...</b> lists every TDC that filled up
and when. Starting the stream again, or <b>Refresh plot</b>, re-arms
it.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "insync",
        "Both boards in step",
        "panels",
        """
<h2>Both boards in step</h2>
<p>In a good two-board run, each board writes one file per acquisition
cycle into its own folder: the same number of files on both sides, each
pair created within a couple of seconds of each other. If one board
stalls or drops a cycle, the two halves can no longer be matched up
afterwards - and the live plot of either half still looks healthy. This
check watches for that in the background.</p>
"""
        + _table(
            [
                (
                    "Board files (Synchronization only)",
                    "The folder each board's own window saves to. Only "
                    "read, never written to. On Full Sensor the two "
                    "plot folders are used instead.",
                ),
                (
                    "Pair tolerance (s)",
                    "How far apart the two files of one cycle may be "
                    "created; 2.0 s to start with. Good runs stay "
                    "within about 2 s.",
                ),
                (
                    "Check every (s)",
                    "How often the two folders are compared; 5 s to "
                    "start with.",
                ),
            ]
        )
        + """
<p>The check runs while the stream runs (Full Sensor) or while
<b>Acquire</b> runs (Synchronization). Only files created after it
started are counted, so leftovers from an earlier run do not matter.
Its settings are locked while it runs.</p>
<p>The lamp is <b>green</b> while both boards keep pace, <b>amber</b>
while it is waiting for the first files or one board is briefly ahead,
and <b>red</b> once the run has gone wrong. A short difference in the
number of files is normal; it counts as a problem only after it has
lasted 30 seconds. A pair further apart than the tolerance is a problem
at once.</p>
<p>When that happens, a <b>Boards out of step</b> message appears,
once per run, without stopping anything. <b>Show Details...</b> lists
the pairs that are too far apart and the files only one board has. The
run cannot be synchronized afterwards: stop it and measure again.</p>
<p>"no working directory set - not checking" and "both boards point at
the same directory - not checking" mean the folders need setting.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "export",
        "Exporting data",
        None,
        """
<h2>Exporting data</h2>
<p><b>File &rarr; Export plotted data...</b> (<b>Ctrl+E</b>) saves the
numbers behind the plot on the current tab - not a picture of it. It
is greyed out until the tab has plotted something, and on
Synchronization, which has no plot.</p>
<p>Choose the format in the save dialog:</p>
<ul>
<li><b>CSV</b> - one column per quantity, with a header row. Above it,
lines starting with <code>#</code> record the application version, the
time of export, the source file, the boards, the firmware and the
settings, so the file still says where it came from months later. In
Python: <code>pandas.read_csv(path, comment="#")</code>.</li>
<li><b>NumPy archive (.npz)</b> - one array per column, plus
<code>notes</code>: <code>numpy.load(path)</code>.</li>
</ul>
<p>The suggested name is the tab and the date and time, such as
<code>online-plot-20261101-143005</code>. Without an extension, the
format chosen in the dialog decides it.</p>
<p>A masked pixel exports with rate 0 and <code>masked = 1</code>. The
columns of each tab are listed on its page.</p>
<p>To save the plot as a picture, use the <b>Save</b> button in the
plot's toolbar.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "appearance",
        "Themes and Preferences",
        None,
        """
<h2>Themes and Preferences</h2>
<p><b>View &rarr; Theme</b> switches the whole look in one click. The
dark themes are listed first, then a line, then the light ones.
<b>Daplis (publication)</b> gives plots ready to put in a paper.</p>
<p><b>View &rarr; Preferences...</b> (<b>Ctrl+,</b>) opens a window for
finer changes. Every change is applied at once, to the window and to
the plots already drawn, so keep it beside a plot and watch.</p>
"""
        + _table(
            [
                (
                    "Theme",
                    "The starting point. Choosing a theme again throws "
                    "away the changes made below.",
                ),
                (
                    "Interface: Window background",
                    "The tab pages and the control column.",
                ),
                (
                    "Interface: Panels",
                    "The tab bar, the menu and status bars, the log and "
                    "this guide.",
                ),
                (
                    "Interface: Input fields",
                    "Line edits, spin boxes and drop-down boxes.",
                ),
                (
                    "Interface: Buttons",
                    "Push buttons and spin-box arrows; the hover shade "
                    "follows.",
                ),
                (
                    "Interface: Borders",
                    "Every thin border: fields, buttons, boxes, the tab "
                    "page.",
                ),
                (
                    "Interface: Text, Secondary text, Muted text",
                    "The main text; labels, check boxes and the log; "
                    "hints, inactive tabs and disabled controls.",
                ),
                (
                    "Interface: Accent",
                    "The selected tab, the box titles, the readings, "
                    "the outline of each tab's main button, and the "
                    "highlight on whatever is selected.",
                ),
                (
                    "Interface: Font size",
                    "Size of the window's text, 7-16 pt. Rows and "
                    "columns grow with it.",
                ),
                (
                    "Status",
                    "OK, Warning and Error: the colours of the "
                    "lamps in <b>TDC memory</b>, <b>Both boards in "
                    "step</b> and the Synchronization clock status - "
                    "worth changing if two of them are hard to tell "
                    "apart.",
                ),
                (
                    "Plots: colours",
                    "Figure background, Plot background, Ticks and "
                    "labels, Axes frame, Grid, and Markers (the seam "
                    "and group-of-64 lines, and the fit threshold).",
                ),
                (
                    "Plots: Font size",
                    "Size of the plot labels on a small window, 8-32 pt; "
                    "it grows as the window widens.",
                ),
                (
                    "Plots: Marker size",
                    "Size of the dots on the traces, 0-12 pt; 0 draws a "
                    "line only.",
                ),
                (
                    "Glow",
                    "A glow under the traces. It redraws each line "
                    "several times, which slows a fast stream.",
                ),
                ("Grid", "Grid lines behind the data."),
                (
                    "Trace colours",
                    "Trace 1: sensor population and the first MZI "
                    "pixel. Trace 2: the second MZI pixel and the fit "
                    "labels. Trace 3: the single-pixel histogram. "
                    "Traces 4 and 5 are spare.",
                ),
                (
                    "Reset to defaults",
                    "Back to the shipped theme, font and marker sizes.",
                ),
            ],
            head=("Setting", "What it changes"),
        )
        + """
<p>Click a colour button to pick a colour. Panels, Buttons, Borders and
Secondary text are worked out from the window background, the text and
the muted text, and follow them when those change - until you set them
yourself. Your theme and changes are remembered for your user account;
the current theme is named at the right of the status bar.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "remembered",
        "What is remembered",
        None,
        """
<h2>What is remembered</h2>
<p>Settings are saved as they are changed and restored when the
application next starts, separately for each tab and for each user
account on the computer:</p>
<ul>
<li>the data folders, boards, firmware version and timestamps;</li>
<li>the check boxes, axis limits and cycle length;</li>
<li>which status boxes are switched on (but not the settings inside
them, such as the pair tolerance or the typed pixels);</li>
<li>the Gaussian fit and its threshold;</li>
<li>on Synchronization: the program path, the settings files, the two
board folders, the ports and the timeout. The path, settings files and
folders are saved when <b>Launch boards</b> or <b>Acquire</b> is
clicked;</li>
<li>the theme, colours and font sizes.</li>
</ul>
<p>Not remembered: the pixel mask, the plots and readings, and anything
about the last run.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "keys",
        "Keyboard and mouse",
        None,
        """
<h2>Keyboard and mouse</h2>
"""
        + _table(
            [
                ("F1", "Open this guide at the current tab's page."),
                ("Ctrl+E", "Export the numbers behind the current plot."),
                ("Ctrl+,", "Open Preferences."),
                ("Ctrl+Q", "Quit."),
                ("Ctrl+click on a plot", "Mask or unmask that pixel."),
                (
                    "Enter in the mask window's quick entry",
                    "Mask the pixels typed.",
                ),
                (
                    "Mouse over a plot",
                    "The toolbar shows the coordinates under the "
                    "cursor.",
                ),
                (
                    "Mouse over a control",
                    "A short explanation of it.",
                ),
            ],
            head=("Key or action", "What it does"),
        )
        + """
<p>Number boxes for pixels take their value when you press Enter or
leave the box, so typing a number never jumps the plot halfway.</p>
""",
    ),
    # ------------------------------------------------------------------
    Section(
        "trouble",
        "Troubleshooting",
        None,
        """
<h2>Troubleshooting</h2>
"""
        + _table(
            [
                (
                    "No data files found - check the working directory.",
                    "The folder is wrong, empty, or its files' names do "
                    "not contain <code>.dat</code>. Check the folder "
                    "path above the plot. While a stream runs, an "
                    "empty folder is waited on instead.",
                ),
                (
                    "Cannot read data file - it may have been removed.",
                    "Usually a setting that does not match the file: "
                    "<b>Timestamps</b>, <b>Firmware version</b> or "
                    "<b>Absolute timestamps</b>. A file still being "
                    "written can also do it; <b>Refresh plot</b> again. "
                    "<b>Show Details...</b> gives the exact error.",
                ),
                (
                    "The plot does not update",
                    "Is the stream running (the button reads <b>Stop "
                    "stream</b>)? Only a file newer than the one shown "
                    "is read. On a network drive allow a couple of "
                    "seconds.",
                ),
                (
                    "One hot pixel flattens the plot",
                    "Ctrl+click it to mask it, tick <b>Preset mask</b>, "
                    "clear <b>Linear scale</b>, or narrow the x limits.",
                ),
                (
                    "No mask data were found for this combination",
                    "No preset mask is recorded for that daughterboard "
                    "and motherboard. Mask by hand instead.",
                ),
                (
                    "FWHM is blank",
                    "The peak runs off the edge of the view; widen the "
                    "x limits.",
                ),
                (
                    "Readout saturated",
                    "A TDC is running out of room. Click <b>Apply</b> "
                    "in <a href=\"#tdc\">TDC memory</a> and set the "
                    "same value in the acquisition, or attenuate the "
                    "light.",
                ),
                (
                    "Boards out of step",
                    "One board stopped keeping pace. The run cannot be "
                    "matched up; stop it and measure again. See "
                    "<a href=\"#insync\">Both boards in step</a>.",
                ),
                (
                    "Synchronization: unreachable / cannot reach "
                    "LinoSPAD_synchro.exe",
                    "The board's window is not running, is not "
                    "<b>Listening</b>, or listens on another port than "
                    "the one under <b>Connection</b>.",
                ),
                (
                    "Synchronization: NOT on external clock",
                    "Check the 25 MHz square wave on CLK_IN (J11) of "
                    "both boards, that <b>Ext MHz</b> reads 25 (not "
                    "about 50), and that it is 25 MHz, not 20.",
                ),
                (
                    "Synchronization: acquisition stops with an error",
                    "If a board needs longer than <b>Acq. timeout "
                    "(s)</b>, raise it.",
                ),
                (
                    "Export is greyed out",
                    "Nothing is plotted on this tab yet, or the tab has "
                    "no plot (Synchronization).",
                ),
            ],
            head=("Problem or message", "What to do"),
        )
        + """
""",
    ),
]

# The guide's page for each tab, by the tab's title in the window, so
# that F1 opens the page of whatever tab is in front.
TAB_SECTIONS = {
    "Online plot": "online",
    "Single Pixel Histogram": "histogram",
    "MZI": "mzi",
    "Full Sensor": "full",
    "Synchronization": "sync",
}


def section(key):
    """The section with this key, or ``None``."""
    for item in SECTIONS:
        if item.key == key:
            return item
    return None
