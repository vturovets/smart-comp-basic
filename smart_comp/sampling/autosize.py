"""Helpers for sampling data frames."""

from __future__ import annotations

from smart_comp.io import get_data_frame_from_csv


def get_autosized_sample(
    file_path1: str,
    file_path2: str | None = None,
    requested_sample_size: int | None = None,
):
    """Return one or two sampled CSV paths sized to the available data."""
    data1 = get_data_frame_from_csv(file_path1)
    data2 = get_data_frame_from_csv(file_path2) if file_path2 else None

    if data2 is None:
        available = len(data1)
        effective_sample_size = min(requested_sample_size, available)
        sample1 = data1.sample(n=effective_sample_size, random_state=42)
        sample1_path = file_path1.replace("_cleaned.csv", "_sample.csv")
        sample1.to_csv(sample1_path, index=False, header=False)
        return sample1_path

    min_available = min(len(data1), len(data2))
    effective_sample_size = min(requested_sample_size, min_available)

    sample1 = data1.sample(n=effective_sample_size, random_state=42)
    sample1_path = file_path1.replace("_cleaned.csv", "_sample.csv")
    sample1.to_csv(sample1_path, index=False, header=False)

    sample2 = data2.sample(n=effective_sample_size, random_state=42)
    sample2_path = file_path2.replace("_cleaned.csv", "_sample.csv")
    sample2.to_csv(sample2_path, index=False, header=False)

    return sample1_path, sample2_path
