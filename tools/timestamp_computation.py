import numpy as np
import tools.unpack_data as unpk


def get_nmr_validtimestamps(path, timestamps: int = 512):

    data = unpk.unpack_numpy(path, timestamps)

    valid_per_pixel = np.zeros(256)

    for j in range(len(data)):
        valid_per_pixel[j] = len(np.where(data[j] > 0)[0])

    return valid_per_pixel
