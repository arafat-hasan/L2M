"""
Logging utility for the Lyrics-to-Melody system.

Provides centralized logging configuration with file and console output.
"""

import logging
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

        # File handler
        log_file = config.LOGS_DIR / "system.log"
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

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
