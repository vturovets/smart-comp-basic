"""Output helpers for persisting analysis results."""

from __future__ import annotations

from typing import Any


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
