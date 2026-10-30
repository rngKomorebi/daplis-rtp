# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.1] - 2026-10-30

### Added

- **Gaussian fit on the online plot.** A row above the plot, under the
  brightest pixels, with a "Gaussian fit" switch (off by default) and a
  threshold in Hz. On every refresh each run of pixels above the
  threshold, within the x-limits, is fitted with a Gaussian on a
  constant background, and the row reports every line's sigma with its
  uncertainty; the tooltip adds centre, FWHM, amplitude and background.
  The fitted curves, their sigmas and the threshold are drawn on the
  plot, masked pixels are left out of the fits, and the results go into
  *File → Export*. The threshold is set by hand to sit above the hot
  pixels and below the lines. Adds `scipy` as a dependency.

### Fixed

- **Python 3.8.** The app failed to import on 3.8, which it claims to
  support: `importlib.resources.files` is 3.9+. On 3.8 it now comes from
  the `importlib_resources` backport, a dependency for that version only.
- **CI runs the tests again.** The workflow still called `tox` after
  `tox.ini` was deleted, so it passed without testing anything; it now
  runs `pytest`. Python 3.8 is tested on Ubuntu 22.04, as `ubuntu-latest`
  (24.04) has no 3.8 build.

## [1.6.0] - 2026-09-18

### Added

- **Six more themes**, ported from the matplotlib styles in
  [komorebi_mpl](https://github.com/rngKomorebi/komorebi_mpl): "Komorebi"
  (deep gold and forest green on parchment), "Night wave" (synthwave
  neon on violet, the second theme that earns the glow), "Blueprint"
  (a CAD drawing - white and ice-blue on deep navy), "Earth"
  (terracotta and olive on aged paper), "Solarized", and "Daplis
  (publication)" - the house palette, anchored on rebeccapurple and
  darkorange and chosen to stay legible for the common forms of colour
  blindness. Ten in all, dark ones first in the menu with a rule where
  the light ones begin.

  The figure, axes, grid and trace colours are komorebi_mpl's. The
  window chrome around them is not, because a matplotlib style sheet has
  nothing to say about a control panel, and neither are the three status
  colours: a warning lamp that matches the data it is warning about is
  not a warning.

  The styles are ported rather than depended on. They set a 30 pt font
  and a 16x10 figure, which are right for a saved figure and wrong for a
  canvas inside a window, so a dependency would mean overriding most of
  what it provided - and the colours have to reach the Qt side of the
  application too, which no ``.mplstyle`` can do.

- A theme's **axis frame and axis text are separate colours**
  (``axes_edge`` alongside ``axes_fg``), both of them pickable in
  Preferences. Several of the ported styles depend on the difference:
  Blueprint draws a dim blue box under bright white labels, and
  Solarized a grey one under slate text.

- **The tabs remember what was typed into them** (`gui/session.py`).
  The folder, the daughterboard, the motherboard, the firmware, the
  timestamp count, the axis limits and every switch come back as they
  were left, per user and per tab. Only the Synchronization tab
  remembered anything before, and only its paths; everything else began
  each session by re-entering the same six things.

  Inputs only. A readout, a lamp or a plot is a statement about the data
  in front of you, and restoring one on a fresh start would be a
  statement about nothing.

- **Ctrl+click a pixel on the plot to mask it**, on "Online plot" and
  "Full Sensor". The pixel number was already under the cursor in the
  toolbar readout; acting on it meant opening the mask window and
  finding one box out of 256. Ctrl+click toggles it, and Ctrl rather
  than a bare click because a stray click during a run would otherwise
  change the mask - and so the rates - with no deliberate gesture. On
  the full-sensor plot the 0-511 axis decides which board the click
  landed on.

  The mask now also takes effect on the trace immediately rather than at
  the next data file: the rates are kept unmasked and the mask applied
  when the plot is drawn, so a tick is one redraw rather than one
  re-read. The preset mask and "Reset" tick their couple of hundred
  boxes with a single notification instead of one each.

- **"Peak in view" box** on "Online plot" and "Full Sensor"
  (`gui/widgets/peak_stats.py`): the brightest pixel and its rate, the
  centroid, the FWHM, and the sum over the x-limits currently shown.

  Aligning means maximising something, and the only figure on screen was
  which pixel was brightest - which says a peak moved but not whether it
  improved. A peak that doubles in height while doubling in width has
  gained nothing, and one that shifts by half a pixel is invisible
  against the sample spacing; the centroid reports it to a hundredth.
  Narrowing the x-limits onto the signal is what stops a hot pixel
  elsewhere on the sensor deciding the answer.

  The FWHM is deliberately blank when the peak runs off the edge of the
  view: a number that is wrong by however much was cut off is worse than
  none.

- **File -> Export plotted data** (`Ctrl+E`): the numbers behind the
  current plot, as `.csv` or `.npz`. The toolbar has always saved a
  picture; there was no way to keep what the picture was of.

  The file carries its own provenance - the version, the time, the
  source file, the board, the firmware, the timestamp count and the
  limits shown - as `#` comments above a plain header row, so a
  spreadsheet reads the columns and `pandas.read_csv(..., comment="#")`
  skips the rest. The menu item greys out on a tab with nothing plotted.

- `tests/test_peak_stats.py` and `tests/test_export.py`, and a
  regression test pinning `sen_pop`'s output to the figures it produced
  before the counting was rewritten.

### Changed

- **The data folders are watched rather than swept**
  (`QFileSystemWatcher`, `gui/tabs/base.py`). The stream used to run
  `glob` plus a `getctime` per entry ten times a second, which on a run
  of several thousand files is several thousand stat calls a second to
  notice one new name. It now waits to be told, settles for 150 ms so a
  burst of writes costs one read, and keeps a 2 s poll as a backstop
  because a watcher is reliable on a local disk and decidedly not on the
  network share a board GUI often writes to.

- **`sen_pop` counts in one pass instead of 256.** It looped over every
  pixel, re-deriving that pixel's TDC with an `np.argwhere` search of a
  256-element array and then making two more passes over that TDC's
  column. The map is now read forwards and the whole matrix counted with
  `np.bincount`: the same numbers, about twice as fast at the counting,
  on the path that runs on every frame of a stream. (Unpacking the file
  still dominates a frame - about 10 ms of 14 on a 1 MB file.)

- **Starting a stream on an empty folder waits instead of failing.**
  The ordinary way a run begins is to arm the stream and then start the
  acquisition, so the folder is empty for the first few seconds by
  design - and "no data files found" was a modal box that also stopped
  the stream to show itself. It is now silent while a stream is running,
  with "waiting…" in the readout, and still a message box when "Refresh
  plot" was pressed, since that is exactly what the user asked about.
  Starting a stream also draws whatever is already in the folder rather
  than waiting for the next file.

- The single-pixel histogram is binned by the tab rather than inside the
  canvas, so that what is exported is the histogram that was drawn.

### Removed

- **The per-code TDC calibration.** It had been commented out in
  `unpack.py` since before the package took its present shape, and
  matrices existed for two of the four daughterboards the application
  offers - which is very likely why. The dead code is gone,
  `functions/calibrate.py` and the two `.csv` matrices have moved to the
  `old` folders beside the rest of the superseded code, and the package
  no longer ships data that nothing reads.

  Timestamps are the raw TDC code times the nominal 17.857 ps bin, as
  they have been all along. That costs nothing for counting rates, which
  is what this package plots; a measurement that needs the true bin
  widths - a delta-t histogram - wants `daplis` offline.

### Fixed

- `peak_stats` collapsed x-limits given the wrong way round to a single
  pixel, because the lower bound was stored before the upper one was
  computed from it. Caught by its own test on the way in.

## [1.5.0] - 2026-09-17

The interface is rebuilt. Every tab is now generated from one skeleton
with one set of geometry rules, and every colour and font size in the
application comes from one place the user can change.

Nothing about the measurements changed: the unpacking, the rate
calculation, the TDC occupancy arithmetic and the two-board acquisition
protocol are the code they were, moved rather than rewritten.

### Added

- **Themes, and a Preferences window to build one**
  (`gui/theme.py`, `gui/preferences.py`, *View → Preferences*, `Ctrl+,`).
  Four presets ship: "Cyberpunk", the look the application has always
  had, glow and all, and still the default; "Midnight", the same dark
  window with the glow off; "Daylight", a white figure for a bright room
  or a document; and "High contrast", pure black with trace colours
  chosen to stay apart for the common forms of colour blindness.

  Every colour in a preset can then be overridden - the accent, the
  figure and plot backgrounds, the axes, the grid, the markers, and each
  of the five trace colours - along with the interface and plot font
  sizes and the glow and grid switches. The window is not modal and
  every change applies the instant it is made, to plots already drawn as
  well as new ones, so a colour is chosen by watching the plot rather
  than from memory.

  Settings are stored per user through `QSettings`, so two people
  sharing a machine keep their own, and an unreadable stored value is
  skipped rather than raised - a settings file is not something a user
  can easily repair, so it must never stop the application opening.

  The reason this needed a rewrite rather than a setting is that the old
  application chose its colours in a dozen places: `dark_background` in
  three canvas modules, `#f48383` and `teal` written into the plotting
  calls, `qdarkstyle` on the application, and a `setPointSize(10)` on
  very nearly every widget built. Now no widget sets its own font - the
  application font is set once and inherited - and no canvas holds a
  colour, which is why a theme change is a redraw rather than a restart.

- **`tests/test_tab_geometry.py`**: the tabs are measured rather than
  looked at. It builds all five headless and asserts that the plot
  occupies the same rectangle on each, that the control column and the
  action buttons are the same size and in the same place, that no tab
  quietly sizes its own combo boxes, that the window's minimum stays
  inside a budget, and that a larger interface font moves the rows
  instead of clipping them.

  Every layout problem this package has had was found by measuring and
  none by looking, and until now the measuring was a script in a scratch
  directory.

### Changed

- **One skeleton for every tab** (`gui/layout.py`, `TabShell`). The plot
  is the same size and in the same place on all five tabs; so is the
  control column; so is every button. A tab that needs only one browse
  row still reserves the two that "Full Sensor" needs, and puts a row of
  readings in the other. "Synchronization", which has no plot, is built
  in the same shell: its log sits where the others' canvas sits, its
  clock status where their axis limits sit, and its three buttons in the
  same three slots.

  The buttons are stacked in three fixed slots with a fixed meaning -
  look again, the thing the tab is for, then the extra - so a tab with
  one button leaves two empty rather than letting its button grow.

- **The control column scrolls** (`gui/layout.py`, `ControlColumn`).
  This is the fix for the oldest problem in the layout: a column's
  minimum height is the sum of the panels stacked in it, and the tallest
  column of the five decided how tall the whole application opened. A
  status box added to one tab made every tab open 70 px taller. A column
  that is too tall now scrolls.

- **The window opens at 1500x900** rather than at its own minimum.
  `MainWindow` had no `resize()` at all, which is why that minimum had
  been the subject of so much attention; it is now only a floor, and one
  the geometry test holds under 1320x720.

- **One canvas class instead of three** (`gui/canvas/`). `plot_figure`,
  `plot_figure_dual` and `plot_figure_MZI` were the same eighty lines
  copied out three times, with the differences that mattered - a
  boundary line here, a second y-axis there - buried among the
  differences that did not. There is now one themed base class and one
  small subclass per plot, which stores what it was given and redraws it
  on demand.

- **Plots use constrained layout** rather than fixed `subplots_adjust`
  fractions, which were tuned for one font size: a large plot font -
  which is exactly what a wide window produces - used to push the y-axis
  label off the edge of the figure.

- The plot font grows with the canvas rather than with the window. Each
  tab used to do this for itself, off the width of the whole window and
  with the same four magic numbers copied out five times; adding a
  control column beside a plot therefore changed the font on it. It is
  also debounced, so dragging a window edge no longer redraws per event.

- **Controls are built once** (`gui/widgets/controls.py`). The
  daughterboard, motherboard, firmware and timestamp controls existed in
  four copies, which is how the "Full Sensor" combo boxes came to be
  80 px `Expanding` while everyone else's were 100 px `Fixed`, and how
  one tab came to offer a motherboard the others did not.

- "Both boards in step" is a checkable group box, as "TDC memory"
  already was: the tick moves into the title, which saves a row of the
  control column and makes the two status boxes match each other.
  Clearing the tick now also stops the sweep, rather than only stopping
  anyone asking about it.

- The MZI trace is kept as three arrays and redrawn whole. It used to be
  built by adding a fresh two-point line segment per refresh, so an
  hour's run ended as some thousands of `Line2D` objects that matplotlib
  walked on every draw - and there was no record of the trace to redraw,
  so a change of colour could only apply to the points that came after
  it.

- The two brightest pixels moved out of the "Online plot" control column
  and into the row above the plot, where they cost the application no
  height, and are joined there by the masked count and the name of the
  file being plotted.

- The single-pixel histogram no longer opens and unpacks the data file
  from inside the plot widget. A plot widget that cannot be drawn
  without a LinoSPAD2 file on disk cannot be tested, and the firmware
  version and timestamp count it needed are chosen on the tab anyway.

- The superseded modules are kept, unmaintained, in `gui/_legacy/`,
  with their imports rewritten so they still run. Nothing in the
  application imports from there; they are the reference for what the
  rebuilt tabs are supposed to do.

### Fixed

- New data arriving while a plot was on a logarithmic scale took the
  stream down with `AttributeError: This method only works with the
  ScalarFormatter`. `ticklabel_format` only understands the linear
  formatter, and the plotting path called it unconditionally.

- The MZI tab's "Linear scale" box raised `AttributeError` when ticked:
  its handler read `checkBox_presetMask_2`, a widget that tab does not
  have. The single-pixel histogram's box was connected to nothing at
  all. Both now switch the scale of the plot they sit beside, and all
  four boxes start ticked, agreeing with the linear axis they are
  drawn against rather than contradicting it.

- The y-axis of every plot lost its scientific notation whenever the
  scale was applied: setting a scale installs that scale's default
  formatter, and the scale was being set after the draw. Rates of a few
  hundred thousand were labelled in full.

- On the MZI plot the right-hand axis label was drawn on the left, on
  top of the left-hand one. Clearing a twin axes resets its label back
  to the left-hand side.

- The line of guidance across the top of each tab set how narrow the
  whole application could be made - over 2000 px - because a `QLabel`
  reports a minimum width equal to the whole of its text. It elides
  instead, keeping the full text in its tooltip.

## [1.4.0] - 2026-09-15

### Added

- An application icon. The window, the taskbar, alt-tab, the pixel
  mask window and the message boxes all carry it, and so do the
  executable, the Explorer listing and any desktop shortcut made from
  it.

  The artwork lives once, full size, in `assets/daplis-rtp-icon.png`.
  `tools/make_icons.py` renders it down to the sizes Qt and Windows
  actually ask for, into `src/daplis_rtp/resources`, and only those
  ship - the master is a few hundred kilobytes that no user of the
  package has a use for. Re-run the script after editing the artwork
  and commit what it writes; the release build has no image library and
  renders nothing itself.

  Qt scales whatever single image it is handed, so the sizes are
  rendered rather than left to it: a 16 px title-bar icon downscaled on
  the fly from the master loses the peak to blur. The `.ico` holds the
  same set in the one file Windows reads.

  The artwork carries no lettering. A name across the bottom of an icon
  is unreadable below about 64 px and costs the drawing the room it
  needs to survive at 16 and 32, where an application icon is actually
  looked at.

  `make_icons.py` also crops the clear space off the master before
  rendering. The export carries about five per cent of transparent
  margin on each side - the convention for macOS artwork - while
  Windows draws its icons to the edge, so keeping it would render the
  tile at 90 % of the size every neighbouring icon gets and leave the
  application looking smaller than the rest of the taskbar.

  `main` also claims an "application user model ID" before the first
  window exists. Without one a Python process inherits the
  interpreter's, and Windows shows the Python icon on the taskbar
  button - and groups it with every other PyQt application running -
  however the window itself is set.

- "TDC memory" box on the "Online plot" and "Full Sensor" tabs
  (`tdc_occupancy_panel.py`, `functions/tdc_occupancy.py`): how much of
  the TDC slot memory the readout is actually using, so that
  `Timestamps` can be set to fit the measurement instead of guessed.

  Each TDC holds `Timestamps` slots per acquisition cycle, shared by its
  four pixels; once they are full the rest of the cycle is dropped and
  the data file gives no sign of it, being exactly the size it would
  have been either way. The loss is rate-dependent, so the two halves of
  a full-sensor run truncate at different times and can no longer be
  compared - which is how the 1000-slot laser run of 2026.09.04 came to
  record only the first ~2.9 ms of each 4 ms window on both boards, and
  why its cross-board reduction never came out cleanly.

  Two figures are shown, because either one alone misleads. A per-sensor
  average hides a single saturating TDC; the sensor-wide maximum is
  usually a hot pixel nobody is measuring. So the box reports the
  busiest TDC among the pixels of interest *and* the busiest TDC
  anywhere on the half, with a suggested `Timestamps` alongside. On the
  B7d run of 2026.09.07 those read TDC 36 at 54/150 and TDC 17 full in
  84.8 % of cycles respectively.

  The pixels of interest are, by default, every pixel that is neither
  masked nor outside the current x-limits, so applying the preset mask
  or zooming in on the signal narrows the figure with no extra input;
  they can also be typed in ("143, 156-159") when the mask is not the
  whole story. A TDC counts as being of interest when it holds at least
  one such pixel, and *all* of that TDC's traffic is counted, including
  a hot pixel sharing it - that hot pixel is eating the slots the signal
  needs, which is the one case where a hot pixel matters and the one a
  TDC-masking rule would have hidden.

  Where a TDC of interest fills up in more than a per cent of the
  cycles, a warning is raised once per run, so that an acquisition
  started and left alone cannot truncate unnoticed.

  Both tabs keep the box in the same place - last panel of the control
  column, above the two buttons - so that what is read during a run is
  read in the same place on either.

  That column's minimum height is the sum of its panels, and the
  tallest tab decides how tall the application opens, so the box is
  built to spend as few rows as it can: the tick that switches it off
  is the group box's own, in the title, and the heading shares a row
  with the first radio button. Putting the heading, both buttons and
  the field on one line would save another row, but costs some 250 px
  of minimum width, which the window can less afford - see
  'plot_figure.toolbar_min_width'.

- `sen_pop` gained `return_occupancy`, which also returns the slot
  occupancy. It is computed from the matrix `sen_pop` has already
  unpacked - one comparison and two small indexed reads per TDC - so the
  check costs no second pass over the file.

- The pixel mask opens in a window of its own (`pixel_mask_window.py`),
  reached from an "Edit mask…" button that replaces the scroll area in
  the control column, with a count of the masked pixels beside it.

  The 256 check boxes took about 250 px of the column on each tab, which
  was at once too little to work in - a handful of the 64 rows visible
  at a time - and enough to decide how tall the whole application
  opened, since a column's minimum height is the sum of what is stacked
  in it. The window is not modal and is a top-level one, so it can be
  dragged next to the plot and left there: mask a pixel, watch the
  stream redraw without it, mask the next.

  Each board's grid carries a quick entry as well, taking the same
  `12, 40-43` syntax as the "TDC memory" box, for when the hot pixels
  are already known and hunting for them in a grid of 256 is the slow
  way. "Clear all" in the window does what "Reset Mask" does on the tab.

  The check boxes are the same objects as before, in the same order, so
  the preset-mask and reset paths address pixel `i` as item `i` exactly
  as they did.

### Removed

- Firmware version 2208. It read every pixel out on its own rather than
  through 64 four-pixel TDCs, so it shared none of the structure the
  rest of the package is built around, and it had been superseded by
  2212 for long enough that the code paths were no longer exercised. The
  "Firmware version" box on every tab now offers `2212b` and `2212s`
  only, and `unpack_bin` raises a `ValueError` naming the versions it
  handles rather than falling through on anything else.

  The 2208 branch of `sen_pop` had in fact been broken for some time and
  could not have produced a plot: `number_of_cycles` counted the `-2`
  end-of-cycle markers that only firmware 2212 inserts, indexing a
  one-dimensional row as if it were the 2212 matrix and raising, while
  `acq_window_length` read the second timestamp slot of every pixel
  instead of the length of the window. Both are gone with the branch.

### Fixed

- Closing the window no longer poisons the next run. Started from an
  interpreter that outlives the call - an IPython kernel, the VS Code
  interactive window, a Spyder console - the application ran once and
  then took the kernel down on the second start, with no traceback.

  Two causes, both in `main.py`. `main()` built a *new* `QApplication`
  on every call, and a second one in a single process is fatal in Qt;
  and it held the application and the window in locals, so returning
  dropped them and destroyed the two in an order Qt does not survive.
  Both now live in module globals, and an existing `QApplication` is
  reused. A previous window is closed properly rather than collected,
  and the event loop is only entered when something else is not already
  running one - a session with `%gui qt` on gets its window without
  `main()` blocking the prompt.

  `closeEvent` used to call `QApplication.quit()`. From a terminal that
  changed nothing, since closing the last window ends the loop anyway,
  but in a kernel it tore down the `QApplication` the session was still
  holding. It now stops what the tabs left running instead: the refresh
  timer each plotting tab starts with its stream and none of them
  stopped, the pixel mask window, the directory sweep behind "Both
  boards in step", and the Synchronization tab's acquisition thread -
  which, having no flag to set in the middle of a socket conversation,
  is given two seconds and then cut short rather than destroyed while
  running, which aborts the process outright.

  Modelled on `dapkel-rtp`, which had already met this and written the
  reasoning down.

- The combo and spin boxes of the "Full Sensor" control column are the
  size they are on every other tab: 100 px wide with a fixed size
  policy, rather than 80 px and `Expanding`. Expanding made them
  stretch across the column as the window widened, so the same four
  settings were a different shape on this tab than on "Online plot".
  The rule the `.ui`-built tabs follow is now stated once, as
  `size_like_ui_tabs()`. Three tabs are generated from `.ui` files and
  two are built in code, and the `.ui` files cannot import a shared
  constant, so this kind of drift is structural rather than an
  oversight - one set of geometry rules for all five tabs is still to
  be done.

- The navigation toolbar no longer folds its cursor readout away when
  the window is narrow. A `QToolBar` squeezed below its contents hides
  them behind an overflow button rather than forcing its parent wider -
  its own `minimumSizeHint` is barely wider than that button - and the
  readout, being the widest item and empty until the cursor reaches the
  axes, was the first to go. It is the quickest way to tell which pixel
  a peak belongs to, so the canvas now carries a minimum width measured
  from what the toolbar and a full reading actually need.

  That minimum reaches the window only because of the next two items;
  on its own it was swallowed on the way up.

- `mainwindow.py` no longer tries to install a second `QGridLayout` on
  the "Online plot" tab, which already brings its own. Qt refused it
  with a warning and the layout was never used, but the tab was left
  reporting a minimum size that was neither its layout's nor anything
  else's, so the plot could be squeezed until the toolbar collapsed.

- The `.ui` files carry a 500x425 placeholder widget where the plot
  canvas goes. Each tab builds the real canvas and rebinds the name, but
  the placeholder stayed in the grid layout, and its minimum size alone
  decided how large three of the tabs had to open. Taking it out drops
  the "Single Pixel Histogram" tab from 502 px to 317 and "MZI" from 570
  to 380.

- The "Synchronization" tab is laid out in two columns - what is set
  before a run on the left, what is watched while it runs on the right -
  rather than one stack of six group boxes 830 px tall. It was the
  tallest thing in the application and so decided how tall the window
  opened; it is now 531.

- Single-pixel histogram: an unrecognized firmware version printed to
  the console and called `sys.exit()` from inside the plotting, taking
  the whole application down with it. The version is now rejected by
  `unpack_bin`, and the tab reports it in the same error box it already
  used for unreadable files - which also catches the `ValueError` raised
  when the number of timestamps does not match the file, previously
  propagating uncaught.

## [1.3.1] - 2026-08-30

Fixes the 1.3.0 executable, which could not start.

### Fixed

- `matplotlib` capped below 3.11 in `pyproject.toml` and `requirements.txt`.
  Matplotlib 3.11 folded `matplotlib/style/core.py` into
  `matplotlib/style/__init__.py`, removing the `matplotlib.style.core`
  submodule. mplcyberpunk 0.7.6 - the newest release, and unbounded on
  matplotlib in its own metadata - calls
  `mpl.style.core.read_style_directory()` while being imported, so an
  unpinned install pairs the two and the app dies at startup with
  "module 'matplotlib.style' has no attribute 'core'".

  This only ever showed up in the released executable: the dependency is
  resolved fresh in CI, which picked up 3.11.1, while a development
  machine keeps whatever older matplotlib it already had. Lift the cap
  once mplcyberpunk supports matplotlib 3.11.

## [1.3.0] - 2026-06-24

New "Full Sensor" tab, PyInstaller packaging improvements, MZI tab fixes.

### Added

- "Full Sensor" tab (`linospad2_dual_tab.py`, `plot_figure_dual.py`): plots
  both halves of the LinoSPAD2 sensor simultaneously (512 pixels on the
  x-axis). Includes two independent browse paths and motherboard selectors,
  shared daughterboard/firmware/timestamps controls, and split pixel-mask
  scroll areas (one per board). A dashed boundary line is always drawn at
  x = 255.5. Pixel-address correction is applied silently to board 2.

- "Absolute timestamps" check box on the "Online plot" tab. Data files
  collected with absolute timestamps carry two extra 32-bit words at the
  start of every acquisition cycle (lower and higher halves of the 64-bit
  counter); without accounting for them the data are reshaped misaligned
  and the sensor population is plotted wrong. `unpack_bin` and `sen_pop`
  gained an `absolute_timestamps` argument that cuts those words before
  unpacking, mirroring
  `daplis.functions.unpack.unpack_binary_data_with_absolute_timestamps`.
  On the "Full Sensor" tab the absolute timestamps are always unpacked -
  they are needed to synchronize the two boards, so the data always hold
  them - and no check box is exposed, same as for the pixel-address
  correction.

- `unpack_bin`: file-length sanity check that raises a `ValueError` naming
  the "Absolute timestamps" check box when the setting does not match the
  data. Previously, reading data without absolute timestamps while the
  option was on produced a silently misaligned plot rather than an error.

- `mplcyberpunk` added to `pyproject.toml` runtime dependencies, and to
  `requirements.txt`, where it was missing.

- `.github/workflows/build-release.yml`: every push to `main` (and manual
  `workflow_dispatch`) builds the Windows executable and publishes it as a
  GitHub release, tagged `v<version>-build.<run number>` so each build is
  distinct, with the version in the exe name. Ported from `dapkel-rtp`.

- `tools/check_version.py`: build gate that fails the release when
  `daplis_rtp.__version__` and the newest numbered `CHANGELOG.md` section
  disagree. The version otherwise surfaces only in a release tag, where
  nobody proof-reads it.

- `daplis_rtp.__version__`, now the single source of the version.
  `pyproject.toml` declares `dynamic = ["version"]` and reads it from
  there instead of carrying its own literal, so the package, the app and
  the CHANGELOG cannot drift apart.

### Changed

- `os.chdir()` calls replaced with absolute-path `glob` across all tabs
  (`live_timestamps_tab.py`, `MZI_tab.py`, `single_pix_hist_tab.py`) and
  `calibrate.py`. This makes the app work correctly when frozen by
  PyInstaller.

- `calibrate.py`: removed `pandas` dependency; calibration matrix is now
  saved with `numpy.savetxt`. `calibrate_load` updated to match the new
  headerless CSV format.

- `setuptools` removed from runtime dependencies in `pyproject.toml`
  (build-only tool, not needed at runtime).

- `main.spec`: renamed output executable from `main` to `daplis-rtp`. The
  file is now tracked by git (`.gitignore` excepts it from `*.spec`) so
  that CI can build from it. No `hiddenimports` or `excludes` are set:
  `mplcyberpunk` is a plain import that PyInstaller finds on its own, and
  `pandas`/`IPython`/`tkinter` never enter the bundle in the first place,
  so excluding them saves nothing. The exe is ~196 MB, almost all of it
  PyQt5, matplotlib and numpy.

- MZI tab x-axis changed from file-count index to elapsed time in seconds
  (derived from file creation timestamps).

- "Online plot" and "Full Sensor" tabs: the two x-limit sliders are now
  spin boxes taking the pixel number directly - 0-255 on "Online plot",
  0-511 on "Full Sensor", which spans both sensor halves. A slider could
  not be placed on an exact pixel; a typed number can. Keyboard tracking
  is off, so a value is committed on Enter or focus loss rather than on
  every keystroke, which would otherwise clamp a half-typed number
  against the other limit.

- MZI tab: the two sliders (lower x, lower y) are replaced by four
  fields - lower and upper, for x and for y. Each takes a float in plain
  or scientific notation ('10e3'), with no range cap, and an empty field
  means that edge autoscales. Clearing a field returns that edge to
  autoscale rather than leaving it at its last value. Both y-axes
  continue to share limits so the two traces stay comparable.

- "Online plot" and "Full Sensor" tabs: the data-read error dialog now
  mentions the absolute-timestamps setting and shows the underlying
  exception message as detailed text.

- "Full Sensor" tab: data files without absolute timestamps now raise a
  clear error instead of being plotted misaligned.

- MZI tab y-scale fixed: the upper limit no longer locks at a historical
  maximum. Both axes now autoscale each frame and share a common upper
  limit.

### Fixed

- All streaming tabs (`live_timestamps_tab.py`, `MZI_tab.py`,
  `linospad2_dual_tab.py`): catching `FileNotFoundError` and `OSError` in
  the inner data-read block so that removing data files while the stream is
  running shows an error dialog and stops the stream instead of crashing.

- `MZI_tab.py`: outer exception was catching `(IndexError, FileNotFoundError)`
  instead of `ValueError`, so an empty folder would crash rather than show
  the "no data files" dialog.

- `single_pix_hist_tab.py`: added `return` after the empty-folder error
  dialog to prevent a subsequent `UnboundLocalError` on `last_file`; wrapped
  the `plot_hist` call in its own `try/except` for the race-condition case
  where a file disappears between the directory scan and the read.

## [1.2.0] - 2025-06-17 #TODO

Flexibility and crash avoidance.

### Added

- Raw '.ui' files to the '.py' with the GUI tab information.

- Option for user input for the daughterboard and motherboard numbers.

### Changed

- Error check when no mask for the requested board combination is found. Does not crash now.

## [1.1.4] - 2025-05-04

Fixes (again).

### Changed

- Updated MANIFEST.in (again) so that it includes the '.txt' files to pypi.

## [1.1.3] - 2025-05-04

Fixes.

### Changed

- Updated MANIFEST.in so that it includes the '.txt' files to pypi.

## [1.1.2] - 2025-05-04

Mask call update.

### Changed

- How the '.txt' files with masks are called. No hard reversing on the path tree, works with every way of installation (manual, from github, pypi, distributable).

## [1.1.1] - 2025-01-28

Setup-file update.

### Changed

- Updated README with instruction on how to install and run the program.

- Added requirement for the 'qdarkstyle' package to the 'pyproject.toml' 
file.

## [1.1.0] - 2025-01-28

Adapted the package for installation via 'pip install'. Now, after
the package is installed, one can run it via 'daplis-rtp' command.

### Added

- Requirement for the 'qdarkstyle' package for dark-themed GUI.

### Changed

- The 'pyproject.toml' setup file: added a link to the 'main.py' so that
after installation the program can be run via 'daplis-rtp' from the 
terminal/command line.

### Removed

- The '.ui' files since they were changed to '.py'. Also, removed the
back-up copies of the second tab (single pixel histogram) UI.

## [1.0.1] - 2025-01-26

Minor fixes in all tabs, specifically regarding the canvas widget.

### Changed

- Fontsize in the plot widget in all three tabs.

## [1.0.0] - 2025-01-24

First official release to PyPI.

### Added

- This changelog.

### Changed

- Installation files: installation is now done using the 'pyproject.toml' 
file instead of 'setup.py'.

## [0.9.9] - 2025-01-24

Preparing the package for the official release

### Added

- Two boxes for the two top-most pixels (looked for automatically) in 
the live-timestamps tab for easier alignment.

### Fixed

### Changed

- The name of the package.

- The layout and size of the boxes in all tabs.

- The single-pixel-histogram tab to match its style to the other
two tabs.

### Removed

- Unused "mask_NL11_all.txt".
- Unused masks in "params/masks/old".
- Test leftovers in "tests/test_data/results".
