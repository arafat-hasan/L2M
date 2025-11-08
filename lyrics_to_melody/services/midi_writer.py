"""
MIDI and MusicXML writer service.

Converts melody IR to music notation and exports to MIDI and MusicXML formats.
"""

from pathlib import Path
from typing import Optional

from music21 import stream, note, metadata, tempo, meter, key

from lyrics_to_melody.config import config
from lyrics_to_melody.models.melody_structure import Melody
from lyrics_to_melody.utils.logger import get_logger

logger = get_logger(__name__)


class MIDIWriter:
    """
    Service for writing melodies to MIDI and MusicXML files.

    Uses music21 library for music notation and export.
    """

    def __init__(self):
        """Initialize MIDI writer."""
        logger.debug("[MIDIWriter] Initialized")

    def create_score(self, melody: Melody) -> stream.Score:
        """
        Create a music21 Score from melody IR.

        Args:
            melody: Melody internal representation

        Returns:
            stream.Score: music21 score object
        """
        logger.info("[MIDIWriter] Creating score")

        # Create score and part
        score = stream.Score()
        part = stream.Part()

        # Add metadata
        score.metadata = metadata.Metadata()
        score.metadata.title = melody.title
        score.metadata.composer = melody.composer

        # Add tempo
        tempo_mark = tempo.MetronomeMark(number=melody.tempo)
        part.append(tempo_mark)

        # Add time signature
        time_sig = self._parse_time_signature(melody.time_signature)
        part.append(time_sig)

        # Add key signature
        key_sig = self._parse_key_signature(melody.key)
        part.append(key_sig)

        # Add notes
        for note_event in melody.notes:
            n = note.Note(note_event.pitch)
            n.quarterLength = note_event.duration
            n.volume.velocity = note_event.velocity
            part.append(n)

        # Add part to score
        score.append(part)

        logger.info(f"[MIDIWriter] Created score with {len(melody.notes)} notes")

        return score

    def write_midi(
        self,
        melody: Melody,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Write melody to MIDI file.

        Args:
            melody: Melody to write
            output_path: Optional custom output path

        Returns:
            Path: Path to written MIDI file
        """
        if output_path is None:
            output_path = config.OUTPUT_DIR / "output.mid"

        logger.info(f"[MIDIWriter] Writing MIDI to: {output_path}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create score
        score = self.create_score(melody)

        # Write MIDI file
        try:
            score.write('midi', fp=str(output_path))
            logger.info(f"[MIDIWriter] Successfully wrote MIDI: {output_path}")
        except Exception as e:
            logger.error(f"[MIDIWriter] Error writing MIDI: {e}")
            raise

        return output_path

    def write_musicxml(
        self,
        melody: Melody,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Write melody to MusicXML file.

        Args:
            melody: Melody to write
            output_path: Optional custom output path

        Returns:
            Path: Path to written MusicXML file
        """
        if output_path is None:
            output_path = config.OUTPUT_DIR / "output.musicxml"

        logger.info(f"[MIDIWriter] Writing MusicXML to: {output_path}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create score
        score = self.create_score(melody)

        # Write MusicXML file
        try:
            score.write('musicxml', fp=str(output_path))
            logger.info(f"[MIDIWriter] Successfully wrote MusicXML: {output_path}")
        except Exception as e:
            logger.error(f"[MIDIWriter] Error writing MusicXML: {e}")
            raise

        return output_path

    def write_both(
        self,
        melody: Melody,
        output_name: str = "output"
    ) -> tuple[Path, Path]:
        """
        Write melody to both MIDI and MusicXML files.

        Args:
            melody: Melody to write
            output_name: Base name for output files (without extension)

        Returns:
            tuple[Path, Path]: Paths to (MIDI file, MusicXML file)
        """
        logger.info(f"[MIDIWriter] Writing both MIDI and MusicXML with base name: {output_name}")

        midi_path = config.OUTPUT_DIR / f"{output_name}.mid"
        xml_path = config.OUTPUT_DIR / f"{output_name}.musicxml"

        midi_path = self.write_midi(melody, midi_path)
        xml_path = self.write_musicxml(melody, xml_path)

        return midi_path, xml_path

    def _parse_time_signature(self, time_sig: str) -> meter.TimeSignature:
        """
        Parse time signature string to music21 object.

        Args:
            time_sig: Time signature string (e.g., '4/4')

        Returns:
            meter.TimeSignature: music21 time signature object
        """
        try:
            return meter.TimeSignature(time_sig)
        except Exception as e:
            logger.warning(f"[MIDIWriter] Invalid time signature '{time_sig}', using 4/4. Error: {e}")
            return meter.TimeSignature('4/4')

    def _parse_key_signature(self, key_str: str) -> key.Key:
        """
        Parse key string to music21 object.

        Args:
            key_str: Key string (e.g., 'C major', 'A minor')

        Returns:
            key.Key: music21 key object
        """
        try:
            # Parse "C major" or "A minor" format
            parts = key_str.strip().split()
            if len(parts) == 2:
                tonic = parts[0]
                mode = parts[1].lower()

                if mode == 'major':
                    return key.Key(tonic)
                elif mode == 'minor':
                    return key.Key(tonic, 'minor')

            # If format is unexpected, try direct parsing
            return key.Key(key_str)

        except Exception as e:
            logger.warning(f"[MIDIWriter] Invalid key '{key_str}', using C major. Error: {e}")
            return key.Key('C')

    def preview_score(self, melody: Melody) -> str:
        """
        Generate a text preview of the score.

        Args:
            melody: Melody to preview

        Returns:
            str: Text representation of the score
        """
        lines = []
        lines.append(f"Title: {melody.title}")
        lines.append(f"Composer: {melody.composer}")
        lines.append(f"Key: {melody.key}")
        lines.append(f"Tempo: {melody.tempo} BPM")
        lines.append(f"Time Signature: {melody.time_signature}")
        lines.append(f"Number of Notes: {melody.get_note_count()}")
        lines.append(f"Total Duration: {melody.get_duration()} beats")
        lines.append("\nNotes:")

        for i, note_event in enumerate(melody.notes, 1):
            lines.append(
                f"  {i:3d}. {note_event.pitch:4s}  "
                f"duration={note_event.duration:4.2f}  "
                f"velocity={note_event.velocity:3d}"
            )

        return "\n".join(lines)
