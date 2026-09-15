"""Module with scripts for unpacking data from LinoSPAD2.

This file can also be imported as a module and contains the following
functions:

    * unpack_bin - function for unpacking data from LinoSPAD2. Utilizes
    the numpy library to speed up the process. Works with firmware
    versions 2212b and 2212s.

"""

import os

import numpy as np

# from daplis_rtp.functions.calibrate import calibrate_load

# Firmware versions the package handles. Both read the sensor out
# through 64 TDCs of four pixels each, differing only in which four:
# '2212b' takes them in blocks of four consecutive pixels, '2212s' in
# steps of 64. Firmware 2208, which read every pixel out on its own and
# so had no shared per-TDC memory, is no longer supported.
FW_VERSIONS = ("2212b", "2212s")


def unpack_bin(
    file,
    board_number: str,
    fw_ver: str,
    timestamps: int = 512,
    absolute_timestamps: bool = False,
):
    """Unpack binary data from LinoSPAD2.

    Unpacks binary-encoded .dat files with data from LinoSPAD2 into a
    matrix with dimensions [64, # of timestamps*cycles + cycles, 2],
    where the third axis contains the timestamp and a pixel coordinate
    in the particular TDC.

    Parameters
    ----------
    file : str
        Name of the '.dat' data file to unpack.
    board_number : str
        LinoSPAD2 daugtherboard number.
    fw_ver : str
        LinoSPAD2 firmware version, '2212b' or '2212s'.
    timestamps : int, optional
        Number of timestamps per TDC per acquisition cycle, by default
        512.
    absolute_timestamps : bool, optional
        Indicator for data files collected with absolute timestamps. In
        such files, each acquisition cycle is preceded by two 32-bit
        words holding the 64-bit absolute timestamp of the cycle; these
        words are cut here so that the rest of the data can be unpacked
        as usual. By default False.

    Returns
    -------
    data_matrix: ndarray
        Matrix of timestamps in each TDC, with the pixel number in that
        TDC alongside each of them.

    Raises
    ------
    ValueError
        Raised if the firmware version is not one of 'FW_VERSIONS', or
        if the file does not match the 'absolute_timestamps' setting.
    """
    if fw_ver not in FW_VERSIONS:
        raise ValueError(
            "Unknown firmware version '{}'; expected one of {}.".format(
                fw_ver, ", ".join(FW_VERSIONS)
            )
        )

    # read data by 32 bit words
    rawFile = np.fromfile(file, dtype=np.uint32)

    # Number of words with pixel data in a single acquisition cycle
    words_per_cycle = 65 * timestamps

    # Data files with absolute timestamps hold two extra 32-bit words at
    # the start of each acquisition cycle - the lower and the higher
    # parts of the 64-bit counter latched at the start of the cycle
    cycle_words = words_per_cycle + 2

    if absolute_timestamps:
        # The file size gives away data without absolute timestamps;
        # without this check such data would be plotted silently
        # misaligned instead of failing
        if (
            len(rawFile) % cycle_words != 0
            and len(rawFile) % words_per_cycle == 0
        ):
            raise ValueError(
                "The data file holds no absolute timestamps while "
                "'absolute_timestamps' is set."
            )
        cycles = len(rawFile) // cycle_words
        # Drop the trailing incomplete cycle, if any, then cut the first
        # two words of each cycle, leaving the pixel data only
        rawFile = (
            rawFile[: cycles * cycle_words]
            .reshape(cycles, cycle_words)[:, 2:]
            .reshape(-1)
        )
    elif (
        len(rawFile) % words_per_cycle != 0
        and len(rawFile) % cycle_words == 0
    ):
        raise ValueError(
            "The data file holds absolute timestamps while "
            "'absolute_timestamps' is not set."
        )

    # lowest 28 bits are the timestamp; convert to longlong, int is not enough
    data_t = (rawFile & 0xFFFFFFF).astype(np.longlong) * 17.857
    # mask nonvalid data with '-1'
    data_t[np.where(rawFile < 0x80000000)] = -1
    # bits 28 and 29 are the pixel's coordinate inside its TDC
    data_p = ((rawFile >> 28) & 0x3).astype(np.longlong)
    # number of acquisition cycles
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

    # pix_coor = (
    #     np.arange(256).reshape(4, 64).T
    #     if fw_ver == "2212s"
    #     else np.arange(256).reshape(64, 4)
    # )
    # for i in range(256):
    #     # transform pixel number to TDC number and pixel coordinates
    #     # in that TDC (from 0 to 3)
    #     tdc, pix = np.argwhere(pix_coor == i)[0]
    #     # find data from that pixel
    #     ind = np.where(data_matrix[tdc].T[0] == pix)[0]
    #     # cut non-valid timestamps ('-1's)
    #     ind = ind[np.where(data_matrix[tdc].T[1][ind] >= 0)[0]]
    #     if not np.any(ind):
    #         continue
    #     # apply calibration
    #     data_matrix[tdc].T[1][ind] = (
    #         data_matrix[tdc].T[1][ind] - data_matrix[tdc].T[1][ind] % 140
    #     ) * 17.857 + cal_mat[i, (data_matrix[tdc].T[1][ind] % 140)]

    return data_matrix
