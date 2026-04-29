"""Input validation and loading helpers."""

from __future__ import annotations

import os

import pandas as pd
from pandas import DataFrame

from smart_comp.io.unit_parser import normalize_series


def validate_and_clean(file_path: str, config, logger=None) -> str:
    """Validate and sanitise an input CSV, writing a cleaned copy."""
    df = get_data_frame_from_csv(file_path)

    if df.empty:
        raise Exception(f"Input file {file_path} is empty.")

    if df.shape[1] != 1:
        raise Exception(f"Input file {file_path} should contain only one column.")

    df["value"], summary = normalize_series(df["value"])

    if summary["ms"] > 0 or summary["s"] > 0:
        fname = os.path.basename(file_path)
        msg = (
            f"Unit normalization: {summary['ms']} ms-suffixed, "
            f"{summary['s']} s-suffixed, {summary['plain']} plain, "
            f"{summary['failed']} failed (file: {fname})"
        )
        if logger:
            logger.info(msg)
        else:
            print(msg)

    df = df[pd.to_numeric(df["value"], errors="coerce").notnull()]
    df["value"] = df["value"].astype(float)
    df = df[df["value"] >= 0]

    threshold = float(config.get("input", "outlier threshold", fallback="20000"))
    df = df[df["value"] <= threshold]

    lower_threshold = float(config.get("input", "lower threshold", fallback=0))
    df = df[df["value"] >= lower_threshold]

    cleaned_path = file_path.replace(".csv", "_cleaned.csv")
    df.to_csv(cleaned_path, index=False, header=False)

    if logger:
        logger.info(f"Cleaning completed for {file_path}")

    return cleaned_path


def get_data_frame_from_csv(file_path: str) -> DataFrame:
    """Return the CSV contents as a DataFrame with a ``value`` column."""
    df = pd.read_csv(file_path, header=None, decimal=".")
    df.columns = ["value"]
    return df
