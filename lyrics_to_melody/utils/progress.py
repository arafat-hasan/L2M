"""
Progress indication utilities for long-running operations.

Provides simple progress indicators and status messages for CLI feedback.
"""

import sys
import time
import threading
from typing import Optional, Callable, Any
from contextlib import contextmanager

from lyrics_to_melody.utils.logger import get_logger

logger = get_logger(__name__)


class ProgressIndicator:
    """Simple progress indicator for CLI operations."""

    def __init__(self, message: str, spinner_chars: str = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
        """
        Initialize progress indicator.

        Args:
            message: Message to display
            spinner_chars: Characters to cycle through for animation
        """
        self.message = message
        self.spinner_chars = spinner_chars
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._start_time: Optional[float] = None

    def start(self) -> None:
        """Start the progress indicator animation."""
        self._stop_event.clear()
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self, final_message: str = "", success: bool = True) -> None:
        """
        Stop the progress indicator.

        Args:
            final_message: Optional final message to display
            success: Whether operation succeeded (affects final symbol)
        """
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=1.0)

        # Clear the spinner line
        sys.stdout.write('\r' + ' ' * (len(self.message) + 20) + '\r')
        sys.stdout.flush()

        # Show final message
        if final_message:
            symbol = "✓" if success else "✗"
            elapsed = time.time() - self._start_time if self._start_time else 0
            print(f"{symbol} {final_message} ({elapsed:.2f}s)")
        elif success:
            elapsed = time.time() - self._start_time if self._start_time else 0
            print(f"✓ {self.message} complete ({elapsed:.2f}s)")

    def _animate(self) -> None:
        """Animation loop (runs in separate thread)."""
        idx = 0
        while not self._stop_event.is_set():
            spinner = self.spinner_chars[idx % len(self.spinner_chars)]
            elapsed = time.time() - self._start_time if self._start_time else 0
            sys.stdout.write(f'\r{spinner} {self.message} ({elapsed:.1f}s)')
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        success = exc_type is None
        if exc_type:
            self.stop(f"{self.message} failed", success=False)
        else:
            self.stop(success=True)


@contextmanager
def progress(message: str):
    """
    Context manager for showing progress indicator.

    Args:
        message: Message to display during operation

    Example:
        with progress("Analyzing emotions..."):
            result = analyze_emotion(lyrics)
    """
    indicator = ProgressIndicator(message)
    try:
        indicator.start()
        yield indicator
    except Exception as e:
        indicator.stop(f"{message} failed", success=False)
        raise
    else:
        indicator.stop(success=True)


class ProgressTracker:
    """Track progress through multiple steps."""

    def __init__(self, total_steps: int, description: str = "Processing"):
        """
        Initialize progress tracker.

        Args:
            total_steps: Total number of steps
            description: Description of the process
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self._start_time = time.time()

    def update(self, step: int = None, message: str = "") -> None:
        """
        Update progress.

        Args:
            step: Step number (if None, increments current step)
            message: Optional message for this step
        """
        if step is not None:
            self.current_step = step
        else:
            self.current_step += 1

        percentage = (self.current_step / self.total_steps) * 100
        elapsed = time.time() - self._start_time

        bar_length = 30
        filled = int(bar_length * self.current_step / self.total_steps)
        bar = '█' * filled + '░' * (bar_length - filled)

        step_msg = f"Step {self.current_step}/{self.total_steps}"
        if message:
            step_msg += f": {message}"

        print(f"[{bar}] {percentage:5.1f}% | {step_msg} ({elapsed:.1f}s)")
        logger.info(f"Progress: {percentage:.1f}% - {step_msg}")

    def complete(self, message: str = "Complete") -> None:
        """
        Mark progress as complete.

        Args:
            message: Completion message
        """
        elapsed = time.time() - self._start_time
        print(f"✓ {self.description} {message} ({elapsed:.2f}s)")
        logger.info(f"{self.description} completed in {elapsed:.2f}s")


def with_progress(message: str):
    """
    Decorator to add progress indicator to a function.

    Args:
        message: Progress message to display

    Example:
        @with_progress("Generating melody...")
        def generate_melody(lyrics):
            # Implementation
            return melody
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            with progress(message):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class StepProgress:
    """Context manager for a single step in a multi-step process."""

    def __init__(self, step_number: int, total_steps: int, description: str):
        """
        Initialize step progress.

        Args:
            step_number: Current step number
            total_steps: Total number of steps
            description: Description of this step
        """
        self.step_number = step_number
        self.total_steps = total_steps
        self.description = description
        self._start_time: Optional[float] = None

    def __enter__(self):
        """Start step."""
        self._start_time = time.time()
        print(f"\n{'='*60}")
        print(f"STEP {self.step_number}/{self.total_steps}: {self.description}")
        print(f"{'='*60}")
        logger.info(f"Starting step {self.step_number}/{self.total_steps}: {self.description}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete step."""
        if self._start_time:
            elapsed = time.time() - self._start_time
            if exc_type is None:
                print(f"✓ Step {self.step_number} complete ({elapsed:.2f}s)")
                logger.info(f"Step {self.step_number} completed in {elapsed:.2f}s")
            else:
                print(f"✗ Step {self.step_number} failed ({elapsed:.2f}s)")
                logger.error(f"Step {self.step_number} failed after {elapsed:.2f}s")


@contextmanager
def step_progress(step_number: int, total_steps: int, description: str):
    """
    Context manager for a single processing step.

    Args:
        step_number: Current step number (1-indexed)
        total_steps: Total number of steps
        description: Description of this step

    Example:
        with step_progress(1, 3, "Parsing lyrics"):
            normalized = parse_lyrics(lyrics)
    """
    step = StepProgress(step_number, total_steps, description)
    with step:
        yield step


def show_status(message: str, status: str = "info") -> None:
    """
    Show a status message with icon.

    Args:
        message: Status message
        status: Type of status (info, success, warning, error)
    """
    icons = {
        "info": "ℹ",
        "success": "✓",
        "warning": "⚠",
        "error": "✗",
    }

    icon = icons.get(status, "•")
    print(f"{icon} {message}")

    log_methods = {
        "info": logger.info,
        "success": logger.info,
        "warning": logger.warning,
        "error": logger.error,
    }

    log_method = log_methods.get(status, logger.info)
    log_method(message)
