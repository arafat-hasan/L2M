"""
Unit tests for emotion analysis components.
"""

import pytest
from pydantic import ValidationError

from lyrics_to_melody.models.emotion_analysis import (
    EmotionAnalysis,
    PhraseAnalysis,
)
from lyrics_to_melody.llm.parsers import EmotionParser


class TestPhraseAnalysis:
    """Tests for PhraseAnalysis model."""

    def test_valid_phrase(self):
        """Test creating a valid phrase analysis."""
        phrase = PhraseAnalysis(line="The sun will rise", syllables=5)
        assert phrase.line == "The sun will rise"
        assert phrase.syllables == 5

    def test_empty_line(self):
        """Test that empty lines are rejected."""
        with pytest.raises(ValidationError):
            PhraseAnalysis(line="", syllables=0)

    def test_negative_syllables(self):
        """Test that negative syllables are rejected."""
        with pytest.raises(ValidationError):
            PhraseAnalysis(line="Hello", syllables=-1)

    def test_line_stripped(self):
        """Test that line text is stripped."""
        phrase = PhraseAnalysis(line="  spaces  ", syllables=2)
        assert phrase.line == "spaces"


class TestEmotionAnalysis:
    """Tests for EmotionAnalysis model."""

    def test_valid_analysis(self):
        """Test creating a valid emotion analysis."""
        analysis = EmotionAnalysis(
            emotion="happy",
            tempo=120,
            time_signature="4/4",
            phrases=[
                PhraseAnalysis(line="Hello world", syllables=3)
            ]
        )
        assert analysis.emotion == "happy"
        assert analysis.tempo == 120
        assert analysis.time_signature == "4/4"
        assert len(analysis.phrases) == 1

    def test_emotion_normalized(self):
        """Test that emotion is normalized to lowercase."""
        analysis = EmotionAnalysis(
            emotion="HAPPY",
            tempo=100,
            time_signature="4/4",
            phrases=[PhraseAnalysis(line="Test", syllables=1)]
        )
        assert analysis.emotion == "happy"

    def test_invalid_tempo(self):
        """Test that invalid tempo is rejected."""
        with pytest.raises(ValidationError):
            EmotionAnalysis(
                emotion="happy",
                tempo=300,  # Too high
                time_signature="4/4",
                phrases=[PhraseAnalysis(line="Test", syllables=1)]
            )

    def test_invalid_time_signature(self):
        """Test that invalid time signatures are normalized."""
        analysis = EmotionAnalysis(
            emotion="happy",
            tempo=100,
            time_signature="99/99",  # Invalid
            phrases=[PhraseAnalysis(line="Test", syllables=1)]
        )
        # Should default to 4/4
        assert analysis.time_signature == "4/4"

    def test_total_syllables(self):
        """Test syllable counting across phrases."""
        analysis = EmotionAnalysis(
            emotion="happy",
            tempo=100,
            time_signature="4/4",
            phrases=[
                PhraseAnalysis(line="Line one", syllables=3),
                PhraseAnalysis(line="Line two", syllables=3),
            ]
        )
        assert analysis.get_total_syllables() == 6

    def test_average_syllables(self):
        """Test average syllables per phrase."""
        analysis = EmotionAnalysis(
            emotion="happy",
            tempo=100,
            time_signature="4/4",
            phrases=[
                PhraseAnalysis(line="Line one", syllables=4),
                PhraseAnalysis(line="Line two", syllables=2),
            ]
        )
        assert analysis.get_average_syllables_per_phrase() == 3.0


class TestEmotionParser:
    """Tests for EmotionParser."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        response = """
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
        """
        analysis = EmotionParser.parse(response)
        assert analysis is not None
        assert analysis.emotion == "hopeful"
        assert analysis.tempo == 90
        assert len(analysis.phrases) == 1

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns None."""
        response = "This is not JSON"
        analysis = EmotionParser.parse(response)
        assert analysis is None

    def test_parse_malformed_json(self):
        """Test parsing malformed JSON returns None."""
        response = """
```json
{
  "emotion": "happy",
  "tempo": "not a number"
}
```
        """
        analysis = EmotionParser.parse(response)
        assert analysis is None
