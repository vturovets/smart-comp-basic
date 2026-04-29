"""Helpers for loading latency groups from folders of CSV files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Union

import numpy as np
import pandas as pd

from smart_comp.io.unit_parser import normalize_series

__all__ = [
    "GroupMetadata",
    "find_group_files",
    "load_group_durations",
]


@dataclass(frozen=True)
class GroupMetadata:
    """Summary statistics and cleanup counts for a loaded group."""

    file_name: str
    n: int
    median: float
    percentile_95: float
    dropped_non_numeric_or_nan: int
    dropped_negative: int


def find_group_files(folder: Union[str, Path], pattern: str) -> List[Path]:
    """Return sorted paths of CSV files matching a glob pattern.

    Args:
        folder: Root directory that should contain the CSV files.
        pattern: Glob pattern (relative to *folder*) for matching files.

    Raises:
        FileNotFoundError: If *folder* does not exist.
        ValueError: If no files match *pattern* or fewer than two files
            (groups) are found.

    Returns:
        A sorted list of :class:`pathlib.Path` objects.
    """

    folder_path = Path(folder)

    if not folder_path.exists():
        raise FileNotFoundError(f"Folder does not exist: '{folder_path}'")

    if not folder_path.is_dir():
        raise NotADirectoryError(f"Expected a directory for folder: '{folder_path}'")

    matches = sorted(folder_path.glob(pattern))

    if not matches:
        raise ValueError(
            f"No files matching pattern '{pattern}' were found in folder '{folder_path}'."
        )

    if len(matches) < 2:
        raise ValueError(
            "At least two CSV files are required to compare groups; "
            f"found only {len(matches)} match for pattern '{pattern}'."
        )

    return matches


def _select_column(df: pd.DataFrame, column: Union[str, int, None]) -> pd.Series:
    """Return the Series that should be treated as the duration column."""

    if column is None:
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if numeric_cols.empty:
            raise ValueError(
                "Unable to auto-detect a numeric column; please specify one via --column."
            )
        selected = numeric_cols[0]
        return df[selected]

    if isinstance(column, str):
        if column not in df.columns:
            raise ValueError(f"Column '{column}' does not exist in the CSV file.")
        return df[column]

    if isinstance(column, int):
        if column < 0 or column >= df.shape[1]:
            raise ValueError(
                f"Column index {column} is out of bounds for {df.shape[1]} column(s)."
            )
        return df.iloc[:, column]

    raise TypeError("column must be a string, integer, or None")


def _clean_duration_series(
    series: pd.Series,
    logger=None,
    file_name: str = "",
) -> Tuple[np.ndarray, int, int]:
    """Convert a series into a clean numpy array of non-negative numeric durations."""

    normalized, summary = normalize_series(series)

    if logger and (summary["ms"] > 0 or summary["s"] > 0):
        logger.info(
            "Unit normalization: %d ms-suffixed, %d s-suffixed, %d plain, %d failed (file: %s)",
            summary["ms"],
            summary["s"],
            summary["plain"],
            summary["failed"],
            file_name,
        )

    coerced = pd.to_numeric(normalized, errors="coerce")

    non_numeric_or_nan = series.size - coerced.notna().sum()

    valid = coerced.dropna()
    negative_mask = valid < 0
    negative_count = int(negative_mask.sum())
    cleaned = valid[~negative_mask]

    return cleaned.to_numpy(dtype=float), int(non_numeric_or_nan), negative_count


def _summarise_group(values: np.ndarray, file_name: str, dropped: Tuple[int, int]) -> GroupMetadata:
    """Create a :class:`GroupMetadata` instance for the cleaned values."""

    if values.size == 0:
        raise ValueError(
            f"File '{file_name}' does not contain any valid (non-negative numeric) durations."
        )

    median = float(np.median(values))
    percentile_95 = float(np.percentile(values, 95))

    non_numeric_or_nan, negative = dropped

    return GroupMetadata(
        file_name=file_name,
        n=int(values.size),
        median=median,
        percentile_95=percentile_95,
        dropped_non_numeric_or_nan=non_numeric_or_nan,
        dropped_negative=negative,
    )


def load_group_durations(
    folder: Union[str, Path],
    pattern: str = "*.csv",
    column: Union[str, int, None] = None,
    logger=None,
) -> Tuple[List[np.ndarray], List[GroupMetadata]]:
    """Load multiple CSV files as latency groups for statistical analysis.

    Args:
        folder: Root directory containing the CSV files.
        pattern: Glob pattern (relative to *folder*) used to locate files.
        column: Optional name or zero-based index of the column that contains
            durations. If ``None`` the first numeric column is used.
        logger: Optional logger for emitting normalization summaries.

    Raises:
        FileNotFoundError: If *folder* does not exist.
        NotADirectoryError: If *folder* is not a directory.
        ValueError: When globbing fails to find enough files, the target column
            cannot be determined, or no valid durations remain after cleaning.

    Returns:
        A tuple of two items:

        1. A list of NumPy arrays containing cleaned duration values for each
           CSV file.
        2. A list of :class:`GroupMetadata` entries (same order as the data
           arrays) with summary statistics and dropped-row counts.
    """

    files = find_group_files(folder=folder, pattern=pattern)

    arrays: List[np.ndarray] = []
    metadata: List[GroupMetadata] = []

    for file_path in files:
        frame = pd.read_csv(file_path)
        series = _select_column(frame, column)
        cleaned, dropped_non_numeric, dropped_negative = _clean_duration_series(
            series, logger=logger, file_name=file_path.name
        )
        info = _summarise_group(
            cleaned,
            file_name=file_path.name,
            dropped=(dropped_non_numeric, dropped_negative),
        )

        arrays.append(cleaned)
        metadata.append(info)

    return arrays, metadata
