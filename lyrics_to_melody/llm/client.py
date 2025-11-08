"""
OpenAI API client wrapper for the Lyrics-to-Melody system.

Provides high-level interface for emotion analysis and melody generation
using LLM (Language Model) capabilities.
"""

from pathlib import Path
from typing import Optional

from openai import OpenAI, OpenAIError

from lyrics_to_melody.config import config
from lyrics_to_melody.llm.parsers import EmotionParser, MelodyParser
from lyrics_to_melody.models.emotion_analysis import (
    EmotionAnalysis,
    EmotionAnalysisResponse,
)
from lyrics_to_melody.models.melody_structure import (
    MelodyStructure,
    MelodyStructureResponse,
)
from lyrics_to_melody.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """
    Client for interacting with OpenAI LLM API.

    Handles prompt loading, API calls, response parsing, and error handling.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM client.

        Args:
            api_key: OpenAI API key (uses config if not provided)
        """
        self.api_key = api_key or config.OPENAI_API_KEY

        if not self.api_key:
            raise ValueError("OpenAI API key not provided and not found in config")

        self.client = OpenAI(api_key=self.api_key)
        self.model = config.MODEL_NAME
        self.temperature = config.TEMPERATURE
        self.max_tokens = config.MAX_TOKENS

        logger.info(f"[LLMClient] Initialized with model: {self.model}")

    def _load_prompt_template(self, template_name: str) -> str:
        """
        Load a prompt template from the prompts directory.

        Args:
            template_name: Name of the template file (e.g., 'emotion_prompt.txt')

        Returns:
            str: Template content

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_path = config.PROMPTS_DIR / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")

        return template_path.read_text(encoding='utf-8')

    def _call_llm(self, prompt: str) -> Optional[str]:
        """
        Make an API call to the LLM.

        Args:
            prompt: The prompt to send

        Returns:
            Optional[str]: LLM response text, or None if call fails
        """
        try:
            logger.debug(f"[LLMClient] Calling API with model: {self.model}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert music composer and analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content
            logger.debug(f"[LLMClient] Received response ({len(content)} chars)")

            return content

        except OpenAIError as e:
            logger.error(f"[LLMClient] OpenAI API error: {e}")
            return None
        except Exception as e:
            logger.error(f"[LLMClient] Unexpected error: {e}")
            return None

    def analyze_emotion(self, lyrics: str) -> EmotionAnalysisResponse:
        """
        Analyze emotion and rhythm of lyrics using LLM.

        Args:
            lyrics: Input lyrics text

        Returns:
            EmotionAnalysisResponse: Response with emotion analysis or fallback
        """
        logger.info("[LLMClient] Starting emotion analysis")

        try:
            # Load prompt template
            template = self._load_prompt_template("emotion_prompt.txt")
            prompt = template.format(lyrics=lyrics)

            # Call LLM
            response_text = self._call_llm(prompt)

            if not response_text:
                logger.warning("[LLMClient] No response from LLM, using fallback")
                return self._fallback_emotion_analysis(lyrics)

            # Parse response
            analysis = EmotionParser.parse(response_text)

            if not analysis:
                logger.warning("[LLMClient] Failed to parse response, using fallback")
                return self._fallback_emotion_analysis(lyrics)

            # Success
            return EmotionAnalysisResponse(
                analysis=analysis,
                raw_response=response_text,
                success=True,
                fallback_used=False
            )

        except Exception as e:
            logger.error(f"[LLMClient] Error in emotion analysis: {e}")
            return self._fallback_emotion_analysis(lyrics)

    def generate_melody_structure(
        self,
        lyrics: str,
        emotion: str,
        tempo: int,
        time_signature: str,
        total_syllables: int
    ) -> MelodyStructureResponse:
        """
        Generate melody structure using LLM.

        Args:
            lyrics: Input lyrics text
            emotion: Detected emotion
            tempo: Tempo in BPM
            time_signature: Time signature (e.g., '4/4')
            total_syllables: Total syllable count

        Returns:
            MelodyStructureResponse: Response with melody structure or fallback
        """
        logger.info("[LLMClient] Starting melody generation")

        try:
            # Load prompt template
            template = self._load_prompt_template("melody_prompt.txt")
            prompt = template.format(
                emotion=emotion,
                tempo=tempo,
                time_signature=time_signature,
                total_syllables=total_syllables,
                lyrics=lyrics
            )

            # Call LLM
            response_text = self._call_llm(prompt)

            if not response_text:
                logger.warning("[LLMClient] No response from LLM, using fallback")
                return self._fallback_melody_structure(
                    emotion, total_syllables
                )

            # Parse response
            structure = MelodyParser.parse(response_text)

            if not structure:
                logger.warning("[LLMClient] Failed to parse response, using fallback")
                return self._fallback_melody_structure(
                    emotion, total_syllables
                )

            # Success
            return MelodyStructureResponse(
                structure=structure,
                raw_response=response_text,
                success=True,
                fallback_used=False
            )

        except Exception as e:
            logger.error(f"[LLMClient] Error in melody generation: {e}")
            return self._fallback_melody_structure(emotion, total_syllables)

    def _fallback_emotion_analysis(self, lyrics: str) -> EmotionAnalysisResponse:
        """
        Create fallback emotion analysis when LLM fails.

        Args:
            lyrics: Input lyrics

        Returns:
            EmotionAnalysisResponse: Fallback response
        """
        from lyrics_to_melody.services.lyric_parser import LyricParser

        logger.warning("[LLMClient] Using fallback emotion analysis")

        parser = LyricParser()
        lines = parser.split_into_lines(lyrics)

        phrases = [
            {"line": line, "syllables": parser.estimate_syllables(line)}
            for line in lines
        ]

        analysis = EmotionAnalysis(
            emotion=config.DEFAULT_EMOTION,
            tempo=config.DEFAULT_TEMPO,
            time_signature=config.DEFAULT_TIME_SIGNATURE,
            phrases=phrases
        )

        return EmotionAnalysisResponse(
            analysis=analysis,
            raw_response=None,
            success=False,
            fallback_used=True
        )

    def _fallback_melody_structure(
        self,
        emotion: str,
        total_syllables: int
    ) -> MelodyStructureResponse:
        """
        Create fallback melody structure when LLM fails.

        Args:
            emotion: Detected emotion
            total_syllables: Number of syllables to generate notes for

        Returns:
            MelodyStructureResponse: Fallback response
        """
        from lyrics_to_melody.services.melody_generator import MelodyGenerator

        logger.warning("[LLMClient] Using fallback melody structure")

        generator = MelodyGenerator(self)
        structure = generator.generate_fallback_melody(emotion, total_syllables)

        return MelodyStructureResponse(
            structure=structure,
            raw_response=None,
            success=False,
            fallback_used=True
        )
