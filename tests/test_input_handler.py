import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Assume input_handler.py has this function
from modules.input_handler import validate_and_clean
from modules.config import load_config

import tempfile
import os

@pytest.fixture
def temp_csv():
    """Create a temporary CSV file."""
    def _create_temp_csv(data, filename="temp_input.csv"):
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        pd.DataFrame(data).to_csv(file_path, header=False, index=False)
        return file_path
    return _create_temp_csv

@pytest.fixture
def dummy_config():
    """Load or mock config."""
    return load_config("C:\\Users\\votu\\Documents\\Ciklum\\2025\\AI toolset for business analysts\\Comp_tool\\smart-comp\\config.txt")  # Adjust if needed


def test_valid_input_cleaning(temp_csv, dummy_config):
    # valid data
    data = np.random.normal(loc=500, scale=50, size=100)
    file_path = temp_csv(data)

    cleaned_path = validate_and_clean(file_path, dummy_config)

    assert Path(cleaned_path).exists()
    cleaned_data = pd.read_csv(cleaned_path, header=None)
    assert not cleaned_data.empty


def test_outlier_removal(temp_csv, dummy_config):
    # add an extreme outlier
    data = np.append(np.random.normal(500, 50, 99), [10000])
    file_path = temp_csv(data)

    cleaned_path = validate_and_clean(file_path, dummy_config)
    cleaned_data = pd.read_csv(cleaned_path, header=None)

    assert cleaned_data.max().values[0] < dummy_config.getint('input', 'outlier threshold')


def test_missing_values(temp_csv, dummy_config):
    # add a missing value
    data = list(np.random.normal(500, 50, 99)) + [np.nan]
    file_path = temp_csv(data)

    cleaned_path = validate_and_clean(file_path, dummy_config)
    cleaned_data = pd.read_csv(cleaned_path, header=None)

    assert cleaned_data.isnull().sum().values[0] == 0  # no missing values left


def test_negative_values(temp_csv, dummy_config):
    # add a negative value
    data = list(np.random.normal(500, 50, 99)) + [-50]
    file_path = temp_csv(data)

    cleaned_path = validate_and_clean(file_path, dummy_config)
    cleaned_data = pd.read_csv(cleaned_path, header=None)

    assert (cleaned_data.values >= 0).all()


def test_invalid_file_path(dummy_config):
    with pytest.raises(Exception):
        validate_and_clean("non_existent_file.csv", dummy_config)


def test_non_numeric_data(temp_csv, dummy_config):
    # add text data
    data = [500, 600, "abc", 700]
    file_path = temp_csv(data)

    with pytest.raises(Exception):
        validate_and_clean(file_path, dummy_config)

if __name__ == "__main__":
    # Wrapper to run all tests automatically
    pytest.main([__file__])