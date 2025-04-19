import pandas as pd
import numpy as np

def validate_and_clean(file_path, config, logger=None):
    try:
        df = pd.read_csv(file_path, header=None, decimal='.')
    except Exception as e:
        raise Exception(f"Cannot read data in {file_path}: {str(e)}")


    # Check if file is empty
    if df.empty:
        raise Exception(f"Input file {file_path} is empty.")

    # Check if only one column exists
    if df.shape[1] != 1:
        raise Exception(f"Input file {file_path} should contain only one column.")

    # Rename column for easier reference
    df.columns = ['value']

    # Detect non-numeric values
    df = df[pd.to_numeric(df['value'], errors='coerce').notnull()]
    df['value'] = df['value'].astype(float)

    # Remove negative values
    df = df[df['value'] >= 0]

    # Remove outliers based on threshold
    threshold = float(config.get('input', 'outlier threshold', fallback='20000'))
    df = df[df['value'] <= threshold]

    # Prepare cleaned file path
    cleaned_path = file_path.replace(".csv", "_cleaned.csv")

    # Save cleaned data
    df.to_csv(cleaned_path, index=False, header=False)

    if logger:
        logger.info(f"Cleaning completed for {file_path}")

    return cleaned_path

def generate_sample(cleaned_data, config, logger=None):
    sample_size = int(config.get('input', 'sample', fallback='0'))
    if sample_size <= 0:
        return cleaned_file  # skip sampling

    if sample_size > len(df):
        raise Exception(f"Requested sample size {sample_size} exceeds available data ({len(df)})")

    df_sample = df.sample(n=sample_size, random_state=42)

    sample_path = cleaned_file.replace("_cleaned.csv", "_sample.csv")
    df_sample.to_csv(sample_path, index=False, header=False)

    if logger:
        logger.info(f"Sample of size {sample_size} saved to {sample_path}")

    return sample_path

def load_and_clean_csv(file_path):
    try:
        data = pd.read_csv(file_path, header=None, decimal='.')
        cleaned = data.dropna()
        cleaned = cleaned[cleaned.applymap(np.isreal)].dropna()
        return cleaned.iloc[:, 0].astype(float).to_numpy()
    except Exception as e:
        raise Exception(f"Error processing file {file_path}: {e}")

def get_data_frame_from_csv(file_path):
    try:
        df = pd.read_csv(file_path, header=None, decimal='.')
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None