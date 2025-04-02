# hypothesis.py

import numpy as np
from scipy.stats import scoreatpercentile

def compute_ci(bootstrap_sample, alpha=0.05):
    """
    Compute the confidence interval for a bootstrap sample.
    """
    lower = np.percentile(bootstrap_sample, 100 * (alpha / 2))
    upper = np.percentile(bootstrap_sample, 100 * (1 - alpha / 2))
    return lower, upper

def bootstrap_percentile(data, percentile=95, iterations=1000):
    """
    Perform bootstrapping to estimate the percentile.
    """
    data = np.asarray(data, dtype=float).flatten()  # Ensure 1D and numeric array
    n = len(data)
    bootstrapped = [np.percentile(np.random.choice(data, n, replace=True), percentile)
                    for _ in range(iterations)]
    return np.array(bootstrapped)

def compare_p95s(p95_sample1, p95_sample2, alpha=0.05):
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
        'p95_1_mean': np.mean(p95_sample1),
        'p95_2_mean': np.mean(p95_sample2),
        'ci_1': ci1,
        'ci_2': ci2,
        'ci_overlap': ci_overlap,
        'p_value': p_value,
        'significant': significant
    }

def run_bootstrap_test(sample1, sample2, config, logger):
    """
    Entry point for the CLI. Runs the bootstrapping test using config and logs the results.
    """
    alpha = float(config.get('test', 'alpha'))
    percentile = 95  # fixed for now
    iterations = int(config.get('test', 'bootstrapping iterations'))

    logger.info("Starting bootstrapping for both samples...")
    p95_sample1 = bootstrap_percentile(sample1, percentile, iterations)
    p95_sample2 = bootstrap_percentile(sample2, percentile, iterations)

    logger.info("Running P95 comparison...")
    result = compare_p95s(p95_sample1, p95_sample2, alpha)

    logger.info("Bootstrapping and comparison completed.")
    return result