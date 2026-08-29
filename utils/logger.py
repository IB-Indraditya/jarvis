"""
utils/logger.py
Centralized logging setup used across all JARVIS modules
(Security -> Activity logging, Automation -> reports, etc.)
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from config import Config


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    log_file = os.path.join(Config.LOG_DIR, "jarvis.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=2_000_000, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
