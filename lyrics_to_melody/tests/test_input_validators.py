"""
Unit tests for input validation utilities.
"""

import pytest
from lyrics_to_melody.utils.input_validators import InputValidator


class TestLyricsValidation:
    """Test lyrics input validation."""

    def test_valid_lyrics(self):
        """Test validation passes for valid lyrics."""
        lyrics = "The sun will rise again"
        is_valid, error = InputValidator.validate_lyrics(lyrics)
        assert is_valid is True
        assert error is None

    def test_empty_lyrics(self):
        """Test validation fails for empty lyrics."""
        is_valid, error = InputValidator.validate_lyrics("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_whitespace_only_lyrics(self):
        """Test validation fails for whitespace-only lyrics."""
        is_valid, error = InputValidator.validate_lyrics("   \n\t  ")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_lyrics_too_long(self):
        """Test validation fails for lyrics exceeding max length."""
        long_lyrics = "A" * 10001  # Over the 10,000 character limit
        is_valid, error = InputValidator.validate_lyrics(long_lyrics)
        assert is_valid is False
        assert "too long" in error

    def test_lyrics_with_null_bytes(self):
        """Test validation fails for lyrics containing null bytes."""
        lyrics = "Hello\x00World"
        is_valid, error = InputValidator.validate_lyrics(lyrics)
        assert is_valid is False
        assert "null bytes" in error

    def test_lyrics_with_unicode(self):
        """Test validation passes for Unicode characters."""
        lyrics = "Café Münich Zürich Ñoño"
        is_valid, error = InputValidator.validate_lyrics(lyrics)
        assert is_valid is True
        assert error is None

    def test_lyrics_wrong_type(self):
        """Test validation fails for non-string input."""
        is_valid, error = InputValidator.validate_lyrics(123)
        assert is_valid is False
        assert "must be a string" in error


class TestOutputNameValidation:
    """Test output name validation."""

    def test_valid_output_name(self):
        """Test validation passes for valid output name."""
        is_valid, error = InputValidator.validate_output_name("my_melody")
        assert is_valid is True
        assert error is None

    def test_empty_output_name(self):
        """Test validation fails for empty output name."""
        is_valid, error = InputValidator.validate_output_name("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_output_name_with_path_traversal(self):
        """Test validation fails for path traversal attempts."""
        is_valid, error = InputValidator.validate_output_name("../../../etc/passwd")
        assert is_valid is False
        assert "path separators" in error

    def test_output_name_with_forward_slash(self):
        """Test validation fails for forward slash."""
        is_valid, error = InputValidator.validate_output_name("folder/file")
        assert is_valid is False
        assert "path separators" in error

    def test_output_name_with_backslash(self):
        """Test validation fails for backslash."""
        is_valid, error = InputValidator.validate_output_name("folder\\file")
        assert is_valid is False
        assert "path separators" in error

    def test_output_name_too_long(self):
        """Test validation fails for names exceeding 255 characters."""
        long_name = "A" * 256
        is_valid, error = InputValidator.validate_output_name(long_name)
        assert is_valid is False
        assert "too long" in error


class TestTemperatureValidation:
    """Test temperature parameter validation."""

    def test_valid_temperature(self):
        """Test validation passes for valid temperature."""
        is_valid, error = InputValidator.validate_temperature(0.7)
        assert is_valid is True
        assert error is None

    def test_temperature_at_min_boundary(self):
        """Test validation passes for minimum temperature (0.0)."""
        is_valid, error = InputValidator.validate_temperature(0.0)
        assert is_valid is True
        assert error is None

    def test_temperature_at_max_boundary(self):
        """Test validation passes for maximum temperature (2.0)."""
        is_valid, error = InputValidator.validate_temperature(2.0)
        assert is_valid is True
        assert error is None

    def test_temperature_below_min(self):
        """Test validation fails for temperature below 0.0."""
        is_valid, error = InputValidator.validate_temperature(-0.1)
        assert is_valid is False
        assert "must be in range" in error

    def test_temperature_above_max(self):
        """Test validation fails for temperature above 2.0."""
        is_valid, error = InputValidator.validate_temperature(2.5)
        assert is_valid is False
        assert "must be in range" in error

    def test_temperature_wrong_type(self):
        """Test validation fails for non-numeric temperature."""
        is_valid, error = InputValidator.validate_temperature("high")
        assert is_valid is False
        assert "must be numeric" in error


class TestMaxTokensValidation:
    """Test max tokens parameter validation."""

    def test_valid_max_tokens(self):
        """Test validation passes for valid max tokens."""
        is_valid, error = InputValidator.validate_max_tokens(1500)
        assert is_valid is True
        assert error is None

    def test_max_tokens_at_min_boundary(self):
        """Test validation passes for minimum tokens (1)."""
        is_valid, error = InputValidator.validate_max_tokens(1)
        assert is_valid is True
        assert error is None

    def test_max_tokens_at_max_boundary(self):
        """Test validation passes for maximum tokens (32000)."""
        is_valid, error = InputValidator.validate_max_tokens(32000)
        assert is_valid is True
        assert error is None

    def test_max_tokens_below_min(self):
        """Test validation fails for tokens below 1."""
        is_valid, error = InputValidator.validate_max_tokens(0)
        assert is_valid is False
        assert "must be in range" in error

    def test_max_tokens_above_max(self):
        """Test validation fails for tokens above 32000."""
        is_valid, error = InputValidator.validate_max_tokens(35000)
        assert is_valid is False
        assert "must be in range" in error

    def test_max_tokens_wrong_type(self):
        """Test validation fails for non-integer tokens."""
        is_valid, error = InputValidator.validate_max_tokens(1500.5)
        assert is_valid is False
        assert "must be an integer" in error


class TestAPIKeyValidation:
    """Test API key format validation."""

    def test_valid_api_key(self):
        """Test validation passes for valid API key."""
        key = "sk-" + "x" * 40
        is_valid, error = InputValidator.validate_api_key(key)
        assert is_valid is True
        assert error is None

    def test_empty_api_key(self):
        """Test validation fails for empty API key."""
        is_valid, error = InputValidator.validate_api_key("")
        assert is_valid is False
        assert "is empty" in error

    def test_api_key_wrong_prefix(self):
        """Test validation fails for key not starting with 'sk-'."""
        key = "pk-" + "x" * 40
        is_valid, error = InputValidator.validate_api_key(key)
        assert is_valid is False
        assert "should start with 'sk-'" in error

    def test_api_key_too_short(self):
        """Test validation fails for key shorter than 20 characters."""
        key = "sk-short"
        is_valid, error = InputValidator.validate_api_key(key)
        assert is_valid is False
        assert "too short" in error


class TestLogLevelValidation:
    """Test log level validation."""

    def test_valid_log_levels(self):
        """Test validation passes for all valid log levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            is_valid, error = InputValidator.validate_log_level(level)
            assert is_valid is True, f"Failed for level: {level}"
            assert error is None

    def test_log_level_case_insensitive(self):
        """Test validation is case-insensitive."""
        levels = ["debug", "Info", "WaRnInG", "error"]
        for level in levels:
            is_valid, error = InputValidator.validate_log_level(level)
            assert is_valid is True, f"Failed for level: {level}"

    def test_invalid_log_level(self):
        """Test validation fails for invalid log level."""
        is_valid, error = InputValidator.validate_log_level("TRACE")
        assert is_valid is False
        assert "Invalid log level" in error


class TestTempoValidation:
    """Test tempo (BPM) validation."""

    def test_valid_tempo(self):
        """Test validation passes for valid tempo."""
        is_valid, error = InputValidator.validate_tempo(120)
        assert is_valid is True
        assert error is None

    def test_tempo_at_min_boundary(self):
        """Test validation passes for minimum tempo (20)."""
        is_valid, error = InputValidator.validate_tempo(20)
        assert is_valid is True
        assert error is None

    def test_tempo_at_max_boundary(self):
        """Test validation passes for maximum tempo (240)."""
        is_valid, error = InputValidator.validate_tempo(240)
        assert is_valid is True
        assert error is None

    def test_tempo_below_min(self):
        """Test validation fails for tempo below 20."""
        is_valid, error = InputValidator.validate_tempo(10)
        assert is_valid is False
        assert "out of reasonable range" in error

    def test_tempo_above_max(self):
        """Test validation fails for tempo above 240."""
        is_valid, error = InputValidator.validate_tempo(300)
        assert is_valid is False
        assert "out of reasonable range" in error

    def test_tempo_wrong_type(self):
        """Test validation fails for non-integer tempo."""
        is_valid, error = InputValidator.validate_tempo(120.5)
        assert is_valid is False
        assert "must be an integer" in error


class TestTimeSignatureValidation:
    """Test time signature validation."""

    def test_valid_time_signatures(self):
        """Test validation passes for common time signatures."""
        valid_sigs = ["4/4", "3/4", "6/8", "5/4", "7/8", "2/4"]
        for sig in valid_sigs:
            is_valid, error = InputValidator.validate_time_signature(sig)
            assert is_valid is True, f"Failed for: {sig}"
            assert error is None

    def test_invalid_time_signature_format(self):
        """Test validation fails for invalid format."""
        invalid_sigs = ["4-4", "4", "four/four", "4/"]
        for sig in invalid_sigs:
            is_valid, error = InputValidator.validate_time_signature(sig)
            assert is_valid is False, f"Should fail for: {sig}"
            assert "format" in error

    def test_invalid_denominator(self):
        """Test validation fails for non-power-of-2 denominator."""
        is_valid, error = InputValidator.validate_time_signature("4/3")
        assert is_valid is False
        assert "power of 2" in error

    def test_numerator_out_of_range(self):
        """Test validation fails for numerator outside 1-16."""
        is_valid, error = InputValidator.validate_time_signature("0/4")
        assert is_valid is False
        assert "numerator out of range" in error

        is_valid, error = InputValidator.validate_time_signature("20/4")
        assert is_valid is False
        assert "numerator out of range" in error

    def test_time_signature_wrong_type(self):
        """Test validation fails for non-string time signature."""
        is_valid, error = InputValidator.validate_time_signature(44)
        assert is_valid is False
        assert "must be a string" in error
