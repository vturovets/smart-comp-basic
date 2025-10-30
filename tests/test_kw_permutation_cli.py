"""Tests for the kw-permutation CLI command."""

from __future__ import annotations

import configparser
import json
from argparse import Namespace
from pathlib import Path

import numpy as np
import pytest

from smart_comp.cli.app import parse_arguments
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


def _create_sample_csvs(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "group_a.csv").write_text("duration\n1\n2\n3\n4\n", encoding="utf-8")
    (root / "group_b.csv").write_text("duration\n2\n3\n4\n5\n", encoding="utf-8")
    (root / "group_c.csv").write_text("duration\n6\n7\n8\n9\n", encoding="utf-8")


def test_kw_permutation_command_generates_outputs(tmp_path, capsys):
    folder = tmp_path / "data"
    _create_sample_csvs(folder)

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
    stdout = capsys.readouterr().out

    assert "Kruskal–Wallis permutation test" in stdout.splitlines()[0]
    assert "group_a.csv" in stdout
    assert "Permutation p-value" in stdout

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
    _create_sample_csvs(folder)

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
