"""This module contains old functions.

* get_nmr_validtimestamps

"""

import numpy as np
import sys

sys.path.append("..")
from tools.unpack import unpack_bin
import sys


def get_nmr_validtimestamps(path, board_number, fw_ver, timestamps: int = 512):
    if fw_ver == "2208":
        data = unpk.unpack_calib(path, board_number, timestamps)

        valid_per_pixel = np.zeros(256)

        for j in range(len(data)):
            valid_per_pixel[j] = len(np.where(data[j] > 0)[0])
    elif fw_ver == "2212b":
        data = unpk.unpack_2212(path, board_number, fw_ver, timestamps)

        valid_per_pixel = np.zeros(256)

        for j in range(len(data)):
            valid_per_pixel[j] = len(np.where(data["{}".format(j)] > 0)[0])

    return valid_per_pixel
