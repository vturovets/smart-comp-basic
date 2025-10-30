"""Tests for the CLI helpers using stubbed dependencies."""

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from smart_comp.cli.app import _remove_cleaned_files, parse_arguments


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
