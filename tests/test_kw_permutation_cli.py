"""Tests for the kw-permutation CLI command."""

from __future__ import annotations

import configparser
import json
import shutil
from argparse import Namespace
from pathlib import Path

import numpy as np
import pytest

from smart_comp.cli.app import parse_arguments, run_cli
from smart_comp.cli.kw_permutation import run_kw_permutation_command
from smart_comp.io import load_group_durations
from smart_comp.stats import kruskal_permutation_test


def test_parse_arguments_kw_permutation():
    args = parse_arguments(
        [
            "kw-permutation",
            "--folder",
            "data",
            "--pattern",
            "*.csv",
            "--column",
            "2",
            "--permutations",
            "500",
            "--seed",
            "123",
            "--quiet",
        ]
    )

    assert args.command == "kw-permutation"
    assert args.folder == "data"
    assert args.pattern == "*.csv"
    assert args.column == 2
    assert args.permutations == 500
    assert args.seed == 123
    assert args.quiet is True
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "kruskal"


def _copy_groups(root: Path, filenames: list[str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name in filenames:
        shutil.copy(FIXTURE_DIR / name, root / name)


def test_kw_permutation_command_generates_outputs(tmp_path, capsys):
    folder = tmp_path / "data"
    _copy_groups(
        folder,
        [
            "same_group_a.csv",
            "same_group_b.csv",
            "shifted_group_c.csv",
        ],
    )

    args = Namespace(
        command="kw-permutation",
        folder=str(folder),
        pattern="*.csv",
        column="duration",
        permutations=64,
        seed=321,
        report=str(tmp_path / "report.json"),
        summary_csv=str(tmp_path / "summary.csv"),
        quiet=False,
    )
    config = configparser.ConfigParser()

    result = run_kw_permutation_command(args, config, logger=None)
    stdout_lines = capsys.readouterr().out.strip().splitlines()

    assert stdout_lines[0] == "Kruskal–Wallis permutation test"
    assert any("group_a.csv" in line for line in stdout_lines)
    assert any("Permutation p-value" in line for line in stdout_lines)
    assert stdout_lines[-2].startswith("Report written to ")
    assert stdout_lines[-1].startswith("Summary CSV written to ")

    assert result["omnibus"]["seed"] == 321
    assert result["omnibus"]["permutations"] == 64
    assert len(result["groups"]) == 3

    report_path = Path(args.report)
    summary_path = Path(args.summary_csv)
    assert report_path.exists()
    assert summary_path.exists()

    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_payload["omnibus"]["observed_h"] == pytest.approx(
        result["omnibus"]["observed_h"]
    )

    summary_lines = summary_path.read_text(encoding="utf-8").strip().splitlines()
    assert summary_lines[0].startswith("file_name")
    assert len(summary_lines) == 4

    arrays, _ = load_group_durations(folder=str(folder), pattern="*.csv", column="duration")
    expected = kruskal_permutation_test(
        arrays,
        iterations=64,
        rng=np.random.default_rng(321),
    )
    assert result["omnibus"]["permutation_p"] == pytest.approx(expected["p_value"])
    assert result["omnibus"]["observed_h"] == pytest.approx(
        expected["observed"]["h_statistic"]
    )


def test_kw_permutation_quiet_output(tmp_path, capsys):
    folder = tmp_path / "datasets"
    _copy_groups(
        folder,
        [
            "same_group_a.csv",
            "same_group_b.csv",
            "shifted_group_c.csv",
        ],
    )

    args = Namespace(
        command="kw-permutation",
        folder=str(folder),
        pattern="*.csv",
        column="duration",
        permutations=10,
        seed=None,
        report=None,
        summary_csv=None,
        quiet=True,
    )
    config = configparser.ConfigParser()

    result = run_kw_permutation_command(args, config, logger=None)
    stdout = capsys.readouterr().out.strip()

    assert stdout.startswith("H=")
    assert "p_perm=" in stdout
    assert "permutations=10" in stdout
    assert "seed" not in stdout
    assert "seed" not in result["omnibus"]


def test_kw_permutation_reports_require_existing_directory(tmp_path):
    folder = tmp_path / "datasets"
    _copy_groups(
        folder,
        [
            "same_group_a.csv",
            "same_group_b.csv",
            "shifted_group_c.csv",
        ],
    )

    args = Namespace(
        command="kw-permutation",
        folder=str(folder),
        pattern="*.csv",
        column="duration",
        permutations=10,
        seed=None,
        report=str(tmp_path / "missing" / "report.json"),
        summary_csv=None,
        quiet=True,
    )
    config = configparser.ConfigParser()

    with pytest.raises(FileNotFoundError) as excinfo:
        run_kw_permutation_command(args, config, logger=None)

    assert "Destination directory does not exist" in str(excinfo.value)


def test_run_cli_kw_permutation_success(tmp_path, monkeypatch, capsys):
    folder = tmp_path / "cli"
    _copy_groups(
        folder,
        [
            "same_group_a.csv",
            "same_group_b.csv",
            "shifted_group_c.csv",
        ],
    )

    monkeypatch.chdir(Path(__file__).resolve().parents[1])

    report_path = tmp_path / "result.json"
    summary_path = tmp_path / "summary.csv"

    run_cli(
        [
            "kw-permutation",
            "--folder",
            str(folder),
            "--pattern",
            "*.csv",
            "--column",
            "duration",
            "--permutations",
            "128",
            "--seed",
            "42",
            "--report",
            str(report_path),
            "--summary-csv",
            str(summary_path),
        ]
    )

    captured = capsys.readouterr().out
    assert "Kruskal–Wallis permutation test" in captured
    assert "Report written to" in captured
    assert report_path.exists()
    assert summary_path.exists()


def test_run_cli_kw_permutation_missing_folder(monkeypatch, capsys):
    monkeypatch.chdir(Path(__file__).resolve().parents[1])

    with pytest.raises(SystemExit) as excinfo:
        run_cli(
            [
                "kw-permutation",
                "--folder",
                "does-not-exist",
            ]
        )

    assert excinfo.value.code == 1
    stderr = capsys.readouterr().out
    assert "[Error]" in stderr
