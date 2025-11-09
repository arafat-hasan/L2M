"""
Path utilities for safe file operations.

Provides functions to sanitize filenames and prevent path traversal attacks.
"""

import re
from pathlib import Path
from typing import Optional

from l2m.utils.logger import get_logger

logger = get_logger(__name__)

# Windows reserved names that cannot be used as filenames
WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
}


def sanitize_filename(filename: str, default: str = "output") -> str:
    """
    Sanitize a filename to prevent path traversal and invalid characters.

    This function removes:
    - Directory components (../, /, etc.)
    - Invalid characters for cross-platform compatibility
    - Windows reserved names
    - Leading/trailing whitespace and dots

    Args:
        filename: The filename to sanitize
        default: Default filename if sanitization results in empty string

    Returns:
        str: Sanitized filename safe for use across platforms

    Examples:
        >>> sanitize_filename("../../../etc/passwd")
        'passwd'
        >>> sanitize_filename("test<>file")
        'testfile'
        >>> sanitize_filename("CON")
        'file_CON'
        >>> sanitize_filename("")
        'output'
    """
    if not filename or not isinstance(filename, str):
        logger.warning(f"Invalid filename type: {type(filename)}, using default")
        return default

    # Remove directory components (prevents path traversal)
    # This strips any path separators and keeps only the filename
    sanitized = Path(filename).name

    if not sanitized:
        logger.warning(f"Filename '{filename}' reduced to empty after path removal")
        return default

    # Remove invalid characters for cross-platform compatibility
    # Windows: < > : " / \ | ? * and control characters (0x00-0x1F)
    # This regex keeps alphanumeric, spaces, dots, hyphens, underscores
    sanitized = re.sub(r'[<>:"|?*\\/\x00-\x1f]', '', sanitized)

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip().strip('.')

    if not sanitized:
        logger.warning(f"Filename '{filename}' reduced to empty after character removal")
        return default

    # Check for Windows reserved names (case-insensitive)
    name_without_ext = sanitized.split('.')[0].upper()
    if name_without_ext in WINDOWS_RESERVED_NAMES:
        logger.warning(f"Filename '{sanitized}' is a Windows reserved name, prefixing")
        sanitized = f"file_{sanitized}"

    # Ensure reasonable length (max 255 bytes on most filesystems)
    if len(sanitized.encode('utf-8')) > 255:
        logger.warning(f"Filename '{sanitized}' too long, truncating")
        # Truncate while preserving extension
        parts = sanitized.rsplit('.', 1)
        if len(parts) == 2:
            name, ext = parts
            max_name_len = 250 - len(ext)
            sanitized = name[:max_name_len] + '.' + ext
        else:
            sanitized = sanitized[:255]

    logger.debug(f"Sanitized filename: '{filename}' -> '{sanitized}'")
    return sanitized


def validate_output_path(base_dir: Path, filename: str) -> Optional[Path]:
    """
    Validate that a filename is safe to use within a base directory.

    This function:
    1. Sanitizes the filename
    2. Resolves the full path
    3. Ensures the resolved path is within base_dir (no escaping)

    Args:
        base_dir: The base directory where files should be written
        filename: The filename to validate

    Returns:
        Optional[Path]: The validated absolute path, or None if unsafe

    Raises:
        ValueError: If the path attempts to escape the base directory

    Examples:
        >>> base = Path("/safe/output")
        >>> validate_output_path(base, "test.mid")
        PosixPath('/safe/output/test.mid')
        >>> validate_output_path(base, "../etc/passwd")
        ValueError: Path escapes base directory
    """
    # Sanitize the filename first
    safe_filename = sanitize_filename(filename)

    # Construct the full path
    full_path = (base_dir / safe_filename).resolve()
    base_resolved = base_dir.resolve()

    # Ensure the resolved path is within the base directory
    try:
        full_path.relative_to(base_resolved)
    except ValueError:
        error_msg = (
            f"Security Error: Path '{filename}' attempts to escape base directory. "
            f"Resolved to '{full_path}', expected within '{base_resolved}'"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    return full_path


def ensure_safe_path(path: Path) -> Path:
    """
    Ensure a path is safe by creating parent directories if needed.

    Args:
        path: The path to ensure

    Returns:
        Path: The validated path

    Raises:
        PermissionError: If directories cannot be created
        OSError: If path is invalid
    """
    try:
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured path exists: {path.parent}")
        return path
    except PermissionError as e:
        logger.error(f"Permission denied creating directory: {path.parent}")
        raise
    except OSError as e:
        logger.error(f"OS error ensuring path: {e}")
        raise
