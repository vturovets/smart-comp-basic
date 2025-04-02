import unittest
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
from unittest.mock import MagicMock
from modules.hypothesis import run_bootstrap_test

class TestHypothesis(unittest.TestCase):

    def setUp(self):
        self.file1 = "sample1.csv"
        self.file2 = "sample2.csv"

        # Create small sample CSV files
        df1 = pd.DataFrame(np.random.normal(loc=1000, scale=100, size=1000))
        df2 = pd.DataFrame(np.random.normal(loc=1050, scale=100, size=1000))
        df1.to_csv(self.file1, index=False, header=False, float_format='%.6f')
        df2.to_csv(self.file2, index=False, header=False, float_format='%.6f')

        self.config = MagicMock()
        self.config.get.side_effect = lambda section, key, fallback=None: {
            ('test', 'bootstrapping iterations'): '1000',
            ('test', 'alpha'): '0.05',
            ('test', 'MoE'): '5'
        }.get((section, key), fallback)

    def tearDown(self):
        for f in [self.file1, self.file2, "identical1.csv", "identical2.csv", "randA.csv", "randB.csv" ]:
            if os.path.exists(f):
                os.remove(f)

    def test_bootstrap_output_keys(self):
        result = run_bootstrap_test(self.file1, self.file2, self.config)
        expected_keys = {
            'p95_1', 'p95_2', 'ci lower diff', 'ci upper diff',
            'p-value', 'alpha', 'significant difference',
            'sample size', 'margin of error p95_1, %', 'margin of error p95_2, %'
        }
        self.assertTrue(expected_keys.issubset(result.keys()))

    def test_margin_of_error_ranges(self):
        result = run_bootstrap_test(self.file1, self.file2, self.config)
        self.assertGreater(result['margin of error p95_1, %'], 0)
        self.assertGreater(result['margin of error p95_2, %'], 0)
        self.assertLessEqual(result['margin of error p95_1, %'], 100)
        self.assertLessEqual(result['margin of error p95_2, %'], 100)

    def test_identical_datasets_yield_non_significant_result(self):
        df = pd.DataFrame(np.random.normal(loc=1000, scale=50, size=1000))
        df.to_csv("identical1.csv", index=False, header=False)
        df.to_csv("identical2.csv", index=False, header=False)

        result = run_bootstrap_test("identical1.csv", "identical2.csv", self.config)
        self.assertFalse(result['significant difference'])
        self.assertGreater(result['p-value'], 0.05)

    def test_randomized_p_value_distribution(self):
        np.random.seed(42)
        p_values = []
        for _ in range(10):
            a = pd.DataFrame(np.random.normal(loc=1000, scale=50, size=1000))
            b = pd.DataFrame(np.random.normal(loc=1100, scale=50, size=1000))
            a.to_csv("randA.csv", index=False, header=False)
            b.to_csv("randB.csv", index=False, header=False)
            result = run_bootstrap_test("randA.csv", "randB.csv", self.config)
            p_values.append(result['p-value'])

        # Plot p-value distribution
        plt.figure(figsize=(8, 4))
        plt.hist(p_values, bins=10, edgecolor='black', alpha=0.7)
        plt.axvline(np.mean(p_values), color='red', linestyle='--', label=f'Mean p-value: {np.mean(p_values):.3f}')
        plt.title("Distribution of p-values across 10 randomized comparisons")
        plt.xlabel("p-value")
        plt.ylabel("Frequency")
        plt.legend()
        plt.tight_layout()
        plt.savefig("p_value_dist.png")
        plt.close()

        self.assertLess(np.mean(p_values), 0.5)

if __name__ == '__main__':
    unittest.main()
