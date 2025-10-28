"""Configuration loading utilities."""

from __future__ import annotations

import configparser
import os
import sys
from pathlib import Path


def _resolve_config_path(config_path: str | os.PathLike | None) -> Path:
    if config_path:
        candidate = Path(config_path).expanduser()
        if candidate.exists():
            return candidate

        if candidate.name:
            fallback = Path(__file__).resolve().parents[2] / candidate.name
            if fallback.exists():
                return fallback

    return Path(__file__).resolve().parents[2] / "config.txt"


def load_config(config_path: str | os.PathLike | None = "config.txt"):
    resolved_path = _resolve_config_path(config_path)

    if not resolved_path.exists():
        print(f"\n❌ ERROR: Configuration file '{resolved_path}' not found.")
        print("👉 Please make sure the config.txt file exists in the working directory.\n")
        sys.exit(1)

    config = configparser.ConfigParser()
    try:
        config.read(resolved_path)
        return config
    except configparser.Error as exc:
        print(f"\n❌ ERROR: Failed to parse the configuration file '{resolved_path}'.")
        print(f"👉 Reason: {exc}\n")
        sys.exit(1)
