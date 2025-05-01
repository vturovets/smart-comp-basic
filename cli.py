import argparse
import os
import sys
from pathlib import Path

from modules.analysis import check_unimodality_kde, run_descriptive_analysis
from modules.interpretation import interpret_results
from modules.input_handler import validate_and_clean
from modules.hypothesis import run_bootstrap_test, run_bootstrap_single_sample_test
from modules.logger import setup_logger
from modules.validation import validate_sample_sizes, validate_ratio_scale
from modules.output import show_progress, save_results
from modules.sampling_utils import get_autosized_sample
from modules.config import load_config

# will hold all the cleaned‐CSV paths we write
_cleaned_files: list[Path] = []

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Hypothesis Testing Tool: Compare P95 values from one or two datasets."
    )
    # collect 1–3 positional paths
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or two input CSVs, plus optional output TXT",
    )
    args = parser.parse_args()
    paths = args.paths

    input1 = paths[0]
    input2 = None
    output = None

    if len(paths) == 2:
        # if second arg endswith .csv → it's a second input, otherwise it's the output file
        if paths[1].lower().endswith(".csv"):
            input2 = paths[1]
        else:
            output = paths[1]
    elif len(paths) >= 3:
        # first two are inputs, third is output; ignore extras
        input2 = paths[1]
        output = paths[2]

    return argparse.Namespace(input1=input1, input2=input2, output=output)

def main(config, logger):
    args = parse_arguments()

    sample_size = config.getint("test", "sample", fallback=10000)
    threshold = config.getfloat("test", "threshold", fallback=None)
    descriptive_enabled = config.getboolean("descriptive analysis", "required", fallback=False)
    unimodality_enabled = config.getboolean("descriptive analysis", "unimodality_test_enabled", fallback=True)
    results = {}

    try:
        if args.input2 is None:
        # SINGLE FILE MODE: P95 vs threshold
            if threshold is None and not descriptive_enabled:
                sys.exit("ERROR: Threshold not specified and descriptive analysis not requested.")

            clean1 = validate_and_clean(args.input1, config)
            _cleaned_files.append(clean1)

            if not validate_ratio_scale(clean1, config, logger):
                sys.exit(f"ERROR: {args.input1} does not meet Ratio Scale requirements.")

            if descriptive_enabled:
                results["001_descriptive_analysis1"] = run_descriptive_analysis (clean1, config)
                if config.getboolean("descriptive analysis", "descriptive only", fallback=False):
                    print("\nOnly descriptive analysis has been requested")
                    save_results(results, args.output, config)
                    return
            if not validate_sample_sizes(clean1, None, config):
                return

            #check unimodality
            if unimodality_enabled:
                if not check_unimodality_kde(clean1, config):
                    return

            # Get sample
            sample1 = get_autosized_sample(clean1, None, sample_size)
            _cleaned_files.append(sample1)

            # Show progress feedback
            show_progress("Running Hypothesis Test...", 50)

            #run the test
            results["002_comp_P95_to_threshold"] = run_bootstrap_single_sample_test(sample1, config, logger)
            show_progress("Hypothesis Test completed", 100)

        else:
            # TWO FILES MODE: P95 vs P95
            # Validate and clean input files
            clean1 = validate_and_clean(args.input1, config, logger)
            clean2 = validate_and_clean(args.input2, config, logger)
            _cleaned_files.append(clean1)
            _cleaned_files.append(clean2)

            if not validate_ratio_scale(clean1, config, logger):
                sys.exit(f"ERROR: {args.input1} does not meet Ratio Scale requirements.")
            if not validate_ratio_scale(clean2, config, logger):
                sys.exit(f"ERROR: {args.input2} does not meet Ratio Scale requirements.")

            if descriptive_enabled:
                results["001_descriptive_analysis1"] = run_descriptive_analysis (clean1, config)
                results["002_descriptive_analysis2"] = run_descriptive_analysis (clean2, config)
                if config.getboolean("descriptive analysis", "descriptive only", fallback=False):
                    print("\nOnly descriptive analysis has been requested")
                    save_results(results, args.output, config)
                    return

            if not validate_sample_sizes(clean1, clean2, config):
                return

            #check unimodality
            if unimodality_enabled:
                if not (check_unimodality_kde(clean1, config) and check_unimodality_kde(clean2, config)):
                    return

            # Get samples
            sample1, sample2 = get_autosized_sample (clean1, clean2, sample_size)
            _cleaned_files.append(sample1)
            _cleaned_files.append(sample2)

            # Show progress feedback
            show_progress("Running Hypothesis Test...", 50)

            #run the test
            results["003_comp_2_P95s"] = run_bootstrap_test(sample1, sample2, config, logger)

            show_progress("Hypothesis Test completed", 100)

        # Output results
        save_results(results, args.output, config)
        if config.getboolean("interpretation", "explain the result", fallback=False):
            show_progress("Running Interpretation ...", 10)
            interpretation_text = interpret_results(results, config)
            # Optionally save into file
            if config.getboolean('interpretation', 'save the results into file', fallback=False):
                interp_file = ("interpretation.md")
                with open(interp_file, "w", encoding="utf-8") as f:
                    f.write(interpretation_text)
                    print(f"\nInterpretation saved to {interp_file}")
            else:
                print("\nInterpretation:")
                print(interpretation_text)

        show_progress("Complete", 100)

    except Exception as e:
        error_msg = f"[Error] {str(e)}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        sys.exit(1)

def _remove_cleaned_files(_cleaned_files, log):
    for path in _cleaned_files:
        try:
            os.remove(path)
            log.info(f"Removed cleaned file: {path}")
        except Exception as e:
            log.warning(f"Could not remove {path}: {e}")

if __name__ == "__main__":
    # Load configuration
    config = load_config("config.txt")
    # Setup logger if configured
    logger = setup_logger(config) if config.getboolean('output', 'create_log', fallback=False) else None
    main(config, logger)
    if config.getboolean("clean", "clean_all", fallback=False):
        #delete aux files
        _remove_cleaned_files(_cleaned_files, logger)
