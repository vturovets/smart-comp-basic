import numpy as np

def get_autosized_sample(data1, data2, requested_sample_size):
    min_available = min(len(data1), len(data2))
    effective_sample_size = min(requested_sample_size, min_available)

    sample1 = np.random.choice(data1, size=effective_sample_size, replace=False)
    sample2 = np.random.choice(data2, size=effective_sample_size, replace=False)

    return sample1, sample2, effective_sample_size