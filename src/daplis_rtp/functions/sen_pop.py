"""Module for collecting number of timestamps in each pixel.

Works with firmware versions 2212b and 2212s.

The following functions are provided.

    * sen-pop - collects the number of timestamps in each pixel for the
    data file provided and returns it as an array.

"""

import numpy as np

from daplis_rtp.functions.tdc_occupancy import slot_occupancy
from daplis_rtp.functions.unpack import unpack_bin


def sen_pop(
    file,
    board_number,
    fw_ver,
    timestamps: int = 512,
    pix_add_fix: bool = False,
    absolute_timestamps: bool = False,
    return_occupancy: bool = False,
):
    """Collect number of timestamps in each pixel.

    The output is used for plotting the sensor population. Works
    with firmware versions 2212b and 2212s.

    Parameters
    ----------
    file : str
        Address of the data file.
    board_number : str
        LinoSPAD2 daughterboard number.
    fw_ver : str
        LinoSPAD2 firmware version, '2212b' or '2212s'.
    timestamps : int, optional
        Number of timestamps per TDC per acquisition cycle, by default
        512.
    pix_add_fix : bool, optional
        Switch for correcting the pixel addressing of the sensor half,
        by default False.
    absolute_timestamps : bool, optional
        Indicator for data files collected with absolute timestamps, by
        default False.
    return_occupancy : bool, optional
        Also return how much of the TDC slot memory the file used, as
        an 'Occupancy'. Computed from the same unpacked matrix as the
        rates, so it costs no extra read of the file. By default False.

    Returns
    -------
    rates : array-like
        Photon rate in each pixel, in Hz.
    occupancy : Occupancy
        Only when 'return_occupancy' is set: slots used per TDC per
        acquisition cycle. See 'daplis_rtp.functions.tdc_occupancy'.
    """
    # 'unpack_bin' rejects any firmware version other than the two
    data = unpack_bin(
        file, board_number, fw_ver, timestamps, absolute_timestamps
    )
    pix_coor = (
        np.arange(256).reshape(4, 64).T
        if fw_ver == "2212s"
        else np.arange(256).reshape(64, 4)
    )

    # One pass over the matrix rather than 256. This used to be a loop
    # over every pixel that re-derived the pixel's TDC with
    # 'np.argwhere(pix_coor == i)' - a fresh search of all 256 entries -
    # and then made two more passes over that TDC's column to find the
    # pixel's own timestamps. It ran on every frame of a stream that
    # polls ten times a second.
    #
    # 'pix_coor[tdc, coordinate]' is the same lookup the loop did, read
    # forwards instead of searched backwards, so every entry is turned
    # into the pixel number it belongs to in one indexing operation and
    # counted with 'bincount'.
    coordinates = data[:, :, 0]
    stamps = data[:, :, 1]
    # A coordinate is 0-3 for real data; -1 marks an empty slot and -2 a
    # cycle boundary, and a non-positive timestamp is not a photon.
    recorded = (coordinates >= 0) & (coordinates < 4) & (stamps > 0)
    tdcs = np.broadcast_to(
        np.arange(data.shape[0])[:, None], coordinates.shape
    )
    pixels = pix_coor[tdcs[recorded], coordinates[recorded]]
    valid_per_pixel = np.bincount(pixels, minlength=256).astype(float)

    if pix_add_fix is True:
        fix = np.zeros(len(valid_per_pixel))
        fix[:128] = valid_per_pixel[128:]
        fix[128:] = np.flip(valid_per_pixel[:128])
        valid_per_pixel = fix
        del fix

    acq_window_length = stamps.max() * 1e-12
    number_of_cycles = np.count_nonzero(coordinates[0] == -2)

    rates = valid_per_pixel / acq_window_length / number_of_cycles

    if return_occupancy:
        # From the matrix already in hand: one comparison per TDC, no
        # second pass over the file. Note that the TDC indices of the
        # result are the ones the board reads out, so a caller that
        # asked for 'pix_add_fix' must map its pixels through
        # 'tdc_occupancy.pixel_to_tdc_map' with the same flag.
        return rates, slot_occupancy(data, fw_ver, timestamps)

    return rates
