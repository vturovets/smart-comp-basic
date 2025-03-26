import numpy as np
import pandas as pd


def run_bootstrapping_p95_ci(df, n_iterations=1000, confidence_level=0.95, n=3000):
    # Ensure dn is numeric
    df['dn'] = pd.to_numeric(df['dn'], errors='coerce')

    # Get sample sizeBpb
    #n = len(df)
    #n=5000

    # Initialize array to store bootstrap percentiles
    bootstrap_percentiles = np.zeros(n_iterations)

    # Perform bootstrap iterations
    for i in range(n_iterations):
        # Sample with replacement
        bootstrap_sample = df['dn'].sample(n=n, replace=True)
        # Calculate 95th percentile for bootstrap sample
        bootstrap_percentiles[i] = np.percentile(bootstrap_sample, 95)

    # Calculate mean of bootstrap percentiles
    mean_percentile = np.mean(bootstrap_percentiles)

    # Calculate confidence interval
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_percentiles, alpha/2 * 100)
    ci_upper = np.percentile(bootstrap_percentiles, (1-alpha/2) * 100)

    # Create output DataFrame
    df_out = pd.DataFrame({
        'var_name': ['mean_percentile', 'ci_lower', 'ci_upper','sample_size'],
        'counts': [mean_percentile, ci_lower, ci_upper,n]
    })

    # Return grouped results
    shares = df_out.groupby('var_name')['counts'].first()

    return shares