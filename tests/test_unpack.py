import unittest
import numpy as np
import os
from LinoSPAD2app.functions.unpack import unpack_bin


class TestUnpackBin(unittest.TestCase):
    def test_unpack_pos(self):
        # Positive test case
        work_dir = r"{}".format(os.path.realpath(__file__) + "../../..")
        os.chdir(work_dir)
        file = r"tests/test_data/test_data_2212b.dat"
        board_number = "A5"
        fw_ver = "2212b"
        timestamps = 200

        data = unpack_bin(file, board_number, fw_ver, timestamps)

        self.assertEqual(data.shape, (64, 4020, 2))
        self.assertEqual(data.dtype, np.longlong)


if __name__ == "__main__":
    unittest.main()
