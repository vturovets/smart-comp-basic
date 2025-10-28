"""Tests for configuration loading utilities."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from smart_comp.config import load_config


def test_load_config_returns_parser_for_unknown_path(tmp_path):
    # Provide a non-existing configuration file name; the loader should fall back
    # to the repository default and still return a usable ConfigParser instance.
    config = load_config(tmp_path / "missing_config.ini")

    assert config.getboolean("output", "create_log") is True
