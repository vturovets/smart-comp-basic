"""Logging configuration helpers."""

from __future__ import annotations

import logging


def setup_logger(config):
    log_enabled = config.getboolean("output", "create_log", fallback=False)
    if not log_enabled:
        return None

    log_file = "tool.log"

    logger = logging.getLogger("hypothesis_tool")
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.debug("Logger initialized.")
    return logger
