import numpy as np
import tools.unpack_data as unpk


def get_nmr_validtimestamps(path, pix_range, timestamps: int = 512):

    data = unpk.unpack_numpy(path, 512)

    valid_per_pixel = np.zeros(256)

    for j in range(len(data)):
        valid_per_pixel[j] = len(np.where(data[j] > 0)[0])
    peak = np.max(valid_per_pixel[pix_range])

    return valid_per_pixel, peak
