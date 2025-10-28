"""Utility helpers for file naming and serialization."""

from __future__ import annotations

import os
from typing import Any

import numpy as np


def get_base_filename(file_path: str) -> str:
    """Return a CSV name without helper suffixes."""
    basename = os.path.basename(file_path)
    for suffix in ("_cleaned.csv", "_sample.csv", ".csv"):
        if basename.endswith(suffix):
            return basename[: -len(suffix)]
    return basename


def sanitize_for_json(obj: Any) -> Any:
    """Recursively convert numpy scalars into JSON serialisable values."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj
