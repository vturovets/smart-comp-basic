def save_results(results, output_path, config):
    print("[Stub] Saving results...")
    if output_path:
        print(f"[Stub] Writing to {output_path}")
    else:
        print("[Stub] Output to console")
        for key, value in results.items():
            print(f"{key} = {value}")

def show_progress(message, percent):
    print(f"{message} [{percent}%]")