"""Module with scripts for unpacking data from LinoSPAD2.

This file can also be imported as a module and contains the following
functions:

    * unpack_bin - function for unpacking data from LinoSPAD2. Utilizes
    the numpy library to speed up the process. Works with firmware
    versions 2208 and 2212.

"""

import os

import numpy as np

from daplis_rtp.functions.calibrate import calibrate_load


def unpack_bin(file, board_number: str, fw_ver: str, timestamps: int = 512):
    """Unpack binary data from LinoSPAD2.

    Unpacks binary-encoded .dat files with data from LinoSPAD2 into a
    matrix with dimensions [256, # of timestamps*cycles] for firwmare
    2208, or [64, # of timestamps*cycles + cycles, 2] for firmware
    version 2212 where the third axis contains the timestamp and a pixel
    coordinate in the particular TDC.

    Parameters
    ----------
    file : str
        Name of the '.dat' data file to unpack.
    board_number : str
        LinoSPAD2 daugtherboard number.
    fw_ver : str
        LinoSPAD2 firmware version.
    timestamps : int, optional
        Number of timetstamps per pixel (firmware 2208) or per TDC
        firmware 2212 and per acquisition cycle, by default 512.

    Returns
    -------
    data_matrix: ndarray
        Matrix of timestamps in each pixel (firmware 2208) or in each
        TDC with pixel number in that TDC (firmware 2212).

    Raises
    ------
    FileNotFoundError
        Raised if no calibration data were found.
    """
    # read data by 32 bit words
    rawFile = np.fromfile(file, dtype=np.uint32)
    # lowest 28 bits are the timestamp; convert to longlong, int is not enough
    data_t = (rawFile & 0xFFFFFFF).astype(np.longlong) * 17.857
    # mask nonvalid data with '-1'
    data_t[np.where(rawFile < 0x80000000)] = -1
    # number of acquisition cycles
    if fw_ver == "2208":
        cycles = int(len(data_t) / timestamps / 256)

        data_matrix = (
            data_t.reshape(cycles, 256, timestamps)
            .transpose((1, 0, 2))
            .reshape(256, timestamps * cycles)
        )
    # firmware 2212 additions
    if fw_ver[:-1] == "2212":
        data_p = ((rawFile >> 28) & 0x3).astype(np.longlong)
        cycles = int(len(data_t) / timestamps / 65)
        data_matrix_p = (
            data_p.reshape(cycles, 65, timestamps)
            .transpose((1, 0, 2))
            .reshape(65, timestamps * cycles)
        )

        data_matrix_t = (
            data_t.reshape(cycles, 65, timestamps)
            .transpose((1, 0, 2))
            .reshape(65, timestamps * cycles)
        )

        # cut the 65th TDC that does not hold any actual data from pixels
        data_matrix_p = data_matrix_p[:-1]
        data_matrix_t = data_matrix_t[:-1]
        # insert '-2' at the end of each cycle
        data_matrix_p = np.insert(
            data_matrix_p,
            np.linspace(timestamps, cycles * timestamps, cycles).astype(
                np.longlong
            ),
            -2,
            1,
        )

        data_matrix_t = np.insert(
            data_matrix_t,
            np.linspace(timestamps, cycles * timestamps, cycles).astype(
                np.longlong
            ),
            -2,
            1,
        )

        # combine both matrices into a single one, where each cell holds pix
        # coordinates in the TDC and the timestamp
        data_matrix = np.stack((data_matrix_p, data_matrix_t), axis=2).astype(
            np.longlong
        )

    if fw_ver == "2212s":
        pix_coor = np.arange(256).reshape(4, 64).T
    elif fw_ver == "2212b":
        pix_coor = np.arange(256).reshape(64, 4)
    else:
        pass

    # # path to the current script, two levels up (the script itself is
    # # in the path) and one level down to the calibration data
    # path_calib_data = (
    #     os.path.realpath(__file__) + "../../.." + "/params/calibration_data"
    # )

    # try:
    #     cal_mat = calibrate_load(path_calib_data, board_number)
    # except FileNotFoundError:
    #     raise FileNotFoundError(
    #         "No .csv file with the calibration"
    #         "data was found, check the path "
    #         "or run the calibration."
    #     )

    # if fw_ver == "2208":
    #     for i in range(256):
    #         ind = np.where(data_matrix[i] >= 0)[0]
    #         data_matrix[i, ind] = (
    #             data_matrix[i, ind] - data_matrix[i, ind] % 140
    #         ) * 17.857 + cal_mat[i, (data_matrix[i, ind] % 140)]

    # elif fw_ver[:-1] == "2212":
    #     for i in range(256):
    #         # transform pixel number to TDC number and pixel coordinates in
    #         # that TDC (from 0 to 3)
    #         tdc, pix = np.argwhere(pix_coor == i)[0]
    #         # find data from that pixel
    #         ind = np.where(data_matrix[tdc].T[0] == pix)[0]
    #         # cut non-valid timestamps ('-1's)
    #         ind = ind[np.where(data_matrix[tdc].T[1][ind] >= 0)[0]]
    #         if not np.any(ind):
    #             continue
    #         # apply calibration
    #         data_matrix[tdc].T[1][ind] = (
    #             data_matrix[tdc].T[1][ind] - data_matrix[tdc].T[1][ind] % 140
    #         ) * 17.857 + cal_mat[i, (data_matrix[tdc].T[1][ind] % 140)]

    return data_matrix
