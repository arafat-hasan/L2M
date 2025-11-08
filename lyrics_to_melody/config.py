"""
Configuration management for the Lyrics-to-Melody system.

This module loads environment variables and provides centralized
configuration settings for the entire application.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Centralized configuration class for the Lyrics-to-Melody system.

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
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1500"))
    API_BASE: str = os.getenv("API_BASE", "https://api.openai.com/v1")

    # Project Paths
    PROJECT_ROOT: Path = Path(__file__).parent
    OUTPUT_DIR: Path = PROJECT_ROOT / "output"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    PROMPTS_DIR: Path = PROJECT_ROOT / "llm" / "prompts"

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

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration is present.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        if not cls.OPENAI_API_KEY:
            return False

        # Create required directories if they don't exist
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)

        return True

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
