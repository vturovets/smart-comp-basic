
def report_p95_intensity(df, col):
    """
    Report the 95th percentile of a column in a dataframe.
    """
    return df[col].quantile(0.95)