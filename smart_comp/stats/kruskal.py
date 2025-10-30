"""Kruskal-Wallis helpers and permutation testing utilities."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
from scipy.stats import rankdata

from smart_comp.utils import sanitize_for_json


def compute_kruskal_h(groups: Sequence[np.ndarray]) -> dict[str, object]:
    """Compute the Kruskal-Wallis H statistic for the provided groups.

    Parameters
    ----------
    groups:
        A non-empty sequence of one-dimensional ``numpy`` arrays.

    Returns
    -------
    dict
        A JSON-serialisable payload containing the observed H statistic,
        the tie-correction factor, total sample size, and the per-group
        sample sizes.
    """

    pooled, sizes, boundaries, tie_correction = _prepare_groups(groups)

    ranks = rankdata(pooled, method="average")
    h_statistic = _compute_h_from_ranks(ranks, sizes, boundaries, tie_correction)

    result = {
        "h_statistic": h_statistic,
        "tie_correction": tie_correction,
        "n_total": pooled.size,
        "group_sizes": sizes.tolist(),
    }
    return sanitize_for_json(result)


def kruskal_permutation_test(
    groups: Sequence[np.ndarray], *, iterations: int, rng: np.random.Generator
) -> dict[str, object]:
    """Run a permutation test for the Kruskal-Wallis H statistic.

    Parameters
    ----------
    groups:
        A non-empty sequence of arrays containing the group samples.
    iterations:
        Number of permutations to evaluate. Must be a positive integer.
    rng:
        ``numpy.random.Generator`` seeded by the caller (e.g. via ``--seed``).

    Returns
    -------
    dict
        JSON-serialisable result with the observed statistic, permutation
        distribution, and permutation p-value computed via ``>=`` comparison.
    """

    if iterations <= 0:
        raise ValueError("iterations must be a positive integer")

    pooled, sizes, boundaries, tie_correction = _prepare_groups(groups)

    observed_ranks = rankdata(pooled, method="average")
    observed_h = _compute_h_from_ranks(
        observed_ranks, sizes, boundaries, tie_correction
    )

    permutations = np.empty(iterations, dtype=float)
    shuffled = pooled.copy()

    for idx in range(iterations):
        rng.shuffle(shuffled)
        ranks = rankdata(shuffled, method="average")
        permutations[idx] = _compute_h_from_ranks(
            ranks, sizes, boundaries, tie_correction
        )

    p_value = float(np.mean(permutations >= observed_h))

    result = {
        "observed": {
            "h_statistic": observed_h,
            "tie_correction": tie_correction,
            "n_total": pooled.size,
            "group_sizes": sizes.tolist(),
        },
        "permutation_distribution": permutations.tolist(),
        "p_value": p_value,
        "iterations": iterations,
    }
    return sanitize_for_json(result)


def _prepare_groups(
    groups: Sequence[np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    if not isinstance(groups, Sequence) or len(groups) == 0:
        raise ValueError("groups must be a non-empty sequence of numpy arrays")

    normalized: list[np.ndarray] = []
    for group in groups:
        array = np.asarray(group, dtype=float).ravel()
        if array.size == 0:
            raise ValueError("each group must contain at least one observation")
        normalized.append(array)

    sizes = np.fromiter((arr.size for arr in normalized), dtype=int)
    pooled = np.concatenate(normalized)

    boundaries = np.empty(len(sizes) + 1, dtype=int)
    boundaries[0] = 0
    np.cumsum(sizes, out=boundaries[1:])

    tie_correction = _tie_correction(pooled)

    return pooled, sizes, boundaries, tie_correction


def _compute_h_from_ranks(
    ranks: np.ndarray,
    sizes: np.ndarray,
    boundaries: np.ndarray,
    tie_correction: float,
) -> float:
    total_n = ranks.size
    if total_n <= 1:
        return 0.0

    group_rank_sums = np.empty(len(sizes), dtype=float)
    for idx in range(len(sizes)):
        start, end = boundaries[idx], boundaries[idx + 1]
        group_rank_sums[idx] = float(np.sum(ranks[start:end]))

    sum_term = np.sum((group_rank_sums**2) / sizes)
    h = (12.0 * sum_term / (total_n * (total_n + 1))) - 3.0 * (total_n + 1)

    if tie_correction <= 0:
        return 0.0
    if tie_correction != 1.0:
        h /= tie_correction
    return float(h)


def _tie_correction(values: Iterable[float]) -> float:
    values_array = np.asarray(values, dtype=float)
    n_total = values_array.size
    if n_total <= 1:
        return 1.0

    _, counts = np.unique(values_array, return_counts=True)
    if counts.size == 0:
        return 1.0

    denominator = float(n_total**3 - n_total)
    if denominator == 0.0:
        return 1.0

    tie_term = np.sum(counts**3 - counts)
    correction = 1.0 - (tie_term / denominator)
    return float(max(correction, 0.0))

