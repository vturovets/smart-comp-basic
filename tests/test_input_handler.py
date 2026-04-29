"""Tests for configuration helpers that keep input handling portable."""

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from smart_comp.config.loader import _resolve_config_path


def test_resolve_config_path_prefers_existing(tmp_path):
    custom = tmp_path / "custom.cfg"
    custom.write_text("[section]\nkey=value\n", encoding="utf-8")

    resolved = _resolve_config_path(str(custom))

    assert resolved == custom


def test_resolve_config_path_fallbacks_to_repo_default():
    expected = _resolve_config_path(None)

    # Supply a Windows-style path that certainly does not exist in the container.
    resolved = _resolve_config_path(r"C:\\nonexistent\\config.txt")

    assert resolved == expected


# ---------------------------------------------------------------------------
# Integration tests for validate_and_clean (Tasks 6.2, 6.3, 6.6, 6.7)
# ---------------------------------------------------------------------------

import configparser
from unittest.mock import MagicMock

import pandas as pd

from smart_comp.io.input import validate_and_clean


def _make_config(outlier_threshold: str = "20000", lower_threshold: str = "0") -> configparser.ConfigParser:
    """Return a ConfigParser with sensible defaults for testing."""
    cfg = configparser.ConfigParser()
    cfg.add_section("input")
    cfg.set("input", "outlier threshold", outlier_threshold)
    cfg.set("input", "lower threshold", lower_threshold)
    return cfg


def test_validate_and_clean_normalizes_suffixed_values(tmp_path):
    """**Validates: Requirements 3.1, 3.2**

    A CSV with ms/s-suffixed values should be normalized to plain ms floats
    and still pass through the outlier/lower-threshold filters.
    """
    csv_path = tmp_path / "suffixed.csv"
    csv_path.write_text("1507ms\n2.08s\n2s\n500\n", encoding="utf-8")

    config = _make_config()
    cleaned_path = validate_and_clean(str(csv_path), config)

    result = pd.read_csv(cleaned_path, header=None)
    values = result[0].tolist()

    assert values == pytest.approx([1507.0, 2080.0, 2000.0, 500.0])


def test_validate_and_clean_plain_numeric_unchanged(tmp_path):
    """**Validates: Requirements 3.3**

    A CSV with only plain numeric values should pass through unchanged.
    """
    csv_path = tmp_path / "plain.csv"
    csv_path.write_text("100\n200\n300\n", encoding="utf-8")

    config = _make_config()
    cleaned_path = validate_and_clean(str(csv_path), config)

    result = pd.read_csv(cleaned_path, header=None)
    values = result[0].tolist()

    assert values == pytest.approx([100.0, 200.0, 300.0])


def test_validate_and_clean_logger_receives_summary(tmp_path):
    """**Validates: Requirements 5.3, 5.4**

    When a logger is provided and conversions occur, logger.info should be
    called with a normalization summary message.
    """
    csv_path = tmp_path / "mixed.csv"
    csv_path.write_text("1507ms\n2.08s\n500\n", encoding="utf-8")

    config = _make_config()
    logger = MagicMock()

    validate_and_clean(str(csv_path), config, logger=logger)

    # At least one info call should contain the normalization summary
    info_calls = [str(c) for c in logger.info.call_args_list]
    summary_logged = any("Unit normalization" in c for c in info_calls)
    assert summary_logged, f"Expected normalization summary in logger.info calls: {info_calls}"


def test_validate_and_clean_stdout_summary_when_no_logger(tmp_path, capsys):
    """**Validates: Requirements 5.5**

    When no logger is provided and conversions occur, the normalization
    summary should be printed to stdout.
    """
    csv_path = tmp_path / "suffixed_stdout.csv"
    csv_path.write_text("1507ms\n2.08s\n500\n", encoding="utf-8")

    config = _make_config()
    validate_and_clean(str(csv_path), config)

    captured = capsys.readouterr()
    assert "Unit normalization" in captured.out
