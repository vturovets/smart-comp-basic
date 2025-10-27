"""Tests for the CLI helpers using stubbed dependencies."""

import sys
import types
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

numpy_stub = types.ModuleType("numpy")
numpy_stub.integer = int
numpy_stub.floating = float
numpy_stub.bool_ = bool
sys.modules.setdefault("numpy", numpy_stub)


def _stub_module(name: str, **attrs):
    module = types.ModuleType(name)
    for attr_name, value in attrs.items():
        setattr(module, attr_name, value)
    sys.modules[name] = module
    return module


# Provide the minimal set of stubs required by cli.py at import time.
_stub_module("modules.analysis", check_unimodality_kde=lambda *_, **__: True, run_descriptive_analysis=lambda *_, **__: {})
_stub_module("modules.interpretation", interpret_results=lambda *_, **__: "")
_stub_module("modules.input_handler", validate_and_clean=lambda path, *_: f"{path}_cleaned")
_stub_module("modules.hypothesis", run_bootstrap_test=lambda *_, **__: {}, run_bootstrap_single_sample_test=lambda *_, **__: {})
_stub_module("modules.logger", setup_logger=lambda *_: None)
_stub_module("modules.validation", validate_sample_sizes=lambda *_, **__: True, validate_ratio_scale=lambda *_, **__: True)
_stub_module("modules.output", show_progress=lambda *_, **__: None, save_results=lambda *_, **__: None)
_stub_module("modules.sampling_utils", get_autosized_sample=lambda *_, **__: "sampled.csv")

# cli.py still relies on the real config/utils modules which are lightweight, so we
# import it only after injecting the stubs above.
from cli import _remove_cleaned_files, parse_arguments


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
