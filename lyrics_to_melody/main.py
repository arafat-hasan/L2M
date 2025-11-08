"""
Main CLI entry point for the Lyrics-to-Melody system.

Provides command-line interface for converting lyrics to musical melodies.
"""

import argparse
import sys
from pathlib import Path

from lyrics_to_melody.config import config
from lyrics_to_melody.llm.client import LLMClient
from lyrics_to_melody.services.lyric_parser import LyricParser
from lyrics_to_melody.services.melody_generator import MelodyGenerator
from lyrics_to_melody.services.midi_writer import MIDIWriter
from lyrics_to_melody.utils.logger import get_logger

logger = get_logger(__name__)


class LyricsToMelodyApp:
    """
    Main application class for Lyrics-to-Melody system.

    Orchestrates the complete pipeline from lyrics to music notation.
    """

    def __init__(self):
        """Initialize the application."""
        logger.info("=" * 60)
        logger.info("Lyrics-to-Melody System")
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

        logger.info("All components initialized successfully")

    def process_lyrics(
        self,
        lyrics: str,
        output_name: str = "output",
        dry_run: bool = False
    ) -> None:
        """
        Process lyrics through the complete pipeline.

        Args:
            lyrics: Input lyrics text
            output_name: Base name for output files
            dry_run: If True, only show analysis without generating files
        """
        logger.info("Starting lyrics-to-melody pipeline")
        logger.info(f"Input lyrics: {lyrics[:100]}{'...' if len(lyrics) > 100 else ''}")

        try:
            # Step 1: Parse and normalize lyrics
            logger.info("\n" + "=" * 60)
            logger.info("STEP 1: Lyrics Parsing")
            logger.info("=" * 60)

            normalized_lyrics = self.lyric_parser.normalize(lyrics)
            logger.info(f"Normalized lyrics: {normalized_lyrics}")

            # Step 2: Emotion and rhythm analysis
            logger.info("\n" + "=" * 60)
            logger.info("STEP 2: Emotion & Rhythm Analysis")
            logger.info("=" * 60)

            emotion_response = self.llm_client.analyze_emotion(normalized_lyrics)
            emotion_analysis = emotion_response.analysis

            logger.info(f"Emotion: {emotion_analysis.emotion}")
            logger.info(f"Tempo: {emotion_analysis.tempo} BPM")
            logger.info(f"Time Signature: {emotion_analysis.time_signature}")
            logger.info(f"Phrases: {len(emotion_analysis.phrases)}")
            logger.info(f"Total Syllables: {emotion_analysis.get_total_syllables()}")

            if emotion_response.fallback_used:
                logger.warning("Note: Fallback emotion analysis was used")

            # Step 3: Melody generation
            logger.info("\n" + "=" * 60)
            logger.info("STEP 3: Melody Generation")
            logger.info("=" * 60)

            melody = self.melody_generator.generate(
                lyrics=normalized_lyrics,
                emotion_analysis=emotion_analysis
            )

            logger.info(f"Generated melody in key: {melody.key}")
            logger.info(f"Number of notes: {melody.get_note_count()}")
            logger.info(f"Total duration: {melody.get_duration()} beats")

            # Preview
            if dry_run:
                logger.info("\n" + "=" * 60)
                logger.info("MELODY PREVIEW (Dry Run)")
                logger.info("=" * 60)
                preview = self.midi_writer.preview_score(melody)
                print("\n" + preview)
                logger.info("\nDry run complete. No files generated.")
                return

            # Step 4: Write output files
            logger.info("\n" + "=" * 60)
            logger.info("STEP 4: Writing Output Files")
            logger.info("=" * 60)

            midi_path, xml_path = self.midi_writer.write_both(melody, output_name)

            logger.info(f"✓ MIDI file: {midi_path}")
            logger.info(f"✓ MusicXML file: {xml_path}")

            # Success summary
            logger.info("\n" + "=" * 60)
            logger.info("PIPELINE COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"Generated files:")
            logger.info(f"  - {midi_path}")
            logger.info(f"  - {xml_path}")

            # Print to console for user
            print("\n" + "=" * 60)
            print("SUCCESS! Melody generated successfully.")
            print("=" * 60)
            print(f"Output files:")
            print(f"  MIDI:      {midi_path}")
            print(f"  MusicXML:  {xml_path}")
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
        description="Lyrics-to-Melody: Convert song lyrics into musical melodies",
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

    args = parser.parse_args()

    # Create and run application
    app = LyricsToMelodyApp()
    app.process_lyrics(
        lyrics=args.lyrics,
        output_name=args.out,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
