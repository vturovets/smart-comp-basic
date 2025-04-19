import unittest
import numpy as np
from modules.sampling_utils import get_autosized_sample

class TestAutoSampleSizing(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        self.data1 = np.arange(1000)
        self.data2 = np.arange(2000)

    def test_no_downsizing_needed(self):
        sample1, sample2, actual_size = get_autosized_sample(self.data1, self.data2, 800)
        self.assertEqual(len(sample1), 800)
        self.assertEqual(len(sample2), 800)
        self.assertEqual(actual_size, 800)

    def test_downsizing_applied(self):
        sample1, sample2, actual_size = get_autosized_sample(self.data1, self.data2, 1500)
        self.assertEqual(len(sample1), 1000)
        self.assertEqual(len(sample2), 1000)
        self.assertEqual(actual_size, 1000)

    def test_exact_match_sample_size(self):
        sample1, sample2, actual_size = get_autosized_sample(self.data1, self.data2, 1000)
        self.assertEqual(len(sample1), 1000)
        self.assertEqual(len(sample2), 1000)
        self.assertEqual(actual_size, 1000)

if __name__ == '__main__':
    unittest.main()
