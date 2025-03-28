import logging

def setup_logger(config):
    logger = logging.getLogger("hypothesis_tool")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("tool.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.debug("[Stub] Logger initialized")
    return logger