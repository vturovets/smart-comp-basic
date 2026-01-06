"""Tests for percentile-aware bootstrap helpers."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from smart_comp.stats import (
    compare_percentile_to_threshold,
    compare_percentiles,
    get_configured_percentile,
    run_bootstrap_single_sample_test,
    run_bootstrap_test,
)


class DummyConfig:
    def __init__(self, percentile=95):
        self.percentile = percentile

    def get(self, section, option, fallback=None):
        if section == "test" and option == "alpha":
            return 0.05
        if section == "test" and option == "bootstrapping iterations":
            return 10
        if section == "test" and option == "threshold":
            return 100
        if section == "test" and option == "percentile":
            return self.percentile
        return fallback

    def getint(self, section, option, fallback=None):
        return int(self.get(section, option, fallback))

    def getboolean(self, section, option, fallback=False):
        return False


def test_compare_percentiles_dynamic_keys():
    rng = np.random.default_rng(0)
    sample1 = rng.normal(loc=100, scale=10, size=100)
    sample2 = rng.normal(loc=110, scale=10, size=100)

    result = compare_percentiles(sample1, sample2, percentile=90, sample_size=100, alpha=0.05)

    assert "p90_1" in result and "p90_2" in result
    assert "ci lower p90_1" in result and "ci upper p90_2" in result
    assert result["alpha"] == 0.05
    assert result["sample size"] == 100


def test_compare_percentile_to_threshold_dynamic_keys():
    rng = np.random.default_rng(1)
    sample = rng.normal(loc=100, scale=5, size=50)

    result = compare_percentile_to_threshold(
        sample, threshold=95, percentile=90, sample_size=50, alpha=0.05
    )

    assert "p90_1" in result
    assert "ci lower p90_1" in result
    assert result["threshold"] == 95


def test_get_configured_percentile_validation():
    cfg = DummyConfig(percentile=90)
    assert get_configured_percentile(cfg) == 90

    cfg_bad = DummyConfig(percentile=120)
    with pytest.raises(ValueError):
        get_configured_percentile(cfg_bad)


def test_run_bootstrap_test_uses_percentile(monkeypatch, tmp_path):
    data1 = tmp_path / "p95_sample1.csv"
    data2 = tmp_path / "p95_sample2.csv"
    data1.write_text("\n".join("100" for _ in range(50)))
    data2.write_text("\n".join("110" for _ in range(50)))

    cfg = DummyConfig(percentile=90)

    # Reduce iterations for speed
    monkeypatch.setattr(
        "smart_comp.stats.bootstrap.bootstrap_percentile",
        lambda *args, **kwargs: np.array([args[1]] * 5),
    )

    result = run_bootstrap_test(str(data1), str(data2), cfg, logger=None)

    assert result["operation"] == "comparing two P90s"
    assert "p90_1" in result and "p90_2" in result


def test_run_bootstrap_single_sample_test_uses_percentile(monkeypatch, tmp_path):
    data1 = tmp_path / "p95_sample1.csv"
    data1.write_text("\n".join("100" for _ in range(50)))

    cfg = DummyConfig(percentile=90)

    monkeypatch.setattr(
        "smart_comp.stats.bootstrap.bootstrap_percentile",
        lambda *args, **kwargs: np.array([args[1]] * 5),
    )

    result = run_bootstrap_single_sample_test(str(data1), cfg, logger=None)

    assert result["operation"] == "comparing P90 to the threshold"
    assert "p90_1" in result

