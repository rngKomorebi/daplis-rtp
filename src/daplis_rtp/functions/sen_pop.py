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
    valid_per_pixel = np.zeros(256)
    for i in range(256):
        tdc, pix = np.argwhere(pix_coor == i)[0]
        ind = np.where(data[tdc].T[0] == pix)[0]
        ind1 = np.where(data[tdc].T[1][ind] > 0)[0]
        valid_per_pixel[i] += len(data[tdc].T[1][ind[ind1]])

    if pix_add_fix is True:
        fix = np.zeros(len(valid_per_pixel))
        fix[:128] = valid_per_pixel[128:]
        fix[128:] = np.flip(valid_per_pixel[:128])
        valid_per_pixel = fix
        del fix

    acq_window_length = np.max(data[:].T[1]) * 1e-12
    number_of_cycles = len(np.where(data[0].T[0] == -2)[0])

    rates = valid_per_pixel / acq_window_length / number_of_cycles

    if return_occupancy:
        # From the matrix already in hand: one comparison per TDC, no
        # second pass over the file. Note that the TDC indices of the
        # result are the ones the board reads out, so a caller that
        # asked for 'pix_add_fix' must map its pixels through
        # 'tdc_occupancy.pixel_to_tdc_map' with the same flag.
        return rates, slot_occupancy(data, fw_ver, timestamps)

    return rates
