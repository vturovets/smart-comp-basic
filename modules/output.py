import os
import configparser
from typing import Dict, Optional

def save_results(
        results: Dict[str, object],
        output_path: Optional[str],
        config: configparser.ConfigParser
) -> None:
    lines = []

    # always print the test title
    test_title = "p95 bootstrapping comparison"
    lines.append(f"Test title: {test_title}")

    # loop through all options in the [output] section
    for key, _ in config.items('output'):
        if not config.getboolean('output', key, fallback=False):
            continue
        if key not in results:
            continue

        value = results[key]
        # apply your existing float-formatting rules
        if isinstance(value, float):
            if key in ('p-value', 'alpha'):
                text = f"{value:.2f}"
            else:
                text = f"{value:.1f}"
        else:
            text = str(value)

        lines.append(f"{key}={text}")

    content = "\n".join(lines)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        print(content)

def show_progress(message, percent):
    print(f"{message} [{percent}%]")
