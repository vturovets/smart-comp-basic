"""Tests for configuration helpers that keep input handling portable."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from smart_comp.config.loader import _resolve_config_path


def test_resolve_config_path_prefers_existing(tmp_path):
    custom = tmp_path / "custom.cfg"
    custom.write_text("[section]\nkey=value\n", encoding="utf-8")

    resolved = _resolve_config_path(str(custom))

    assert resolved == custom


def test_resolve_config_path_fallbacks_to_repo_default():
    expected = _resolve_config_path(None)

    # Supply a Windows-style path that certainly does not exist in the container.
    resolved = _resolve_config_path(r"C:\\nonexistent\\config.txt")

    assert resolved == expected
