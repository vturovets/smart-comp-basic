import unittest
import pandas as pd
import os
from unittest.mock import MagicMock
from modules.input_handler import validate_and_clean

class TestInputHandler(unittest.TestCase):

    def setUp(self):
        self.sample_file = "test_sample.csv"
        self.cleaned_file = "test_sample_cleaned.csv"

        # Create a sample input file
        with open(self.sample_file, "w") as f:
            f.write("10.5\n-5\nabc\n20001\n15.2\n")

        self.config = MagicMock()
        self.config.get.return_value = '20000'
        self.config.getboolean.return_value = False

    def tearDown(self):
        if os.path.exists(self.sample_file):
            os.remove(self.sample_file)
        if os.path.exists(self.cleaned_file):
            os.remove(self.cleaned_file)

    def test_validate_and_clean_filters_correctly(self):
        result_file = validate_and_clean(self.sample_file, self.config)
        self.assertTrue(os.path.exists(result_file))

        df = pd.read_csv(result_file, header=None)
        self.assertEqual(len(df), 2)  # only 10.5 and 15.2 should remain
        self.assertAlmostEqual(df.iloc[0, 0], 10.5, places=2)
        self.assertAlmostEqual(df.iloc[1, 0], 15.2, places=2)

    def test_raises_on_invalid_format(self):
        bad_file = "bad_sample.csv"
        with open(bad_file, "w") as f:
            f.write("1,2,3\n4,5,6\n")  # multiple columns

        with self.assertRaises(Exception) as cm:
            validate_and_clean(bad_file, self.config)

        os.remove(bad_file)
        self.assertIn("should contain only one column", str(cm.exception))

    def test_raises_on_empty_file(self):
        empty_file = "empty.csv"
        with open(empty_file, "w") as f:
            pass

        with self.assertRaises(Exception) as cm:
            validate_and_clean(empty_file, self.config)

        os.remove(empty_file)
        self.assertIn("is empty", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
