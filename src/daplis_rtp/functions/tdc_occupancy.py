"""How much of the TDC slot memory an acquisition actually uses.

Each TDC of LinoSPAD2 holds 'timestamps' slots per acquisition cycle,
shared by the four pixels wired to it (firmware 2212b: TDC t serves
pixels 4t..4t+3; 2212s: pixels t, t+64, t+128, t+192). Once those slots
are full the rest of the cycle is dropped on the floor, and nothing in
the data file says so - a saturated file is exactly the same size as a
healthy one, it just stops part way through every window. The damage is
rate-dependent and time-correlated: the brighter of a pair of boards
truncates earlier than the dimmer one, so a cross-board reduction of
such a run silently compares different slices of time.

Hence this module. It counts, per TDC and per cycle, how many slots
were used, and turns that into the two numbers worth looking at before
a long acquisition is started:

* the busiest TDC among the pixels actually being measured, as a
  fraction of its slots - "TDC 36 at 36 % of 150" - which says whether
  *this* measurement is truncated;
* the worst TDC anywhere on the sensor, which says whether the board is
  near the edge at all.

Both are needed. A per-sensor average hides a single saturating TDC,
and the sensor-wide maximum is usually a hot pixel nobody is measuring
- on the B7d run of 2026.09.07, TDC 17 saturated in 848 of 1000 cycles
while TDC 36 and TDC 39, which carried the pixels of interest, used 54
and 25 of their 150 slots.

The one case where a hot pixel does matter is when it shares a TDC with
a pixel of interest: the four pixels compete for the same slots, so the
hot one eats the memory the signal needs. That is why the TDCs of
interest are taken as "every TDC holding at least one pixel of
interest", counting all of that TDC's traffic - dropping the hot pixel
would hide exactly the case that hurts.

Nothing here reads a file: the caller hands over the unpacked matrix it
already has, so the check costs one comparison and a couple of small
fancy-indexed reads on top of the unpacking that has happened anyway.

"""

import numpy as np

from daplis_rtp.functions.unpack import FW_VERSIONS

# A TDC that fills up in more than this fraction of the cycles is
# losing data in a way that shows up in the reduction, not just in the
# tail of the distribution.
SAT_WARN_FRACTION = 0.01

# Below this fraction of the slots there is room for the rate to drift
# up during a long run; above it, the setting is cutting things fine.
HEADROOM_WARN_FRACTION = 0.7

# What to multiply the needed slots by when suggesting a setting. The
# cost of too large a 'timestamps' is file size and unpacking time; the
# cost of too small a one is data truncated without a trace.
HEADROOM_FACTOR = 1.3

# Suggestions are rounded up to a multiple of this, so that they do not
# read as more precise than they are.
SUGGESTION_STEP = 50


def pixel_to_tdc_map(fw_ver: str, pix_add_fix: bool = False):
    """Return the TDC index of every pixel, as a 256-long array.

    Indexed by pixel number *as plotted*, which is not the pixel number
    the board reads out: with 'pix_add_fix' the sensor half is
    re-addressed for display exactly as 'sen_pop' does it, so the
    x-axis of the plot can be used directly to pick TDCs.

    Parameters
    ----------
    fw_ver : str
        LinoSPAD2 firmware version, '2212b' or '2212s'.
    pix_add_fix : bool, optional
        Whether the pixel addressing of the sensor half is corrected
        for display, by default False.

    Returns
    -------
    ndarray
        'tdc_of_pixel[plotted_pixel]' -> TDC index.

    Raises
    ------
    ValueError
        Raised if the firmware version is not one of 'FW_VERSIONS'.
    """
    if fw_ver not in FW_VERSIONS:
        raise ValueError(
            "Unknown firmware version '{}'; expected one of {}.".format(
                fw_ver, ", ".join(FW_VERSIONS)
            )
        )

    # Plotted pixel -> the pixel number the board actually read out.
    # 'sen_pop' builds the corrected array as
    #     fix[:128] = raw[128:]; fix[128:] = flip(raw[:128])
    # so plotted 0..127 are raw 128..255, and plotted 128..255 are raw
    # 127..0.
    readout = np.arange(256)
    if pix_add_fix:
        readout = np.concatenate([np.arange(128, 256), np.arange(127, -1, -1)])

    if fw_ver == "2212s":
        # pix_coor = np.arange(256).reshape(4, 64).T: pixels 64 apart
        return readout % 64
    # 2212b: pix_coor = np.arange(256).reshape(64, 4), four consecutive
    # pixels per TDC
    return readout // 4


def parse_pixel_spec(text: str, n_pixels: int = 256):
    """Read a pixel list like '36, 40-43, 100' into an index array.

    Whitespace, commas and semicolons all separate entries; 'a-b' and
    'a:b' are inclusive ranges. Returns an empty array for empty input.

    Raises
    ------
    ValueError
        If an entry is neither a number nor a range, or lies outside
        0..n_pixels-1.
    """
    pixels = []
    for entry in text.replace(";", ",").replace(" ", ",").split(","):
        entry = entry.strip()
        if not entry:
            continue
        for separator in ("-", ":"):
            if separator in entry:
                low, _, high = entry.partition(separator)
                try:
                    low, high = int(low), int(high)
                except ValueError:
                    raise ValueError(
                        "'{}' is not a pixel or a range of pixels".format(
                            entry
                        )
                    )
                if low > high:
                    low, high = high, low
                pixels.extend(range(low, high + 1))
                break
        else:
            try:
                pixels.append(int(entry))
            except ValueError:
                raise ValueError(
                    "'{}' is not a pixel or a range of pixels".format(entry)
                )

    outside = [p for p in pixels if not 0 <= p < n_pixels]
    if outside:
        raise ValueError(
            "pixel {} is outside 0-{}".format(outside[0], n_pixels - 1)
        )
    return np.unique(np.asarray(pixels, dtype=int))


class Occupancy:
    """Slot use of every TDC, cycle by cycle.

    Attributes
    ----------
    timestamps : int
        Slots per TDC per acquisition cycle - the setting under test.
    cycles : int
        Acquisition cycles in the file.
    used : ndarray
        Slots used, shape (n_tdc, cycles).
    median_used, max_used : ndarray
        Per TDC, over the cycles. The median is the headroom figure; the
        maximum is what the setting has to cover.
    sat_fraction : ndarray
        Per TDC, the fraction of cycles that used every slot - i.e. in
        which the rest of the window was thrown away.
    fill_time : ndarray
        Per TDC, the median time in picoseconds at which it filled up,
        over the cycles in which it did; NaN for TDCs that never did.
    window : float
        Length of the timestamping window in picoseconds, taken as the
        latest timestamp seen in a cycle that did *not* fill up. NaN
        when every cycle of every TDC filled up, in which case the file
        holds no evidence of how long the window really was.
    """

    def __init__(
        self, timestamps, cycles, used, sat_fraction, fill_time, window
    ):
        self.timestamps = timestamps
        self.cycles = cycles
        self.used = used
        self.sat_fraction = sat_fraction
        self.median_used = np.median(used, axis=1)
        self.max_used = used.max(axis=1)
        self.fill_time = fill_time
        self.window = window

    @property
    def n_tdc(self):
        return len(self.used)


def slot_occupancy(data, fw_ver: str, timestamps: int):
    """Count the slots each TDC used in each acquisition cycle.

    Parameters
    ----------
    data : ndarray
        The matrix returned by 'unpack_bin':
        (64, cycles * (timestamps + 1), 2), where the extra column per
        cycle holds the '-2' end-of-cycle marker.
    fw_ver : str
        LinoSPAD2 firmware version, '2212b' or '2212s'. Only checked
        here - the slot bookkeeping is the same for both, since they
        differ in which four pixels share a TDC and not in how many.
    timestamps : int
        Slots per TDC per cycle - the same value the data were unpacked
        with.

    Returns
    -------
    Occupancy

    Raises
    ------
    ValueError
        If the firmware version is not one of 'FW_VERSIONS', or if
        'data' does not divide into whole cycles of 'timestamps' slots,
        which means it was unpacked with a different setting than the
        one passed here.
    """
    if fw_ver not in FW_VERSIONS:
        raise ValueError(
            "Unknown firmware version '{}'; expected one of {}.".format(
                fw_ver, ", ".join(FW_VERSIONS)
            )
        )

    # 'unpack_bin' inserts one '-2' marker after each cycle. Comparing
    # before reshaping keeps the copy a boolean one - the timestamps
    # themselves are 64-bit and the matrix is large.
    stride = timestamps + 1
    valid = data[:, :, 1] >= 0
    values = data[:, :, 1]

    n_tdc, length = valid.shape
    if length % stride:
        raise ValueError(
            "data of {} words per TDC do not divide into cycles of {} "
            "slots - check the 'Timestamps' setting".format(length, stride)
        )
    cycles = length // stride

    # Slots used, cycle by cycle. The marker column is sliced off rather
    # than relied upon to be negative.
    used = (
        valid.reshape(n_tdc, cycles, stride)[:, :, :timestamps]
        .sum(axis=2)
        .astype(np.int64)
    )
    saturated = used == timestamps
    sat_fraction = saturated.mean(axis=1)

    # A TDC fills its slots in the order the photons arrive, so the last
    # used slot of a cycle carries the time at which that TDC stopped
    # listening. Only n_tdc x cycles values are wanted, so they are read
    # straight out of the flat row instead of reshaping the timestamps.
    rows = np.arange(n_tdc)[:, None]
    cols = np.arange(cycles)[None, :] * stride + np.maximum(used - 1, 0)
    last_used = np.where(used > 0, values[rows, cols], -1)

    # The window is only visible in cycles that did not fill up: a
    # saturated cycle stops early, so its last timestamp measures the
    # truncation and not the window.
    window = np.nan if saturated.all() else float(last_used[~saturated].max())

    # Where a TDC did fill up, how far into the window it got
    fill_time = np.full(n_tdc, np.nan)
    for tdc in np.flatnonzero(sat_fraction > 0):
        fill_time[tdc] = np.median(last_used[tdc][saturated[tdc]])

    return Occupancy(timestamps, cycles, used, sat_fraction, fill_time, window)


class OccupancySummary:
    """The busiest TDC of a set, and what to do about it.

    Attributes
    ----------
    tdc : int or None
        The TDC picked out of the set: the one that saturates in most
        cycles, or, when none of them saturate, the one using most of
        its slots. None when the set is empty.
    median_used, max_used, sat_fraction : float
        That TDC's figures, from 'Occupancy'.
    fraction : float
        'median_used / timestamps' - the headroom figure to display.
    state : str
        'ok', 'warn' (running close to the limit) or 'bad' (losing
        data), by 'HEADROOM_WARN_FRACTION' and 'SAT_WARN_FRACTION'.
    suggested_timestamps : int or None
        A setting that would hold the traffic measured here, with
        'HEADROOM_FACTOR' to spare. None when the set saturated
        throughout, since the file then shows neither the real rate nor
        the length of the window.
    n_tdc : int
        How many TDCs the set holds - 64 means nothing was narrowed
        down and the figure is the sensor-wide one.
    """

    def __init__(self, occupancy, tdcs):
        self.timestamps = occupancy.timestamps
        self.cycles = occupancy.cycles
        tdcs = np.unique(np.asarray(tdcs, dtype=int))
        self.n_tdc = len(tdcs)

        if not self.n_tdc:
            self.tdc = None
            self.median_used = 0.0
            self.max_used = 0
            self.sat_fraction = 0.0
            self.fraction = 0.0
            self.state = "ok"
            self.suggested_timestamps = None
            return

        # Saturation first: a TDC that throws data away outranks a
        # merely busy one even if its median is lower, which is what a
        # bursty source looks like.
        order = np.lexsort(
            (occupancy.median_used[tdcs], occupancy.sat_fraction[tdcs])
        )
        self.tdc = int(tdcs[order[-1]])

        self.median_used = float(occupancy.median_used[self.tdc])
        self.max_used = int(occupancy.max_used[self.tdc])
        self.sat_fraction = float(occupancy.sat_fraction[self.tdc])
        self.fraction = self.median_used / occupancy.timestamps

        if self.sat_fraction > SAT_WARN_FRACTION:
            self.state = "bad"
        elif self.sat_fraction > 0 or self.fraction > HEADROOM_WARN_FRACTION:
            self.state = "warn"
        else:
            self.state = "ok"

        self.suggested_timestamps = _suggest(occupancy, tdcs)


def _suggest(occupancy, tdcs):
    """Slots needed to hold the traffic of 'tdcs', with headroom.

    For a TDC that never filled up, the traffic is simply the busiest
    cycle seen. For one that did, the count is truncated, so the rate is
    recovered from *when* it filled up instead: filling 'timestamps'
    slots in 'fill_time' out of a window of 'window' means the whole
    window holds 'timestamps * window / fill_time'. That is the same
    arithmetic as the rule of thumb

        slots per TDC per cycle = 4 * rate per pixel * window

    only measured rather than estimated - it is what says the 1000-slot
    laser run of 2026.09.04 needed about 1380.

    """
    needed = 0.0
    for tdc in tdcs:
        if occupancy.sat_fraction[tdc] <= 0:
            needed = max(needed, float(occupancy.max_used[tdc]))
            continue
        fill_time = occupancy.fill_time[tdc]
        # Saturated, and either no undamaged cycle to take the window
        # from or a TDC that was already full at the first timestamp
        if (
            not np.isfinite(occupancy.window)
            or not np.isfinite(fill_time)
            or fill_time <= 0
        ):
            return None
        needed = max(
            needed, occupancy.timestamps * occupancy.window / float(fill_time)
        )

    if needed <= 0:
        return None
    suggested = int(np.ceil(needed * HEADROOM_FACTOR / SUGGESTION_STEP))
    return max(SUGGESTION_STEP, suggested * SUGGESTION_STEP)
