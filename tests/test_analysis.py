"""Tests for lightweight utility helpers used by the analysis layer."""

from __future__ import annotations

import configparser
import sys
import types
from pathlib import Path
from unittest import mock

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Provide a minimal ``numpy`` stub so smart_comp.utils can be imported without the
# heavy dependency.
numpy_stub = types.ModuleType("numpy")
numpy_stub.integer = int
numpy_stub.floating = float
numpy_stub.bool_ = bool
sys.modules.setdefault("numpy", numpy_stub)

from smart_comp.analysis.descriptive import _generate_histogram
from smart_comp.utils import get_base_filename


def test_get_base_filename_for_cleaned_and_raw_files():
    """The helper should strip known suffixes regardless of the pattern."""
    assert get_base_filename("data_cleaned.csv") == "data"
    assert get_base_filename("sample_sample.csv") == "sample"
    assert get_base_filename("example_sample.csv") == "example"
    assert get_base_filename("metrics.csv") == "metrics"


def test_generate_histogram_uses_log_scale_when_requested(tmp_path):
    """The histogram helper should switch the axis to log scale when configured."""

    data = pd.DataFrame({"value": [1, 10, 100]})

    config = configparser.ConfigParser()
    config.add_section("output")
    config.set("output", "histogram_log_scale", "true")

    mock_plt = mock.Mock()

    with mock.patch("smart_comp.analysis.descriptive.plt", mock_plt):
        _generate_histogram(data, "sample", config)

    mock_plt.xscale.assert_called_once_with("log")
    mock_plt.xlabel.assert_called_once_with("Response time, ms (log scale)")
