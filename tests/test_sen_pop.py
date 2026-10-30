import os
import unittest

from daplis_rtp.functions import sen_pop

# Next to this file rather than relative to the working directory, so the
# tests pass from wherever pytest is started.
DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "test_data",
    "test_data_2212b.dat",
)


class SenPopTestCase(unittest.TestCase):
    def setUp(self):
        self.path = "tests/test_data"
        self.board_number = "A5"
        self.fw_ver = "2212b"
        self.timestamps = 200

    def test_sen_pop_positive(self):
        # Positive test case
        file = DATA_FILE

        data = sen_pop.sen_pop(
            file, self.board_number, self.fw_ver, self.timestamps
        )

        self.assertTrue(data.any())

    def test_sen_pop_counts_are_unchanged(self):
        """Lock the numbers down against the vectorised counting.

        The per-pixel loop that used to do this was replaced with a
        single 'bincount' pass in 1.6. It produced exactly these figures
        beforehand, on this file, for both firmware versions - the
        totals agree because the two only differ in which TDC a pixel
        sits in, not in how many timestamps it recorded.

        """
        file = DATA_FILE

        for fw_ver, brightest in (("2212b", 95), ("2212s", 215)):
            rates = sen_pop.sen_pop(
                file, self.board_number, fw_ver, self.timestamps
            )
            self.assertEqual(rates.shape, (256,))
            self.assertAlmostEqual(rates.sum(), 13156246.679625, places=4)
            self.assertAlmostEqual(rates.max(), 129702.431921, places=4)
            self.assertEqual(int(rates.argmax()), brightest)
            self.assertEqual(int((rates > 0).sum()), 251)


if __name__ == "__main__":
    unittest.main()
