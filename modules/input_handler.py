import pandas as pd

def validate_and_clean(file_path, config, logger=None):

    df = get_data_frame_from_csv(file_path)

    # Check if file is empty
    if df.empty:
        raise Exception(f"Input file {file_path} is empty.")

    # Check if only one column exists
    if df.shape[1] != 1:
        raise Exception(f"Input file {file_path} should contain only one column.")

    # Detect non-numeric values
    df = df[pd.to_numeric(df['value'], errors='coerce').notnull()]
    df['value'] = df['value'].astype(float)

    # Remove negative values
    df = df[df['value'] >= 0]

    # Remove outliers based on threshold
    threshold = float(config.get('input', 'outlier threshold', fallback='20000'))
    df = df[df['value'] <= threshold]

    # Remove cache responses if needed
    lower_threshold = float(config.get('input', 'lower threshold', fallback=0))
    df = df[df['value'] >= lower_threshold]

    # Prepare cleaned file path
    cleaned_path = file_path.replace(".csv", "_cleaned.csv")

    # Save cleaned data
    df.to_csv(cleaned_path, index=False, header=False)

    if logger:
        logger.info(f"Cleaning completed for {file_path}")

    return cleaned_path

def get_data_frame_from_csv(file_path):
    try:
        df = pd.read_csv(file_path, header=None, decimal='.')
        df.columns = ['value']
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return None