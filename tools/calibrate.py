import numpy as np
import os
import glob


def calibrate_load(path):
    """
    Function for loading the calibration data.

    Parameters
    ----------
    path : str
        Path to the .csv file with the calibration matrix.

    Returns
    -------
    data_matrix : ndarray
        Matrix of 256x140 with the calibrated data.

    """

    path_to_back = os.getcwd()
    os.chdir(path)

    file = glob.glob("*Calibration_data*")[0]

    data_matrix = np.genfromtxt(file, delimiter=",", skip_header=1)
    data_matrix = np.delete(data_matrix, 0, axis=1)

    os.chdir(path_to_back)

    return data_matrix
