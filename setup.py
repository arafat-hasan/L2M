"""
Setup script for the l2m system.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="l2m",
    version="1.0.0",
    description="A modular Python system that converts lyrics into melodic output (MIDI/MusicXML)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AI Developer",
    author_email="",
    url="https://github.com/arafat-hasan/L2M",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "l2m=lyrics_to_melody.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: MIDI",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    package_data={
        "lyrics_to_melody": [
            "llm/prompts/*.txt",
            "output/.gitkeep",
            "logs/.gitkeep",
        ],
    },
)
