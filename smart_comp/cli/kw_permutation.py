"""Handlers for the ``kw-permutation`` CLI command."""

from __future__ import annotations

from dataclasses import asdict
from typing import Sequence

import numpy as np

from smart_comp.io import (
    GroupMetadata,
    load_group_durations,
    write_kw_permutation_reports,
)
from smart_comp.stats import kruskal_permutation_test
from smart_comp.utils import sanitize_for_json

__all__ = ["run_kw_permutation_command"]


def run_kw_permutation_command(args, config, logger=None):
    """Execute the Kruskal–Wallis permutation command and render output."""

    arrays, metadata = load_group_durations(
        folder=args.folder,
        pattern=args.pattern,
        column=args.column,
    )

    if logger:
        logger.info(
            "Loaded %s groups from '%s' using pattern '%s'", len(metadata), args.folder, args.pattern
        )

    rng = np.random.default_rng(args.seed)
    permutation_result = kruskal_permutation_test(
        arrays,
        iterations=args.permutations,
        rng=rng,
    )

    result = _assemble_result(metadata, permutation_result, args.seed)

    report_path = None
    summary_path = None

    if args.report or args.summary_csv:
        report_path, summary_path = write_kw_permutation_reports(
            metadata,
            result,
            report_path=args.report,
            summary_csv_path=args.summary_csv,
        )
        if logger:
            if report_path:
                logger.info("Wrote kw-permutation report to %s", report_path)
            if summary_path:
                logger.info("Wrote kw-permutation summary CSV to %s", summary_path)

    _render_console_output(result, quiet=args.quiet)

    if not args.quiet:
        if report_path:
            print(f"Report written to {report_path}")
        if summary_path:
            print(f"Summary CSV written to {summary_path}")

    return result


def _assemble_result(
    metadata: Sequence[GroupMetadata],
    permutation_result: dict[str, object],
    seed: int | None,
) -> dict[str, object]:
    groups = [asdict(entry) for entry in metadata]
    observed = permutation_result.get("observed", {})

    omnibus = {
        "total_n": observed.get("n_total"),
        "observed_h": observed.get("h_statistic"),
        "permutation_p": permutation_result.get("p_value"),
        "permutations": permutation_result.get("iterations"),
        "tie_correction": observed.get("tie_correction"),
        "group_sizes": observed.get("group_sizes"),
    }

    if seed is not None:
        omnibus["seed"] = seed

    payload = {
        "groups": groups,
        "omnibus": omnibus,
    }
    return sanitize_for_json(payload)


def _render_console_output(result: dict[str, object], *, quiet: bool) -> None:
    omnibus = result.get("omnibus", {})
    groups = result.get("groups", [])

    if quiet:
        line = _format_quiet_line(omnibus)
        print(line)
        return

    lines = _format_verbose_lines(groups, omnibus)
    print("\n".join(lines))


def _format_quiet_line(omnibus: dict[str, object]) -> str:
    parts = [
        f"H={float(omnibus.get('observed_h', 0.0)):.6f}",
        f"p_perm={float(omnibus.get('permutation_p', 0.0)):.6f}",
        f"N={int(omnibus.get('total_n', 0))}",
        f"permutations={int(omnibus.get('permutations', 0))}",
    ]
    tie = omnibus.get("tie_correction")
    if tie is not None:
        parts.append(f"tie={float(tie):.6f}")
    seed = omnibus.get("seed")
    if seed is not None:
        parts.append(f"seed={seed}")
    return " ".join(parts)


def _format_verbose_lines(groups: Sequence[dict[str, object]], omnibus: dict[str, object]) -> list[str]:
    headers = [
        "Group",
        "n",
        "Median",
        "P95",
        "Dropped (non-numeric/NaN)",
        "Dropped (negative)",
    ]

    rows: list[list[str]] = []
    for group in groups:
        rows.append(
            [
                str(group.get("file_name", "")),
                str(group.get("n", "")),
                f"{float(group.get('median', 0.0)):.3f}",
                f"{float(group.get('p95', 0.0)):.3f}",
                str(group.get("dropped_non_numeric_or_nan", 0)),
                str(group.get("dropped_negative", 0)),
            ]
        )

    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    table_lines: list[str] = []
    header_line = " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers))
    separator = "-+-".join("-" * widths[idx] for idx in range(len(headers)))
    table_lines.append(header_line)
    table_lines.append(separator)
    for row in rows:
        table_lines.append(" | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row)))

    lines = ["Kruskal–Wallis permutation test", ""]
    lines.extend(table_lines)
    lines.append("")

    lines.append(f"Total N: {int(omnibus.get('total_n', 0))}")
    lines.append(f"Observed H: {float(omnibus.get('observed_h', 0.0)):.6f}")
    lines.append(
        "Permutation p-value: "
        f"{float(omnibus.get('permutation_p', 0.0)):.6f} "
        f"(permutations={int(omnibus.get('permutations', 0))})"
    )

    tie = omnibus.get("tie_correction")
    if tie is not None:
        lines.append(f"Tie correction: {float(tie):.6f}")

    group_sizes = omnibus.get("group_sizes")
    if group_sizes:
        size_text = ", ".join(str(size) for size in group_sizes)
        lines.append(f"Group sizes: {size_text}")

    seed = omnibus.get("seed")
    if seed is not None:
        lines.append(f"RNG seed: {seed}")

    return lines
