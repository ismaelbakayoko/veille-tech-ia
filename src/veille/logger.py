"""Journalisation : console + fichier logs/veille-YYYY-MM-DD.log."""

from __future__ import annotations

import logging
from pathlib import Path

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logging(log_dir: Path, date_str: str, level: int = logging.INFO) -> logging.Logger:
    """Configure le logger racine du projet et renvoie le logger 'veille'.

    Appelable plusieurs fois sans dupliquer les handlers.
    """
    logger = logging.getLogger("veille")
    logger.setLevel(level)
    if logger.handlers:
        return logger

    log_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(log_dir / f"veille-{date_str}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(console)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Logger enfant, ex. get_logger('verify') -> 'veille.verify'."""
    return logging.getLogger(f"veille.{name}")
