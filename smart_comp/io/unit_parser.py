"""Unit-aware duration parser.

Converts raw duration strings (e.g. '1507ms', '2.08s', '1507') into
plain floating-point millisecond values.  Designed as a pure-function
layer invoked before ``pd.to_numeric`` in both ingestion paths.
"""

from __future__ import annotations

import math

import pandas as pd


def parse_duration_value(raw: str) -> float:
    """Parse a single raw duration string into milliseconds.

    Rules applied in order:
    1. Strip leading/trailing whitespace.
    2. If the string ends with ``ms`` (case-insensitive), strip the suffix
       and interpret the remainder as milliseconds.
    3. Else if the string ends with ``s`` (case-insensitive), strip the
       suffix, interpret the remainder as seconds, and multiply by 1000.
    4. Else attempt to interpret the whole string as a plain number
       (milliseconds).
    5. If none of the above succeed, return ``NaN``.

    Returns:
        ``float`` millisecond value, or ``float('nan')`` for unparseable
        input.
    """
    if not isinstance(raw, str):
        try:
            return float(raw)
        except (TypeError, ValueError):
            return float("nan")

    text = raw.strip()
    lower = text.lower()

    # ms suffix (checked first so "ms" is not caught by the "s" branch)
    if lower.endswith("ms"):
        numeric_part = text[:-2]
        try:
            return float(numeric_part)
        except ValueError:
            return float("nan")

    # s suffix
    if lower.endswith("s"):
        numeric_part = text[:-1]
        try:
            return float(numeric_part) * 1000
        except ValueError:
            return float("nan")

    # plain numeric
    try:
        return float(text)
    except ValueError:
        return float("nan")


def normalize_series(
    series: pd.Series,
) -> tuple[pd.Series, dict[str, int]]:
    """Normalize an entire Series of raw duration values to milliseconds.

    Each element is parsed independently via :func:`parse_duration_value`.

    Returns:
        normalized: Series of ``float`` ms values (``NaN`` for failures).
        summary: ``{"ms": <count>, "s": <count>, "plain": <count>,
                  "failed": <count>}``
    """
    counts: dict[str, int] = {"ms": 0, "s": 0, "plain": 0, "failed": 0}
    results: list[float] = []

    for val in series:
        parsed = parse_duration_value(val)

        if math.isnan(parsed):
            counts["failed"] += 1
            results.append(parsed)
            continue

        # Classify which branch was taken
        if isinstance(val, str):
            stripped = val.strip().lower()
            if stripped.endswith("ms"):
                counts["ms"] += 1
            elif stripped.endswith("s"):
                counts["s"] += 1
            else:
                counts["plain"] += 1
        else:
            counts["plain"] += 1

        results.append(parsed)

    normalized = pd.Series(results, index=series.index, dtype=float)
    return normalized, counts
