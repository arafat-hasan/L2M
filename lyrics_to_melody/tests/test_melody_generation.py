"""
Unit tests for melody generation components.
"""

import pytest
from pydantic import ValidationError

from lyrics_to_melody.models.melody_structure import (
    MelodyStructure,
    NoteStructure,
    NoteEvent,
    Melody,
)
from lyrics_to_melody.llm.parsers import MelodyParser


class TestNoteStructure:
    """Tests for NoteStructure model."""

    def test_valid_note(self):
        """Test creating a valid note."""
        note = NoteStructure(note="C4", duration=1.0, velocity=64)
        assert note.note == "C4"
        assert note.duration == 1.0
        assert note.velocity == 64

    def test_note_with_sharp(self):
        """Test note with sharp."""
        note = NoteStructure(note="F#5", duration=0.5)
        assert note.note == "F#5"

    def test_note_with_flat(self):
        """Test note with flat."""
        note = NoteStructure(note="Bb3", duration=2.0)
        assert note.note == "Bb3"

    def test_invalid_duration(self):
        """Test that negative duration is rejected."""
        with pytest.raises(ValidationError):
            NoteStructure(note="C4", duration=-1.0)

    def test_invalid_velocity(self):
        """Test that invalid velocity is rejected."""
        with pytest.raises(ValidationError):
            NoteStructure(note="C4", duration=1.0, velocity=200)

    def test_invalid_note_format(self):
        """Test that invalid note format is rejected."""
        with pytest.raises(ValidationError):
            NoteStructure(note="invalid", duration=1.0)


class TestMelodyStructure:
    """Tests for MelodyStructure model."""

    def test_valid_melody(self):
        """Test creating a valid melody structure."""
        melody = MelodyStructure(
            key="C major",
            melody=[
                NoteStructure(note="C4", duration=1.0),
                NoteStructure(note="D4", duration=1.0),
            ]
        )
        assert melody.key == "C major"
        assert len(melody.melody) == 2

    def test_total_duration(self):
        """Test calculating total duration."""
        melody = MelodyStructure(
            key="C major",
            melody=[
                NoteStructure(note="C4", duration=1.0),
                NoteStructure(note="D4", duration=0.5),
                NoteStructure(note="E4", duration=2.0),
            ]
        )
        assert melody.get_total_duration() == 3.5

    def test_note_count(self):
        """Test counting notes."""
        melody = MelodyStructure(
            key="A minor",
            melody=[
                NoteStructure(note="A3", duration=1.0),
                NoteStructure(note="C4", duration=1.0),
            ]
        )
        assert melody.get_note_count() == 2


class TestNoteEvent:
    """Tests for NoteEvent dataclass."""

    def test_valid_note_event(self):
        """Test creating a valid note event."""
        event = NoteEvent(pitch="C4", duration=1.0)
        assert event.pitch == "C4"
        assert event.duration == 1.0
        assert event.velocity == 64  # Default

    def test_invalid_duration(self):
        """Test that invalid duration raises error."""
        with pytest.raises(ValueError):
            NoteEvent(pitch="C4", duration=-1.0)

    def test_invalid_velocity(self):
        """Test that invalid velocity raises error."""
        with pytest.raises(ValueError):
            NoteEvent(pitch="C4", duration=1.0, velocity=200)


class TestMelody:
    """Tests for Melody IR dataclass."""

    def test_valid_melody_ir(self):
        """Test creating a valid melody IR."""
        melody = Melody(
            key="C major",
            tempo=120,
            time_signature="4/4",
            notes=[
                NoteEvent(pitch="C4", duration=1.0),
                NoteEvent(pitch="D4", duration=1.0),
            ]
        )
        assert melody.key == "C major"
        assert melody.tempo == 120
        assert melody.get_note_count() == 2
        assert melody.get_duration() == 2.0

    def test_invalid_tempo(self):
        """Test that invalid tempo raises error."""
        with pytest.raises(ValueError):
            Melody(
                key="C major",
                tempo=-10,
                time_signature="4/4",
                notes=[NoteEvent(pitch="C4", duration=1.0)]
            )

    def test_empty_notes(self):
        """Test that empty notes list raises error."""
        with pytest.raises(ValueError):
            Melody(
                key="C major",
                tempo=120,
                time_signature="4/4",
                notes=[]
            )


class TestMelodyParser:
    """Tests for MelodyParser."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        response = """
```json
{
  "key": "G major",
  "melody": [
    {"note": "G4", "duration": 0.5},
    {"note": "A4", "duration": 1.0}
  ]
}
```
        """
        structure = MelodyParser.parse(response)
        assert structure is not None
        assert structure.key == "G major"
        assert len(structure.melody) == 2
        assert structure.melody[0].note == "G4"

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns None."""
        response = "This is not JSON"
        structure = MelodyParser.parse(response)
        assert structure is None

    def test_parse_missing_fields(self):
        """Test parsing JSON with missing fields returns None."""
        response = """
```json
{
  "key": "C major"
}
```
        """
        structure = MelodyParser.parse(response)
        assert structure is None
