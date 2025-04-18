import sys

def validate_sample_sizes(data1, data2, config):
    min_required = int(config["input"].get("minimum sample size", 500))
    descriptive_required = config.getboolean("descriptive analysis", "required", fallback=True)

    if len(data1) < min_required or len(data2) < min_required:
        print(f"⚠️ Warning: One or both input files contain fewer than {min_required} observations.")
        if descriptive_required:
            print("Running descriptive analysis only (fallback mode).")
            return False
        else:
            print("Descriptive analysis disabled. Aborting.")
            sys.exit(1)
    return True