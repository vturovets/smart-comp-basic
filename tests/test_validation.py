import unittest
import tempfile
import pandas as pd
import configparser
from pathlib import Path
from validation import validate_sample_sizes, validate_ratio_scale

class TestValidationFunctions(unittest.TestCase):

    def setUp(self):
        # Create temporary CSV files for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_adequate = Path(self.temp_dir.name) / "adequate.csv"
        self.file_inadequate = Path(self.temp_dir.name) / "inadequate.csv"
        self.file_negative = Path(self.temp_dir.name) / "negative.csv"
        self.file_binary = Path(self.temp_dir.name) / "binary.csv"
        self.file_mixed = Path(self.temp_dir.name) / "mixed.csv"

        # Adequate sample (600 rows of positive values)
        pd.DataFrame({"value": [1.0] * 600}).to_csv(self.file_adequate, index=False, header=False)

        # Inadequate sample (100 rows)
        pd.DataFrame({"value": [1.0] * 100}).to_csv(self.file_inadequate, index=False, header=False)

        # Sample with negative values
        pd.DataFrame({"value": [-1.0, 2.0, 3.0]}).to_csv(self.file_negative, index=False, header=False)

        # Sample with only 0 and 1
        pd.DataFrame({"value": [0, 1, 0, 1, 0]}).to_csv(self.file_binary, index=False, header=False)

        # Mixed sample (normal data)
        pd.DataFrame({"value": [10, 20, 30, 40, 50]}).to_csv(self.file_mixed, index=False, header=False)

        # Mock config
        self.config = configparser.ConfigParser()
        self.config.read_dict({
            'input': {
                'minimum sample size': '500',
                'validate_ratio_scale': 'True'
            }
        })

    def tearDown(self):
        # Cleanup
        self.temp_dir.cleanup()

    def test_validate_sample_sizes_adequate(self):
        self.assertTrue(validate_sample_sizes(self.file_adequate, config=self.config))

    def test_validate_sample_sizes_inadequate(self):
        self.assertFalse(validate_sample_sizes(self.file_inadequate, config=self.config))

    def test_validate_ratio_scale_positive(self):
        self.assertTrue(validate_ratio_scale(self.file_mixed, config=self.config))

    def test_validate_ratio_scale_negative_values(self):
        self.assertFalse(validate_ratio_scale(self.file_negative, config=self.config))

    def test_validate_ratio_scale_binary_values(self):
        self.assertFalse(validate_ratio_scale(self.file_binary, config=self.config))

    def test_validate_ratio_scale_disabled_in_config(self):
        # Disable validation in config
        self.config['input']['validate_ratio_scale'] = 'False'
        self.assertTrue(validate_ratio_scale(self.file_negative, config=self.config))  # Should pass because validation is OFF

if __name__ == '__main__':
    unittest.main()
