import numpy as np
import pandas as pd

def run_bootstrap_test(file1, file2, config, logger=None):
    try:
        df1 = pd.read_csv(file1, header=None)
        df2 = pd.read_csv(file2, header=None)
    except Exception as e:
        raise Exception(f"Failed to read input files: {str(e)}")

    df1.columns = ['value']
    df2.columns = ['value']

    sample_size = min(len(df1), len(df2))
    iterations = int(config.get('test', 'bootstrapping iterations', fallback='1000'))
    alpha = float(config.get('test', 'alpha', fallback='0.05'))
    moe = float(config.get('test', 'MoE', fallback='5')) / 100

    boot_p95_1 = np.array([np.percentile(df1.sample(n=sample_size, replace=True)['value'], 95) for _ in range(iterations)])
    boot_p95_2 = np.array([np.percentile(df2.sample(n=sample_size, replace=True)['value'], 95) for _ in range(iterations)])

    diff_distribution = boot_p95_1 - boot_p95_2
    observed_diff = np.percentile(df1['value'], 95) - np.percentile(df2['value'], 95)

    extreme_count = np.sum(np.abs(diff_distribution) >= np.abs(observed_diff))
    p_value = extreme_count / iterations

    lower_ci = np.percentile(diff_distribution, 100 * alpha / 2)
    upper_ci = np.percentile(diff_distribution, 100 * (1 - alpha / 2))

    significant = p_value < alpha

    if logger:
        logger.info(f"Bootstrap test completed: observed_diff={observed_diff:.2f}, p={p_value:.4f}")

    return {
        'p95_1': np.percentile(df1['value'], 95),
        'p95_2': np.percentile(df2['value'], 95),
        'ci lower diff': lower_ci,
        'ci upper diff': upper_ci,
        'p-value': p_value,
        'alpha': alpha,
        'significant difference': significant,
        'sample size': sample_size
    }
