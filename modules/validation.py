import sys
import pandas as pd
from analysis import run_descriptive_analysis
from input_handler import get_data_frame_from_csv


def validate_sample_sizes(file_path1, file_path2=None, config=None):
    data2 = None
    data1 = get_data_frame_from_csv(file_path1)
    if file_path2 is not None:
        data2 = get_data_frame_from_csv(file_path2)

    min_required = config.getint("input", "minimum sample size", fallback=500)
    descriptive_required = config.getboolean("descriptive analysis", "required", fallback=True)

    insufficient_data = False
    if data2 is None:
        if len(data1) < min_required:
            print(f"⚠️ Warning: Input file contains fewer than {min_required} observations.")
            insufficient_data = True
    else:
        if len(data1) < min_required or len(data2) < min_required:
            print(f"⚠️ Warning: One or both input files contain fewer than {min_required} observations.")
            insufficient_data = True

    if insufficient_data:
        if descriptive_required:
            print("Running descriptive analysis only (fallback mode).")
            run_descriptive_analysis (file_path1, config)
            if data2 is not None:
                run_descriptive_analysis (file_path2, config)
            return False
        else:
            print("Descriptive analysis disabled. Aborting.")
            sys.exit(1)

    return True