#!/usr/bin/env python3
"""
Launcher script for the Lyrics-to-Melody system.

This script ensures the correct Python path and runs the main application.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run the main application
from lyrics_to_melody.main import main

if __name__ == "__main__":
    main()
