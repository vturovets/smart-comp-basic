import os

def get_base_filename(file_path):
    if "_cleaned.csv" in file_path:
        return os.path.basename(file_path).replace("_cleaned.csv", ".csv")
    elif "_sample.csv" in file_path:
        return os.path.basename(file_path).replace("_sample.csv", ".csv")
    return file_path

import numpy as np

def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()  # Convert numpy int/float to Python int/float
    elif isinstance(obj, np.bool_):
        return bool(obj)  # Convert numpy bool to Python bool
    else:
        return obj