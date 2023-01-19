""" Function for calculating timestamp differences for the given pair of
pixels.

This file can also be imported as a module and contains the following
functions:

    * calculate differences - calculate timestamp differences for a given
    pair of pixels. Returns an array of differences.

"""


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
