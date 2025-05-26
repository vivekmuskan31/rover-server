import logging
import os

import yaml
config = None
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

def get_logger(name: str, log_dir: str = "logs", console: bool = False) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if not logger.handlers:
        file_handler = logging.FileHandler(f"{log_dir}/{name}.log")
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        if console:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

    return logger
