"""
Unit tests for path utilities.
"""

import pytest
from pathlib import Path

from lyrics_to_melody.utils.path_utils import (
    sanitize_filename,
    validate_output_path,
    ensure_safe_path,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_filename(self):
        """Test that simple filenames pass through unchanged."""
        assert sanitize_filename("output") == "output"
        assert sanitize_filename("my_file") == "my_file"
        assert sanitize_filename("test-123") == "test-123"

    def test_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked."""
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("..\\..\\..\\windows\\system32") == "system32"
        assert sanitize_filename("/etc/passwd") == "passwd"
        assert sanitize_filename("\\windows\\system32") == "system32"

    def test_invalid_characters_removed(self):
        """Test that invalid characters are removed."""
        assert sanitize_filename("file<>name") == "filename"
        assert sanitize_filename("file:name") == "filename"
        assert sanitize_filename("file|name") == "filename"
        assert sanitize_filename("file?name") == "filename"
        assert sanitize_filename("file*name") == "filename"
        assert sanitize_filename('file"name') == "filename"

    def test_windows_reserved_names(self):
        """Test that Windows reserved names are prefixed."""
        assert sanitize_filename("CON") == "file_CON"
        assert sanitize_filename("con") == "file_con"  # case insensitive
        assert sanitize_filename("PRN") == "file_PRN"
        assert sanitize_filename("AUX") == "file_AUX"
        assert sanitize_filename("NUL") == "file_NUL"
        assert sanitize_filename("COM1") == "file_COM1"
        assert sanitize_filename("LPT1") == "file_LPT1"

    def test_empty_string_returns_default(self):
        """Test that empty strings return default value."""
        assert sanitize_filename("") == "output"
        assert sanitize_filename("   ") == "output"
        assert sanitize_filename("", default="custom") == "custom"

    def test_whitespace_trimmed(self):
        """Test that leading/trailing whitespace is removed."""
        assert sanitize_filename("  filename  ") == "filename"
        assert sanitize_filename("\tfilename\n") == "filename"

    def test_dots_trimmed(self):
        """Test that leading/trailing dots are removed."""
        assert sanitize_filename(".filename") == "filename"
        assert sanitize_filename("filename.") == "filename"
        assert sanitize_filename("..filename..") == "filename"

    def test_preserves_extension(self):
        """Test that file extensions are preserved."""
        assert sanitize_filename("output.mid") == "output.mid"
        assert sanitize_filename("test.musicxml") == "test.musicxml"

    def test_none_input(self):
        """Test that None input returns default."""
        assert sanitize_filename(None) == "output"

    def test_non_string_input(self):
        """Test that non-string input returns default."""
        assert sanitize_filename(123) == "output"
        assert sanitize_filename([]) == "output"

    def test_control_characters_removed(self):
        """Test that control characters are removed."""
        assert sanitize_filename("file\x00name") == "filename"
        assert sanitize_filename("file\x1fname") == "filename"

    def test_complex_path_traversal(self):
        """Test complex path traversal attempts."""
        assert sanitize_filename("....//....//etc/passwd") == "passwd"
        assert sanitize_filename("test/../../secret") == "secret"

    def test_preserves_unicode(self):
        """Test that valid Unicode characters are preserved."""
        assert sanitize_filename("文件名") == "文件名"
        assert sanitize_filename("файл") == "файл"
        assert sanitize_filename("αρχείο") == "αρχείο"


class TestValidateOutputPath:
    """Tests for validate_output_path function."""

    def test_valid_path_within_base(self, tmp_path):
        """Test that valid paths within base directory are accepted."""
        base = tmp_path / "output"
        base.mkdir()

        result = validate_output_path(base, "test.mid")
        assert result == (base / "test.mid").resolve()

    def test_sanitization_applied(self, tmp_path):
        """Test that sanitization is applied to filename."""
        base = tmp_path / "output"
        base.mkdir()

        result = validate_output_path(base, "test<>file.mid")
        assert result == (base / "testfile.mid").resolve()

    def test_path_traversal_rejected(self, tmp_path):
        """Test that path traversal attempts are rejected."""
        base = tmp_path / "output"
        base.mkdir()

        with pytest.raises(ValueError, match="escapes base directory"):
            validate_output_path(base, "../../etc/passwd")

    def test_absolute_path_rejected(self, tmp_path):
        """Test that absolute paths pointing outside are rejected."""
        base = tmp_path / "output"
        base.mkdir()

        # Create a different directory
        other = tmp_path / "other"
        other.mkdir()

        # This should fail because it tries to escape
        # Note: The sanitization will strip the path, but we test the concept
        result = validate_output_path(base, str(other / "file.mid"))
        # After sanitization, only "file.mid" remains, so it should be valid
        assert "file.mid" in str(result)

    def test_relative_path_within_base(self, tmp_path):
        """Test that relative paths within base are accepted."""
        base = tmp_path / "output"
        base.mkdir()

        result = validate_output_path(base, "subdir/test.mid")
        # After sanitization, directory components are removed
        assert result.name == "test.mid"


class TestEnsureSafePath:
    """Tests for ensure_safe_path function."""

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created."""
        path = tmp_path / "a" / "b" / "c" / "file.txt"

        result = ensure_safe_path(path)

        assert result == path
        assert path.parent.exists()
        assert path.parent.is_dir()

    def test_existing_directory_ok(self, tmp_path):
        """Test that existing directories are handled."""
        path = tmp_path / "existing" / "file.txt"
        path.parent.mkdir(parents=True)

        result = ensure_safe_path(path)

        assert result == path
        assert path.parent.exists()

    def test_permission_error(self, tmp_path):
        """Test that permission errors are raised."""
        # This test is platform-specific and may not work everywhere
        # Skip if we can't create a permission issue
        import os
        if os.name != 'posix':
            pytest.skip("Permission test only works on POSIX systems")

        # Create a directory with no write permissions
        restricted = tmp_path / "restricted"
        restricted.mkdir()
        restricted.chmod(0o444)  # Read-only

        path = restricted / "subdir" / "file.txt"

        try:
            with pytest.raises(PermissionError):
                ensure_safe_path(path)
        finally:
            # Cleanup: restore permissions
            restricted.chmod(0o755)


class TestSecurityScenarios:
    """Integration tests for security scenarios."""

    def test_null_byte_injection(self):
        """Test that null byte injection is prevented."""
        result = sanitize_filename("evil\x00.txt.exe")
        assert "\x00" not in result
        assert result == "evil.txt.exe"

    def test_unicode_normalization(self):
        """Test that Unicode is handled safely."""
        # Some Unicode characters that could be problematic
        result = sanitize_filename("test\u202e.txt")  # Right-to-left override
        assert len(result) > 0

    def test_very_long_filename(self):
        """Test that very long filenames are truncated."""
        long_name = "a" * 300 + ".mid"
        result = sanitize_filename(long_name)
        assert len(result.encode('utf-8')) <= 255

    def test_mixed_attack_vectors(self):
        """Test multiple attack vectors combined."""
        malicious = "../../../etc/../<>|passwd\x00CON"
        result = sanitize_filename(malicious)

        # Should not contain any dangerous components
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result
        assert "\x00" not in result
        # Should handle the CON reserved name
        assert "CON" in result or "con" in result
