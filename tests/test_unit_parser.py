"""Property-based tests for smart_comp.io.unit_parser.

Each test maps to a correctness property from the design document.
"""

from __future__ import annotations

import math
import string

import pandas as pd
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from smart_comp.io.unit_parser import parse_duration_value, normalize_series


# ---------------------------------------------------------------------------
# Helpers / strategies
# ---------------------------------------------------------------------------

_positive_finite_floats = st.floats(
    min_value=0, allow_nan=False, allow_infinity=False
)

_finite_floats = st.floats(allow_nan=False, allow_infinity=False)

_whitespace_chars = st.sampled_from([" ", "\t", "\n", "\r", "  ", "\t\t"])


def _whitespace_st() -> st.SearchStrategy[str]:
    """Generate a random whitespace padding string (possibly empty)."""
    return st.text(alphabet=" \t\n\r", min_size=0, max_size=5)


# Strategy for strings that are NOT valid plain numbers and do NOT end with
# a recognised suffix followed by a valid number.
@st.composite
def _unrecognised_strings(draw: st.DrawFn) -> str:
    """Generate strings that parse_duration_value should map to NaN."""
    # Pick a base that is definitely not a number
    base = draw(
        st.text(
            alphabet=st.sampled_from(
                list(string.ascii_letters.replace("s", "").replace("S", ""))
                + ["!", "@", "#", "$", "%", "^", "&"]
            ),
            min_size=1,
            max_size=10,
        )
    )
    # Make sure it doesn't accidentally become a valid float
    assume(not _is_valid_duration(base))
    return base


def _is_valid_duration(s: str) -> bool:
    """Return True if s would parse to a non-NaN value."""
    result = parse_duration_value(s)
    return not math.isnan(result)


# ---------------------------------------------------------------------------
# Property 1: Millisecond suffix round-trip
# ---------------------------------------------------------------------------
# Feature: unclean-data-ingestion, Property 1: Millisecond suffix round-trip

@given(x=_positive_finite_floats)
@settings(max_examples=100)
def test_ms_round_trip(x: float) -> None:
    """**Validates: Requirements 1.1, 6.1**

    For any positive finite float x, formatting as '{x}ms' and parsing
    should return a value ≈ x.
    """
    raw = f"{x}ms"
    result = parse_duration_value(raw)
    assert math.isclose(result, x, rel_tol=1e-9, abs_tol=1e-12), (
        f"ms round-trip failed: parse_duration_value({raw!r}) = {result}, expected ≈ {x}"
    )


# ---------------------------------------------------------------------------
# Property 2: Seconds suffix round-trip
# ---------------------------------------------------------------------------
# Feature: unclean-data-ingestion, Property 2: Seconds suffix round-trip

@given(
    x=st.floats(
        min_value=0,
        max_value=1e304,  # keep x*1000 finite (avoid overflow to inf)
        allow_nan=False,
        allow_infinity=False,
    )
)
@settings(max_examples=100)
def test_s_round_trip(x: float) -> None:
    """**Validates: Requirements 1.2, 6.2**

    For any positive finite float x (where x*1000 won't overflow),
    formatting as '{x}s' and parsing should return y (ms) where y / 1000 ≈ x.
    """
    raw = f"{x}s"
    result = parse_duration_value(raw)
    assert math.isclose(result / 1000, x, rel_tol=1e-9, abs_tol=1e-12), (
        f"s round-trip failed: parse_duration_value({raw!r}) = {result}, "
        f"result/1000 = {result / 1000}, expected ≈ {x}"
    )


# ---------------------------------------------------------------------------
# Property 3: Plain numeric identity
# ---------------------------------------------------------------------------
# Feature: unclean-data-ingestion, Property 3: Plain numeric identity

@given(x=_finite_floats)
@settings(max_examples=100)
def test_plain_numeric_identity(x: float) -> None:
    """**Validates: Requirements 1.3, 6.3**

    For any finite float x, str(x) → parse → assert == float(str(x)).
    """
    raw = str(x)
    result = parse_duration_value(raw)
    expected = float(raw)
    assert result == expected, (
        f"Plain identity failed: parse_duration_value({raw!r}) = {result}, "
        f"expected {expected}"
    )


# ---------------------------------------------------------------------------
# Property 4: Unrecognized input produces NaN
# ---------------------------------------------------------------------------
# Feature: unclean-data-ingestion, Property 4: Unrecognized input produces NaN

@given(s=_unrecognised_strings())
@settings(max_examples=100)
def test_unrecognised_input_produces_nan(s: str) -> None:
    """**Validates: Requirements 1.4**

    For any string that is not a valid number and does not carry a
    recognised suffix with a valid numeric prefix, the result is NaN.
    """
    result = parse_duration_value(s)
    assert math.isnan(result), (
        f"Expected NaN for unrecognised input {s!r}, got {result}"
    )


# ---------------------------------------------------------------------------
# Property 5: Whitespace invariance
# ---------------------------------------------------------------------------
# Feature: unclean-data-ingestion, Property 5: Whitespace invariance

@st.composite
def _valid_duration_with_padding(draw: st.DrawFn) -> tuple[str, str]:
    """Return (padded_string, unpadded_string) for a valid duration."""
    kind = draw(st.sampled_from(["ms", "s", "plain"]))
    x = draw(_positive_finite_floats)
    if kind == "ms":
        core = f"{x}ms"
    elif kind == "s":
        core = f"{x}s"
    else:
        core = str(x)
    leading = draw(_whitespace_st())
    trailing = draw(_whitespace_st())
    return leading + core + trailing, core


@given(pair=_valid_duration_with_padding())
@settings(max_examples=100)
def test_whitespace_invariance(pair: tuple[str, str]) -> None:
    """**Validates: Requirements 1.5**

    Parsing a valid duration string with arbitrary leading/trailing
    whitespace should produce the same result as parsing without it.
    """
    padded, core = pair
    result_padded = parse_duration_value(padded)
    result_core = parse_duration_value(core)

    if math.isnan(result_core):
        assert math.isnan(result_padded), (
            f"Whitespace invariance failed: core {core!r} → NaN but "
            f"padded {padded!r} → {result_padded}"
        )
    else:
        assert result_padded == result_core, (
            f"Whitespace invariance failed: "
            f"parse({padded!r}) = {result_padded} != parse({core!r}) = {result_core}"
        )


# ---------------------------------------------------------------------------
# Property 6: Row independence
# ---------------------------------------------------------------------------
# Feature: unclean-data-ingestion, Property 6: Row independence

@st.composite
def _mixed_series_with_mutation(draw: st.DrawFn) -> tuple[list[str], int]:
    """Generate a list of valid duration strings and an index to mutate."""
    n = draw(st.integers(min_value=2, max_value=20))
    items: list[str] = []
    for _ in range(n):
        kind = draw(st.sampled_from(["ms", "s", "plain"]))
        x = draw(_positive_finite_floats)
        if kind == "ms":
            items.append(f"{x}ms")
        elif kind == "s":
            items.append(f"{x}s")
        else:
            items.append(str(x))
    idx = draw(st.integers(min_value=0, max_value=n - 1))
    return items, idx


@given(data=_mixed_series_with_mutation())
@settings(max_examples=100)
def test_row_independence(data: tuple[list[str], int]) -> None:
    """**Validates: Requirements 2.2**

    Mutating one row in a Series should not change the parsed result of
    any other row.
    """
    items, idx = data
    series_original = pd.Series(items)
    result_original, _ = normalize_series(series_original)

    # Mutate the chosen row to an invalid value
    mutated_items = list(items)
    mutated_items[idx] = "INVALID_VALUE"
    series_mutated = pd.Series(mutated_items)
    result_mutated, _ = normalize_series(series_mutated)

    # All rows except the mutated one should be identical
    for i in range(len(items)):
        if i == idx:
            continue
        orig_val = result_original.iloc[i]
        mut_val = result_mutated.iloc[i]
        if math.isnan(orig_val):
            assert math.isnan(mut_val), (
                f"Row {i} changed after mutating row {idx}: "
                f"original=NaN, mutated={mut_val}"
            )
        else:
            assert orig_val == mut_val, (
                f"Row {i} changed after mutating row {idx}: "
                f"original={orig_val}, mutated={mut_val}"
            )


# ---------------------------------------------------------------------------
# Property 7: Summary counts accuracy
# ---------------------------------------------------------------------------
# Feature: unclean-data-ingestion, Property 7: Summary counts accuracy

@st.composite
def _series_with_known_counts(draw: st.DrawFn) -> tuple[list[str], dict[str, int]]:
    """Generate a Series with a known composition of value types."""
    n_ms = draw(st.integers(min_value=0, max_value=5))
    n_s = draw(st.integers(min_value=0, max_value=5))
    n_plain = draw(st.integers(min_value=0, max_value=5))
    n_failed = draw(st.integers(min_value=0, max_value=5))
    assume(n_ms + n_s + n_plain + n_failed > 0)

    items: list[str] = []
    for _ in range(n_ms):
        x = draw(_positive_finite_floats)
        items.append(f"{x}ms")
    for _ in range(n_s):
        x = draw(_positive_finite_floats)
        items.append(f"{x}s")
    for _ in range(n_plain):
        x = draw(_finite_floats)
        items.append(str(x))
    for _ in range(n_failed):
        items.append("INVALID")

    # Shuffle to avoid ordering bias
    shuffled = draw(st.permutations(items))

    expected = {"ms": n_ms, "s": n_s, "plain": n_plain, "failed": n_failed}
    return list(shuffled), expected


@given(data=_series_with_known_counts())
@settings(max_examples=100)
def test_summary_counts_accuracy(data: tuple[list[str], dict[str, int]]) -> None:
    """**Validates: Requirements 5.1, 5.2**

    For a Series with a known composition, normalize_series should return
    a summary dict whose counts exactly match the known counts.
    """
    items, expected_counts = data
    series = pd.Series(items)
    _, summary = normalize_series(series)
    assert summary == expected_counts, (
        f"Summary mismatch: got {summary}, expected {expected_counts}\n"
        f"Input: {items}"
    )


# ---------------------------------------------------------------------------
# Unit tests — specific examples (Task 6.1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("1507ms", 1507.0),
        ("2.08s", 2080.0),
        ("2s", 2000.0),
        ("1507", 1507.0),
        ("1507MS", 1507.0),
    ],
    ids=["ms-suffix", "s-suffix-decimal", "s-suffix-int", "plain-numeric", "ms-upper"],
)
def test_parse_duration_value_valid_examples(raw: str, expected: float) -> None:
    """Specific example-based tests for valid duration values."""
    result = parse_duration_value(raw)
    assert result == pytest.approx(expected), (
        f"parse_duration_value({raw!r}) = {result}, expected {expected}"
    )


@pytest.mark.parametrize(
    "raw",
    ["", "ms", "abc"],
    ids=["empty-string", "suffix-only", "non-numeric"],
)
def test_parse_duration_value_nan_examples(raw: str) -> None:
    """Specific example-based tests for inputs that should produce NaN."""
    result = parse_duration_value(raw)
    assert math.isnan(result), (
        f"parse_duration_value({raw!r}) = {result}, expected NaN"
    )
