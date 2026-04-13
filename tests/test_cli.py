"""Tests for the CLI helpers using stubbed dependencies."""

import configparser
import io
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from smart_comp.cli.app import _add_visual_analysis, _remove_cleaned_files, parse_arguments


def test_parse_arguments_single_input(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["cli.py", "input1.csv"])

    args = parse_arguments()

    assert args.input1 == "input1.csv"
    assert args.input2 is None
    assert args.output is None


def test_parse_arguments_two_inputs_and_output(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["cli.py", "input1.csv", "input2.csv", "result.txt"])

    args = parse_arguments()

    assert args.input1 == "input1.csv"
    assert args.input2 == "input2.csv"
    assert args.output == "result.txt"


def test_remove_cleaned_files(tmp_path):
    temp_file = tmp_path / "file_cleaned.csv"
    temp_file.write_text("content")
    logger_calls = {"info": [], "warning": []}

    class DummyLogger:
        def info(self, message):
            logger_calls["info"].append(message)

        def warning(self, message):
            logger_calls["warning"].append(message)

    _remove_cleaned_files([temp_file], DummyLogger())

    assert not temp_file.exists()
    assert any("Removed cleaned file" in message for message in logger_calls["info"])


def test_add_visual_analysis_includes_new_diagrams():
    config = configparser.ConfigParser()
    config.add_section("output")
    config.set("output", "normal_probability_qq_plot", "true")
    config.set("output", "lag_plot", "true")
    config.set("output", "run_sequence_plot", "true")
    config.set("output", "histogram", "false")
    config.set("output", "kde_plot", "false")
    config.set("output", "boxplot", "false")

    handle = io.StringIO()
    _add_visual_analysis(handle, config, "sample.csv")
    output = handle.getvalue()

    assert "normal_probability_qq_plot_sample.png" in output
    assert "lag_plot_sample.png" in output
    assert "run_sequence_plot_sample.png" in output
