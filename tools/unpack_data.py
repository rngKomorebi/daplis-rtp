"""Unpack data from LinoSPAD2

Functions for unpacking either 'txt' of 'dat' data files of LinoSPAD2.
Functions for either 10, 512 or a given number of timestamps per acquisition
cycle per pixel are available.

This file can also be imported as a module and contains the following
functions:

    * unpack_txt_512 - unpacks the 'txt' data files with 512 timestamps
    per acquisition cycle
    * unpack_txt_10 - unpacks the 'txt' data files with 10 timestamps per
    acquisition cycle
    * unpack_binary_10 - unpacks the 'dat' data files with 10 timestamps
    per acquisition cycle
    * unpack_binary_512 - unpack the 'dat' data files with 512 timestamps
    per acquisition point
    * unpack_binary_flex - unpacks the 'dat' data files with a given number of
    timestamps per acquisition cycle

"""

from struct import unpack
import numpy as np
import sys
import os
from tools.calibrate import calibrate_load


def unpack_binary_flex(filename, timestamps: int = 512):
    """Unpacks the 'dat' data files with certain timestamps per acquistion
    cycle.

    Parameters
    ----------
    filename : str
        File with data from LinoSPAD2 in which precisely timestamps lines
        of data per acquistion cycle is written.
    timestamps: int, optional
        Number of binary-encoded timestamps in the 'dat' file. The default
        value is 512.

    Returns
    -------
    data_matrix : array_like
        A 2D matrix (256 pixels by timestamps X number-of-cycles) of
        timestamps.

    """

    timestamp_list = []
    address_list = []

    with open(filename, "rb") as f:
        while True:
            rawpacket = f.read(4)  # read 32 bits
            if not rawpacket:
                break  # stop when the are no further 4 bytes to readout
            packet = unpack("<I", rawpacket)
            if (packet[0] >> 31) == 1:  # check validity bit: if 1
                # - timestamp is valid
                timestamp = packet[0] & 0xFFFFFFF  # cut the higher bits,
                # leave only timestamp ones
                # 2.5 ns from TDC 400 MHz clock read out 140 bins from 35
                # elements of the delay line - average bin size is 17.857 ps
                timestamp = timestamp * 17.857  # in ps
            else:
                timestamp = -1
            timestamp_list.append(timestamp)
            address = (packet[0] >> 28) & 0x3  # gives away only zeroes -
            # not in this firmware??
            address_list.append(address)
    # rows=#pixels, cols=#cycles
    data_matrix = np.zeros((256, int(len(timestamp_list) / 256)))

    noc = len(timestamp_list) / timestamps / 256  # number of cycles,
    # timestamps data lines per pixel per cycle, 256 pixels

    # pack the data from a 1D array into a 2D matrix
    k = 0
    while k != noc:
        i = 0
        while i < 256:
            data_matrix[i][
                k * timestamps : k * timestamps + timestamps
            ] = timestamp_list[
                (i + 256 * k) * timestamps : (i + 256 * k) * timestamps + timestamps
            ]
            i = i + 1
        k = k + 1
    return data_matrix


def unpack_numpy(filename, timestamps):
    rawFile = np.fromfile(filename, dtype=np.uint32)  # read data
    data = (rawFile & 0xFFFFFFF).astype(int) * 17.857  # Multiply with the lowes bin
    data[np.where(rawFile < 0x80000000)] = -1  # Mask not valid data
    nmrCycles = int(len(data) / timestamps / 256)  # number of cycles,
    data_matrix = (
        data.reshape((timestamps, nmrCycles * 256), order="F")
        .reshape((timestamps, 256, -1), order="F")
        .transpose((0, 2, 1))
        .reshape((-1, 256), order="F")
        .transpose()
    )  # reshape the matrix
    return data_matrix


def unpack_calib(filename, board_number: str, timestamps: int = 512):
    """
    Function for unpacking the .dat data files using the calibration
    data. The output is a matrix of '256 x timestamps*number_of_cycles'
    timestamps in ps.

    Parameters
    ----------
    filename : str
        Name of the .dat file.
    board_number : str
        LinoSPAD2 board number.
    timestamps : int, optional
        Number of timestamps per acquisition cycle per pixel. The default is 512.

    Returns
    -------
    data_matrix : ndarray
        Matrix of '256 x timestamps*number_of_cycles' timestamps.

    """

    # read data by 32 bit words
    rawFile = np.fromfile(filename, dtype=np.uint32)
    # lowest 28 bits are the timestamp; convert to longlong, int is not enough
    data = (rawFile & 0xFFFFFFF).astype(np.longlong)
    # mask nonvalid data with '-1'
    data[np.where(rawFile < 0x80000000)] = -1
    # number of acquisition cycles
    cycles = int(len(data) / timestamps / 256)

    data_matrix = (
        data.reshape(cycles, 256, timestamps)
        .transpose((1, 0, 2))
        .reshape(256, timestamps * cycles)
    )
    # path to the current script, two levels up (the script itself is in the path) and
    # one level down to the calibration data
    path_calib_data = os.path.realpath(__file__) + "/../.." + "/calibration_data"

    try:
        cal_mat = calibrate_load(path_calib_data, board_number)
    except FileNotFoundError:
        print(
            "No .csv file with the calibration data was found, check the path "
            "or run the calibration."
        )
        sys.exit()
    for i in range(256):
        ind = np.where(data_matrix[i] >= 0)[0]
        data_matrix[i, ind] = (
            data_matrix[i, ind] - data_matrix[i, ind] % 140
        ) * 17.857 + cal_mat[i, (data_matrix[i, ind] % 140)]
    return data_matrix


def unpack_2212(filename, board_number, fw_ver, timestamps: int = 512):
    """Unpack binary data from LinoSPAD2 2212 firmware version.

    Function for unpacking data into a dictionary for the firmware versions 2212 "skip"
    and "block". Uses the calibration data.

    Parameters
    ----------
    filename : str
        The name of the ".dat" data file.
    board_number : str
        The LinoSPAD2 dautherboard number.
    fw_ver : str
        2212 firmware version: either "skip" or "block".
    timestamps : int, optional
        Number of timestamps per acquisition cycle per pixel. The default is 512.

    Returns
    -------
    dict
        Matrix of timestamps with 256 rows. Output is a dictionary as the number
        of columns is different for each row.

    """
    timestamp_list = {}

    for i in range(0, 256):
        timestamp_list["{}".format(i)] = []

    # Variables that follow the cycle and the TDC numbers
    cycler = 0
    tdc = 0

    # Function for assigning pixel addresses bases on the type of the 2212
    # firmware version
    def _pix_num(tdc_num, pix_coor):
        if fw_ver == "2212b":
            out = 4 * tdc_num + pix_coor
        elif fw_ver == "2212s":
            out = tdc_num + 64 * pix_coor

        return out

    with open(filename, "rb") as f:
        while True:
            rawpacket = f.read(4)
            # All steps are in units of 32 bits
            # Reaching the end of a cycle, assign a '-1' to each pixel
            if not cycler % (32 * 65 * timestamps) and cycler != 0:
                for i in range(256):
                    timestamp_list["{}".format(i)].append(-1)
            # Next TDC
            if not cycler % (32 * timestamps) and cycler != 0:
                tdc += 1
            cycler += 32
            # Cut the 64th (TDC=[0,...63]) that does not contain timestamps
            if tdc != 0 and tdc == 64:
                continue
            # Reset the TDC number - end of cycle
            if tdc != 0 and tdc == 65:
                tdc = 0
            if not rawpacket:
                break
            packet = unpack("<I", rawpacket)
            if (packet[0] >> 31) == 1:
                pix_coor = (packet[0] >> 28) & 0x3
                address = _pix_num(tdc, pix_coor)
                timestamp_list["{}".format(address)].append((packet[0] & 0xFFFFFFF))

    for key in timestamp_list:
        timestamp_list[key] = np.array(timestamp_list[key]).astype(np.longlong)

    # path to the current script, two levels up (the script itself is in the path) and
    # one level down to the calibration data
    path_calib_data = os.path.realpath(__file__) + "/../.." + "/calibration_data"

    try:
        cal_mat = calibrate_load(path_calib_data, board_number)
    except FileNotFoundError:
        print(
            "No .csv file with the calibration data was found, check the path "
            "or run the calibration."
        )
        sys.exit()
    for i in range(256):
        ind = np.where(np.array(timestamp_list["{}".format(i)]) >= 0)[0]
        if not np.any(ind):
            continue
        timestamp_list["{}".format(i)][ind] = (
            timestamp_list["{}".format(i)][ind]
            - timestamp_list["{}".format(i)][ind] % 140
        ) * 17.857 + cal_mat[i, (timestamp_list["{}".format(i)][ind] % 140)]

    return timestamp_list
