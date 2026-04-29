from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from smart_comp.io.folder_loader import (
    GroupMetadata,
    find_group_files,
    load_group_durations,
)


def _write_csv(path: Path, data: pd.DataFrame) -> None:
    data.to_csv(path, index=False)


def test_find_group_files_errors(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        find_group_files(tmp_path / "missing", "*.csv")

    non_dir = tmp_path / "file.txt"
    non_dir.write_text("not a directory")
    with pytest.raises(NotADirectoryError):
        find_group_files(non_dir, "*.csv")

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(ValueError, match="No files matching pattern"):  # type: ignore[arg-type]
        find_group_files(empty_dir, "*.csv")

    single_file_dir = tmp_path / "single"
    single_file_dir.mkdir()
    (single_file_dir / "only.csv").write_text("value\n1\n")
    with pytest.raises(ValueError, match="At least two CSV files are required"):
        find_group_files(single_file_dir, "*.csv")

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _copy_fixture(name: str, destination: Path) -> Path:
    target = destination / name
    target.write_text((FIXTURE_DIR / "ingestion" / name).read_text(), encoding="utf-8")
    return target


def test_load_group_durations_auto_detect(tmp_path: Path) -> None:
    folder = tmp_path / "data"
    folder.mkdir()

    for filename in ["autodetect_alpha.csv", "autodetect_beta.csv"]:
        _copy_fixture(filename, folder)

    arrays, meta = load_group_durations(folder, "*.csv")

    assert [arr.tolist() for arr in arrays] == [
        [10.0, 20.0, 30.0],
        [15.0, 25.0, 35.0, 45.0],
    ]

    assert [m.file_name for m in meta] == [
        "autodetect_alpha.csv",
        "autodetect_beta.csv",
    ]
    assert [m.n for m in meta] == [3, 4]
    assert meta[0].median == pytest.approx(20.0)
    assert meta[1].percentile_95 == pytest.approx(np.percentile([15, 25, 35, 45], 95))


def test_load_group_durations_with_column_selection(tmp_path: Path) -> None:
    folder = tmp_path / "data"
    folder.mkdir()

    df1 = pd.DataFrame({"id": [1, 2, 3], "duration": [5, 10, 15]})
    df2 = pd.DataFrame({"id": [1, 2, 3], "duration": [7, 14, 21]})

    _write_csv(folder / "first.csv", df1)
    _write_csv(folder / "second.csv", df2)

    arrays, _ = load_group_durations(folder, "*.csv", column="duration")
    assert [arr.tolist() for arr in arrays] == [[5.0, 10.0, 15.0], [7.0, 14.0, 21.0]]

    arrays_idx, _ = load_group_durations(folder, "*.csv", column=1)
    assert [arr.tolist() for arr in arrays_idx] == [[5.0, 10.0, 15.0], [7.0, 14.0, 21.0]]


def test_load_group_durations_filters_invalid_values(tmp_path: Path) -> None:
    folder = tmp_path / "data"
    folder.mkdir()

    _copy_fixture("clean_latencies.csv", folder)
    _copy_fixture("noisy_latencies.csv", folder)

    arrays, meta = load_group_durations(folder, "*.csv", column="latency_ms")

    assert [arr.tolist() for arr in arrays] == [[2.0, 4.0, 6.0, 8.0], [1.0, 3.0, 5.0]]

    by_name = {entry.file_name: entry for entry in meta}
    noisy = by_name["noisy_latencies.csv"]
    assert noisy.dropped_non_numeric_or_nan == 2
    assert noisy.dropped_negative == 1


def test_load_group_durations_errors_when_no_valid_rows(tmp_path: Path) -> None:
    folder = tmp_path / "data"
    folder.mkdir()

    df1 = pd.DataFrame({"duration": [-1, -2]})
    df2 = pd.DataFrame({"duration": [10, 11]})

    _write_csv(folder / "bad.csv", df1)
    _write_csv(folder / "good.csv", df2)

    with pytest.raises(ValueError, match="does not contain any valid"):
        load_group_durations(folder, "*.csv", column="duration")


def test_select_column_errors(tmp_path: Path) -> None:
    folder = tmp_path / "data"
    folder.mkdir()

    df1 = pd.DataFrame({"a": ["x"], "b": ["y"]})
    df2 = pd.DataFrame({"a": ["x"], "b": ["y"]})

    _write_csv(folder / "1.csv", df1)
    _write_csv(folder / "2.csv", df2)

    with pytest.raises(ValueError, match="auto-detect"):
        load_group_durations(folder, "*.csv")

    with pytest.raises(ValueError, match="does not exist"):
        load_group_durations(folder, "*.csv", column="missing")

    with pytest.raises(ValueError, match="out of bounds"):
        load_group_durations(folder, "*.csv", column=10)


def test_find_group_files_requires_multiple_csvs(tmp_path: Path) -> None:
    folder = tmp_path / "datasets"
    folder.mkdir()

    single = FIXTURE_DIR / "ingestion" / "single_group.csv"
    shutil.copy(single, folder / single.name)

    with pytest.raises(ValueError, match="At least two CSV files are required"):
        find_group_files(folder, "*.csv")


def test_group_metadata_dataclass_repr() -> None:
    meta = GroupMetadata("file.csv", 3, 1.0, 2.0, 1, 0)
    assert "file.csv" in repr(meta)


# ---------------------------------------------------------------------------
# Integration tests for unit normalization in folder ingestion (Tasks 6.4, 6.5)
# ---------------------------------------------------------------------------


def test_load_group_durations_normalizes_suffixed_csvs(tmp_path: Path) -> None:
    """**Validates: Requirements 4.1, 4.2**

    A folder with CSVs containing ms/s-suffixed values should be normalized
    to plain ms floats and negative-value filters still applied.
    """
    folder = tmp_path / "suffixed"
    folder.mkdir()

    (folder / "group_a.csv").write_text("duration\n1507ms\n2.08s\n500\n", encoding="utf-8")
    (folder / "group_b.csv").write_text("duration\n3s\n250ms\n100\n", encoding="utf-8")

    arrays, meta = load_group_durations(folder, "*.csv", column="duration")

    assert [sorted(arr.tolist()) for arr in arrays] == [
        sorted([1507.0, 2080.0, 500.0]),
        sorted([3000.0, 250.0, 100.0]),
    ]

    assert all(m.n > 0 for m in meta)


def test_load_group_durations_plain_numeric_unchanged() -> None:
    """**Validates: Requirements 4.3**

    Plain-numeric fixtures in tests/fixtures/kruskal/ should pass through
    load_group_durations unchanged.
    """
    fixture_dir = FIXTURE_DIR / "kruskal"

    arrays, meta = load_group_durations(fixture_dir, "*.csv", column="duration")

    expected_a = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    expected_b = [11.0, 13.0, 15.0, 17.0, 19.0, 21.0]
    expected_c = [30.0, 32.0, 34.0, 36.0, 38.0, 40.0]

    by_name = {m.file_name: (arr, m) for arr, m in zip(arrays, meta)}

    assert sorted(by_name["same_group_a.csv"][0].tolist()) == expected_a
    assert sorted(by_name["same_group_b.csv"][0].tolist()) == expected_b
    assert sorted(by_name["shifted_group_c.csv"][0].tolist()) == expected_c


# ---------------------------------------------------------------------------
# Logger integration test for folder ingestion (Task 6.6)
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock


def test_load_group_durations_logger_receives_summary(tmp_path: Path) -> None:
    """**Validates: Requirements 5.3, 5.4**

    When a logger is provided and suffixed conversions occur, logger.info
    should be called with a normalization summary for each file.
    """
    folder = tmp_path / "logged"
    folder.mkdir()

    (folder / "a.csv").write_text("duration\n1507ms\n2.08s\n", encoding="utf-8")
    (folder / "b.csv").write_text("duration\n3s\n250ms\n", encoding="utf-8")

    logger = MagicMock()
    load_group_durations(folder, "*.csv", column="duration", logger=logger)

    info_calls = [str(c) for c in logger.info.call_args_list]
    summary_calls = [c for c in info_calls if "Unit normalization" in c]
    assert len(summary_calls) >= 2, (
        f"Expected normalization summary for each file, got: {info_calls}"
    )
