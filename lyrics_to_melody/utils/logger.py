"""
Logging utility for the Lyrics-to-Melody system.

Provides centralized logging configuration with file and console output,
including log rotation to prevent disk space issues.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from lyrics_to_melody.config import config


class Logger:
    """
    Centralized logging manager for the application.

    Provides structured logging with both file and console handlers,
    formatted according to configuration settings.
    """

    _loggers: dict[str, logging.Logger] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls) -> None:
        """Initialize the logging system (called once)."""
        if cls._initialized:
            return

        # Ensure logs directory exists
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.LOG_LEVEL))

        # Clear existing handlers
        root_logger.handlers.clear()

        # Create formatters
        formatter = logging.Formatter(
            config.LOG_FORMAT,
            datefmt=config.LOG_DATE_FORMAT
        )

        # Rotating file handler for all logs
        # Max 10 MB per file, keep 5 backup files (total ~50 MB)
        log_file = config.LOGS_DIR / "system.log"
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            # If we can't create log file, print warning but continue
            print(f"WARNING: Cannot create log file {log_file}: {e}", file=sys.stderr)
            print("Logging will only be available to console.", file=sys.stderr)

        # Separate rotating file handler for errors only
        # Max 5 MB per file, keep 3 backup files
        error_log_file = config.LOGS_DIR / "error.log"
        try:
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=5 * 1024 * 1024,  # 5 MB
                backupCount=3,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)
        except (PermissionError, OSError) as e:
            # Non-critical if error log fails
            print(f"WARNING: Cannot create error log file {error_log_file}: {e}", file=sys.stderr)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a logger with the specified name.

        Args:
            name: Logger name (typically module name)

        Returns:
            logging.Logger: Configured logger instance
        """
        if not cls._initialized:
            cls._initialize()

        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger

        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        logging.Logger: Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return Logger.get_logger(name)


# Create module-level logger for this utility
_logger = get_logger(__name__)
