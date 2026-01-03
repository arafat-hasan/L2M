"""
Main CLI entry point for the l2m system.

Provides command-line interface for converting lyrics to musical melodies.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from l2m.config import config
from l2m.llm.client import LLMClient
from l2m.services.lyric_parser import LyricParser
from l2m.services.melody_generator import MelodyGenerator
from l2m.services.midi_writer import MIDIWriter
from l2m.services.audio_renderer import AudioRenderer
from l2m.utils.logger import get_logger
from l2m.utils.path_utils import sanitize_filename
from l2m.utils.input_validators import InputValidator
from l2m.utils.progress import step_progress, show_status

logger = get_logger(__name__)


class LyricsToMelodyApp:
    """
    Main application class for l2m system.

    Orchestrates the complete pipeline from lyrics to music notation.
    """

    def __init__(self):
        """Initialize the application."""
        logger.info("=" * 60)
        logger.info("l2m System")
        logger.info("=" * 60)

        # Validate configuration
        if not config.validate():
            logger.error("Configuration validation failed")
            logger.error("Please ensure OPENAI_API_KEY is set in .env file")
            sys.exit(1)

        # Initialize components
        self.lyric_parser = LyricParser()
        self.llm_client = LLMClient()
        self.melody_generator = MelodyGenerator(self.llm_client)
        self.midi_writer = MIDIWriter()
        self.audio_renderer = None  # Lazy initialization

        logger.info("All components initialized successfully")

    def process_lyrics(
        self,
        lyrics: str,
        output_name: str = "output",
        dry_run: bool = False,
        enable_audio: bool = False,
        soundfont_path: Optional[str] = None
    ) -> None:
        """
        Process lyrics through the complete pipeline.

        Args:
            lyrics: Input lyrics text
            output_name: Base name for output files (will be sanitized for security)
            dry_run: If True, only show analysis without generating files
            enable_audio: If True, also generate audio files (WAV/MP3)
            soundfont_path: Optional path to SoundFont file for audio rendering

        Raises:
            ValueError: If inputs fail validation
        """
        # Validate lyrics input
        is_valid, error_msg = InputValidator.validate_lyrics(lyrics)
        if not is_valid:
            logger.error(f"Lyrics validation failed: {error_msg}")
            raise ValueError(f"Invalid lyrics input:\n{error_msg}")

        # Validate output name
        is_valid, error_msg = InputValidator.validate_output_name(output_name)
        if not is_valid:
            logger.error(f"Output name validation failed: {error_msg}")
            raise ValueError(f"Invalid output name:\n{error_msg}")

        # Sanitize output_name to prevent path traversal attacks
        safe_output_name = sanitize_filename(output_name)
        if safe_output_name != output_name:
            logger.warning(
                f"Output name sanitized for security: '{output_name}' -> '{safe_output_name}'"
            )

        logger.info("Starting l2m pipeline")
        logger.info(f"Output name: {safe_output_name}")
        logger.info(f"Input lyrics: {lyrics[:100]}{'...' if len(lyrics) > 100 else ''}")

        try:
            # Step 1: Parse and normalize lyrics
            with step_progress(1, 4, "Lyrics Parsing"):
                normalized_lyrics = self.lyric_parser.normalize(lyrics)
                logger.info(f"Normalized lyrics: {normalized_lyrics}")

            # Step 2: Emotion and rhythm analysis
            with step_progress(2, 4, "Emotion & Rhythm Analysis"):
                emotion_response = self.llm_client.analyze_emotion(normalized_lyrics)
                emotion_analysis = emotion_response.analysis

                show_status(f"Emotion: {emotion_analysis.emotion}", "info")
                show_status(f"Tempo: {emotion_analysis.tempo} BPM", "info")
                show_status(f"Time Signature: {emotion_analysis.time_signature}", "info")
                show_status(f"Phrases: {len(emotion_analysis.phrases)}", "info")
                show_status(f"Total Syllables: {emotion_analysis.get_total_syllables()}", "info")

                if emotion_response.fallback_used:
                    show_status("Fallback emotion analysis was used", "warning")

            # Step 3: Melody generation
            with step_progress(3, 4, "Melody Generation"):
                melody = self.melody_generator.generate(
                    lyrics=normalized_lyrics,
                    emotion_analysis=emotion_analysis
                )

                show_status(f"Generated melody in key: {melody.key}", "success")
                show_status(f"Number of notes: {melody.get_note_count()}", "info")
                show_status(f"Total duration: {melody.get_duration()} beats", "info")

            # Preview
            if dry_run:
                logger.info("\n" + "=" * 60)
                logger.info("MELODY PREVIEW (Dry Run)")
                logger.info("=" * 60)
                preview = self.midi_writer.preview_score(melody)
                print("\n" + preview)
                show_status("Dry run complete. No files generated.", "success")
                return

            # Determine total steps (4 base + 1 if audio enabled)
            total_steps = 5 if enable_audio else 4

            # Step 4: Write output files
            with step_progress(4, total_steps, "Writing Output Files"):
                midi_path, xml_path = self.midi_writer.write_both(melody, safe_output_name)

            logger.info(f"✓ MIDI file: {midi_path}")
            logger.info(f"✓ MusicXML file: {xml_path}")

            # Step 5: Render audio (optional)
            audio_paths = {}
            if enable_audio:
                with step_progress(5, total_steps, "Rendering Audio"):
                    try:
                        # Initialize audio renderer if needed
                        if self.audio_renderer is None:
                            sf_path = Path(soundfont_path) if soundfont_path else None
                            self.audio_renderer = AudioRenderer(soundfont_path=sf_path)

                        # Render audio
                        audio_paths = self.audio_renderer.render_all(midi_path, safe_output_name)

                        for fmt, path in audio_paths.items():
                            logger.info(f"✓ {fmt.upper()} file: {path}")
                            show_status(f"Generated {fmt.upper()}: {path.name}", "success")

                    except Exception as e:
                        logger.warning(f"Audio rendering failed: {e}")
                        show_status(f"Audio rendering failed: {e}", "warning")
                        print(f"\nWARNING: Audio rendering failed: {e}")
                        print("MIDI and MusicXML files were generated successfully.")

            # Success summary
            logger.info("\n" + "=" * 60)
            logger.info("PIPELINE COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"Generated files:")
            logger.info(f"  - {midi_path}")
            logger.info(f"  - {xml_path}")
            for fmt, path in audio_paths.items():
                logger.info(f"  - {path}")

            # Print to console for user
            print("\n" + "=" * 60)
            print("SUCCESS! Melody generated successfully.")
            print("=" * 60)
            print(f"Output files:")
            print(f"  MIDI:      {midi_path}")
            print(f"  MusicXML:  {xml_path}")
            for fmt, path in audio_paths.items():
                print(f"  {fmt.upper()}:      {path}")
            print(f"\nMelody info:")
            print(f"  Key:       {melody.key}")
            print(f"  Tempo:     {melody.tempo} BPM")
            print(f"  Notes:     {melody.get_note_count()}")
            print(f"  Duration:  {melody.get_duration():.1f} beats")
            print("=" * 60 + "\n")

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            print(f"\nERROR: {e}")
            print("Check logs for details: logs/system.log")
            sys.exit(1)


def main():
    """
    Main CLI entry point.
    """
    parser = argparse.ArgumentParser(
        description="l2m: Convert song lyrics into musical melodies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --lyrics "The sun will rise again"
  python main.py --lyrics "Dancing in the moonlight" --out dance.mid
  python main.py --lyrics "Stars guide me home" --dry-run

For more information, see README.md
        """
    )

    parser.add_argument(
        "--lyrics",
        type=str,
        required=True,
        help="Input lyrics as a string"
    )

    parser.add_argument(
        "--out",
        type=str,
        default="output",
        help="Base name for output files (without extension). Default: output"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show analysis and preview without generating files"
    )

    parser.add_argument(
        "--audio",
        action="store_true",
        help="Also generate audio file (WAV/MP3) from MIDI using FluidSynth"
    )

    parser.add_argument(
        "--soundfont",
        type=str,
        help="Path to SoundFont (.sf2) file for audio rendering. "
             "If not specified, uses SOUNDFONT_PATH from .env"
    )

    args = parser.parse_args()

    # Create and run application
    app = LyricsToMelodyApp()
    app.process_lyrics(
        lyrics=args.lyrics,
        output_name=args.out,
        dry_run=args.dry_run,
        enable_audio=args.audio,
        soundfont_path=args.soundfont
    )


if __name__ == "__main__":
    main()
