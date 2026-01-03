"""
Configuration management for the l2m system.

This module loads environment variables and provides centralized
configuration settings for the entire application.
"""

import logging
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use basic logging for config (before full logger is initialized)
_config_logger = logging.getLogger(__name__)


def _safe_float(
    env_var: str,
    default: float,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> float:
    """
    Safely parse a float from environment variable with validation.

    Args:
        env_var: Environment variable name
        default: Default value if parsing fails
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        float: Parsed and validated value or default
    """
    raw_value = os.getenv(env_var)

    try:
        value = float(raw_value if raw_value is not None else str(default))

        # Range validation
        if min_val is not None and value < min_val:
            _config_logger.warning(
                f"{env_var}={value} below minimum {min_val}, using default {default}"
            )
            return default

        if max_val is not None and value > max_val:
            _config_logger.warning(
                f"{env_var}={value} above maximum {max_val}, using default {default}"
            )
            return default

        return value

    except (ValueError, TypeError) as e:
        _config_logger.warning(
            f"Invalid {env_var}='{raw_value}', using default {default}. Error: {e}"
        )
        return default


def _safe_int(
    env_var: str,
    default: int,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None
) -> int:
    """
    Safely parse an integer from environment variable with validation.

    Args:
        env_var: Environment variable name
        default: Default value if parsing fails
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        int: Parsed and validated value or default
    """
    return int(_safe_float(env_var, float(default),
                          float(min_val) if min_val else None,
                          float(max_val) if max_val else None))


def _validate_url(url: str) -> bool:
    """
    Validate URL format and scheme.

    Args:
        url: URL string to validate

    Returns:
        bool: True if URL is valid
    """
    try:
        parsed = urlparse(url)

        # Must have scheme and netloc
        if not all([parsed.scheme, parsed.netloc]):
            return False

        # Only allow HTTPS (or HTTP for localhost/testing)
        if parsed.scheme not in ['https', 'http']:
            return False

        # Warn if using HTTP
        if parsed.scheme == 'http' and parsed.netloc not in ['localhost', '127.0.0.1']:
            _config_logger.warning(
                f"Using insecure HTTP URL: {url}. Consider using HTTPS."
            )

        return True
    except Exception:
        return False


def _safe_url(env_var: str, default: str) -> str:
    """
    Safely get URL from environment with validation.

    Args:
        env_var: Environment variable name
        default: Default URL

    Returns:
        str: Validated URL or default
    """
    url = os.getenv(env_var, default)

    if not _validate_url(url):
        _config_logger.warning(
            f"Invalid URL in {env_var}='{url}', using default '{default}'"
        )
        return default

    return url


class Config:
    """
    Centralized configuration class for the l2m system.

    Attributes:
        OPENAI_API_KEY: API key for OpenAI services
        MODEL_NAME: Name of the LLM model to use
        TEMPERATURE: Sampling temperature for LLM generation
        MAX_TOKENS: Maximum tokens in LLM response
        API_BASE: Base URL for OpenAI API
        PROJECT_ROOT: Root directory of the project
        OUTPUT_DIR: Directory for generated music files
        LOGS_DIR: Directory for log files
        DEFAULT_TEMPO: Default tempo when LLM fails
        DEFAULT_TIME_SIGNATURE: Default time signature
        DEFAULT_EMOTION: Default emotion classification
    """

    # OpenAI API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    TEMPERATURE: float = _safe_float("TEMPERATURE", 0.7, 0.0, 2.0)
    MAX_TOKENS: int = _safe_int("MAX_TOKENS", 1500, 1, 32000)
    API_BASE: str = _safe_url("API_BASE", "https://api.openai.com/v1")
    API_TIMEOUT: int = _safe_int("API_TIMEOUT", 30, 1, 300)

    # Project Paths
    PROJECT_ROOT: Path = Path(__file__).parent
    OUTPUT_DIR: Path = PROJECT_ROOT / "output"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    PROMPTS_DIR: Path = PROJECT_ROOT / "llm" / "prompts"
    ASSETS_DIR: Path = PROJECT_ROOT / "assets"
    SOUNDFONTS_DIR: Path = ASSETS_DIR / "soundfonts"

    # Musical Defaults (Fallback Values)
    DEFAULT_TEMPO: int = 100
    DEFAULT_TIME_SIGNATURE: str = "4/4"
    DEFAULT_EMOTION: str = "neutral"
    DEFAULT_KEY: str = "C major"
    DEFAULT_VELOCITY: int = 64

    # Emotion-to-Musical-Parameters Mapping
    EMOTION_MAP = {
        "happy": {
            "keys": ["C major", "G major", "D major"],
            "tempo_range": (100, 120),
            "contour": "ascending"
        },
        "hopeful": {
            "keys": ["G major", "D major", "A major"],
            "tempo_range": (80, 100),
            "contour": "wavy"
        },
        "sad": {
            "keys": ["A minor", "D minor", "E minor"],
            "tempo_range": (60, 80),
            "contour": "descending"
        },
        "tense": {
            "keys": ["D minor", "B minor", "F# minor"],
            "tempo_range": (90, 110),
            "contour": "erratic"
        },
        "neutral": {
            "keys": ["C major", "A minor"],
            "tempo_range": (90, 110),
            "contour": "balanced"
        },
        "calm": {
            "keys": ["F major", "Bb major"],
            "tempo_range": (60, 80),
            "contour": "balanced"
        },
        "excited": {
            "keys": ["E major", "A major"],
            "tempo_range": (120, 140),
            "contour": "ascending"
        }
    }

    # Scale definitions (note sequences for each key)
    SCALE_NOTES = {
        "C major": ["C", "D", "E", "F", "G", "A", "B"],
        "G major": ["G", "A", "B", "C", "D", "E", "F#"],
        "D major": ["D", "E", "F#", "G", "A", "B", "C#"],
        "A major": ["A", "B", "C#", "D", "E", "F#", "G#"],
        "E major": ["E", "F#", "G#", "A", "B", "C#", "D#"],
        "F major": ["F", "G", "A", "Bb", "C", "D", "E"],
        "Bb major": ["Bb", "C", "D", "Eb", "F", "G", "A"],
        "A minor": ["A", "B", "C", "D", "E", "F", "G"],
        "D minor": ["D", "E", "F", "G", "A", "Bb", "C"],
        "E minor": ["E", "F#", "G", "A", "B", "C", "D"],
        "B minor": ["B", "C#", "D", "E", "F#", "G", "A"],
        "F# minor": ["F#", "G#", "A", "B", "C#", "D", "E"]
    }

    # Audio Rendering Configuration
    SOUNDFONT_PATH: Optional[Path] = (
        Path(os.getenv("SOUNDFONT_PATH")) if os.getenv("SOUNDFONT_PATH") else None
    )
    AUDIO_SAMPLE_RATE: int = _safe_int("AUDIO_SAMPLE_RATE", 44100, 8000, 192000)
    AUDIO_FORMAT: str = os.getenv("AUDIO_FORMAT", "wav")  # wav, mp3, or both
    ENABLE_AUDIO_EXPORT: bool = os.getenv("ENABLE_AUDIO_EXPORT", "true").lower() == "true"

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration is present and valid.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        is_valid = True

        # Validate API key presence
        if not cls.OPENAI_API_KEY:
            _config_logger.error(
                "OPENAI_API_KEY not set. Please set it in .env file.\n"
                f"Expected location: {cls.PROJECT_ROOT}/.env\n"
                "Example: OPENAI_API_KEY=sk-your-key-here"
            )
            is_valid = False
        else:
            # Validate API key format
            if not cls.OPENAI_API_KEY.startswith('sk-'):
                _config_logger.warning(
                    f"API key format looks suspicious (should start with 'sk-'). "
                    f"Current: {cls.OPENAI_API_KEY[:10]}..."
                )

            if len(cls.OPENAI_API_KEY) < 20:
                _config_logger.warning(
                    f"API key seems too short (length: {len(cls.OPENAI_API_KEY)}). "
                    "Valid OpenAI keys are typically 40+ characters."
                )

        # Create required directories if they don't exist
        try:
            cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            _config_logger.debug(f"Output directory ready: {cls.OUTPUT_DIR}")
        except (PermissionError, OSError) as e:
            _config_logger.error(f"Cannot create output directory {cls.OUTPUT_DIR}: {e}")
            is_valid = False

        try:
            cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            _config_logger.debug(f"Logs directory ready: {cls.LOGS_DIR}")
        except (PermissionError, OSError) as e:
            _config_logger.error(f"Cannot create logs directory {cls.LOGS_DIR}: {e}")
            is_valid = False

        return is_valid

    @classmethod
    def get_emotion_params(cls, emotion: str) -> dict:
        """
        Get musical parameters for a given emotion.

        Args:
            emotion: The emotion classification

        Returns:
            dict: Musical parameters (keys, tempo_range, contour)
        """
        emotion_lower = emotion.lower()
        return cls.EMOTION_MAP.get(emotion_lower, cls.EMOTION_MAP["neutral"])

    @classmethod
    def get_scale_notes(cls, key: str) -> list[str]:
        """
        Get the note sequence for a given musical key.

        Args:
            key: The musical key (e.g., "C major")

        Returns:
            list[str]: List of note names in the scale
        """
        return cls.SCALE_NOTES.get(key, cls.SCALE_NOTES["C major"])


# Create a singleton config instance
config = Config()
