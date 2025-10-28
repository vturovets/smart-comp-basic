"""Backward compatible entry point for the CLI."""

from smart_comp.cli.app import _remove_cleaned_files, main, parse_arguments, run_cli

__all__ = ["_remove_cleaned_files", "main", "parse_arguments", "run_cli"]


if __name__ == "__main__":
    run_cli()
