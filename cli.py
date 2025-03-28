import argparse
import os
import sys
from configparser import ConfigParser
from modules.logger import setup_logger
from modules.config import load_config
from modules.input_handler import validate_and_clean
from modules.analysis import run_descriptive_analysis
from modules.hypothesis import run_bootstrap_test
from modules.output import save_results, show_progress

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Hypothesis Testing Tool: Compare P95 values from two datasets."
    )
    parser.add_argument("input1", help="First input CSV file")
    parser.add_argument("input2", help="Second input CSV file")
    parser.add_argument("output", nargs="?", help="Optional output text file")
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Load configuration
    config = load_config("config.txt")

    # Setup logger if configured
    logger = setup_logger(config) if config.getboolean('output', 'create_log', fallback=False) else None

    try:
        # Validate and clean input files
        clean1 = validate_and_clean(args.input1, config, logger)
        clean2 = validate_and_clean(args.input2, config, logger)

        # Run descriptive statistics if enabled
        if config.getboolean('descriptive analysis', 'mean', fallback=False):
            run_descriptive_analysis(clean1, config, logger)
            run_descriptive_analysis(clean2, config, logger)

        # Show progress feedback
        show_progress("Running Hypothesis Test...", 50)

        # Run hypothesis testing
        results = run_bootstrap_test(clean1, clean2, config, logger)

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
