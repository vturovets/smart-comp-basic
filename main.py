import pandas as pd
import numpy as np

import os
from pathlib import Path

# Configuration
mode = "extract"  # Change this to "extract", "random",  or "max_load" as needed
sampleSize = 3000


def process_all_logs():
    # Get the current project directory
    current_dir = Path.cwd()
    # Path to input and output directories
    input_dir = current_dir / 'data_input'
    output_dir = current_dir / 'data_output'

    # Check if input directory exists
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)

    # List to store results from all files
    all_results =0
    accumulated_df = None

    # Process each file in the directory
    for file_path in input_dir.glob('*'):
        if file_path.is_file():  # Make sure it's a file, not a subdirectory
            try:
                # Process the file

                print(f"Successfully processed: {file_path.name}")
            except Exception as e:
                print(f"Error processing {file_path.name}: {str(e)}")

    return accumulated_df

# Usage
if __name__ == "__main__":
    try:
        results = process_all_logs()
        if results is not None:
            results.to_csv('data_output/accumulated_Nov-30-2024.csv', index=True)
            print(f"Processed {str(results)} files successfully")
    except Exception as e:
        print(f"Error: {str(e)}")




