import logging
import os

def setup_logger(config):
    log_enabled = config.getboolean('output', 'create_log', fallback=False)
    if not log_enabled:
        return None

    log_file = "tool.log"

    # Create logger
    logger = logging.getLogger("hypothesis_tool")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if re-running
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create file handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Define log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(fh)

    logger.debug("Logger initialized.")
    return logger
