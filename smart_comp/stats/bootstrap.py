"""Bootstrapping helpers for the CLI."""

from __future__ import annotations

import numpy as np

from smart_comp.io import get_data_frame_from_csv


def _validate_percentile(percentile: int) -> int:
    try:
        percentile_int = int(percentile)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid percentile: must be an integer between 1 and 99.") from exc

    if not 1 <= percentile_int <= 99:
        raise ValueError("Invalid percentile: must be between 1 and 99.")

    return percentile_int


def get_configured_percentile(config) -> int:
    percentile = config.getint("test", "percentile", fallback=95)
    return _validate_percentile(percentile)


def compute_ci(bootstrap_sample, alpha: float = 0.05):
    lower = np.percentile(bootstrap_sample, 100 * (alpha / 2))
    upper = np.percentile(bootstrap_sample, 100 * (1 - alpha / 2))
    return lower, upper


def bootstrap_percentile(file_path: str, percentile: int = 95, iterations: int = 1000):
    percentile = _validate_percentile(percentile)
    data = get_data_frame_from_csv(file_path).iloc[:, 0]
    n = len(data)
    bootstrapped = [
        np.percentile(np.random.choice(data, n, replace=True), percentile)
        for _ in range(iterations)
    ]
    return np.array(bootstrapped)


def compare_percentiles(p_sample1, p_sample2, percentile, sample_size, alpha: float = 0.05):
    percentile = _validate_percentile(percentile)

    ci1 = compute_ci(p_sample1, alpha)
    ci2 = compute_ci(p_sample2, alpha)

    ci_overlap = not (ci1[1] < ci2[0] or ci2[1] < ci1[0])

    if ci_overlap:
        diff_distribution = np.array(p_sample1) - np.array(p_sample2)
        p_value = 2 * min(np.mean(diff_distribution < 0), np.mean(diff_distribution > 0))
        significant = p_value < alpha
    else:
        p_value = 0.0
        significant = True

    p1_mean = np.mean(p_sample1)
    p2_mean = np.mean(p_sample2)

    margin_error1 = ((ci1[1] - ci1[0]) / (2 * p1_mean)) * 100
    margin_error2 = ((ci2[1] - ci2[0]) / (2 * p2_mean)) * 100

    return {
        f"p{percentile}_1": p1_mean,
        f"p{percentile}_2": p2_mean,
        f"ci lower p{percentile}_1": ci1[0],
        f"ci upper p{percentile}_1": ci1[1],
        f"ci lower p{percentile}_2": ci2[0],
        f"ci upper p{percentile}_2": ci2[1],
        f"p{percentile}_1_moe": margin_error1,
        f"p{percentile}_2_moe": margin_error2,
        "p-value": p_value,
        "alpha": alpha,
        "sample size": sample_size,
        "significant difference": significant,
    }


def compare_p95s(sample1_percentiles, sample2_percentiles, sample_size, alpha: float = 0.05):
    return compare_percentiles(sample1_percentiles, sample2_percentiles, 95, sample_size, alpha)


def run_bootstrap_test(sample_file_path1, sample_file_path2, config, logger):
    alpha = float(config.get("test", "alpha"))
    percentile = get_configured_percentile(config)
    iterations = int(config.get("test", "bootstrapping iterations"))
    sample_size = _get_sample_size(sample_file_path1)

    if logger:
        logger.info(f"Starting bootstrapping for both samples at P{percentile}...")
    p_sample1 = bootstrap_percentile(sample_file_path1, percentile, iterations)
    p_sample2 = bootstrap_percentile(sample_file_path2, percentile, iterations)

    if logger:
        logger.info(f"Running P{percentile} comparison...")
    result = compare_percentiles(p_sample1, p_sample2, percentile, sample_size, alpha)
    top_fields = {"operation": f"comparing two P{percentile}s"}

    empirical_key1 = f"p{percentile}_1_empirical"
    if config.getboolean("output", empirical_key1, fallback=False) or config.getboolean(
        "output", "percentile_1_empirical", fallback=False
    ):
        sample1_df = get_data_frame_from_csv(sample_file_path1)
        p_empirical = np.percentile(sample1_df["value"], percentile)
        top_fields[empirical_key1] = p_empirical
        result["data source 1"] = sample_file_path1

    empirical_key2 = f"p{percentile}_2_empirical"
    if config.getboolean("output", empirical_key2, fallback=False) or config.getboolean(
        "output", "percentile_2_empirical", fallback=False
    ):
        sample2_df = get_data_frame_from_csv(sample_file_path2)
        p_empirical = np.percentile(sample2_df["value"], percentile)
        top_fields[empirical_key2] = p_empirical
        result["data source 2"] = sample_file_path2

    if logger:
        logger.info("Bootstrapping and comparison completed.")
    return _merge_fields(result, top_fields)


def compare_percentile_to_threshold(p_samples, threshold, percentile, sample_size, alpha: float):
    percentile = _validate_percentile(percentile)

    ci1 = compute_ci(p_samples, alpha)
    is_threshold_in_ci = not (ci1[1] < threshold or threshold < ci1[0])

    if is_threshold_in_ci:
        diff_distribution = np.array(p_samples) - threshold
        p_value = np.mean(diff_distribution > 0)
        significant = p_value < alpha
    else:
        p_value = 0.0
        significant = True

    p1_mean = np.mean(p_samples)
    margin_error = ((ci1[1] - ci1[0]) / (2 * p1_mean)) * 100

    return {
        f"p{percentile}_1": p1_mean,
        "threshold": threshold,
        f"ci lower p{percentile}_1": ci1[0],
        f"ci upper p{percentile}_1": ci1[1],
        f"p{percentile}_1_moe": margin_error,
        "p-value": p_value,
        "alpha": alpha,
        "sample size": sample_size,
        "significant difference": significant,
    }


def compare_p95_to_threshold(sample_percentiles, threshold, sample_size, alpha: float):
    return compare_percentile_to_threshold(sample_percentiles, threshold, 95, sample_size, alpha)


def run_bootstrap_single_sample_test(sample_file_path1, config, logger):
    alpha = float(config.get("test", "alpha"))
    percentile = get_configured_percentile(config)
    iterations = int(config.get("test", "bootstrapping iterations"))
    threshold = float(config.get("test", "threshold"))
    sample_size = _get_sample_size(sample_file_path1)

    if logger:
        logger.info(f"Starting bootstrapping for single sample at P{percentile}...")
    p_sample1 = bootstrap_percentile(sample_file_path1, percentile, iterations)

    if logger:
        logger.info(f"Running single sample P{percentile} comparison...")
    result = compare_percentile_to_threshold(p_sample1, threshold, percentile, sample_size, alpha)
    top_fields = {"operation": f"comparing P{percentile} to the threshold"}

    empirical_key1 = f"p{percentile}_1_empirical"
    if (
        config.getboolean("output", empirical_key1, fallback=False)
        or config.getboolean("output", f"p{percentile}_2_empirical", fallback=False)
        or config.getboolean("output", "percentile_1_empirical", fallback=False)
        or config.getboolean("output", "percentile_2_empirical", fallback=False)
    ):
        sample1_df = get_data_frame_from_csv(sample_file_path1)
        p_empirical = np.percentile(sample1_df["value"], percentile)
        top_fields[empirical_key1] = p_empirical
        result["data source 1"] = sample_file_path1

    if logger:
        logger.info("Bootstrapping and comparison completed.")
    return _merge_fields(result, top_fields)


def _get_sample_size(sample_file_path: str) -> int:
    data = get_data_frame_from_csv(sample_file_path).iloc[:, 0]
    return len(data)


def _merge_fields(result: dict, top_fields: dict) -> dict:
    merged = dict(top_fields)
    merged.update(result)
    return merged
