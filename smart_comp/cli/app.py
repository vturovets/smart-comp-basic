"""Command line interface for the smart-comp toolkit."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable

from smart_comp.analysis import check_unimodality_kde, run_descriptive_analysis
from smart_comp.config import load_config
from smart_comp.interpretation import interpret_results
from smart_comp.io import save_results, show_progress, validate_and_clean
from smart_comp.logging import setup_logger
from smart_comp.sampling import get_autosized_sample
from smart_comp.stats import run_bootstrap_single_sample_test, run_bootstrap_test
from smart_comp.utils import get_base_filename
from smart_comp.validation import validate_ratio_scale, validate_sample_sizes

_CLEANED_FILES: list[Path] = []


def parse_arguments(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hypothesis Testing Tool: Compare P95 values from one or two datasets."
    )
    parser.add_argument("paths", nargs="+", help="One or two input CSVs, plus optional output TXT")
    args = parser.parse_args(list(argv) if argv is not None else None)

    paths = args.paths
    input1 = paths[0]
    input2 = None
    output = None

    if len(paths) == 2:
        if paths[1].lower().endswith(".csv"):
            input2 = paths[1]
        else:
            output = paths[1]
    elif len(paths) >= 3:
        input2 = paths[1]
        output = paths[2]

    return argparse.Namespace(input1=input1, input2=input2, output=output)


def main(config, logger=None) -> None:
    args = parse_arguments()

    sample_size = config.getint("test", "sample", fallback=10000)
    threshold = config.getfloat("test", "threshold", fallback=None)
    descriptive_enabled = config.getboolean("descriptive analysis", "required", fallback=False)
    unimodality_enabled = config.getboolean(
        "descriptive analysis", "unimodality_test_enabled", fallback=True
    )
    results: dict[str, dict] = {}

    try:
        if args.input2 is None:
            if threshold is None and not descriptive_enabled:
                sys.exit(
                    "ERROR: Threshold not specified and descriptive analysis not requested."
                )

            clean1 = validate_and_clean(args.input1, config)
            _CLEANED_FILES.append(Path(clean1))

            if not validate_ratio_scale(clean1, config, logger):
                sys.exit(
                    f"ERROR: {args.input1} does not meet Ratio Scale requirements."
                )

            if descriptive_enabled:
                results["001_descriptive_analysis1"] = run_descriptive_analysis(clean1, config)
                if config.getboolean("descriptive analysis", "descriptive only", fallback=False):
                    print("\nOnly descriptive analysis has been requested.")
                    save_results(results, args.output, config)
                    if config.getboolean("interpretation", "explain the result", fallback=False):
                        _interpret_results(results, config, args.input1)
                    return

            if not validate_sample_sizes(clean1, None, config):
                return

            if unimodality_enabled and not check_unimodality_kde(clean1, config):
                return

            sample1 = get_autosized_sample(clean1, None, sample_size)
            _CLEANED_FILES.append(Path(sample1))

            show_progress("Running Hypothesis Test...", 50)
            results["002_comp_P95_to_threshold"] = run_bootstrap_single_sample_test(
                sample1, config, logger
            )
            show_progress("Hypothesis Test completed", 100)
        else:
            clean1 = validate_and_clean(args.input1, config, logger)
            clean2 = validate_and_clean(args.input2, config, logger)
            _CLEANED_FILES.extend([Path(clean1), Path(clean2)])

            if not validate_ratio_scale(clean1, config, logger):
                sys.exit(
                    f"ERROR: {args.input1} does not meet Ratio Scale requirements."
                )
            if not validate_ratio_scale(clean2, config, logger):
                sys.exit(
                    f"ERROR: {args.input2} does not meet Ratio Scale requirements."
                )

            if descriptive_enabled:
                results["001_descriptive_analysis1"] = run_descriptive_analysis(clean1, config)
                results["002_descriptive_analysis2"] = run_descriptive_analysis(clean2, config)
                if config.getboolean("descriptive analysis", "descriptive only", fallback=False):
                    print("\nOnly descriptive analysis has been requested")
                    save_results(results, args.output, config)
                    if config.getboolean("interpretation", "explain the result", fallback=False):
                        _interpret_results(results, config, args.input1, args.input2)
                    return

            if not validate_sample_sizes(clean1, clean2, config):
                return

            if unimodality_enabled and not (
                check_unimodality_kde(clean1, config)
                and check_unimodality_kde(clean2, config)
            ):
                return

            sample1, sample2 = get_autosized_sample(clean1, clean2, sample_size)
            _CLEANED_FILES.extend([Path(sample1), Path(sample2)])

            show_progress("Running Hypothesis Test...", 50)
            results["003_comp_2_P95s"] = run_bootstrap_test(sample1, sample2, config, logger)
            show_progress("Hypothesis Test completed", 100)

        save_results(results, args.output, config)

        if config.getboolean("interpretation", "explain the result", fallback=False):
            _interpret_results(results, config, args.input1, args.input2)

        show_progress("Complete.", 100)

    except Exception as exc:
        error_msg = f"[Error] {exc}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        sys.exit(1)


def _interpret_results(results, config, input1, input2=None) -> None:
    show_progress("Running Interpretation ...", 10)
    interpretation_text = interpret_results(results, config)
    if config.getboolean("interpretation", "save the results into file", fallback=False):
        interp_file = "interpretation.md"
        with open(interp_file, "w", encoding="utf-8") as handle:
            handle.write(interpretation_text)
            _add_visual_analysis(handle, config, input1, input2)
            print(f"\nInterpretation saved to {interp_file}")
    else:
        print("\nInterpretation:")
        print(interpretation_text)


def _add_visual_analysis(handle, config, input_file1, input_file2=None) -> None:
    if not (
        config.getboolean("output", "histogram", fallback=False)
        or config.getboolean("output", "kde_plot", fallback=False)
    ):
        return

    handle.write("\n## Visual Analysis\n")

    base_filename1 = get_base_filename(input_file1)
    if config.getboolean("output", "histogram", fallback=False):
        handle.write(f"![Histogram](histogram_{base_filename1}.png)\n")
    if config.getboolean("output", "kde_plot", fallback=False):
        handle.write(f"![KDE Plot](kde_peaks_{base_filename1}.png)\n")

    if input_file2:
        base_filename2 = get_base_filename(input_file2)
        if config.getboolean("output", "histogram", fallback=False):
            handle.write(f"![Histogram](histogram_{base_filename2}.png)\n")
        if config.getboolean("output", "kde_plot", fallback=False):
            handle.write(f"![KDE Plot](kde_peaks_{base_filename2}.png)\n")


def _remove_cleaned_files(cleaned_files: Iterable[Path], log=None) -> None:
    for path in cleaned_files:
        try:
            os.remove(path)
            if log:
                log.info(f"Removed cleaned file: {path}")
        except Exception as exc:
            if log:
                log.warning(f"Could not remove {path}: {exc}")


def run_cli() -> None:
    config = load_config("config.txt")
    logger = setup_logger(config) if config.getboolean("output", "create_log", fallback=False) else None
    main(config, logger)
    if config.getboolean("clean", "clean_all", fallback=False):
        _remove_cleaned_files(_CLEANED_FILES, logger)
