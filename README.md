# Lyrics-to-Melody System

A complete, modular Python system that converts human lyrics into structured melodic output (MIDI/MusicXML) using AI-powered emotion analysis and melody generation.

## Features

- **Intelligent Emotion Analysis**: Uses OpenAI's LLM to analyze lyrical emotion, tempo, and rhythm
- **AI-Powered Melody Generation**: Creates melodies that match the emotional content of lyrics
- **Fallback Heuristics**: Deterministic algorithms ensure robust operation even without LLM
- **Multiple Output Formats**: Exports to both MIDI (.mid) and MusicXML (.musicxml)
- **Clean Architecture**: Modular design with clear separation of concerns
- **Type-Safe**: Full type hints and Pydantic validation
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Architecture

The system follows a clean, modular architecture with five main stages:

1. **Lyrics Input & Parsing**: Text normalization and syllable estimation
2. **Emotion & Rhythm Analysis**: LLM-based emotional classification and tempo detection
3. **Melody Structure Generation**: AI-powered note and duration assignment
4. **Music Notation**: Conversion to music21 internal representation
5. **Output**: Export to MIDI and MusicXML formats

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key

### Option 1: Install as Package (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd L2M

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

This installs the package and makes the `lyrics-to-melody` command available.

### Option 2: Install Dependencies Only

```bash
# Clone the repository
git clone <repository-url>
cd L2M

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

If you use this option, run the app with `python run.py` instead of the command.

### Option 3: Using Poetry

```bash
# Clone the repository
git clone <repository-url>
cd L2M

# Install with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

## Configuration

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=gpt-4o-mini
TEMPERATURE=0.7
MAX_TOKENS=1500
```

## Usage

### Basic Usage

**If installed as package (Option 1):**

```bash
lyrics-to-melody --lyrics "The sun will rise again"
```

**If using run.py (Option 2):**

```bash
python run.py --lyrics "The sun will rise again"
```

This will generate:
- `lyrics_to_melody/output/output.mid` - MIDI file
- `lyrics_to_melody/output/output.musicxml` - MusicXML file

### Custom Output Name

```bash
# With installed package
lyrics-to-melody --lyrics "Dancing in the moonlight" --out dance

# Or with run.py
python run.py --lyrics "Dancing in the moonlight" --out dance
```

Generates:
- `lyrics_to_melody/output/dance.mid`
- `lyrics_to_melody/output/dance.musicxml`

### Dry Run (Preview Only)

Preview the analysis without generating files:

```bash
# With installed package
lyrics-to-melody --lyrics "Stars will guide me home" --dry-run

# Or with run.py
python run.py --lyrics "Stars will guide me home" --dry-run
```

### More Examples

```bash
# Happy, upbeat lyrics
python run.py --lyrics "Sunshine and rainbows fill the sky, dancing together you and I"

# Sad, melancholic lyrics
python run.py --lyrics "Memories fade like photographs left in the rain"

# Hopeful lyrics
python run.py --lyrics "Tomorrow brings a brand new day, hope will light the way"
```

**Note:** Replace `python run.py` with `lyrics-to-melody` if you installed as a package.

## Project Structure

```
lyrics_to_melody/
│
├── main.py                      # CLI entry point
├── config.py                    # Configuration management
│
├── llm/
│   ├── client.py                # OpenAI API wrapper
│   ├── parsers.py               # JSON validation & extraction
│   └── prompts/
│       ├── emotion_prompt.txt   # Emotion analysis prompt
│       └── melody_prompt.txt    # Melody generation prompt
│
├── models/
│   ├── emotion_analysis.py      # Pydantic models for emotion
│   └── melody_structure.py      # Pydantic models for melody
│
├── services/
│   ├── lyric_parser.py          # Lyrics normalization & syllable estimation
│   ├── melody_generator.py      # Melody generation with fallbacks
│   └── midi_writer.py           # MIDI/MusicXML export
│
├── utils/
│   ├── logger.py                # Logging configuration
│   └── validators.py            # Musical validation utilities
│
├── tests/
│   ├── test_emotion_analysis.py
│   └── test_melody_generation.py
│
├── output/                      # Generated files
└── logs/                        # System logs
```

## How It Works

### 1. Lyrics Parsing

The `LyricParser` service:
- Normalizes text (whitespace, punctuation)
- Splits lyrics into lines/phrases
- Estimates syllable count for rhythm mapping

### 2. Emotion Analysis

The LLM analyzes lyrics and extracts:
- **Emotion**: happy, sad, hopeful, tense, calm, excited
- **Tempo**: Suggested BPM (40-200)
- **Time Signature**: 4/4, 3/4, 6/8, etc.
- **Phrase Structure**: Line-by-line syllable breakdown

Example output:
```json
{
  "emotion": "hopeful",
  "tempo": 90,
  "time_signature": "4/4",
  "phrases": [
    {"line": "The sun will rise again", "syllables": 6}
  ]
}
```

### 3. Melody Generation

The LLM generates a melody structure:
- **Musical Key**: Selected based on emotion
- **Note Sequence**: One note per syllable
- **Durations**: Rhythmic values (quarter notes, eighth notes, etc.)

Example output:
```json
{
  "key": "G major",
  "melody": [
    {"note": "G4", "duration": 0.5, "velocity": 64},
    {"note": "A4", "duration": 1.0, "velocity": 64}
  ]
}
```

### 4. Fallback Heuristics

If LLM calls fail, the system uses deterministic rules:

| Emotion | Key     | Tempo Range | Contour     |
|---------|---------|-------------|-------------|
| Happy   | C major | 100-120 BPM | Ascending   |
| Hopeful | G major | 80-100 BPM  | Wavy        |
| Sad     | A minor | 60-80 BPM   | Descending  |
| Tense   | D minor | 90-110 BPM  | Erratic     |

### 5. Music Notation

The `MIDIWriter` service:
- Converts internal representation to music21 format
- Adds tempo, key, and time signature
- Exports to MIDI and MusicXML

## Logging

All operations are logged to `logs/system.log`:

```
[2025-01-08 10:30:15] [LyricsParsing] [INFO] Normalizing lyrics
[2025-01-08 10:30:16] [EmotionAnalysis] [INFO] Successfully parsed: emotion=hopeful
[2025-01-08 10:30:18] [MelodyGeneration] [INFO] Generated melody with 12 notes
[2025-01-08 10:30:19] [MIDIWriter] [INFO] Successfully wrote MIDI: output/output.mid
```

## Testing

Run the test suite:

```bash
# Using pytest
pytest

# With coverage report
pytest --cov=lyrics_to_melody --cov-report=html
```

Run individual test files:

```bash
pytest lyrics_to_melody/tests/test_emotion_analysis.py
pytest lyrics_to_melody/tests/test_melody_generation.py
```

## API Reference

### LLMClient

```python
from lyrics_to_melody.llm.client import LLMClient

client = LLMClient(api_key="your_key")

# Analyze emotion
response = client.analyze_emotion("The sun will rise again")
print(response.analysis.emotion)  # "hopeful"
print(response.analysis.tempo)    # 90
```

### MelodyGenerator

```python
from lyrics_to_melody.services.melody_generator import MelodyGenerator

generator = MelodyGenerator(llm_client)
melody = generator.generate(lyrics, emotion_analysis)

print(f"Key: {melody.key}")
print(f"Notes: {melody.get_note_count()}")
```

### MIDIWriter

```python
from lyrics_to_melody.services.midi_writer import MIDIWriter

writer = MIDIWriter()
midi_path, xml_path = writer.write_both(melody, "my_song")
```

## Troubleshooting

### OpenAI API Errors

If you see `OpenAI API error: ...`:
1. Check your API key in `.env`
2. Verify your OpenAI account has credits
3. Check internet connectivity

### Music21 Installation Issues

If music21 fails to install:
```bash
# On Ubuntu/Debian
sudo apt-get install python3-tk

# On macOS
brew install tcl-tk
```

### No MIDI Output

If MIDI files are not generated:
1. Check `logs/system.log` for errors
2. Ensure `output/` directory exists (created automatically)
3. Verify file permissions

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- OpenAI for GPT models
- music21 library for music notation
- Pydantic for data validation

## Future Enhancements

Potential extensions:
- Harmony generation (chord progressions)
- Multiple instrument support
- Style selection (jazz, classical, pop)
- Real-time playback
- Web interface
- Batch processing
- Custom training for specific musical styles

## Contact

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Enjoy creating melodies from your lyrics!** 🎵
