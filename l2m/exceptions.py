"""
Custom exception hierarchy for the l2m system.

Provides specific exceptions for different error scenarios with actionable error messages.
"""


class LyricsToMelodyError(Exception):
    """Base exception for all l2m errors."""

    def __init__(self, message: str, details: str = ""):
        """
        Initialize exception with message and optional details.

        Args:
            message: Main error message
            details: Additional details or guidance (optional)
        """
        self.message = message
        self.details = details

        full_message = message
        if details:
            full_message = f"{message}\n{details}"

        super().__init__(full_message)


# Input/Validation Errors


class ValidationError(LyricsToMelodyError):
    """Raised when input validation fails."""
    pass


class LyricsValidationError(ValidationError):
    """Raised when lyrics input is invalid."""
    pass


class ConfigurationError(LyricsToMelodyError):
    """Raised when configuration is invalid or missing."""
    pass


class InvalidAPIKeyError(ConfigurationError):
    """Raised when API key is invalid or missing."""

    def __init__(self, message: str = ""):
        default_message = "OpenAI API key is invalid or not configured."
        details = (
            "  → Set OPENAI_API_KEY environment variable\n"
            "  → Get your key from: https://platform.openai.com/api-keys\n"
            "  → Example: export OPENAI_API_KEY='sk-...'"
        )
        super().__init__(message or default_message, details)


class InvalidConfigValueError(ConfigurationError):
    """Raised when a configuration value is invalid."""
    pass


# API/Network Errors


class APIError(LyricsToMelodyError):
    """Base class for API-related errors."""
    pass


class APIConnectionError(APIError):
    """Raised when unable to connect to the API."""

    def __init__(self, message: str = "", cause: Exception = None):
        default_message = "Failed to connect to OpenAI API."
        details = (
            "  → Check your internet connection\n"
            "  → Verify API endpoint is reachable\n"
            "  → Check firewall settings"
        )
        if cause:
            details += f"\n  → Underlying error: {cause}"

        super().__init__(message or default_message, details)


class APITimeoutError(APIError):
    """Raised when API request times out."""

    def __init__(self, timeout: int = None, message: str = ""):
        default_message = f"API request timed out{f' after {timeout}s' if timeout else ''}."
        details = (
            "  → Try again in a moment\n"
            "  → Check network stability\n"
            "  → Consider increasing API_TIMEOUT environment variable"
        )
        super().__init__(message or default_message, details)


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, retry_after: int = None, message: str = ""):
        default_message = "OpenAI API rate limit exceeded."
        details = (
            f"  → Wait {retry_after}s before retrying\n" if retry_after
            else "  → Wait a moment before retrying\n"
        )
        details += (
            "  → Check your rate limits: https://platform.openai.com/account/rate-limits\n"
            "  → Consider upgrading your plan for higher limits"
        )
        super().__init__(message or default_message, details)


class APIResponseError(APIError):
    """Raised when API returns invalid or unexpected response."""

    def __init__(self, message: str, response_data: str = ""):
        details = "  → This may be a temporary API issue\n  → Try again in a moment"
        if response_data:
            details += f"\n  → Response data: {response_data[:200]}"

        super().__init__(message, details)


class APIQuotaExceededError(APIError):
    """Raised when API quota is exceeded."""

    def __init__(self, message: str = ""):
        default_message = "OpenAI API quota exceeded."
        details = (
            "  → Check your billing: https://platform.openai.com/account/billing\n"
            "  → Verify payment method is valid\n"
            "  → Add credits to your account"
        )
        super().__init__(message or default_message, details)


# LLM Processing Errors


class LLMError(LyricsToMelodyError):
    """Base class for LLM-related errors."""
    pass


class EmotionAnalysisError(LLMError):
    """Raised when emotion analysis fails."""

    def __init__(self, message: str = "", fallback_available: bool = True):
        default_message = "Failed to analyze emotion from lyrics."
        details = ""
        if fallback_available:
            details = "  → Using fallback emotion analysis\n  → Results may be less accurate"
        else:
            details = "  → No fallback available\n  → Check API connectivity"

        super().__init__(message or default_message, details)


class MelodyGenerationError(LLMError):
    """Raised when melody generation fails."""

    def __init__(self, message: str = "", fallback_available: bool = True):
        default_message = "Failed to generate melody."
        details = ""
        if fallback_available:
            details = "  → Using fallback melody generator\n  → Results may be simpler"
        else:
            details = "  → No fallback available\n  → Check API connectivity"

        super().__init__(message or default_message, details)


class InvalidLLMResponseError(LLMError):
    """Raised when LLM response cannot be parsed or is invalid."""

    def __init__(self, message: str, response_text: str = ""):
        details = "  → LLM returned unexpected format\n  → Using fallback generator"
        if response_text:
            details += f"\n  → Response: {response_text[:200]}..."

        super().__init__(message, details)


# Music Processing Errors


class MusicError(LyricsToMelodyError):
    """Base class for music processing errors."""
    pass


class InvalidNoteError(MusicError):
    """Raised when a note specification is invalid."""

    def __init__(self, note: str, message: str = ""):
        default_message = f"Invalid note: '{note}'"
        details = (
            "  → Use format: NoteName + Octave (e.g., 'C4', 'F#5')\n"
            "  → Valid note names: C, C#, D, D#, E, F, F#, G, G#, A, A#, B\n"
            "  → Valid octaves: 0-8"
        )
        super().__init__(message or default_message, details)


class InvalidKeyError(MusicError):
    """Raised when a musical key is invalid."""

    def __init__(self, key: str, message: str = ""):
        default_message = f"Invalid musical key: '{key}'"
        details = (
            "  → Use format: NoteName + 'major' or 'minor'\n"
            "  → Examples: 'C major', 'A minor', 'G major'"
        )
        super().__init__(message or default_message, details)


class InvalidTempoError(MusicError):
    """Raised when tempo is invalid."""

    def __init__(self, tempo: int, message: str = ""):
        default_message = f"Invalid tempo: {tempo} BPM"
        details = (
            "  → Tempo must be between 20 and 240 BPM\n"
            "  → Slow: 40-60 (ballads)\n"
            "  → Moderate: 80-120 (pop, rock)\n"
            "  → Fast: 140-180 (dance)"
        )
        super().__init__(message or default_message, details)


class InvalidTimeSignatureError(MusicError):
    """Raised when time signature is invalid."""

    def __init__(self, time_sig: str, message: str = ""):
        default_message = f"Invalid time signature: '{time_sig}'"
        details = (
            "  → Use format: 'numerator/denominator'\n"
            "  → Examples: '4/4', '3/4', '6/8'\n"
            "  → Denominator must be power of 2: 1, 2, 4, 8, 16, 32"
        )
        super().__init__(message or default_message, details)


class MIDIGenerationError(MusicError):
    """Raised when MIDI file generation fails."""

    def __init__(self, message: str, file_path: str = ""):
        details = "  → Check file permissions\n  → Ensure output directory exists"
        if file_path:
            details += f"\n  → Target path: {file_path}"

        super().__init__(message, details)


# File I/O Errors


class FileError(LyricsToMelodyError):
    """Base class for file I/O errors."""
    pass


class FileWriteError(FileError):
    """Raised when file write operation fails."""

    def __init__(self, file_path: str, message: str = "", cause: Exception = None):
        default_message = f"Failed to write file: {file_path}"
        details = (
            "  → Check file permissions\n"
            "  → Ensure directory exists\n"
            "  → Check available disk space"
        )
        if cause:
            details += f"\n  → Error: {cause}"

        super().__init__(message or default_message, details)


class FileReadError(FileError):
    """Raised when file read operation fails."""

    def __init__(self, file_path: str, message: str = "", cause: Exception = None):
        default_message = f"Failed to read file: {file_path}"
        details = (
            "  → Check file exists\n"
            "  → Check file permissions\n"
            "  → Verify file path is correct"
        )
        if cause:
            details += f"\n  → Error: {cause}"

        super().__init__(message or default_message, details)


class InvalidFileFormatError(FileError):
    """Raised when file format is invalid or unsupported."""

    def __init__(self, file_path: str, expected_format: str = "", message: str = ""):
        default_message = f"Invalid file format: {file_path}"
        details = ""
        if expected_format:
            details = f"  → Expected format: {expected_format}"

        super().__init__(message or default_message, details)


# Utility function to convert standard exceptions to custom ones


def convert_exception(exc: Exception, context: str = "") -> LyricsToMelodyError:
    """
    Convert a standard exception to a custom LyricsToMelody exception.

    Args:
        exc: The exception to convert
        context: Additional context about where the error occurred

    Returns:
        LyricsToMelodyError: Custom exception with enhanced error message
    """
    exc_type = type(exc).__name__
    exc_msg = str(exc)

    if "openai" in exc_type.lower():
        if "rate" in exc_msg.lower() or "429" in exc_msg:
            return APIRateLimitError()
        elif "timeout" in exc_msg.lower():
            return APITimeoutError()
        elif "connection" in exc_msg.lower():
            return APIConnectionError(cause=exc)
        elif "quota" in exc_msg.lower() or "insufficient" in exc_msg.lower():
            return APIQuotaExceededError()
        else:
            return APIError(f"OpenAI API error: {exc_msg}")

    elif isinstance(exc, (ConnectionError, TimeoutError)):
        return APIConnectionError(cause=exc)

    elif isinstance(exc, ValueError):
        return ValidationError(exc_msg)

    elif isinstance(exc, (IOError, OSError)):
        return FileError(exc_msg)

    else:
        # Generic wrapper
        message = f"{exc_type}: {exc_msg}"
        if context:
            message = f"{context}: {message}"
        return LyricsToMelodyError(message)
