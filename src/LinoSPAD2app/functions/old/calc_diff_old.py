""" Function for calculating timestamp differences for the given pair of
pixels.

This file can also be imported as a module and contains the following
functions:

    * calc_diff_2208 - calculate timestamp differences for a given
    pair of pixels. Returns an array of differences.
    
    * calc_diff_2212

"""

import numpy as np

def calc_diff(
    data_pair,
    timestamps: int = 512,
    range_left: float = -2.5e3,
    range_right: float = 2.5e3,
):
    """
    Function for calculating timestamp differences for a given pair of pixels.

    Parameters
    ----------
    data_pair : array-like
        Data from 2 pixels.
    timestamps : int, optional
        Number of timestamps per pixel per acquisition window. The default is
        512.
    range_left : float, optional
        Left limit for the timestamp differences. Values below that are not
        taken into account and the differences are not returned. The default
        is -2.5e3.
    range_right : float, optional
        Right limit for the timestamp differences. Values above that are not
        taken into account and the differences are not returned. The default
        is 2.5e3.

    Returns
    -------
    output : array-like
        An array of timestamp differences for the given pair of pixels.

    """

    timestamps_total = len(data_pair[0])

    output = []

    acq = 0  # number of acq cycle
    for j in range(timestamps_total):
        if j % timestamps == 0:
            acq = acq + 1  # next acq cycle
        if data_pair[0][j] == -1:
            continue
        for p in range(timestamps):
            n = timestamps * (acq - 1) + p
            if data_pair[1][n] == -1:
                continue
            else:
                delta = data_pair[0][j] - data_pair[1][n]
                if delta > range_right:
                    continue
                elif delta < range_left:
                    continue
                else:
                    output.append(delta)
    return output


def calc_diff_2212(data1, data2, cycle_ends, delta_window: float = 10e3):
    """Calculate timestamp differences for firmware 2212.

    Calculate timestamp differences for two given pixels and LinoSPAD2
    firmware version 2212b.

    Parameters
    ----------
    data1 : array-like
        Array of data from the first pixel of the pair for which
        timestamp differences are calculated.
    data2 : array-like
        Array of data from the second pixel of the pair for which
        timestamp differecnes are calculated.
    cycle_ends : array-like
        Array of positions of '-2's that indicate ends of cycles.
    delta_window : float, optional
        A width of a window in which the number of timestamp differences
        are counted. The default value is 10 ns. The default is 10e3.

    Returns
    -------
    deltas_out : list
        All timestamp differences found in a given time window for a
        given pair of pixels.

    """
    deltas_out = []

    for cyc in range(len(cycle_ends) - 1):
        data1_cycle = data1[cycle_ends[cyc] : cycle_ends[cyc + 1]]
        data2_cycle = data2[cycle_ends[cyc] : cycle_ends[cyc + 1]]

        # calculate delta t
        tmsp1 = data1_cycle[np.where(data1_cycle > 0)[0]]
        tmsp2 = data2_cycle[np.where(data2_cycle > 0)[0]]
        for t1 in tmsp1:
            # calculate all timestamp differences in the given cycle
            deltas = tmsp2 - t1
            # take values in the given delta t window only
            ind = np.where(np.abs(deltas) < delta_window)[0]
            deltas_out.extend(deltas[ind])

    return deltas_out