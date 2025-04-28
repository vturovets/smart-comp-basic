import configparser
import sys
import os

def load_config(config_path="config.txt"):
    """
    Load the configuration file safely.
    If the file is missing or cannot be parsed, exit gracefully.
    """
    if not os.path.exists(config_path):
        print(f"\n❌ ERROR: Configuration file '{config_path}' not found.")
        print("👉 Please make sure the config.txt file exists in the working directory.\n")
        sys.exit(1)

    config = configparser.ConfigParser()
    try:
        config.read(config_path)
        return config
    except configparser.Error as e:
        print(f"\n❌ ERROR: Failed to parse the configuration file '{config_path}'.")
        print(f"👉 Reason: {e}\n")
        sys.exit(1)
