import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest import mock

# Assume input_handler.py has this function
from modules.input_handler import validate_and_clean
from modules.config import load_config
from analysis import run_descriptive_analysis, check_unimodality_kde
from modules.hypothesis import run_bootstrap_test, run_bootstrap_single_sample_test
from cli import parse_arguments, _remove_cleaned_files

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
    return load_config("C:\\Users\\votu\\Documents\\Ciklum\\2025\\AI toolset for business analysts\\Comp_tool\\smart-comp\\config.txt")


def test_parse_arguments_single(monkeypatch):
    monkeypatch.setattr("sys.argv", ["cli.py", "input1.csv"])
    args = parse_arguments()
    assert args.input1 == "input1.csv"
    assert args.input2 is None
    assert args.output is None


def test_parse_arguments_two_inputs(monkeypatch):
    monkeypatch.setattr("sys.argv", ["cli.py", "input1.csv", "input2.csv"])
    args = parse_arguments()
    assert args.input1 == "input1.csv"
    assert args.input2 == "input2.csv"
    assert args.output is None


def test_parse_arguments_with_output(monkeypatch):
    monkeypatch.setattr("sys.argv", ["cli.py", "input1.csv", "input2.csv", "output.txt"])
    args = parse_arguments()
    assert args.input1 == "input1.csv"
    assert args.input2 == "input2.csv"
    assert args.output == "output.txt"


def test_remove_cleaned_files_success(tmp_path):
    file1 = tmp_path / "file1_cleaned.csv"
    file1.write_text("dummy content")
    cleaned_files = [file1]
    logger = mock.Mock()

    _remove_cleaned_files(cleaned_files, logger)

    assert not file1.exists()
    logger.info.assert_called()


def test_remove_cleaned_files_missing(tmp_path):
    file1 = tmp_path / "file1_cleaned.csv"
    cleaned_files = [file1]
    logger = mock.Mock()

    _remove_cleaned_files(cleaned_files, logger)

    logger.warning.assert_called()


def test_run_bootstrap_test_basic(dummy_config):
    sample1 = pd.DataFrame(np.random.normal(0, 1, 1000))
    sample2 = pd.DataFrame(np.random.normal(0, 1, 1000))
    results = run_bootstrap_test(sample1, sample2, dummy_config, logger=None)
    assert 'p-value' in results
    assert 'significant difference' in results


def test_run_bootstrap_single_sample_test_basic(dummy_config):
    sample = pd.DataFrame(np.random.normal(0, 1, 1000))
    results = run_bootstrap_single_sample_test(sample, dummy_config, logger=None)
    assert 'p-value' in results
    assert 'significant difference' in results


def test_bootstrap_high_difference(dummy_config):
    sample1 = pd.DataFrame(np.random.normal(0, 1, 1000))
    sample2 = pd.DataFrame(np.random.normal(5, 1, 1000))
    results = run_bootstrap_test(sample1, sample2, dummy_config, logger=None)
    assert results['p-value'] < 0.05


def test_bootstrap_small_samples(dummy_config):
    sample1 = pd.DataFrame(np.random.normal(0, 1, 5))
    sample2 = pd.DataFrame(np.random.normal(0, 1, 5))
    results = run_bootstrap_test(sample1, sample2, dummy_config, logger=None)
    assert 'p-value' in results


def test_bootstrap_empty_sample(dummy_config):
    sample1 = pd.DataFrame()
    sample2 = pd.DataFrame()
    with pytest.raises(Exception):
        run_bootstrap_test(sample1, sample2, dummy_config, logger=None)


if __name__ == "__main__":
    pytest.main([__file__])