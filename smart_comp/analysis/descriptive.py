"""Descriptive analysis and unimodality helpers."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from diptest import diptest
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde, kurtosis, skew

from smart_comp.io import get_data_frame_from_csv
from smart_comp.utils import get_base_filename


def run_descriptive_analysis(cleaned_file, config, logger=None, mode="w"):
    df = get_data_frame_from_csv(cleaned_file)
    results: dict[str, object] = {}

    base_filename = get_base_filename(cleaned_file)
    results["operation"] = "descriptive analysis"
    results["data source"] = base_filename

    if config.getboolean("descriptive analysis", "mean", fallback=False):
        results["mean"] = df["value"].mean()
    if config.getboolean("descriptive analysis", "median", fallback=False):
        results["median"] = df["value"].median()
    if config.getboolean("descriptive analysis", "min", fallback=False):
        results["min"] = df["value"].min()
    if config.getboolean("descriptive analysis", "max", fallback=False):
        results["max"] = df["value"].max()
    if config.getboolean("descriptive analysis", "sample size", fallback=False):
        results["sample size"] = df["value"].count()
    if config.getboolean("descriptive analysis", "standard deviation", fallback=False):
        results["standard deviation"] = df["value"].std()
    if config.getboolean("descriptive analysis", "skewness", fallback=False):
        results["skewness"] = skew(df["value"])
    if config.getboolean("descriptive analysis", "mode", fallback=False):
        results["mode"] = df["value"].mode()[0]
    if config.getboolean("descriptive analysis", "p95_empirical", fallback=False):
        results["p95_empirical"] = np.percentile(df["value"], 95)

    if config.getboolean("descriptive analysis", "diagraming", fallback=False):
        if config.getboolean("output", "histogram", fallback=False):
            _generate_histogram(df, base_filename, config)
        if config.getboolean("output", "boxplot", fallback=False):
            _generate_boxplot(df, base_filename, config)

    if config.getboolean("descriptive analysis", "get extended report", fallback=False):
        unimodality_report = run_unimodality_analysis(cleaned_file, config, logger)
        results["extended analysis"] = "unimodality"
        for key, value in unimodality_report.items():
            results[key] = value

    if logger:
        logger.info(f"Descriptive analysis completed for {cleaned_file}")

    return results


def _generate_histogram(df: pd.DataFrame, base_filename: str, config) -> None:
    plt.figure()
    plt.hist(df["value"], bins=50, alpha=0.7)
    plt.axvline(
        df["value"].mean(),
        color="red",
        linestyle="dashed",
        linewidth=1,
        label=f"Mean: {df['value'].mean():.1f} ms",
    )
    plt.axvline(
        df["value"].median(),
        color="green",
        linestyle="dashed",
        linewidth=1,
        label=f"Median: {df['value'].median():.1f} ms",
    )
    p95 = np.percentile(df["value"], 95)
    plt.axvline(p95, color="orange", linestyle="dashed", linewidth=1, label=f"P95: {p95:.1f} ms")

    plt.title(f"Histogram of {base_filename}")
    plt.xlabel("Response time, ms")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"histogram_{base_filename}.png")
    plt.close()


def _generate_boxplot(df: pd.DataFrame, base_filename: str, config) -> None:
    plt.figure()
    plt.boxplot(df["value"], vert=False)
    plt.title(f"Boxplot of {base_filename}")
    plt.xlabel("Value")
    plt.tight_layout()
    plt.savefig(f"boxplot_{base_filename}.png")
    plt.close()


def check_unimodality_kde(cleaned_file, config, logger=None):
    unimodality_report = run_unimodality_analysis(cleaned_file, config, logger)
    dip_p_value = unimodality_report["Dip Test p-value"]
    peak_count = unimodality_report["KDE Peak Count"]
    bc_value = unimodality_report["Bimodality Coefficient"]

    is_unimodal = (peak_count == 1) and (dip_p_value > 0.05) and (bc_value < 0.55)

    if not is_unimodal:
        print(
            f"⚠️ Warning: Input file {cleaned_file} contains data that does not meet unimodality condition. "
            "Only descriptive analysis is allowed."
        )

    if logger:
        logger.info(f"Unimodality check completed for {cleaned_file}")

    return is_unimodal


def _generate_kde_plot(x_grid, kde_values, all_peaks, cleaned_file):
    base_filename = get_base_filename(cleaned_file)
    plt.figure()
    plt.plot(x_grid, kde_values, label="KDE")
    plt.plot(x_grid[list(all_peaks)], kde_values[list(all_peaks)], "x", color="red", label="Detected Peaks")
    plt.title(f"KDE with Peak Detection: {base_filename}")
    plt.xlabel("Response time, ms")
    plt.ylabel("Density")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"kde_peaks_{base_filename}.png")
    plt.close()


def _check_unimodality_dip_test(cleaned_file):
    df = get_data_frame_from_csv(cleaned_file)
    data = df.iloc[:, 0].dropna().values
    _, p_value = diptest(data)
    return p_value


def _check_unimodality_bimodality_coefficient(cleaned_file):
    df = get_data_frame_from_csv(cleaned_file)
    data = df.iloc[:, 0].dropna().values
    g = skew(data)
    k = kurtosis(data, fisher=False)
    return (g**2 + 1) / k


def run_unimodality_analysis(cleaned_file, config, logger=None):
    bandwidth = config.get("descriptive analysis", "bandwidth")
    df = get_data_frame_from_csv(cleaned_file)
    data = df.iloc[:, 0].dropna().values
    kde = gaussian_kde(data, bw_method=bandwidth)

    x_grid = np.linspace(data.min(), data.max(), 2000)
    kde_values = kde(x_grid)
    kde_values = pd.Series(kde_values).rolling(window=3, center=True, min_periods=1).mean().values

    max_kde = np.max(kde_values)
    peak_prominence = 0.0025 * max_kde

    main_peak_index = np.argmax(kde_values)
    peaks, _ = find_peaks(kde_values, prominence=peak_prominence, distance=25)
    all_peaks = set(peaks)
    all_peaks.add(main_peak_index)
    peak_count = len(all_peaks)

    dip_p_value = _check_unimodality_dip_test(cleaned_file)
    bc_value = _check_unimodality_bimodality_coefficient(cleaned_file)

    unimodality_report: dict[str, object] = {}
    base_filename = get_base_filename(cleaned_file)
    unimodality_report["data source"] = base_filename
    unimodality_report["bandwidth"] = str(bandwidth)
    unimodality_report["peak_prominence"] = peak_prominence
    unimodality_report["KDE Peak Count"] = peak_count
    unimodality_report["Dip Test p-value"] = dip_p_value
    unimodality_report["Bimodality Coefficient"] = bc_value

    if config.getboolean("descriptive analysis", "diagraming", fallback=False):
        if config.getboolean("output", "kde_plot", fallback=False):
            _generate_kde_plot(x_grid, kde_values, all_peaks, cleaned_file)

    if logger:
        logger.info(f"Unimodality analysis completed for {cleaned_file}")

    return unimodality_report
