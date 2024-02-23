"""Module for collecting number of timestamps in each pixel.

Works with firmware versions 2208 and 2212.

The following functions are provided.

    * sen-pop - collects the number of timestamps in each pixel for the
    data file provided and returns it as an array.

"""

import numpy as np
from LinoSPAD2app.functions.unpack import unpack_bin


def sen_pop(
    file,
    board_number,
    fw_ver,
    timestamps: int = 512,
    pix_add_fix: bool = False,
):
    """Collect number of timestamps in each pixel.

    The output is used for plotting the sensor population. Works
    with firmware versions 2208 and 2212.

    Parameters
    ----------
    file : str
        Address of the data file.
    board_number : str
        LinoSPAD2 daughterboard number.
    fw_ver : str
        LinoSPAD2 firmware version.
    timestamps : int, optional
        Number of timestamps per acquisition cycle per pixel/TDC, by
        default 512.

    Returns
    -------
    valid_per_pixel: array-like
        Array of number of timestamps in each pixel.
    """
    if fw_ver == "2208":
        data = unpack_bin(file, board_number, fw_ver, timestamps)
        valid_per_pixel = np.zeros(256)
        for i in range(len(data)):
            valid_per_pixel[i] = len(np.where(data[i] > 0)[0])
    elif fw_ver[:-1] == "2212":
        data = unpack_bin(file, board_number, fw_ver, timestamps)
        valid_per_pixel = np.zeros(256)
        if fw_ver == "2212s":
            pix_coor = np.arange(256).reshape(4, 64).T
        elif fw_ver == "2212b":
            pix_coor = np.arange(256).reshape(64, 4)
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

    return valid_per_pixel
