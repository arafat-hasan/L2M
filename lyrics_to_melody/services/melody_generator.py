"""
Melody generation service.

Integrates LLM-based melody generation with deterministic fallback heuristics.
Builds the internal representation (IR) for music notation.
"""

import random
from typing import List, TYPE_CHECKING

from lyrics_to_melody.config import config
from lyrics_to_melody.models.melody_structure import (
    Melody,
    MelodyStructure,
    NoteEvent,
    NoteStructure,
)
from lyrics_to_melody.models.emotion_analysis import EmotionAnalysis
from lyrics_to_melody.utils.logger import get_logger

if TYPE_CHECKING:
    from lyrics_to_melody.llm.client import LLMClient

logger = get_logger(__name__)


class MelodyGenerator:
    """
    Service for generating melodies from lyrics and emotion analysis.

    Coordinates LLM-based generation with fallback heuristics.
    """

    def __init__(self, llm_client: 'LLMClient'):
        """
        Initialize melody generator.

        Args:
            llm_client: LLM client for melody generation
        """
        self.llm_client = llm_client
        logger.debug("[MelodyGenerator] Initialized")

    def generate(
        self,
        lyrics: str,
        emotion_analysis: EmotionAnalysis
    ) -> Melody:
        """
        Generate complete melody from lyrics and emotion analysis.

        Args:
            lyrics: Input lyrics
            emotion_analysis: Validated emotion analysis

        Returns:
            Melody: Complete melody IR
        """
        logger.info("[MelodyGenerator] Starting melody generation")

        # Get total syllables
        total_syllables = emotion_analysis.get_total_syllables()

        # Generate melody structure via LLM
        response = self.llm_client.generate_melody_structure(
            lyrics=lyrics,
            emotion=emotion_analysis.emotion,
            tempo=emotion_analysis.tempo,
            time_signature=emotion_analysis.time_signature,
            total_syllables=total_syllables
        )

        if not response.success or response.fallback_used:
            logger.warning("[MelodyGenerator] Using fallback melody generation")

        # Build internal representation
        melody = self.build_melody_ir(
            melody_structure=response.structure,
            tempo=emotion_analysis.tempo,
            time_signature=emotion_analysis.time_signature
        )

        logger.info(f"[MelodyGenerator] Generated melody with {melody.get_note_count()} notes")

        return melody

    def build_melody_ir(
        self,
        melody_structure: MelodyStructure,
        tempo: int,
        time_signature: str
    ) -> Melody:
        """
        Build internal representation from melody structure.

        Args:
            melody_structure: Validated melody structure from LLM
            tempo: Tempo in BPM
            time_signature: Time signature

        Returns:
            Melody: Complete melody IR
        """
        logger.debug("[MelodyGenerator] Building melody IR")

        # Convert NoteStructure to NoteEvent
        notes = []
        for note_struct in melody_structure.melody:
            note_event = NoteEvent(
                pitch=note_struct.note,
                duration=note_struct.duration,
                velocity=note_struct.velocity
            )
            notes.append(note_event)

        # Create melody IR
        melody = Melody(
            key=melody_structure.key,
            tempo=tempo,
            time_signature=time_signature,
            notes=notes
        )

        return melody

    def generate_fallback_melody(
        self,
        emotion: str,
        total_syllables: int
    ) -> MelodyStructure:
        """
        Generate melody using deterministic heuristics (fallback).

        Args:
            emotion: Detected emotion
            total_syllables: Number of notes to generate

        Returns:
            MelodyStructure: Fallback melody structure
        """
        logger.info(f"[MelodyGenerator] Generating fallback melody for emotion: {emotion}")

        # Get emotion parameters
        emotion_params = config.get_emotion_params(emotion)

        # Select key
        key = random.choice(emotion_params["keys"])
        logger.debug(f"[MelodyGenerator] Selected key: {key}")

        # Get scale notes
        scale_notes = config.get_scale_notes(key)

        # Generate notes based on contour
        contour = emotion_params["contour"]
        notes = self._generate_notes_by_contour(
            scale_notes=scale_notes,
            contour=contour,
            note_count=total_syllables
        )

        # Create melody structure
        melody_structure = MelodyStructure(
            key=key,
            melody=notes
        )

        logger.info(f"[MelodyGenerator] Generated fallback melody: {len(notes)} notes in {key}")

        return melody_structure

    def _generate_notes_by_contour(
        self,
        scale_notes: List[str],
        contour: str,
        note_count: int
    ) -> List[NoteStructure]:
        """
        Generate notes following a melodic contour.

        Args:
            scale_notes: List of note names in the scale
            contour: Contour type ('ascending', 'descending', 'wavy', 'balanced', 'erratic')
            note_count: Number of notes to generate

        Returns:
            List[NoteStructure]: List of notes with durations
        """
        logger.debug(f"[MelodyGenerator] Generating {note_count} notes with {contour} contour")

        notes = []
        octave = 4  # Start in middle octave

        # Define contour patterns
        if contour == "ascending":
            # Gradually ascend through the scale
            for i in range(note_count):
                scale_index = min(i % len(scale_notes), len(scale_notes) - 1)
                note_name = scale_notes[scale_index]

                # Move up octave every scale cycle
                if i > 0 and i % len(scale_notes) == 0:
                    octave = min(octave + 1, 5)

                notes.append(self._create_note(note_name, octave, i, note_count))

        elif contour == "descending":
            # Gradually descend through the scale
            for i in range(note_count):
                scale_index = len(scale_notes) - 1 - (i % len(scale_notes))
                note_name = scale_notes[scale_index]

                # Move down octave every scale cycle
                if i > 0 and i % len(scale_notes) == 0:
                    octave = max(octave - 1, 3)

                notes.append(self._create_note(note_name, octave, i, note_count))

        elif contour == "wavy":
            # Wave pattern: up and down
            for i in range(note_count):
                # Create sine-like wave through scale
                wave_position = (i % 8) / 8.0  # 0 to 1
                scale_index = int(wave_position * len(scale_notes))
                if (i // 8) % 2 == 1:  # Reverse every wave
                    scale_index = len(scale_notes) - 1 - scale_index

                note_name = scale_notes[scale_index]
                notes.append(self._create_note(note_name, octave, i, note_count))

        elif contour == "erratic":
            # Random jumps within scale
            for i in range(note_count):
                scale_index = random.randint(0, len(scale_notes) - 1)
                note_name = scale_notes[scale_index]

                # Occasional octave changes
                if random.random() < 0.3:
                    octave = random.choice([3, 4, 5])

                notes.append(self._create_note(note_name, octave, i, note_count))

        else:  # balanced
            # Balanced: stay in middle range
            for i in range(note_count):
                # Favor middle of scale
                scale_index = random.choices(
                    range(len(scale_notes)),
                    weights=[1, 2, 3, 3, 3, 2, 1][:len(scale_notes)]
                )[0]
                note_name = scale_notes[scale_index]
                notes.append(self._create_note(note_name, octave, i, note_count))

        return notes

    def _create_note(
        self,
        note_name: str,
        octave: int,
        position: int,
        total_notes: int
    ) -> NoteStructure:
        """
        Create a note structure with appropriate duration.

        Args:
            note_name: Note name (e.g., 'C', 'D#')
            octave: Octave number
            position: Position in the sequence
            total_notes: Total number of notes

        Returns:
            NoteStructure: Note with pitch and duration
        """
        # Create note with octave
        pitch = f"{note_name}{octave}"

        # Assign duration based on position
        # Last note is longer, others are equal
        if position == total_notes - 1:
            duration = 2.0  # Half note for ending
        elif position % 4 == 3:
            duration = 1.0  # Quarter note at phrase ends
        else:
            duration = 0.5  # Eighth notes for most

        # Vary velocity slightly for musicality
        base_velocity = 64
        velocity = max(48, min(80, base_velocity + random.randint(-8, 8)))

        return NoteStructure(
            note=pitch,
            duration=duration,
            velocity=velocity
        )
