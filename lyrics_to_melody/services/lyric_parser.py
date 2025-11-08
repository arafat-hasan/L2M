"""
Lyric parsing service.

Handles normalization, cleaning, and syllable estimation for lyrics.
"""

import re
from typing import List

from lyrics_to_melody.utils.logger import get_logger
from lyrics_to_melody.utils.validators import LyricsValidator

logger = get_logger(__name__)


class LyricParser:
    """
    Parser for processing and analyzing lyrics.

    Provides text normalization, line splitting, and syllable estimation.
    """

    def __init__(self):
        """Initialize the lyric parser."""
        logger.debug("[LyricsParsing] Initialized")

    def normalize(self, lyrics: str) -> str:
        """
        Normalize lyrics text.

        - Remove extra whitespace
        - Normalize line breaks
        - Preserve basic punctuation

        Args:
            lyrics: Raw lyrics text

        Returns:
            str: Normalized lyrics
        """
        logger.info("[LyricsParsing] Normalizing lyrics")

        # Validate input
        is_valid, error = LyricsValidator.validate_lyrics(lyrics)
        if not is_valid:
            raise ValueError(f"Invalid lyrics: {error}")

        # Normalize whitespace
        lyrics = re.sub(r'\s+', ' ', lyrics)

        # Normalize line breaks (preserve intentional breaks)
        lyrics = lyrics.strip()

        logger.debug(f"[LyricsParsing] Normalized to {len(lyrics)} characters")

        return lyrics

    def split_into_lines(self, lyrics: str) -> List[str]:
        """
        Split lyrics into lines/phrases.

        Args:
            lyrics: Normalized lyrics text

        Returns:
            List[str]: List of lyric lines
        """
        logger.debug("[LyricsParsing] Splitting into lines")

        # Split by common delimiters
        # Try newlines first
        if '\n' in lyrics:
            lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        # Try periods
        elif '.' in lyrics:
            lines = [line.strip() + '.' for line in lyrics.split('.') if line.strip()]
        # Try commas
        elif ',' in lyrics:
            lines = [line.strip() for line in lyrics.split(',') if line.strip()]
        # Fall back to full text as one line
        else:
            lines = [lyrics.strip()]

        logger.debug(f"[LyricsParsing] Split into {len(lines)} lines")

        return lines

    def estimate_syllables(self, text: str) -> int:
        """
        Estimate syllable count for a text phrase.

        Uses a simple heuristic based on vowel groups.

        Args:
            text: Text to analyze

        Returns:
            int: Estimated syllable count
        """
        # Remove punctuation and convert to lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())

        if not text.strip():
            return 0

        # Count vowel groups
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False

        for char in text:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for common patterns
        # Silent 'e' at the end
        if text.endswith('e'):
            syllable_count = max(1, syllable_count - 1)

        # Words ending in 'le' with consonant before
        if len(text) >= 3 and text[-2:] == 'le' and text[-3] not in vowels:
            syllable_count += 1

        # Ensure at least 1 syllable per word
        word_count = len(text.split())
        syllable_count = max(word_count, syllable_count)

        logger.debug(f"[LyricsParsing] Estimated {syllable_count} syllables for: '{text}'")

        return syllable_count

    def estimate_syllables_per_line(self, lyrics: str) -> List[dict]:
        """
        Estimate syllables for each line in lyrics.

        Args:
            lyrics: Normalized lyrics text

        Returns:
            List[dict]: List of dicts with 'line' and 'syllables' keys
        """
        lines = self.split_into_lines(lyrics)

        result = []
        for line in lines:
            syllables = self.estimate_syllables(line)
            result.append({
                'line': line,
                'syllables': syllables
            })

        logger.info(f"[LyricsParsing] Processed {len(result)} lines, "
                   f"total syllables: {sum(r['syllables'] for r in result)}")

        return result

    def clean_for_melody(self, lyrics: str) -> str:
        """
        Clean lyrics specifically for melody mapping.

        Removes punctuation but preserves word spacing.

        Args:
            lyrics: Lyrics text

        Returns:
            str: Cleaned lyrics
        """
        # Remove punctuation except spaces
        cleaned = re.sub(r'[^\w\s]', '', lyrics)

        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())

        return cleaned

    def get_word_count(self, lyrics: str) -> int:
        """
        Get word count for lyrics.

        Args:
            lyrics: Lyrics text

        Returns:
            int: Number of words
        """
        cleaned = self.clean_for_melody(lyrics)
        return len(cleaned.split())


# Example usage
if __name__ == "__main__":
    parser = LyricParser()

    test_lyrics = "The sun will rise again, bringing hope to every heart"

    normalized = parser.normalize(test_lyrics)
    print(f"Normalized: {normalized}")

    lines = parser.split_into_lines(normalized)
    print(f"Lines: {lines}")

    for line in lines:
        syllables = parser.estimate_syllables(line)
        print(f"  '{line}' -> {syllables} syllables")
