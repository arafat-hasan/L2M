"""
Pydantic models for emotion and rhythm analysis.

These models validate the structure of LLM responses during
the emotion analysis phase of the pipeline.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class PhraseAnalysis(BaseModel):
    """
    Represents the analysis of a single phrase or line.

    Attributes:
        line: The text of the lyric line
        syllables: Estimated syllable count for the line
    """

    line: str = Field(..., description="The text of the lyric line")
    syllables: int = Field(..., ge=1, description="Number of syllables in the line")

    @field_validator('line')
    @classmethod
    def line_not_empty(cls, v: str) -> str:
        """Validate that line is not empty."""
        if not v.strip():
            raise ValueError("Line cannot be empty")
        return v.strip()


class EmotionAnalysis(BaseModel):
    """
    Represents the complete emotion and rhythm analysis of lyrics.

    This is the expected output structure from the LLM during
    the emotion analysis stage.

    Attributes:
        emotion: Dominant emotion (e.g., 'happy', 'sad', 'hopeful')
        tempo: Suggested tempo in BPM
        time_signature: Musical time signature (e.g., '4/4', '3/4')
        phrases: List of analyzed phrases with syllable counts
    """

    emotion: str = Field(
        ...,
        description="Dominant emotion of the lyrics"
    )
    tempo: int = Field(
        ...,
        ge=40,
        le=200,
        description="Suggested tempo in beats per minute"
    )
    time_signature: str = Field(
        default="4/4",
        description="Musical time signature"
    )
    phrases: List[PhraseAnalysis] = Field(
        ...,
        min_length=1,
        description="Breakdown of phrases with syllable counts"
    )

    @field_validator('emotion')
    @classmethod
    def normalize_emotion(cls, v: str) -> str:
        """Normalize emotion to lowercase."""
        return v.lower().strip()

    @field_validator('time_signature')
    @classmethod
    def validate_time_signature(cls, v: str) -> str:
        """Validate time signature format."""
        valid_signatures = ["4/4", "3/4", "6/8", "2/4", "5/4", "7/8"]
        if v not in valid_signatures:
            # Return default if invalid
            return "4/4"
        return v

    def get_total_syllables(self) -> int:
        """
        Calculate total syllables across all phrases.

        Returns:
            int: Total syllable count
        """
        return sum(phrase.syllables for phrase in self.phrases)

    def get_average_syllables_per_phrase(self) -> float:
        """
        Calculate average syllables per phrase.

        Returns:
            float: Average syllable count
        """
        if not self.phrases:
            return 0.0
        return self.get_total_syllables() / len(self.phrases)


class EmotionAnalysisResponse(BaseModel):
    """
    Wrapper for the emotion analysis response with metadata.

    Attributes:
        analysis: The validated emotion analysis
        raw_response: Original LLM response for debugging
        success: Whether the analysis was successful
        fallback_used: Whether fallback values were applied
    """

    analysis: EmotionAnalysis
    raw_response: Optional[str] = None
    success: bool = True
    fallback_used: bool = False
