"""
Verification script to check that all components are properly installed.

Run this after installation to verify the system is ready to use.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_imports():
    """Check that all modules can be imported."""
    print("Checking imports...")

    modules = [
        "l2m.config",
        "l2m.models.emotion_analysis",
        "l2m.models.melody_structure",
        "l2m.llm.client",
        "l2m.llm.parsers",
        "l2m.services.lyric_parser",
        "l2m.services.melody_generator",
        "l2m.services.midi_writer",
        "l2m.utils.logger",
        "l2m.utils.validators",
    ]

    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module}: {e}")
            failed.append(module)

    return len(failed) == 0


def check_dependencies():
    """Check that required dependencies are installed."""
    print("\nChecking dependencies...")

    dependencies = [
        ("openai", "OpenAI API client"),
        ("pydantic", "Data validation"),
        ("music21", "Music notation"),
        ("dotenv", "Environment variables"),
    ]

    failed = []
    for package, description in dependencies:
        try:
            __import__(package)
            print(f"  ✓ {package:15s} ({description})")
        except ImportError:
            print(f"  ✗ {package:15s} ({description}) - NOT INSTALLED")
            failed.append(package)

    return len(failed) == 0


def check_directories():
    """Check that required directories exist."""
    print("\nChecking directories...")

    base = Path(__file__).parent / "l2m"
    directories = [
        base / "output",
        base / "logs",
        base / "llm" / "prompts",
    ]

    all_exist = True
    for directory in directories:
        if directory.exists():
            print(f"  ✓ {directory.relative_to(Path(__file__).parent)}")
        else:
            print(f"  ✗ {directory.relative_to(Path(__file__).parent)} - MISSING")
            all_exist = False

    return all_exist


def check_config():
    """Check configuration."""
    print("\nChecking configuration...")

    try:
        from l2m.config import config

        print(f"  Model: {config.MODEL_NAME}")
        print(f"  Temperature: {config.TEMPERATURE}")
        print(f"  Max Tokens: {config.MAX_TOKENS}")

        if config.OPENAI_API_KEY:
            print(f"  ✓ API Key: Set (length: {len(config.OPENAI_API_KEY)})")
        else:
            print(f"  ✗ API Key: NOT SET")
            print("     → Set OPENAI_API_KEY in .env file")
            return False

        return True

    except Exception as e:
        print(f"  ✗ Error loading config: {e}")
        return False


def check_prompts():
    """Check that prompt templates exist."""
    print("\nChecking prompt templates...")

    base = Path(__file__).parent / "l2m" / "llm" / "prompts"
    prompts = [
        "emotion_prompt.txt",
        "melody_prompt.txt",
    ]

    all_exist = True
    for prompt in prompts:
        prompt_path = base / prompt
        if prompt_path.exists():
            size = prompt_path.stat().st_size
            print(f"  ✓ {prompt} ({size} bytes)")
        else:
            print(f"  ✗ {prompt} - MISSING")
            all_exist = False

    return all_exist


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("l2m INSTALLATION VERIFICATION")
    print("=" * 60)

    checks = [
        ("Module Imports", check_imports),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Configuration", check_config),
        ("Prompt Templates", check_prompts),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\nError in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8s} {name}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All checks passed! System is ready to use.")
        print("\nTry running:")
        print('  python l2m/main.py --lyrics "The sun will rise" --dry-run')
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
