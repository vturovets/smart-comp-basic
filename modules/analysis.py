import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from scipy.stats import skew

def run_descriptive_analysis(cleaned_file, config, logger=None, mode='w'):
    try:
        df = pd.read_csv(cleaned_file, header=None)
        df.columns = ['value']
    except Exception as e:
        raise Exception(f"Failed to load cleaned file {cleaned_file}: {str(e)}")

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
    plt.hist(df['value'], bins=50, alpha=0.7, color='blue')
    plt.axvline(df['value'].mean(), color='red', linestyle='dashed', linewidth=1, label='Mean')
    plt.axvline(df['value'].median(), color='green', linestyle='dashed', linewidth=1, label='Median')
    p95 = np.percentile(df['value'], 95)
    plt.axvline(p95, color='orange', linestyle='dashed', linewidth=1, label='P95')
    plt.title(f"Histogram of {base_filename}")
    plt.xlabel("Value")
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
