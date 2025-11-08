"""
Pydantic models for melody structure and musical representation.

These models validate melody generation from LLM and provide
the internal representation (IR) for music notation.
"""

from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class NoteStructure(BaseModel):
    """
    Represents a single note with pitch and duration.

    Attributes:
        note: Note name with octave (e.g., 'C4', 'D#5')
        duration: Duration in beats (e.g., 0.5 for eighth, 1.0 for quarter)
        velocity: MIDI velocity (0-127), controls volume
    """

    note: str = Field(..., description="Note name with octave (e.g., 'C4', 'A#5')")
    duration: float = Field(..., gt=0, description="Duration in beats")
    velocity: int = Field(default=64, ge=0, le=127, description="MIDI velocity")

    @field_validator('note')
    @classmethod
    def validate_note(cls, v: str) -> str:
        """Validate note format (e.g., C4, D#5, Bb3)."""
        if not v or len(v) < 2:
            raise ValueError(f"Invalid note format: {v}")

        # Basic validation: should contain a letter and a number
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)

        if not (has_letter and has_number):
            raise ValueError(f"Note must contain both letter and octave number: {v}")

        return v.strip()


class MelodyStructure(BaseModel):
    """
    Represents the complete melody structure from LLM.

    This is the expected output structure from the LLM during
    the melody generation stage.

    Attributes:
        key: Musical key (e.g., 'C major', 'A minor')
        melody: List of notes with durations
    """

    key: str = Field(..., description="Musical key (e.g., 'C major', 'A minor')")
    melody: List[NoteStructure] = Field(
        ...,
        min_length=1,
        description="Sequence of notes with durations"
    )

    @field_validator('key')
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Validate and normalize musical key."""
        return v.strip()

    def get_total_duration(self) -> float:
        """
        Calculate total duration of the melody in beats.

        Returns:
            float: Total duration
        """
        return sum(note.duration for note in self.melody)

    def get_note_count(self) -> int:
        """
        Get the number of notes in the melody.

        Returns:
            int: Number of notes
        """
        return len(self.melody)


class MelodyStructureResponse(BaseModel):
    """
    Wrapper for melody structure response with metadata.

    Attributes:
        structure: The validated melody structure
        raw_response: Original LLM response for debugging
        success: Whether the generation was successful
        fallback_used: Whether fallback values were applied
    """

    structure: MelodyStructure
    raw_response: Optional[str] = None
    success: bool = True
    fallback_used: bool = False


# Internal Representation (IR) for music generation
# Using dataclasses for performance and simplicity


@dataclass
class NoteEvent:
    """
    Internal representation of a musical note event.

    This is used internally for music generation and differs from
    the Pydantic model used for validation.

    Attributes:
        pitch: Note name with octave (e.g., 'C4')
        duration: Duration in beats
        velocity: MIDI velocity (0-127)
        offset: Start time offset in beats (optional)
    """

    pitch: str
    duration: float
    velocity: int = 64
    offset: float = 0.0

    def __post_init__(self):
        """Validate note event after initialization."""
        if self.duration <= 0:
            raise ValueError(f"Duration must be positive: {self.duration}")
        if not (0 <= self.velocity <= 127):
            raise ValueError(f"Velocity must be 0-127: {self.velocity}")


@dataclass
class Melody:
    """
    Complete internal representation of a melody.

    This IR is used by the MIDI writer and music notation generator.

    Attributes:
        key: Musical key
        tempo: Tempo in BPM
        time_signature: Time signature (e.g., '4/4')
        notes: List of note events
        title: Optional title for the composition
        composer: Optional composer name
    """

    key: str
    tempo: int
    time_signature: str
    notes: List[NoteEvent]
    title: str = "AI Generated Melody"
    composer: str = "AI Composer"

    def __post_init__(self):
        """Validate melody after initialization."""
        if self.tempo <= 0:
            raise ValueError(f"Tempo must be positive: {self.tempo}")
        if not self.notes:
            raise ValueError("Melody must contain at least one note")

    def get_duration(self) -> float:
        """
        Get total duration of the melody.

        Returns:
            float: Total duration in beats
        """
        if not self.notes:
            return 0.0
        return sum(note.duration for note in self.notes)

    def get_note_count(self) -> int:
        """
        Get number of notes in the melody.

        Returns:
            int: Number of notes
        """
        return len(self.notes)
