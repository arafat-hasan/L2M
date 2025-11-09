"""
Validation utilities for the l2m system.

Provides functions for validating musical parameters, note names,
and other domain-specific data.
"""

import re
from typing import Tuple, Optional

from l2m.utils.logger import get_logger

logger = get_logger(__name__)


class MusicValidator:
    """
    Validator for musical concepts and parameters.

    Provides static methods for validating notes, keys, tempos, etc.
    """

    # Valid note names (natural, sharp, flat)
    NOTE_NAMES = {
        'C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F',
        'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B'
    }

    # Valid octave range for most MIDI applications
    OCTAVE_RANGE = range(0, 9)

    # Valid time signatures
    VALID_TIME_SIGNATURES = [
        "4/4", "3/4", "2/4", "6/8", "5/4", "7/8", "9/8", "12/8"
    ]

    @staticmethod
    def validate_note(note: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a note string (e.g., 'C4', 'F#5', 'Bb3').

        Args:
            note: Note string to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not note or not isinstance(note, str):
            return False, "Note must be a non-empty string"

        # Match pattern: Note name + optional sharp/flat + octave number
        pattern = r'^([A-Ga-g])([#b]?)(\d)$'
        match = re.match(pattern, note)

        if not match:
            return False, f"Invalid note format: {note}. Expected format: C4, F#5, Bb3"

        note_name, accidental, octave = match.groups()
        note_name = note_name.upper()
        full_note = note_name + accidental

        if full_note not in MusicValidator.NOTE_NAMES:
            return False, f"Invalid note name: {full_note}"

        octave_num = int(octave)
        if octave_num not in MusicValidator.OCTAVE_RANGE:
            return False, f"Octave must be in range 0-8, got {octave_num}"

        return True, None

    @staticmethod
    def validate_key(key: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a musical key (e.g., 'C major', 'A minor').

        Args:
            key: Key string to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not key or not isinstance(key, str):
            return False, "Key must be a non-empty string"

        # Parse key: Note + mode
        parts = key.strip().split()
        if len(parts) != 2:
            return False, f"Key must be in format 'C major' or 'A minor', got: {key}"

        note_part, mode = parts
        mode = mode.lower()

        # Validate note part
        note_pattern = r'^([A-Ga-g])([#b]?)$'
        match = re.match(note_pattern, note_part)
        if not match:
            return False, f"Invalid note in key: {note_part}"

        # Validate mode
        if mode not in ['major', 'minor']:
            return False, f"Mode must be 'major' or 'minor', got: {mode}"

        return True, None

    @staticmethod
    def validate_tempo(tempo: int) -> Tuple[bool, Optional[str]]:
        """
        Validate tempo (BPM).

        Args:
            tempo: Tempo in beats per minute

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not isinstance(tempo, int):
            return False, "Tempo must be an integer"

        if tempo < 20 or tempo > 300:
            return False, f"Tempo must be between 20-300 BPM, got: {tempo}"

        return True, None

    @staticmethod
    def validate_time_signature(time_sig: str) -> Tuple[bool, Optional[str]]:
        """
        Validate time signature.

        Args:
            time_sig: Time signature (e.g., '4/4', '3/4')

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if time_sig not in MusicValidator.VALID_TIME_SIGNATURES:
            logger.warning(f"Unusual time signature: {time_sig}")
            # Still accept it but warn
            if '/' not in time_sig:
                return False, f"Time signature must contain '/', got: {time_sig}"

        return True, None

    @staticmethod
    def validate_duration(duration: float) -> Tuple[bool, Optional[str]]:
        """
        Validate note duration.

        Args:
            duration: Duration in beats

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not isinstance(duration, (int, float)):
            return False, "Duration must be a number"

        if duration <= 0:
            return False, f"Duration must be positive, got: {duration}"

        if duration > 32:
            return False, f"Duration too long (max 32 beats), got: {duration}"

        return True, None

    @staticmethod
    def validate_velocity(velocity: int) -> Tuple[bool, Optional[str]]:
        """
        Validate MIDI velocity.

        Args:
            velocity: MIDI velocity (0-127)

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not isinstance(velocity, int):
            return False, "Velocity must be an integer"

        if velocity < 0 or velocity > 127:
            return False, f"Velocity must be 0-127, got: {velocity}"

        return True, None

    @staticmethod
    def sanitize_note(note: str) -> str:
        """
        Attempt to sanitize a note string.

        Args:
            note: Potentially malformed note string

        Returns:
            str: Sanitized note string

        Raises:
            ValueError: If note cannot be sanitized
        """
        note = note.strip().upper()

        # Try to extract note name and octave
        pattern = r'([A-G][#b]?)(\d)'
        match = re.search(pattern, note)

        if match:
            return match.group(1) + match.group(2)

        raise ValueError(f"Cannot sanitize note: {note}")


class LyricsValidator:
    """
    Validator for lyrics input.
    """

    @staticmethod
    def validate_lyrics(lyrics: str) -> Tuple[bool, Optional[str]]:
        """
        Validate lyrics input.

        Args:
            lyrics: Input lyrics string

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not lyrics or not isinstance(lyrics, str):
            return False, "Lyrics must be a non-empty string"

        if len(lyrics.strip()) < 3:
            return False, "Lyrics too short (minimum 3 characters)"

        if len(lyrics) > 10000:
            return False, "Lyrics too long (maximum 10000 characters)"

        return True, None

    @staticmethod
    def normalize_lyrics(lyrics: str) -> str:
        """
        Normalize lyrics text.

        Args:
            lyrics: Raw lyrics string

        Returns:
            str: Normalized lyrics
        """
        # Remove extra whitespace
        lyrics = ' '.join(lyrics.split())

        # Ensure proper sentence endings
        lyrics = lyrics.strip()

        return lyrics
