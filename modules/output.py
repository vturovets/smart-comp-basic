import os

def save_results(results: dict, output_path: str, config):
    lines = []

    test_title = "p95 bootstrapping comparison"
    lines.append(f"Test title: {test_title}")

    def write_if_enabled(key, label=None):
        if config.getboolean('output', key, fallback=False):
            value = results.get(label or key)
            if isinstance(value, float):
                if key=='p-value' or key=='alpha':
                    lines.append(f"{label or key}={value:.2f}")
                else:
                    lines.append(f"{label or key}={value:.1f}")
            else:
                lines.append(f"{label or key}={value}")

    write_if_enabled('p95_1')
    write_if_enabled('p95_2')
    write_if_enabled('ci lower diff', 'ci lower diff')
    write_if_enabled('ci upper diff', 'ci upper diff')
    write_if_enabled('ci lower p95_1', 'ci lower p95_1')
    write_if_enabled('ci upper p95_1', 'ci upper p95_1')
    write_if_enabled('ci lower p95_2', 'ci lower p95_2')
    write_if_enabled('ci upper p95_2', 'ci upper p95_2')
    write_if_enabled('p-value', 'p-value')
    write_if_enabled('alpha')
    write_if_enabled('sample size', 'sample size')
    write_if_enabled('Significant difference', 'significant difference')
    write_if_enabled('margin of error p95_1, %')
    write_if_enabled('margin of error p95_2, %')

    content = "\n".join(lines)

    if output_path:
        with open(output_path, "w") as f:
            f.write(content)
    else:
        print(content)

def show_progress(message, percent):
    print(f"{message} [{percent}%]")
