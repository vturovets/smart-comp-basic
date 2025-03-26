import numpy as np
from scipy import stats
import pandas as pd

def calculate_percentile_ci(data):
    """
    Calculate 95th percentile and its confidence interval using binomial approximation.

    Args:
        data: DataFrame containing 'dn' column
    Returns:
        pandas Series with results
    """
    # Ensure data is numeric
    data['dn'] = pd.to_numeric(data['dn'], errors='coerce')

    # Calculate sample size
    n = len(data)

    # Calculate 95th percentile
    p95 = np.percentile(data['dn'], 95)

    # For 95th percentile, p = 0.95
    p = 0.95

    # Calculate confidence interval using binomial approximation
    # For 95% confidence level, alpha = 0.05
    alpha = 0.05

    # Calculate ranks for confidence interval
    # Using normal approximation to binomial
    z = stats.norm.ppf(1 - alpha/2)

    # Standard error for binomial proportion
    se = np.sqrt(p * (1-p) / n)

    # Calculate rank numbers for CI
    lower_rank = int(np.round((n * p - z * np.sqrt(n * p * (1-p)))))
    upper_rank = int(np.round((n * p + z * np.sqrt(n * p * (1-p)))))

    # Ensure ranks are within valid range
    lower_rank = max(1, lower_rank)
    upper_rank = min(n, upper_rank)

    # Sort data to find values at ranks
    sorted_data = np.sort(data['dn'])
    ci_lower = sorted_data[lower_rank-1]  # -1 because Python uses 0-based indexing
    ci_upper = sorted_data[upper_rank-1]

    # Calculate margin of error as percentage
    margin_error = ((ci_upper - ci_lower) / (2 * p95)) * 100

    # Create output DataFrame
    df_out = pd.DataFrame({
        'var_name': ['p95', 'ci_lower', 'ci_upper', 'margin_error', 'sample_size'],
        'counts': [p95, ci_lower, ci_upper, margin_error, n]
    })

    # Return grouped results
    shares = df_out.groupby('var_name')['counts'].first()
    return shares

def compare_p95(df1, df2, bootstrappingIterations=1000):
    # Ensure data is numeric
    df1['dn'] = pd.to_numeric(df1['dn'], errors='coerce')
    df2['dn'] = pd.to_numeric(df2['dn'], errors='coerce')

    # Calculate sample size
    n = len(df1)

    p95_1 = np.percentile(df1['dn'], 95)
    p95_2 = np.percentile(df2['dn'], 95)

# Initialize array to store bootstrap percentiles
    bootstrap_percentiles1 = np.zeros(bootstrappingIterations)
    bootstrap_percentiles2 = np.zeros(bootstrappingIterations)
    bootstrap_diffs = np.zeros(bootstrappingIterations)

    # Perform bootstrap iterations
    for i in range(bootstrappingIterations):
        # Sample with replacement
        bootstrap_sample1 = df1['dn'].sample(n=n, replace=True)
        bootstrap_sample2 = df2['dn'].sample(n=n, replace=True)
        # Calculate 95th percentile for bootstrap sample
        bootstrap_percentiles1[i] = np.percentile(bootstrap_sample1, 95)
        bootstrap_percentiles2[i] = np.percentile(bootstrap_sample2, 95)
        # Calculate difference between percentiles
        bootstrap_diffs[i] = bootstrap_percentiles1[i] - bootstrap_percentiles2[i]

    # Calculate observed difference
    observed_diff = p95_1 - p95_2

    # Calculate p-value (two-sided test)
    p_value = np.mean(np.abs(bootstrap_diffs) >= np.abs(observed_diff))

    # Calculate confidence intervals for the difference
    alpha = 0.05  # 95% confidence level
    ci_lower = np.percentile(bootstrap_diffs, alpha/2 * 100)
    ci_upper = np.percentile(bootstrap_diffs, (1-alpha/2) * 100)

    # Determine test conclusion based on p-value
    test_result = "True" if p_value < alpha else "False"

    # Create output DataFrame
    df_out = pd.DataFrame({
        'var_name': ['p95_1', 'p95_2', 'ci_lower_diff', 'ci_upper_diff', 'p_value', 'Significant difference', 'sample_size'],
        'counts': [p95_1, p95_2, ci_lower, ci_upper, p_value, test_result, n]
    })
    shares = df_out.groupby('var_name')['counts'].first()
    return shares