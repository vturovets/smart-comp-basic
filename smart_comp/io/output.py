"""Output helpers for persisting analysis results."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Sequence

from smart_comp.utils import sanitize_for_json

if TYPE_CHECKING:  # typing imports for type checkers without circular dependencies
    from .folder_loader import GroupMetadata


def save_results(results: dict[str, Any], output_path: str | None = None, config=None) -> None:
    """Persist results to disk or print them to stdout."""

    def iter_lines():
        sorted_keys = sorted(k for k in results if isinstance(results[k], dict))
        if sorted_keys:
            for key in sorted_keys:
                yield from _render_section(key, results[key], config)
                yield " "
        else:
            key = next(iter(results))
            yield from _render_section(key, results[key], config)
            yield " "

    lines = list(iter_lines())
    output_text = "\n".join(lines)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(output_text)
    else:
        print(output_text)


def _render_section(title: str, section: dict[str, Any], config) -> list[str]:
    lines: list[str] = []
    for key, value in section.items():
        if "descriptive" not in title:
            if key == "operation":
                lines.append(f"{key}={value}")
            elif config.getboolean("output", key, fallback=False):
                lines.append(f"{key}={_format_value(value, key)}")
        else:
            lines.append(f"{key}={_format_value(value, key)}")
    return lines


def _format_value(value: Any, key: str) -> str:
    if isinstance(value, float):
        return f"{value:.2f}" if key in {"p-value", "alpha"} else f"{value:.1f}"
    return str(value)


def show_progress(message: str, percent: int) -> None:
    """Display progress feedback for the CLI."""
    print(f"{message} [{percent}%]")


def write_kw_permutation_reports(
    metadata: Sequence["GroupMetadata"],
    result: dict[str, Any],
    *,
    report_path: str | Path | None = None,
    summary_csv_path: str | Path | None = None,
) -> tuple[Path | None, Path | None]:
    """Persist Kruskal–Wallis permutation outputs to optional destinations.

    Args:
        metadata: Sequence of :class:`GroupMetadata` entries describing each group.
        result: Aggregated permutation test payload.
        report_path: Optional destination for a JSON report.
        summary_csv_path: Optional destination for the per-group summary CSV.

    Returns:
        A tuple containing the resolved paths for the JSON report and summary CSV
        (``None`` for any output that was not written).

    Raises:
        FileNotFoundError: If the parent directory of a destination does not exist.
        NotADirectoryError: If a parent component is not a directory.
        OSError: If writing either report fails for IO-related reasons.
    """

    if report_path is None and summary_csv_path is None:
        return None, None

    json_destination = _maybe_write_json_report(result, report_path)
    csv_destination = _maybe_write_summary_csv(metadata, summary_csv_path)
    return json_destination, csv_destination


def _maybe_write_json_report(result: dict[str, Any], path_like: str | Path | None) -> Path | None:
    if path_like is None:
        return None

    path = _validate_output_path(path_like)
    sanitized = sanitize_for_json(result)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(sanitized, handle, indent=2)
        handle.write("\n")

    return path


def _maybe_write_summary_csv(
    metadata: Iterable["GroupMetadata"], path_like: str | Path | None
) -> Path | None:
    if path_like is None:
        return None

    path = _validate_output_path(path_like)

    fieldnames = [
        "file_name",
        "n",
        "median",
        "p95",
        "dropped_non_numeric_or_nan",
        "dropped_negative",
    ]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for entry in metadata:
            writer.writerow(asdict(entry))

    return path


def _validate_output_path(path_like: str | Path) -> Path:
    path = Path(path_like).expanduser()
    parent = path.parent

    if parent and parent != Path("."):
        if not parent.exists():
            raise FileNotFoundError(
                f"Destination directory does not exist: '{parent}'"
            )
        if not parent.is_dir():
            raise NotADirectoryError(
                f"Destination parent is not a directory: '{parent}'"
            )

    return path
