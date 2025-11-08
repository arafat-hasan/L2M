# Lyrics-to-Melody Production Improvements Checklist

Quick reference for tracking implementation progress.

## 🔴 CRITICAL Priority (Must Fix Before Production)

- [ ] **#1** Path traversal vulnerability in `output_name` (main.py:51)
  - Add `sanitize_filename()` function
  - Block `../`, invalid chars, reserved names
  - **Security risk: HIGH**

- [ ] **#2** Unsafe environment variable parsing (config.py:39-40)
  - Add try/except for `float()` and `int()`
  - Add range validation
  - **Crash risk: HIGH**

- [ ] **#3** Missing API response validation (llm/client.py:97)
  - Check `response.choices` is not empty
  - Check `content` is not None
  - **Crash risk: HIGH**

- [ ] **#4** No retry logic for API calls (llm/client.py:84-107)
  - Implement exponential backoff
  - Handle transient failures
  - **Reliability: CRITICAL**

- [ ] **#5** No log rotation (utils/logger.py:49-50)
  - Use `RotatingFileHandler`
  - Set max size 10MB, 5 backups
  - **Operations risk: HIGH**

- [ ] **#6** Circular dependencies (llm/client.py ↔ services/)
  - Refactor to remove circular imports
  - Use dependency injection or separate module
  - **Architecture: CRITICAL**

---

## 🟡 HIGH Priority (Should Fix Soon)

- [ ] **#7** Missing input validation
  - Validate lyrics (not empty, length < 10k)
  - Validate config parameters (ranges)
  - Validate all user inputs

- [ ] **#8** No rate limiting handling (429 errors)
  - Parse `Retry-After` header
  - Wait before retry
  - Log rate limit events

- [ ] **#9** No API timeout configuration
  - Add `timeout` parameter to API calls
  - Make configurable via env var
  - Default: 30 seconds

- [ ] **#10** Unvalidated API_BASE URL
  - Validate URL format
  - Require HTTPS (except localhost)
  - Whitelist domains (optional)

- [ ] **#11** No progress indicators
  - Add progress bars for LLM calls
  - Show "Analyzing..." messages
  - Improve user feedback

- [ ] **#12** Poor error messages
  - Include actionable guidance
  - Show file paths, examples
  - Link to troubleshooting docs

- [ ] **#13** Generic exception handling
  - Use specific exceptions
  - Different handling per error type
  - Better error recovery

- [ ] **#14** No API key format validation
  - Check starts with 'sk-'
  - Minimum length check
  - Warn if suspicious format

---

## 🟢 MEDIUM Priority (Nice to Have)

- [ ] **#15** Prompt templates loaded every call
  - Add `@lru_cache` decorator
  - Load once, reuse multiple times
  - **Performance gain: 100ms per call**

- [ ] **#16** MIDI Score created twice
  - Create once, write to both formats
  - Reuse object in `write_both()`
  - **Performance gain: 50% faster**

- [ ] **#17** Regex patterns compiled every call
  - Pre-compile at module level
  - Significant speedup in validators
  - **Performance gain: 10-20%**

- [ ] **#18** No structured logging
  - Add JSON log format option
  - Include correlation IDs
  - Better log parsing/analysis

- [ ] **#19** Long method: `_generate_notes_by_contour`
  - Split into separate methods
  - One method per contour type
  - **Code quality**

- [ ] **#20** EMOTION_MAP hardcoded in code
  - Move to YAML/JSON file
  - Allow user customization
  - **Flexibility**

- [ ] **#21** Missing CLI flags
  - Add `--verbose`, `--quiet`
  - Add `--version`
  - Add `--config` for config file

- [ ] **#22** Magic numbers everywhere
  - Create constants module
  - Named constants for all magic numbers
  - **Code readability**

---

## 🔵 LOW Priority (Future Enhancements)

- [ ] **#23** No LLM response caching
  - Cache responses by prompt hash
  - Avoid duplicate API calls
  - **Performance + Cost savings**

- [ ] **#24** NOTE_NAMES is dict, should be Enum
  - Convert to proper Enum
  - Better type safety
  - **Code quality**

- [ ] **#25** No syllable estimation caching
  - Add `@lru_cache` decorator
  - Cache syllable counts
  - **Performance: minor**

---

## Implementation Phases

### **Phase 1: Security & Stability** (2-3 days)
Priority: 🔴 Critical issues #1-6

**Goal:** Make system safe and stable
- No crashes from bad input
- No security vulnerabilities
- Reliable API calls

### **Phase 2: Robustness** (3-4 days)
Priority: 🟡 High issues #7-14

**Goal:** Handle edge cases gracefully
- Comprehensive validation
- Better error handling
- Improved UX

### **Phase 3: Performance** (2-3 days)
Priority: 🟢 Medium issues #15-22

**Goal:** Optimize hot paths
- Caching
- Code refactoring
- CLI improvements

### **Phase 4: Polish** (1-2 days)
Priority: 🔵 Low issues #23-25

**Goal:** Final touches
- Additional optimizations
- Code quality improvements

---

## Quick Stats

- **Total Issues:** 25
- **Critical:** 6 (24%)
- **High:** 8 (32%)
- **Medium:** 8 (32%)
- **Low:** 3 (12%)

**Estimated Time:**
- Phase 1: 16-24 hours
- Phase 2: 24-32 hours
- Phase 3: 16-24 hours
- Phase 4: 8-16 hours
- **Total: 8-12 days** (full-time work)

---

## Files Most Affected

| File | Critical | High | Medium | Total |
|------|----------|------|--------|-------|
| `llm/client.py` | 4 | 3 | 1 | 8 |
| `config.py` | 2 | 2 | 1 | 5 |
| `main.py` | 1 | 2 | 1 | 4 |
| `utils/logger.py` | 1 | 0 | 1 | 2 |
| `services/melody_generator.py` | 1 | 0 | 2 | 3 |
| `services/midi_writer.py` | 0 | 0 | 1 | 1 |
| `utils/validators.py` | 0 | 0 | 2 | 2 |

---

## Testing Requirements

Each fix must include:

1. **Unit Tests**
   - Test valid inputs
   - Test invalid inputs
   - Test edge cases

2. **Integration Tests**
   - Test end-to-end flow
   - Test with real API (optional)
   - Test error scenarios

3. **Security Tests** (for security issues)
   - Test attack vectors
   - Test sanitization
   - Test access controls

4. **Performance Tests** (for performance issues)
   - Benchmark before/after
   - Measure improvement
   - Profile hot paths

---

## Definition of Done

For each issue:

- [ ] Code implemented
- [ ] Unit tests written and passing
- [ ] Integration tests updated
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Manually tested
- [ ] CHANGELOG entry added
- [ ] GitHub issue closed

---

## Resources Needed

### Dependencies to Add
```bash
# For retry logic
pip install tenacity

# For progress bars
pip install tqdm

# For validation
pip install validators

# For YAML config
pip install pyyaml
```

### Tools for Development
- `pylint` - Code quality
- `mypy` - Type checking
- `pytest-cov` - Coverage
- `bandit` - Security scanning
- `import-linter` - Dependency checks

---

## Success Metrics

After all phases complete:

- [ ] 0 critical vulnerabilities
- [ ] 0 unhandled crash scenarios
- [ ] 95%+ test coverage
- [ ] < 5 second cold start time
- [ ] 99%+ API retry success rate
- [ ] Clear, actionable error messages
- [ ] Comprehensive documentation

---

**Last Updated:** 2025-01-08
**Next Review:** After Phase 1 completion
