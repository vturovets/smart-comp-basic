from modules.input_handler import get_data_frame_from_csv


def get_autosized_sample(file_path1, file_path2=None, requested_sample_size=None):
    #Returns one or two samples with auto-sized sampling based on available data and requested size.
    data2 = None
    data1 = get_data_frame_from_csv(file_path1)

    if file_path2 is not None:
        data2 = get_data_frame_from_csv(file_path2)

    if data2 is None:
        available = len(data1)
        effective_sample_size = min(requested_sample_size, available)
        sample1 = data1.sample(n=effective_sample_size, random_state=42)
        sample1_path = file_path1.replace("_cleaned.csv", "_sample.csv")
        sample1.to_csv(sample1_path, index=False, header=False)
        return sample1_path
    else:
        min_available = min(len(data1), len(data2))
        effective_sample_size = min(requested_sample_size, min_available)
        sample1 = data1.sample(n=effective_sample_size, random_state=42)
        sample1_path = file_path1.replace("_cleaned.csv", "_sample.csv")
        sample1.to_csv(sample1_path, index=False, header=False)
        sample2 = data2.sample(n=effective_sample_size, random_state=42)
        sample2_path = file_path2.replace("_cleaned.csv", "_sample.csv")
        sample2.to_csv(sample2_path, index=False, header=False)
        return sample1_path, sample2_path