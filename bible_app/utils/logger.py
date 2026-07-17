"""Application logging setup."""

import logging
from logging.handlers import RotatingFileHandler

from bible_app.config.paths import APP_DIR, USER_DATA_DIR


LOG_DIR = USER_DATA_DIR / "logs"
LOG_PATH = LOG_DIR / "app.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(level=logging.INFO):
    """Configure app-wide logging once and return the root app logger."""
    root_logger = logging.getLogger("bible_app")
    root_logger.setLevel(level)
    root_logger.propagate = False

    if not root_logger.handlers:
        log_path = _usable_log_path()
        file_handler = _file_handler_for(log_path)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)

    return root_logger


def _usable_log_path():
    for directory in (LOG_DIR, APP_DIR / "logs"):
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return directory / "app.log"
        except OSError:
            continue
    return APP_DIR / "app.log"


def _file_handler_for(log_path):
    """Create a rotating file handler, falling back if the file is blocked."""
    candidates = [log_path, APP_DIR / "logs" / "app.log", APP_DIR / "app.log"]
    last_error = None
    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            return RotatingFileHandler(candidate, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        except OSError as exc:
            last_error = exc
    raise last_error


def get_logger(name="bible_app"):
    setup_logging()
    if name == "bible_app" or name.startswith("bible_app."):
        return logging.getLogger(name)
    return logging.getLogger(f"bible_app.{name}")


logger = setup_logging()
