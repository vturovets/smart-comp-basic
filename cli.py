import argparse
import sys
from config_handler import parse_config
from input_handler import load_and_clean_csv
from validation import validate_sample_sizes
from sampling_utils import get_autosized_sample
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Hypothesis Testing Tool with Auto Sample Sizing")
    parser.add_argument("input1", help="Path to first input CSV file")
    parser.add_argument("input2", help="Path to second input CSV file")
    parser.add_argument("--config", default="config.txt", help="Path to config file")
    args = parser.parse_args()

    config = parse_config(args.config)
    requested_sample_size = int(config["test"].get("sample", 10000))

    data1 = load_and_clean_csv(args.input1)
    data2 = load_and_clean_csv(args.input2)

    if not validate_sample_sizes(data1, data2, config):
        return  # descriptive fallback logic would follow here

    sample1, sample2, final_sample_size = get_autosized_sample(data1, data2, requested_sample_size)

    print(f"Final autosized sample size: {final_sample_size}")
    print(f"Sample 1 stats: mean={np.mean(sample1):.2f}, size={len(sample1)}")
    print(f"Sample 2 stats: mean={np.mean(sample2):.2f}, size={len(sample2)}")

if __name__ == "__main__":
    main()