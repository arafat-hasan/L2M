"""
OpenAI API client wrapper for the Lyrics-to-Melody system.

Provides high-level interface for emotion analysis and melody generation
using LLM (Language Model) capabilities.
"""

import time
from functools import wraps
from pathlib import Path
from typing import Optional, TypeVar, Callable

from openai import (
    OpenAI,
    OpenAIError,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
)

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

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (RateLimitError, APITimeoutError, APIConnectionError)
):
    """
    Retry decorator with exponential backoff for API calls.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay between retries
        retryable_exceptions: Tuple of exceptions that should trigger retry

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"[Retry] Max retries ({max_retries}) exceeded for {func.__name__}"
                        )
                        raise

                    # Special handling for rate limits
                    if isinstance(e, RateLimitError):
                        # Try to get retry-after from headers if available
                        retry_after = delay
                        if hasattr(e, 'response') and e.response is not None:
                            headers = getattr(e.response, 'headers', {})
                            if 'retry-after' in headers:
                                try:
                                    retry_after = float(headers['retry-after'])
                                except (ValueError, TypeError):
                                    pass

                        logger.warning(
                            f"[Retry] Rate limited (attempt {attempt + 1}/{max_retries}). "
                            f"Waiting {retry_after:.1f}s before retry..."
                        )
                        time.sleep(retry_after)
                    else:
                        logger.warning(
                            f"[Retry] Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)

                    delay *= backoff_factor

                except Exception as e:
                    # Non-retryable exception
                    logger.error(f"[Retry] Non-retryable error in {func.__name__}: {type(e).__name__}: {e}")
                    raise

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


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

    @retry_with_backoff(max_retries=3, initial_delay=2.0, backoff_factor=2.0)
    def _call_llm(self, prompt: str) -> str:
        """
        Make an API call to the LLM with retry logic and validation.

        Args:
            prompt: The prompt to send

        Returns:
            str: LLM response text

        Raises:
            ValueError: If response is invalid or empty
            OpenAIError: If API call fails after retries
        """
        logger.debug(f"[LLMClient] Calling API with model: {self.model}")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert music composer and analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=config.API_TIMEOUT,  # Add timeout to prevent hanging
        )

        # Validate response structure
        if not response.choices:
            raise ValueError(
                "API returned empty choices array. This may indicate a service issue."
            )

        if len(response.choices) == 0:
            raise ValueError(
                "API returned zero choices. Expected at least one completion."
            )

        # Get the content
        message = response.choices[0].message
        if not message:
            raise ValueError(
                "API response choice has no message. Response may be malformed."
            )

        content = message.content
        if content is None:
            raise ValueError(
                "API returned None content. This may indicate content filtering "
                "or an incomplete response."
            )

        if not content.strip():
            raise ValueError(
                "API returned empty content. The model may not have generated a response."
            )

        logger.debug(f"[LLMClient] Received valid response ({len(content)} chars)")

        return content

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

            # Call LLM (will raise exception if fails)
            response_text = self._call_llm(prompt)

            # Parse response
            analysis = EmotionParser.parse(response_text)

            if not analysis:
                logger.warning("[LLMClient] Failed to parse LLM response, using fallback")
                return self._fallback_emotion_analysis(lyrics)

            # Success
            logger.info(f"[LLMClient] Emotion analysis successful: {analysis.emotion}")
            return EmotionAnalysisResponse(
                analysis=analysis,
                raw_response=response_text,
                success=True,
                fallback_used=False
            )

        except (OpenAIError, ValueError) as e:
            logger.warning(f"[LLMClient] API error in emotion analysis: {type(e).__name__}: {e}")
            logger.info("[LLMClient] Using fallback emotion analysis")
            return self._fallback_emotion_analysis(lyrics)

        except Exception as e:
            logger.error(f"[LLMClient] Unexpected error in emotion analysis: {type(e).__name__}: {e}", exc_info=True)
            logger.info("[LLMClient] Using fallback emotion analysis")
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

            # Call LLM (will raise exception if fails)
            response_text = self._call_llm(prompt)

            # Parse response
            structure = MelodyParser.parse(response_text)

            if not structure:
                logger.warning("[LLMClient] Failed to parse LLM response, using fallback")
                return self._fallback_melody_structure(emotion, total_syllables)

            # Success
            logger.info(f"[LLMClient] Melody generation successful: {structure.key}, {len(structure.melody)} notes")
            return MelodyStructureResponse(
                structure=structure,
                raw_response=response_text,
                success=True,
                fallback_used=False
            )

        except (OpenAIError, ValueError) as e:
            logger.warning(f"[LLMClient] API error in melody generation: {type(e).__name__}: {e}")
            logger.info("[LLMClient] Using fallback melody generation")
            return self._fallback_melody_structure(emotion, total_syllables)

        except Exception as e:
            logger.error(f"[LLMClient] Unexpected error in melody generation: {type(e).__name__}: {e}", exc_info=True)
            logger.info("[LLMClient] Using fallback melody generation")
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
