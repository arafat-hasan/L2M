"""
Example usage script for the Lyrics-to-Melody system.

This script demonstrates how to use the system programmatically
(as opposed to using the CLI).
"""

from lyrics_to_melody.llm.client import LLMClient
from lyrics_to_melody.services.lyric_parser import LyricParser
from lyrics_to_melody.services.melody_generator import MelodyGenerator
from lyrics_to_melody.services.midi_writer import MIDIWriter
from lyrics_to_melody.config import config


def example_1_basic():
    """Basic example: Generate melody from simple lyrics."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 60)

    lyrics = "The sun will rise again"

    # Initialize components
    parser = LyricParser()
    llm_client = LLMClient()
    generator = MelodyGenerator(llm_client)
    writer = MIDIWriter()

    # Process lyrics
    normalized = parser.normalize(lyrics)
    print(f"Lyrics: {normalized}")

    # Analyze emotion
    emotion_response = llm_client.analyze_emotion(normalized)
    analysis = emotion_response.analysis

    print(f"Emotion: {analysis.emotion}")
    print(f"Tempo: {analysis.tempo} BPM")

    # Generate melody
    melody = generator.generate(normalized, analysis)
    print(f"Key: {melody.key}")
    print(f"Notes: {melody.get_note_count()}")

    # Write files
    midi_path, xml_path = writer.write_both(melody, "example1")
    print(f"Output: {midi_path}")


def example_2_fallback():
    """Example demonstrating fallback heuristics."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Using Fallback Heuristics")
    print("=" * 60)

    # Simulate LLM failure by directly using fallback
    from lyrics_to_melody.models.emotion_analysis import (
        EmotionAnalysis,
        PhraseAnalysis,
    )

    lyrics = "Dancing in the moonlight"

    # Manual emotion analysis (simulating LLM output)
    analysis = EmotionAnalysis(
        emotion="happy",
        tempo=115,
        time_signature="4/4",
        phrases=[PhraseAnalysis(line=lyrics, syllables=7)]
    )

    print(f"Using predefined analysis:")
    print(f"  Emotion: {analysis.emotion}")
    print(f"  Tempo: {analysis.tempo}")

    # Generate with fallback
    llm_client = LLMClient()
    generator = MelodyGenerator(llm_client)

    # Use fallback melody generation directly
    melody_structure = generator.generate_fallback_melody(
        emotion="happy",
        total_syllables=7
    )

    print(f"Generated fallback melody:")
    print(f"  Key: {melody_structure.key}")
    print(f"  Notes: {len(melody_structure.melody)}")


def example_3_parser():
    """Example focusing on lyric parsing."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Lyric Parsing")
    print("=" * 60)

    parser = LyricParser()

    lyrics = """
    Memories fade like photographs
    Left in the rain
    """

    # Normalize
    normalized = parser.normalize(lyrics)
    print(f"Normalized: {normalized}")

    # Split lines
    lines = parser.split_into_lines(normalized)
    print(f"Lines: {len(lines)}")

    # Estimate syllables
    for line in lines:
        syllables = parser.estimate_syllables(line)
        print(f"  '{line}' → {syllables} syllables")


def example_4_preview():
    """Example showing melody preview without file generation."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Preview Mode")
    print("=" * 60)

    from lyrics_to_melody.models.melody_structure import Melody, NoteEvent

    # Create a simple melody manually
    melody = Melody(
        key="C major",
        tempo=100,
        time_signature="4/4",
        notes=[
            NoteEvent(pitch="C4", duration=1.0),
            NoteEvent(pitch="D4", duration=1.0),
            NoteEvent(pitch="E4", duration=1.0),
            NoteEvent(pitch="C4", duration=2.0),
        ]
    )

    # Preview
    writer = MIDIWriter()
    preview = writer.preview_score(melody)
    print(preview)


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("LYRICS-TO-MELODY EXAMPLE USAGE")
    print("=" * 60)

    # Check configuration
    if not config.OPENAI_API_KEY:
        print("\nWARNING: OPENAI_API_KEY not set.")
        print("Examples requiring LLM will fail.")
        print("Set your API key in .env file to run all examples.\n")

    try:
        # Example 3 (no API needed)
        example_3_parser()

        # Example 4 (no API needed)
        example_4_preview()

        # Example 2 (no API needed for fallback)
        example_2_fallback()

        # Example 1 (requires API)
        if config.OPENAI_API_KEY:
            example_1_basic()
        else:
            print("\nSkipping Example 1 (requires API key)")

        print("\n" + "=" * 60)
        print("EXAMPLES COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
