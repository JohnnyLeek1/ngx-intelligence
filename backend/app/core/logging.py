"""
Logging configuration for ngx-intelligence.

Provides structured logging with rotation and multiple output handlers.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from logging.handlers import RotatingFileHandler


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    app_name: str = "ngx-intelligence",
) -> None:
    """
    Configure application logging with console and file handlers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (None = logs only to console)
        app_name: Application name for logger identification
    """
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)

    # File handlers (if log directory specified)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Application log (all messages)
        app_log_path = log_dir / f"{app_name}.log"
        app_handler = RotatingFileHandler(
            app_log_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(app_handler)

        # Error log (errors and critical only)
        error_log_path = log_dir / f"{app_name}-error.log"
        error_handler = RotatingFileHandler(
            error_log_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)

        # Processing log (dedicated for document processing)
        processing_log_path = log_dir / f"{app_name}-processing.log"
        processing_handler = RotatingFileHandler(
            processing_log_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=10,
        )
        processing_handler.setLevel(logging.INFO)
        processing_handler.setFormatter(detailed_formatter)

        # Create processing logger
        processing_logger = logging.getLogger("processing")
        processing_logger.addHandler(processing_handler)
        processing_logger.setLevel(logging.INFO)

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
