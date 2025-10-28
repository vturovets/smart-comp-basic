"""Validation helpers for incoming data."""

from __future__ import annotations

import numpy as np
import pandas as pd

from smart_comp.io import get_data_frame_from_csv


def validate_sample_sizes(file_path1, file_path2=None, config=None):
    data1 = get_data_frame_from_csv(file_path1)
    data2 = get_data_frame_from_csv(file_path2) if file_path2 else None

    min_required = config.getint("input", "minimum sample size", fallback=500)

    if data2 is None:
        if len(data1) < min_required:
            print(
                f"⚠️ Warning: Input file {file_path1} contains fewer than {min_required} observations."
            )
            return False
    else:
        if len(data1) < min_required or len(data2) < min_required:
            print(
                "⚠️ Warning: One or both input files contain fewer than "
                f"{min_required} observations."
            )
            return False

    return True


def validate_ratio_scale(clean_file, config=None, logger=None):
    if config and not config.getboolean("input", "validate_ratio_scale", fallback=True):
        return True

    data = get_data_frame_from_csv(clean_file)["value"]

    if isinstance(data, pd.Series):
        values = data.dropna().values
    elif isinstance(data, (np.ndarray, list)):
        values = np.array(data)
    else:
        msg = "Unsupported data type for ratio scale validation."
        if logger:
            logger.error(msg)
        else:
            print(f"[Error] {msg}")
        return False

    if not np.issubdtype(values.dtype, np.number):
        msg = "Data contains non-numeric values."
        if logger:
            logger.error(msg)
        else:
            print(f"[Error] {msg}")
        return False

    if np.any(values < 0):
        msg = "Data contains negative values, violating ratio scale requirement."
        if logger:
            logger.error(msg)
        else:
            print(f"[Error] {msg}")
        return False

    unique_values = np.unique(values)
    if np.array_equal(unique_values, [0, 1]) or np.array_equal(unique_values, [0]) or np.array_equal(
        unique_values, [1]
    ):
        msg = "Data contains only binary values (0 and 1), suggesting categorical scale, not ratio scale."
        if logger:
            logger.error(msg)
        else:
            print(f"[Error] {msg}")
        return False

    return True
