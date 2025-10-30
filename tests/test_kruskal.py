"""Unit tests for the Kruskal–Wallis helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from smart_comp.stats.kruskal import compute_kruskal_h, kruskal_permutation_test


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "kruskal"


def _load_groups(*filenames: str) -> list[np.ndarray]:
    arrays: list[np.ndarray] = []
    for name in filenames:
        series = pd.read_csv(FIXTURE_DIR / name)["duration"]
        arrays.append(series.to_numpy(dtype=float))
    return arrays


def test_compute_kruskal_h_same_distribution() -> None:
    groups = _load_groups("same_group_a.csv", "same_group_b.csv")

    result = compute_kruskal_h(groups)

    assert result["n_total"] == 12
    assert result["group_sizes"] == [6, 6]
    assert result["tie_correction"] == pytest.approx(1.0)
    assert result["h_statistic"] == pytest.approx(0.2307692308)


def test_kruskal_permutation_test_same_vs_shifted() -> None:
    same_groups = _load_groups("same_group_a.csv", "same_group_b.csv")
    shifted_groups = _load_groups("same_group_a.csv", "shifted_group_c.csv")

    same_result = kruskal_permutation_test(
        same_groups, iterations=2048, rng=np.random.default_rng(2024)
    )
    shifted_result = kruskal_permutation_test(
        shifted_groups, iterations=2048, rng=np.random.default_rng(2024)
    )

    assert same_result["observed"]["h_statistic"] == pytest.approx(0.2307692308)
    assert 0.3 < same_result["p_value"] < 0.9

    assert shifted_result["observed"]["h_statistic"] == pytest.approx(8.3076923077)
    assert shifted_result["p_value"] < 0.01
    assert shifted_result["iterations"] == 2048
