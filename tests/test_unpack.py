import os
import unittest

import numpy as np

from daplis_rtp.functions.unpack import unpack_bin

# Next to this file rather than relative to the working directory, so the
# tests pass from wherever pytest is started.
DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "test_data",
    "test_data_2212b.dat",
)


class TestUnpackBin(unittest.TestCase):
    def test_unpack_pos(self):
        # Positive test case
        file = DATA_FILE
        board_number = "A5"
        fw_ver = "2212b"
        timestamps = 200

        data = unpack_bin(file, board_number, fw_ver, timestamps)

        self.assertEqual(data.shape, (64, 4020, 2))
        self.assertEqual(data.dtype, np.longlong)


if __name__ == "__main__":
    unittest.main()
