import numpy as np

def select_random_records(df, num_records):
    """
    Select a specified number of random records from the DataFrame.
    """
    if num_records > len(df):
        num_records = len(df)
    return df.sample(n=num_records)

def select_random_sequential_records(df, num_records):
    df['date'] = pd.to_datetime(df['date'], format='mixed')
    df = df.sort_values(by='date')

    # Get random starting index that allows num_records sequential records
    max_start_idx = len(df) - num_records
    if max_start_idx < 0:
        num_records = len(df)
        max_start_idx = 0
    start_idx = np.random.randint(0, max_start_idx + 1)

    return df.iloc[start_idx:start_idx + num_records]