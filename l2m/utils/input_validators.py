"""
Input validation utilities.

Provides comprehensive validation for user inputs with descriptive error messages.
"""

from typing import Tuple, Optional
import re

from l2m.utils.logger import get_logger

logger = get_logger(__name__)


class InputValidator:
    """Validates user inputs with detailed error messages."""

    # Validation constants
    MAX_LYRICS_LENGTH = 10000
    MIN_LYRICS_LENGTH = 1
    MIN_API_KEY_LENGTH = 20

    # Valid log levels
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    @staticmethod
    def validate_lyrics(lyrics: str) -> Tuple[bool, Optional[str]]:
        """
        Validate lyrics input.

        Args:
            lyrics: Lyrics text to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
                - is_valid: True if lyrics are valid
                - error_message: Descriptive error if invalid, None if valid
        """
        # Type check
        if not isinstance(lyrics, str):
            return False, f"Lyrics must be a string, got {type(lyrics).__name__}"

        # Empty check
        if not lyrics.strip():
            return False, (
                "Lyrics cannot be empty.\n"
                "  → Please provide at least one word or phrase.\n"
                "  → Example: 'The sun will rise again'"
            )

        # Length check - minimum
        if len(lyrics.strip()) < InputValidator.MIN_LYRICS_LENGTH:
            return False, (
                f"Lyrics too short (minimum {InputValidator.MIN_LYRICS_LENGTH} character).\n"
                "  → Provide meaningful lyrics for melody generation.\n"
                "  → Example: 'Hope springs eternal'"
            )

        # Length check - maximum
        if len(lyrics) > InputValidator.MAX_LYRICS_LENGTH:
            return False, (
                f"Lyrics too long (maximum {InputValidator.MAX_LYRICS_LENGTH:,} characters, got {len(lyrics):,}).\n"
                f"  → Please reduce lyrics length by {len(lyrics) - InputValidator.MAX_LYRICS_LENGTH:,} characters.\n"
                "  → Consider splitting into multiple shorter songs."
            )

        # Security check - null bytes
        if '\x00' in lyrics:
            return False, (
                "Lyrics contain null bytes (\\x00), which are not allowed.\n"
                "  → Please remove these invalid characters.\n"
                "  → Ensure text is properly encoded (UTF-8)."
            )

        # Check for excessive non-printable characters
        non_printable_count = sum(1 for c in lyrics if ord(c) < 32 and c not in ['\n', '\r', '\t'])
        if non_printable_count > 10:
            return False, (
                f"Lyrics contain too many non-printable characters ({non_printable_count}).\n"
                "  → Please use standard text characters.\n"
                "  → Check if file encoding is correct (should be UTF-8)."
            )

        logger.debug(f"[Validation] Lyrics validated: {len(lyrics)} characters, {len(lyrics.split())} words")
        return True, None

    @staticmethod
    def validate_output_name(output_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate output file name.

        Args:
            output_name: Desired output file name (without extension)

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Type check
        if not isinstance(output_name, str):
            return False, f"Output name must be a string, got {type(output_name).__name__}"

        # Empty check
        if not output_name.strip():
            return False, (
                "Output name cannot be empty.\n"
                "  → Provide a filename for the generated melody.\n"
                "  → Example: 'my_melody' or 'song_001'"
            )

        # Length check
        if len(output_name) > 255:
            return False, (
                f"Output name too long (maximum 255 characters, got {len(output_name)}).\n"
                "  → Please use a shorter filename."
            )

        # Check for path traversal attempts
        if '..' in output_name or '/' in output_name or '\\' in output_name:
            return False, (
                "Output name contains path separators or parent directory references.\n"
                "  → Use simple filenames only (no paths).\n"
                "  → Example: 'melody' instead of '../melody' or 'folder/melody'"
            )

        logger.debug(f"[Validation] Output name validated: '{output_name}'")
        return True, None

    @staticmethod
    def validate_temperature(temp: float) -> Tuple[bool, Optional[str]]:
        """
        Validate temperature parameter for LLM.

        Args:
            temp: Temperature value (0.0 to 2.0)

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Type check
        if not isinstance(temp, (int, float)):
            return False, (
                f"Temperature must be numeric, got {type(temp).__name__}.\n"
                "  → Use a number between 0.0 and 2.0.\n"
                "  → Example: 0.7 (balanced), 0.3 (conservative), 1.5 (creative)"
            )

        # Range check
        if not (0.0 <= temp <= 2.0):
            return False, (
                f"Temperature must be in range [0.0, 2.0], got {temp}.\n"
                "  → Lower values (0.0-0.5): More focused and deterministic\n"
                "  → Medium values (0.6-1.0): Balanced creativity\n"
                "  → Higher values (1.1-2.0): More creative and varied"
            )

        logger.debug(f"[Validation] Temperature validated: {temp}")
        return True, None

    @staticmethod
    def validate_max_tokens(tokens: int) -> Tuple[bool, Optional[str]]:
        """
        Validate max tokens parameter for LLM.

        Args:
            tokens: Maximum tokens value

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Type check
        if not isinstance(tokens, int):
            return False, (
                f"Max tokens must be an integer, got {type(tokens).__name__}.\n"
                "  → Use a whole number between 1 and 32000.\n"
                "  → Example: 1500 (default), 500 (short), 4000 (long)"
            )

        # Range check
        if not (1 <= tokens <= 32000):
            return False, (
                f"Max tokens must be in range [1, 32000], got {tokens}.\n"
                "  → Typical values: 500-2000 for melody generation\n"
                "  → Higher values allow more detailed responses\n"
                "  → Note: Higher values increase API costs"
            )

        logger.debug(f"[Validation] Max tokens validated: {tokens}")
        return True, None

    @staticmethod
    def validate_api_key(key: str) -> Tuple[bool, Optional[str]]:
        """
        Validate OpenAI API key format.

        Args:
            key: API key string

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Empty check
        if not key:
            return False, (
                "API key is empty.\n"
                "  → Set OPENAI_API_KEY environment variable.\n"
                "  → Get your key from: https://platform.openai.com/api-keys\n"
                "  → Example: export OPENAI_API_KEY='sk-...'"
            )

        # Format check - OpenAI keys start with 'sk-'
        if not key.startswith('sk-'):
            return False, (
                f"API key format looks suspicious (should start with 'sk-').\n"
                f"  → Current key starts with: '{key[:10]}...'\n"
                "  → OpenAI API keys always start with 'sk-'\n"
                "  → Double-check your key from https://platform.openai.com/api-keys"
            )

        # Length check
        if len(key) < InputValidator.MIN_API_KEY_LENGTH:
            return False, (
                f"API key seems too short (length: {len(key)} characters).\n"
                "  → Valid OpenAI keys are typically 40+ characters.\n"
                "  → Ensure you copied the complete key.\n"
                "  → Get your key from: https://platform.openai.com/api-keys"
            )

        logger.debug(f"[Validation] API key validated: {key[:10]}... (length: {len(key)})")
        return True, None

    @staticmethod
    def validate_log_level(level: str) -> Tuple[bool, Optional[str]]:
        """
        Validate log level string.

        Args:
            level: Log level name

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Type check
        if not isinstance(level, str):
            return False, f"Log level must be a string, got {type(level).__name__}"

        # Case-insensitive check
        level_upper = level.upper()
        if level_upper not in InputValidator.VALID_LOG_LEVELS:
            return False, (
                f"Invalid log level: '{level}'.\n"
                f"  → Valid levels: {', '.join(InputValidator.VALID_LOG_LEVELS)}\n"
                "  → DEBUG: Detailed diagnostic information\n"
                "  → INFO: General informational messages (default)\n"
                "  → WARNING: Warning messages\n"
                "  → ERROR: Error messages\n"
                "  → CRITICAL: Critical error messages"
            )

        logger.debug(f"[Validation] Log level validated: {level_upper}")
        return True, None

    @staticmethod
    def validate_tempo(tempo: int) -> Tuple[bool, Optional[str]]:
        """
        Validate tempo (BPM) value.

        Args:
            tempo: Tempo in beats per minute

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Type check
        if not isinstance(tempo, int):
            return False, (
                f"Tempo must be an integer, got {type(tempo).__name__}.\n"
                "  → Use whole number BPM (beats per minute).\n"
                "  → Example: 120 (moderate), 60 (slow), 180 (fast)"
            )

        # Reasonable range check (20-240 BPM)
        if not (20 <= tempo <= 240):
            return False, (
                f"Tempo out of reasonable range [20, 240] BPM, got {tempo}.\n"
                "  → Slow: 40-60 BPM (ballads)\n"
                "  → Moderate: 80-120 BPM (pop, rock)\n"
                "  → Fast: 140-180 BPM (dance, electronic)\n"
                "  → Very fast: 200+ BPM (extreme genres)"
            )

        logger.debug(f"[Validation] Tempo validated: {tempo} BPM")
        return True, None

    @staticmethod
    def validate_time_signature(time_sig: str) -> Tuple[bool, Optional[str]]:
        """
        Validate time signature format.

        Args:
            time_sig: Time signature string (e.g., "4/4", "3/4", "6/8")

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Type check
        if not isinstance(time_sig, str):
            return False, f"Time signature must be a string, got {type(time_sig).__name__}"

        # Format check
        pattern = r'^\d+/\d+$'
        if not re.match(pattern, time_sig):
            return False, (
                f"Invalid time signature format: '{time_sig}'.\n"
                "  → Must be in format 'numerator/denominator'\n"
                "  → Examples: '4/4' (common time), '3/4' (waltz), '6/8' (compound)\n"
                "  → Numerator: beats per measure\n"
                "  → Denominator: note value (4=quarter, 8=eighth)"
            )

        # Parse and validate values
        try:
            numerator, denominator = time_sig.split('/')
            num = int(numerator)
            denom = int(denominator)

            # Validate numerator (typically 1-16)
            if not (1 <= num <= 16):
                return False, (
                    f"Time signature numerator out of range: {num}.\n"
                    "  → Typical values: 2, 3, 4, 5, 6, 7, 9, 12\n"
                    "  → Common: 4/4, 3/4, 6/8, 5/4"
                )

            # Validate denominator (must be power of 2: 1, 2, 4, 8, 16, 32)
            if denom not in [1, 2, 4, 8, 16, 32]:
                return False, (
                    f"Time signature denominator must be power of 2: got {denom}.\n"
                    "  → Valid values: 1, 2, 4, 8, 16, 32\n"
                    "  → 4 = quarter note (most common)\n"
                    "  → 8 = eighth note\n"
                    "  → 16 = sixteenth note"
                )

        except ValueError:
            return False, (
                f"Could not parse time signature: '{time_sig}'.\n"
                "  → Ensure format is 'number/number'\n"
                "  → Example: '4/4'"
            )

        logger.debug(f"[Validation] Time signature validated: {time_sig}")
        return True, None
