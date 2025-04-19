import argparse
import configparser
import os
import sys
import numpy as np

from analysis import  check_unimodality_dip_test, check_unimodality_bimodality_coefficient, \
    check_unimodality_kde
from modules.input_handler import load_and_clean_csv, validate_and_clean, generate_sample
from modules.hypothesis import run_bootstrap_test, run_bootstrap_single_sample_test
from modules.logger import setup_logger
from modules.validation import validate_sample_sizes
from output import show_progress, save_results
from sampling_utils import get_autosized_sample
from modules.config import load_config

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Hypothesis Testing Tool: Compare P95 values from two datasets."
    )
    parser.add_argument("input1", help="First input CSV file")
    parser.add_argument("input2", nargs="?", default=None, help="Path to second CSV input file (optional)")
    parser.add_argument("output", nargs="?", help="Optional output text file")
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Load configuration
    config = load_config("config.txt")

    # Setup logger if configured
    # Setup logger if configured
    logger = setup_logger(config) if config.getboolean('output', 'create_log', fallback=False) else None

    sample_size = config.getint("test", "sample", fallback=10000)
    threshold = config.getfloat("test", "threshold", fallback=None)
    descriptive_enabled = config.getboolean("descriptive analysis", "Save the result to file", fallback=False)

    try:
        if args.input2 is None:
        # SINGLE FILE MODE: P95 vs threshold
            if threshold is None and not descriptive_enabled:
                sys.exit("ERROR: Threshold not specified and descriptive analysis not requested.")

            clean1 = validate_and_clean(args.input1, config)

            if not validate_sample_sizes(clean1, None, config):
                return

            #check unimodality
            if not check_unimodality_kde (clean1,config):
                return

            # Get sample
            sample1 = get_autosized_sample(clean1, None, sample_size)

            # Show progress feedback
            show_progress("Running Hypothesis Test...", 50)

            #run the test
            results = run_bootstrap_single_sample_test(sample1, config, logger)

        else:
            # TWO FILES MODE: P95 vs P95
            # Validate and clean input files
            clean1 = validate_and_clean(args.input1, config, logger)
            clean2 = validate_and_clean(args.input2, config, logger)

            if not validate_sample_sizes(clean1, clean2, config):
                return

            #check unimodality
            if not (check_unimodality_kde(clean1, config) and check_unimodality_kde(clean1, config)):
                return

            # Get samples
            sample1, sample2 = get_autosized_sample (clean1, clean2, sample_size)

            # Show progress feedback
            show_progress("Running Hypothesis Test...", 50)

            #run the test
            results = run_bootstrap_test(sample1, sample2, config, logger)

        # Output results
        save_results(results, args.output, config)

        show_progress("Complete", 100)

    except Exception as e:
        error_msg = f"[Error] {str(e)}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
