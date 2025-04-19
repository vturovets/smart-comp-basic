import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from scipy.stats import skew
from scipy.stats import kurtosis
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde
from input_handler import get_data_frame_from_csv
from diptest import diptest

def run_descriptive_analysis(cleaned_file, config, logger=None, mode='w'):

    df = get_data_frame_from_csv(cleaned_file)
    results = {}

    if config.getboolean('descriptive analysis', 'mean', fallback=False):
        results['mean'] = df['value'].mean()
    if config.getboolean('descriptive analysis', 'median', fallback=False):
        results['median'] = df['value'].median()
    if config.getboolean('descriptive analysis', 'min', fallback=False):
        results['min'] = df['value'].min()
    if config.getboolean('descriptive analysis', 'max', fallback=False):
        results['max'] = df['value'].max()
    if config.getboolean('descriptive analysis', 'sample size', fallback=False):
        results['sample size'] = df['value'].count()
    if config.getboolean('descriptive analysis', 'standard deviation', fallback=False):
        results['standard deviation'] = df['value'].std()
    if config.getboolean('descriptive analysis', 'skewness', fallback=False):
        results['skewness'] = skew(df['value'])

    base_filename = os.path.basename(cleaned_file).replace("_cleaned.csv", "")
    output_txt = "descriptive.txt"

    if config.getboolean('descriptive analysis', 'save the result to file', fallback=True):
        with open(output_txt, mode) as f:
            f.write(f"data set={base_filename}\n")
            for k, v in results.items():
                if k == 'sample size':
                    f.write(f"{k}={int(v)}\n")
                else:
                    f.write(f"{k}={v:.1f}\n")
            f.write("\n")
    else:
        print(f"data set={base_filename}")
        for k, v in results.items():
            if k == 'sample size':
                print(f"{k}={int(v)}")
            print(f"{k}={v:.1f}")

    if config.getboolean('descriptive analysis', 'diagraming', fallback=False):
        _generate_histogram(df, base_filename, config)
        _generate_boxplot(df, base_filename, config)

    if logger:
        logger.info(f"Descriptive analysis completed for {cleaned_file}")

def _generate_histogram(df, base_filename, config):
    plt.figure()
    plt.hist(df['value'], bins=50, alpha=0.7)
    plt.axvline(df['value'].mean(), color='red', linestyle='dashed', linewidth=1, label=f'Mean: {df['value'].mean():.1f} ms')
    plt.axvline(df['value'].median(), color='green', linestyle='dashed', linewidth=1, label=f'Median: {df['value'].median():.1f} ms')
    p95 = np.percentile(df['value'], 95)
    plt.axvline(p95, color='orange', linestyle='dashed', linewidth=1, label=f'P95: {p95:.1f} ms')

    plt.title(f"Histogram of {base_filename}")
    plt.xlabel('Response time, ms')
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"histogram_{base_filename}.png")
    plt.close()

def _generate_boxplot(df, base_filename, config):
    plt.figure()
    plt.boxplot(df['value'], vert=False)
    plt.title(f"Boxplot of {base_filename}")
    plt.xlabel("Value")
    plt.tight_layout()
    plt.savefig(f"boxplot_{base_filename}.png")
    plt.close()

def check_unimodality_kde(cleaned_file, config, logger=None):
    #get config data
    bandwidth = config.get('descriptive analysis', 'bandwidth')
    peak_prominence = float(config.get('descriptive analysis', 'peak_prominence'))
    df = get_data_frame_from_csv(cleaned_file)
    data = df.iloc[:, 0].dropna().values
    kde = gaussian_kde(data, bw_method=bandwidth)

    x_grid = np.linspace(data.min(), data.max(), 1000)
    kde_values = kde(x_grid)

    kde_values = pd.Series(kde_values).rolling(window=5, center=True, min_periods=1).mean().values

    # Automatically estimate prominence if not given
    max_kde = np.max(kde_values)

    peak_prominence = 0.01 * max_kde  # more lenient than before

    # Always include the global maximum as the main peak
    main_peak_index = np.argmax(kde_values)

    # Detect other peaks
    peaks, properties = find_peaks(kde_values, prominence=peak_prominence)

    # Ensure main peak is counted
    all_peaks = set(peaks)
    all_peaks.add(main_peak_index)
    peak_count = len(all_peaks)

    is_unimodal = peak_count == 1

    is_unimodal = peak_count == 1
    if not is_unimodal:
        print(f"⚠️ Warning: Input file {cleaned_file} contains data that does not meet unimodality condition. Only descriptive analysis is allowed.")

    if logger:
        logger.info(f"Unimodality check completed for {cleaned_file}")

    return is_unimodal

def check_unimodality_dip_test(cleaned_file):
    df = get_data_frame_from_csv(cleaned_file)
    data = df.iloc[:, 0].dropna().values
    stat, p_value = diptest(data)
    is_unimodal = p_value > 0.05
    return is_unimodal

def check_unimodality_bimodality_coefficient(cleaned_file):
    df = get_data_frame_from_csv(cleaned_file)
    data = df.iloc[:, 0].dropna().values
    g = skew(data)
    k = kurtosis(data, fisher=False)
    bc = (g**2 + 1) / k
    is_unimodal = bc < 0.55
    return is_unimodal