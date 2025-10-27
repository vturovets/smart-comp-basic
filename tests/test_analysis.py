"""Tests for lightweight utility helpers used by the analysis layer."""

import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Provide a minimal ``numpy`` stub so modules.utils can be imported without the
# heavy dependency.
numpy_stub = types.ModuleType("numpy")
numpy_stub.integer = int
numpy_stub.floating = float
numpy_stub.bool_ = bool
sys.modules.setdefault("numpy", numpy_stub)

from modules.utils import get_base_filename


def test_get_base_filename_for_cleaned_and_raw_files():
    """The helper should strip known suffixes regardless of the pattern."""
    assert get_base_filename("data_cleaned.csv") == "data"
    assert get_base_filename("sample_sample.csv") == "sample"
    assert get_base_filename("example_sample.csv") == "example"
    assert get_base_filename("metrics.csv") == "metrics"
