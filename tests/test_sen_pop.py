import unittest
import os
from LinoSPAD2app.functions import sen_pop


class SenPopTestCase(unittest.TestCase):
    def setUp(self):
        self.path = "tests/test_data"
        self.board_number = "A5"
        self.fw_ver = "2212b"
        self.timestamps = 200

    def test_sen_pop_positive(self):
        # Positive test case
        work_dir = r"{}".format(os.path.realpath(__file__) + "../../..")
        os.chdir(work_dir)
        file = r"tests/test_data/test_data_2212b.dat"

        data = sen_pop.sen_pop(
            file, self.board_number, self.fw_ver, self.timestamps
        )

        self.assertTrue(data.any())


if __name__ == "__main__":
    unittest.main()
