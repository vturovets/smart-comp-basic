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
