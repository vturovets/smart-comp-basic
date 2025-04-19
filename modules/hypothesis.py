# hypothesis.py
import pandas as pd
import numpy as np

def compute_ci(bootstrap_sample, alpha=0.05):
    """
    Compute the confidence interval for a bootstrap sample.
    """
    lower = np.percentile(bootstrap_sample, 100 * (alpha / 2))
    upper = np.percentile(bootstrap_sample, 100 * (1 - alpha / 2))
    return lower, upper

def bootstrap_percentile(file_path, percentile=95, iterations=1000):
    """
       Perform bootstrapping to estimate the percentile.
       """
    #data = np.asarray(data, dtype=float).flatten()  # Ensure 1D and numeric array
    try:
        data = pd.read_csv(file_path, header=None, decimal='.')
        data = pd.to_numeric(data.iloc[:, 0], errors='coerce').dropna().to_numpy()
    except Exception as e:
        raise Exception(f"Cannot read data in {file_path}: {str(e)}")
    n = len(data)
    bootstrapped = [np.percentile(np.random.choice(data, n, replace=True), percentile)
                    for _ in range(iterations)]
    return np.array(bootstrapped)

def compare_p95s(p95_sample1, p95_sample2, sample_size, alpha=0.05):
    """
    Compare two sets of bootstrapped P95 values using CI overlap and p-value.
    """
    # Confidence Intervals
    ci1 = compute_ci(p95_sample1, alpha)
    ci2 = compute_ci(p95_sample2, alpha)

    # Check CI overlap
    ci_overlap = not (ci1[1] < ci2[0] or ci2[1] < ci1[0])

    # Compute difference distribution
    diff_distribution = np.array(p95_sample1) - np.array(p95_sample2)

    # Compute p-value if needed
    if ci_overlap:
        p_value = 2 * min(
            np.mean(diff_distribution < 0),
            np.mean(diff_distribution > 0)
        )
        significant = p_value < alpha
    else:
        p_value = 0.0  # Since non-overlapping CIs indicate clear significance
        significant = True

    return {
        'p95_1': np.mean(p95_sample1),
        'p95_2': np.mean(p95_sample2),
        'ci lower p95_1': ci1[0],
        'ci upper p95_1': ci1[1],
        'ci lower p95_2': ci2[0],
        'ci upper p95_2': ci2[1],
        'p-value': p_value,
        'alpha': alpha,
        'sample size': sample_size,
        'significant difference': significant
    }

def run_bootstrap_test(sample_file_path1, sample_file_path2, config, logger):
    """
    Entry point for the CLI. Runs the bootstrapping test using config and logs the results.
    """
    alpha = float(config.get('test', 'alpha'))
    percentile = 95  # fixed for now
    iterations = int(config.get('test', 'bootstrapping iterations'))
    sample_size = _get_sample_size (sample_file_path1)

    logger.info("Starting bootstrapping for both samples...")
    p95_sample1 = bootstrap_percentile(sample_file_path1, percentile, iterations)
    p95_sample2 = bootstrap_percentile(sample_file_path2, percentile, iterations)

    logger.info("Running P95 comparison...")
    result = compare_p95s(p95_sample1, p95_sample2, sample_size, alpha)

    logger.info("Bootstrapping and comparison completed.")
    return result

def compare_p95_to_threshold(p95_samples, threshold, sample_size, alpha):
    """
    Compare a bootstrapped P95 sample distribution to a fixed threshold.
    Returns p-value and significance flag.
    """
    # Confidence Intervals
    ci1 = compute_ci(p95_samples, alpha)

    # Check CI overlap
    is_threshold_in_ci = not (ci1[1] < threshold or threshold < ci1[0])

    diff_distribution = np.array(p95_samples) - threshold
    # Compute p-value if needed
    if is_threshold_in_ci:
        p_value = 2 * min(
            np.mean(diff_distribution < 0),
            np.mean(diff_distribution > 0)
        )
        significant = p_value < alpha
    else:
        p_value = 0.0  # Since the threshold is outside of CI, the significance is clear
        significant = True

    return {
            'p95_1': np.mean(p95_samples),
            'threshold': threshold,
            'ci lower p95_1': ci1[0],
            'ci upper p95_1': ci1[1],
            'p-value': p_value,
            'alpha': alpha,
            'sample size': sample_size,
            'significant difference': significant
            }

def run_bootstrap_single_sample_test(sample_file_path1, config, logger):
    """
    Entry point for the CLI. Runs the bootstrapping test using config and logs the results.
    """
    alpha = float(config.get('test', 'alpha'))
    percentile = 95  # fixed for now
    iterations = int(config.get('test', 'bootstrapping iterations'))
    threshold = int(config.get('test', 'threshold'))
    sample_size = _get_sample_size (sample_file_path1)

    logger.info("Starting bootstrapping for single sample...")
    p95_sample1 = bootstrap_percentile(sample_file_path1, percentile, iterations)

    logger.info("Running single sample P95 comparison...")
    result = compare_p95_to_threshold(p95_sample1, threshold, sample_size, alpha)

    logger.info("Bootstrapping and comparison completed.")
    return result

def _get_sample_size(sample_file_path):
    sample_size = None
    try:
        data = pd.read_csv(sample_file_path, header=None, decimal='.')
        sample_size = len(data)
    except Exception as e:
        raise Exception(f"Cannot read data in {sample_file_path}: {str(e)}")
    return sample_size