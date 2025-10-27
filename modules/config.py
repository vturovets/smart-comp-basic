import configparser
import sys
import os
from pathlib import Path


def _resolve_config_path(config_path: str | os.PathLike | None) -> Path:
    """Return a usable configuration path.

    IntelliJ creates project specific virtual environments inside the project
    directory (``.venv`` by default).  When the tests run inside that virtual
    environment, ``load_config`` receives Windows style absolute paths coming
    from the IDE configuration.  Those paths obviously do not exist inside the
    container or on other developer machines.  To make the project portable we
    try the provided path first and, if it does not exist, fall back to the
    repository level ``config.txt``.
    """

    if config_path:
        candidate = Path(config_path).expanduser()
        if candidate.exists():
            return candidate

        # Some IDEs keep the config path from another machine (e.g. Windows).
        # When that happens we still want to use the default config that ships
        # with the repository so developers can run the project without
        # editing the settings manually.
        if candidate.name:
            fallback = Path(__file__).resolve().parent.parent / candidate.name
            if fallback.exists():
                return fallback

    return Path(__file__).resolve().parent.parent / "config.txt"


def load_config(config_path: str | os.PathLike | None = "config.txt"):
    """Load the configuration file safely.

    If the file is missing or cannot be parsed, exit gracefully.  The helper
    also normalises IDE-provided paths that may point outside of the project.
    """

    resolved_path = _resolve_config_path(config_path)

    if not resolved_path.exists():
        print(f"\n❌ ERROR: Configuration file '{resolved_path}' not found.")
        print("👉 Please make sure the config.txt file exists in the working directory.\n")
        sys.exit(1)

    config = configparser.ConfigParser()
    try:
        config.read(resolved_path)
        return config
    except configparser.Error as e:
        print(f"\n❌ ERROR: Failed to parse the configuration file '{resolved_path}'.")
        print(f"👉 Reason: {e}\n")
        sys.exit(1)
