# GitHub Issues for l2m Production Improvements

This document contains formatted GitHub issues for critical fixes and improvements.
Copy each issue block to create a new GitHub issue.

---

## 🔴 CRITICAL Priority Issues

### Issue #1: Path Traversal Vulnerability in Output Name

**Priority:** 🔴 Critical (Security)
**Labels:** `security`, `bug`, `high-priority`
**Files:** `lyrics_to_melody/main.py:51`

#### Description
The `output_name` parameter in `main.py` is not sanitized, allowing path traversal attacks. A malicious user could write files to arbitrary locations on the filesystem.

#### Vulnerability
```python
# Current vulnerable code (main.py:51)
def process_lyrics(
    self,
    lyrics: str,
    output_name: str = "output",  # ⚠️ No sanitization!
    dry_run: bool = False
) -> None:
```

**Attack vector:**
```bash
python run.py --lyrics "test" --out "../../../etc/passwd"
# This could write to /etc/passwd!
```

#### Solution
Add path sanitization using `Path.name` to strip directory components:

```python
def sanitize_filename(name: str) -> str:
    """Remove dangerous path components and invalid characters."""
    import re
    from pathlib import Path

    # Remove directory components
    name = Path(name).name

    # Remove invalid characters for cross-platform compatibility
    name = re.sub(r'[<>:"|?*\x00-\x1f]', '', name)

    # Remove reserved names on Windows
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}

    if name.upper() in reserved:
        name = f"file_{name}"

    # Ensure non-empty
    return name.strip() or "output"
```

#### Acceptance Criteria
- [ ] `output_name` parameter is sanitized before use
- [ ] Path traversal attempts (`../`, `..\\`) are blocked
- [ ] Invalid characters are removed
- [ ] Windows reserved names are handled
- [ ] Unit tests added for path sanitization
- [ ] Security test added to verify protection

---

### Issue #2: Unsafe Environment Variable Parsing

**Priority:** 🔴 Critical (Crash/Stability)
**Labels:** `bug`, `crash`, `high-priority`
**Files:** `lyrics_to_melody/config.py:39-40`

#### Description
Environment variables are parsed using `float()` and `int()` without exception handling. Invalid values will crash the application on startup.

#### Bug
```python
# Current code (config.py:39-40)
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1500"))
```

**Crash scenario:**
```bash
export TEMPERATURE="not_a_number"
python run.py --lyrics "test"
# ValueError: could not convert string to float: 'not_a_number'
```

#### Solution
Add safe parsing with validation:

```python
@classmethod
def _safe_float(cls, env_var: str, default: float, min_val: float, max_val: float) -> float:
    """Safely parse float from environment variable with validation."""
    try:
        value = float(os.getenv(env_var, str(default)))
        if not (min_val <= value <= max_val):
            logger.warning(
                f"{env_var}={value} out of range [{min_val}, {max_val}], "
                f"using default {default}"
            )
            return default
        return value
    except (ValueError, TypeError) as e:
        logger.warning(
            f"Invalid {env_var}={os.getenv(env_var)}, using default {default}. "
            f"Error: {e}"
        )
        return default

# Usage
TEMPERATURE: float = _safe_float("TEMPERATURE", 0.7, 0.0, 2.0)
MAX_TOKENS: int = int(_safe_float("MAX_TOKENS", 1500, 1, 32000))
```

#### Acceptance Criteria
- [ ] All environment variables parsed with exception handling
- [ ] Range validation for numeric values
- [ ] Warnings logged when invalid values detected
- [ ] Application doesn't crash on invalid env vars
- [ ] Unit tests for valid/invalid env var scenarios

---

### Issue #3: Missing API Response Validation

**Priority:** 🔴 Critical (Crash)
**Labels:** `bug`, `crash`, `api`
**Files:** `lyrics_to_melody/llm/client.py:97`

#### Description
The code accesses `response.choices[0]` without validating that the array is non-empty, causing `IndexError` crashes.

#### Bug
```python
# Current code (llm/client.py:97)
content = response.choices[0].message.content
# ⚠️ IndexError if choices is empty!
# ⚠️ AttributeError if content is None!
```

#### Solution
Add validation before accessing:

```python
def _call_llm(self, prompt: str) -> str:
    try:
        logger.debug(f"[LLMClient] Calling API with model: {self.model}")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert music composer and analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=30.0,  # Add timeout
        )

        # Validate response structure
        if not response.choices:
            raise ValueError("API returned empty choices array")

        content = response.choices[0].message.content

        if content is None:
            raise ValueError("API returned None content")

        logger.debug(f"[LLMClient] Received response ({len(content)} chars)")
        return content

    except OpenAIError as e:
        logger.error(f"[LLMClient] OpenAI API error: {e}")
        raise  # Re-raise instead of returning None
    except Exception as e:
        logger.error(f"[LLMClient] Unexpected error: {e}")
        raise
```

#### Acceptance Criteria
- [ ] Validate `response.choices` is non-empty
- [ ] Validate `content` is not None
- [ ] Raise exceptions instead of returning None
- [ ] Add timeout to API calls
- [ ] Update all callers to handle exceptions
- [ ] Add unit tests with mock responses

---

### Issue #4: Implement Retry Logic with Exponential Backoff

**Priority:** 🔴 Critical (Reliability)
**Labels:** `enhancement`, `api`, `reliability`
**Files:** `lyrics_to_melody/llm/client.py:84-107`

#### Description
API calls have no retry logic. Transient network failures or temporary API issues cause permanent failures.

#### Current Limitation
```python
# Current: Single attempt, no retries
def _call_llm(self, prompt: str) -> Optional[str]:
    try:
        response = self.client.chat.completions.create(...)
        return content
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        return None  # Permanent failure!
```

#### Solution
Implement retry decorator with exponential backoff:

```python
import time
from functools import wraps
from typing import TypeVar, Callable
from openai import RateLimitError, APITimeoutError, APIConnectionError

T = TypeVar('T')

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (RateLimitError, APITimeoutError, APIConnectionError)
):
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"[Retry] Max retries ({max_retries}) exceeded for {func.__name__}"
                        )
                        raise

                    # Special handling for rate limits
                    if isinstance(e, RateLimitError):
                        # Use retry-after header if available
                        retry_after = getattr(e, 'retry_after', delay)
                        logger.warning(
                            f"[Retry] Rate limited. Waiting {retry_after}s before retry {attempt + 1}/{max_retries}"
                        )
                        time.sleep(retry_after)
                    else:
                        logger.warning(
                            f"[Retry] Attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)

                    delay *= backoff_factor
                except Exception as e:
                    # Non-retryable exception
                    logger.error(f"[Retry] Non-retryable error in {func.__name__}: {e}")
                    raise

            raise last_exception

        return wrapper
    return decorator

# Usage
@retry_with_backoff(max_retries=3, initial_delay=2.0)
def _call_llm(self, prompt: str) -> str:
    # Implementation
    ...
```

#### Acceptance Criteria
- [ ] Retry logic with exponential backoff (1s, 2s, 4s, 8s)
- [ ] Special handling for 429 rate limit errors
- [ ] Respect `Retry-After` header when present
- [ ] Log retry attempts with attempt number
- [ ] Configurable max retries via environment variable
- [ ] Unit tests with mocked API failures
- [ ] Integration test with actual API

---

### Issue #5: Add Log Rotation to Prevent Disk Space Issues

**Priority:** 🔴 Critical (Operational)
**Labels:** `bug`, `ops`, `logging`
**Files:** `lyrics_to_melody/utils/logger.py:49-50`

#### Description
Logs are written to a single file with no rotation, which will eventually fill the disk.

#### Issue
```python
# Current code (utils/logger.py:49-50)
log_file = config.LOGS_DIR / "system.log"
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
# ⚠️ No rotation! File grows indefinitely
```

#### Solution
Use `RotatingFileHandler` with size limits:

```python
from logging.handlers import RotatingFileHandler

# Create rotating file handler
log_file = config.LOGS_DIR / "system.log"
file_handler = RotatingFileHandler(
    log_file,
    mode='a',
    maxBytes=10 * 1024 * 1024,  # 10 MB per file
    backupCount=5,               # Keep 5 backup files
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# Optional: Add separate error log
error_log = config.LOGS_DIR / "error.log"
error_handler = RotatingFileHandler(
    error_log,
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding='utf-8'
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
root_logger.addHandler(error_handler)
```

**Result:** Logs will rotate as:
- `system.log` (current)
- `system.log.1` (previous)
- `system.log.2`, `system.log.3`, etc.

#### Acceptance Criteria
- [ ] Replace `FileHandler` with `RotatingFileHandler`
- [ ] Set max file size (10 MB)
- [ ] Keep last 5 rotated files
- [ ] Add separate error log with rotation
- [ ] Add configuration options for rotation settings
- [ ] Test log rotation behavior
- [ ] Document log file locations in README

---

### Issue #6: Fix Circular Dependency Between Client and Services

**Priority:** 🔴 Critical (Architecture)
**Labels:** `refactor`, `architecture`, `technical-debt`
**Files:** `lyrics_to_melody/llm/client.py`, `lyrics_to_melody/services/`

#### Description
`llm/client.py` imports from `services/` in fallback methods, while services import `LLMClient`. This creates circular dependencies and makes testing difficult.

#### Circular Dependency
```
llm/client.py
  ↓ imports (in _fallback_emotion_analysis)
services/lyric_parser.py

services/melody_generator.py
  ↓ imports (in __init__)
llm/client.py
```

#### Solution Options

**Option 1: Dependency Injection (Recommended)**
```python
# Remove imports from client fallback methods
# Instead, inject dependencies or use callbacks

class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        fallback_emotion_fn: Optional[Callable] = None,
        fallback_melody_fn: Optional[Callable] = None
    ):
        self.api_key = api_key or config.OPENAI_API_KEY
        self._fallback_emotion_fn = fallback_emotion_fn
        self._fallback_melody_fn = fallback_melody_fn

    def _fallback_emotion_analysis(self, lyrics: str) -> EmotionAnalysisResponse:
        if self._fallback_emotion_fn:
            return self._fallback_emotion_fn(lyrics)
        # Or use built-in simple fallback
        return self._simple_fallback(lyrics)
```

**Option 2: Move Fallbacks to Separate Module**
```
lyrics_to_melody/
  ├── fallbacks/
  │   ├── __init__.py
  │   ├── emotion_fallback.py
  │   └── melody_fallback.py
  ├── llm/
  │   └── client.py (uses fallbacks module)
  └── services/
      └── melody_generator.py (uses llm.client)
```

**Option 3: Use Factory Pattern**
```python
# factory.py
class MelodyGeneratorFactory:
    @staticmethod
    def create() -> MelodyGenerator:
        client = LLMClient()
        return MelodyGenerator(client)
```

#### Acceptance Criteria
- [ ] Remove circular imports
- [ ] Services don't import from each other
- [ ] Clear dependency flow (config → models → services → llm)
- [ ] All tests pass
- [ ] Update architecture documentation
- [ ] Verify with `import-linter` or similar tool

---

## 🟡 HIGH Priority Issues

### Issue #7: Add Comprehensive Input Validation

**Priority:** 🟡 High
**Labels:** `enhancement`, `validation`, `ux`
**Files:** `lyrics_to_melody/main.py`, `lyrics_to_melody/config.py`, `lyrics_to_melody/services/`

#### Description
Public methods lack input validation, allowing invalid data to propagate through the system.

#### Missing Validations
1. **Lyrics validation** (main.py:48)
   - Empty string
   - Only whitespace
   - Too long (> 10,000 chars)

2. **Config validation** (config.py)
   - Temperature not in [0.0, 2.0]
   - Max tokens not in [1, 32000]
   - Invalid LOG_LEVEL
   - Malformed API_BASE URL

3. **Output name validation** (covered in Issue #1)

#### Solution
Create validation utility:

```python
# utils/input_validators.py
from typing import Tuple, Optional

class InputValidator:
    """Validates user inputs."""

    @staticmethod
    def validate_lyrics(lyrics: str) -> Tuple[bool, Optional[str]]:
        """Validate lyrics input."""
        if not isinstance(lyrics, str):
            return False, "Lyrics must be a string"

        if not lyrics.strip():
            return False, "Lyrics cannot be empty"

        if len(lyrics) > 10000:
            return False, "Lyrics too long (max 10,000 characters)"

        # Check for null bytes (security)
        if '\x00' in lyrics:
            return False, "Lyrics contain invalid characters"

        return True, None

    @staticmethod
    def validate_temperature(temp: float) -> Tuple[bool, Optional[str]]:
        """Validate temperature parameter."""
        if not isinstance(temp, (int, float)):
            return False, f"Temperature must be numeric, got {type(temp)}"

        if not (0.0 <= temp <= 2.0):
            return False, f"Temperature must be in [0.0, 2.0], got {temp}"

        return True, None

    @staticmethod
    def validate_api_key(key: str) -> Tuple[bool, Optional[str]]:
        """Validate OpenAI API key format."""
        if not key:
            return False, "API key is empty"

        if not key.startswith('sk-'):
            return False, "API key should start with 'sk-'"

        if len(key) < 20:
            return False, "API key too short (possibly invalid)"

        return True, None
```

#### Acceptance Criteria
- [ ] All public methods validate inputs
- [ ] Validation errors include helpful messages
- [ ] Range checks for numeric parameters
- [ ] Type checks before processing
- [ ] Security checks (null bytes, path traversal)
- [ ] Unit tests for all validators
- [ ] Document validation rules in docstrings

---

### Issue #8: Implement Rate Limiting Handling (429 Errors)

**Priority:** 🟡 High
**Labels:** `enhancement`, `api`, `reliability`
**Files:** `lyrics_to_melody/llm/client.py`

#### Description
429 (Rate Limit) errors are not specifically handled. Should use `Retry-After` header.

#### Solution
(Covered in Issue #4 retry logic, but warrants separate tracking)

Add specific 429 handling:
```python
from openai import RateLimitError

try:
    response = self.client.chat.completions.create(...)
except RateLimitError as e:
    retry_after = getattr(e.response.headers, 'retry-after', 60)
    logger.warning(f"Rate limited. Retry after {retry_after}s")
    time.sleep(float(retry_after))
    # Retry
```

#### Acceptance Criteria
- [ ] Detect 429 status codes
- [ ] Parse `Retry-After` header
- [ ] Wait specified duration before retry
- [ ] Log rate limit events
- [ ] Track rate limit metrics
- [ ] Add configuration for rate limit behavior

---

### Issue #9: Add Timeout Configuration for API Calls

**Priority:** 🟡 High
**Labels:** `enhancement`, `api`, `config`
**Files:** `lyrics_to_melody/llm/client.py:87-94`

#### Description
API calls have no timeout, causing indefinite hangs on network issues.

#### Solution
```python
# config.py
API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))

# client.py
response = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    temperature=self.temperature,
    max_tokens=self.max_tokens,
    timeout=config.API_TIMEOUT,  # Add timeout
)
```

#### Acceptance Criteria
- [ ] Add timeout to all API calls
- [ ] Make timeout configurable via env var
- [ ] Handle timeout exceptions gracefully
- [ ] Log timeout events
- [ ] Document timeout configuration
- [ ] Test timeout behavior

---

### Issue #10: Validate and Sanitize API_BASE URL

**Priority:** 🟡 High (Security)
**Labels:** `security`, `validation`, `config`
**Files:** `lyrics_to_melody/config.py:41`

#### Description
`API_BASE` URL is not validated, could point to malicious servers.

#### Solution
```python
from urllib.parse import urlparse

@classmethod
def _validate_url(cls, url: str) -> bool:
    """Validate URL format and scheme."""
    try:
        parsed = urlparse(url)

        # Must have scheme and netloc
        if not all([parsed.scheme, parsed.netloc]):
            return False

        # Only allow HTTPS (or HTTP for localhost/testing)
        if parsed.scheme not in ['https', 'http']:
            return False

        # Optional: Whitelist domains
        # allowed_domains = ['api.openai.com', 'localhost', '127.0.0.1']
        # if parsed.netloc not in allowed_domains:
        #     return False

        return True
    except Exception:
        return False

# Usage
API_BASE = os.getenv("API_BASE", "https://api.openai.com/v1")
if not Config._validate_url(API_BASE):
    logger.warning(f"Invalid API_BASE URL: {API_BASE}, using default")
    API_BASE = "https://api.openai.com/v1"
```

#### Acceptance Criteria
- [ ] Validate URL format
- [ ] Require HTTPS (except localhost)
- [ ] Log warning if invalid URL detected
- [ ] Optional: Whitelist allowed domains
- [ ] Unit tests for URL validation

---

*Continue with remaining HIGH and MEDIUM priority issues...*

---

## Implementation Order

### Phase 1: Critical Security & Stability (Week 1)
- Issue #1: Path traversal fix
- Issue #2: Safe env var parsing
- Issue #3: API response validation
- Issue #6: Fix circular dependencies

### Phase 2: Critical Reliability (Week 2)
- Issue #4: Retry logic
- Issue #5: Log rotation
- Issue #8: Rate limiting
- Issue #9: API timeouts

### Phase 3: High Priority Enhancements (Week 3)
- Issue #7: Input validation
- Issue #10: URL validation
- Issue #11-14: (Remaining HIGH priority)

### Phase 4: Medium Priority Polish (Week 4)
- Performance optimizations
- Code refactoring
- CLI enhancements
- Documentation updates

---

## Testing Checklist

For each issue:
- [ ] Unit tests added
- [ ] Integration tests updated
- [ ] Security tests (for security issues)
- [ ] Manual testing performed
- [ ] Documentation updated
- [ ] CHANGELOG entry added

---

## Labels to Create in GitHub

```
Priority Labels:
- 🔴 critical
- 🟡 high-priority
- 🟢 medium-priority
- 🔵 low-priority

Type Labels:
- bug
- enhancement
- security
- refactor
- documentation
- testing

Component Labels:
- api
- config
- cli
- logging
- validation
- performance
```

---

**End of GitHub Issues Document**
