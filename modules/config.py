from configparser import ConfigParser

def load_config(config_path):
    config = ConfigParser()
    config.read(config_path)
    return config
