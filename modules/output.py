import os
import configparser
from typing import Dict, Optional

def save_results(results: dict, output_path: str = None, config = None):
    lines = []

    def write_section(title, section):
       for key, value in section.items():
            if not("descriptive" in title):
                if key == 'operation': lines.append(f"{key}={value}")
                if config.getboolean('output', key, fallback=False):
                    lines.append(f"{key}={_get_formatted_value(value, key)}")
            else:
                lines.append(f"{key}={_get_formatted_value(value, key)}")

    # Sort section names alphabetically (skip 'operation' itself)
    sorted_keys = sorted(k for k in results if isinstance(results[k], dict))
    if sorted_keys:
        for key in sorted_keys:
            section = results[key]
            write_section(key, section)
            lines.append(f" ")
    else:
        key = next(iter(results))
        write_section(key, results[key])
        lines.append(f" ")
    output_text = "\n".join(lines)

    if output_path:
        with open(output_path, "w") as f:
            f.write(output_text)
    else:
        print(output_text)

def _get_formatted_value(value, key):
    if isinstance(value, float):
        formatted_value = f"{value:.2f}" if key in ['p-value', 'alpha'] else f"{value:.1f}"
    else:
        formatted_value = str(value)
    return formatted_value

def show_progress(message, percent):
    print(f"{message} [{percent}%]")
