"""
JSON parsers for LLM responses.

Handles extraction and validation of JSON from LLM outputs,
including extraction from markdown code fences.
"""

import json
import re
from typing import Optional, Any, Dict

from pydantic import ValidationError

from lyrics_to_melody.models.emotion_analysis import EmotionAnalysis
from lyrics_to_melody.models.melody_structure import MelodyStructure
from lyrics_to_melody.utils.logger import get_logger

logger = get_logger(__name__)


class JSONParser:
    """
    Parser for extracting and validating JSON from LLM responses.

    Handles various formats including markdown code fences and raw JSON.
    """

    @staticmethod
    def extract_json_from_markdown(text: str) -> Optional[str]:
        """
        Extract JSON content from markdown code fences.

        Args:
            text: Text potentially containing ```json ... ``` fences

        Returns:
            Optional[str]: Extracted JSON string, or None if not found
        """
        # Try to find JSON within ```json ``` code fences
        pattern = r'```json\s*\n(.*?)\n\s*```'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # Try generic code fence
        pattern = r'```\s*\n(.*?)\n\s*```'
        match = re.search(pattern, text, re.DOTALL)

        if match:
            content = match.group(1).strip()
            # Verify it looks like JSON
            if content.startswith('{') and content.endswith('}'):
                return content

        return None

    @staticmethod
    def extract_json_from_text(text: str) -> Optional[str]:
        """
        Extract JSON object from text (with or without markdown).

        Args:
            text: Text containing JSON

        Returns:
            Optional[str]: Extracted JSON string, or None if not found
        """
        # First try markdown extraction
        json_str = JSONParser.extract_json_from_markdown(text)
        if json_str:
            return json_str

        # Try to find a JSON object directly in the text
        # Look for balanced braces
        brace_count = 0
        start_idx = -1

        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    # Found complete JSON object
                    json_str = text[start_idx:i + 1]
                    return json_str

        return None

    @staticmethod
    def parse_json(text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from text.

        Args:
            text: Text containing JSON

        Returns:
            Optional[Dict[str, Any]]: Parsed JSON object, or None if parsing fails
        """
        json_str = JSONParser.extract_json_from_text(text)

        if not json_str:
            logger.error("Could not extract JSON from LLM response")
            return None

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.debug(f"Attempted to parse: {json_str[:200]}")
            return None


class EmotionParser:
    """
    Parser for emotion analysis responses from LLM.
    """

    @staticmethod
    def parse(response_text: str) -> Optional[EmotionAnalysis]:
        """
        Parse emotion analysis from LLM response.

        Args:
            response_text: Raw LLM response text

        Returns:
            Optional[EmotionAnalysis]: Validated emotion analysis, or None if parsing fails
        """
        logger.info("[EmotionAnalysis] Parsing LLM response")

        # Extract JSON
        json_data = JSONParser.parse_json(response_text)

        if not json_data:
            logger.error("[EmotionAnalysis] Failed to extract JSON from response")
            return None

        # Validate with Pydantic
        try:
            analysis = EmotionAnalysis(**json_data)
            logger.info(f"[EmotionAnalysis] Successfully parsed: emotion={analysis.emotion}, "
                       f"tempo={analysis.tempo}, phrases={len(analysis.phrases)}")
            return analysis
        except ValidationError as e:
            logger.error(f"[EmotionAnalysis] Validation error: {e}")
            logger.debug(f"JSON data: {json_data}")
            return None


class MelodyParser:
    """
    Parser for melody structure responses from LLM.
    """

    @staticmethod
    def parse(response_text: str) -> Optional[MelodyStructure]:
        """
        Parse melody structure from LLM response.

        Args:
            response_text: Raw LLM response text

        Returns:
            Optional[MelodyStructure]: Validated melody structure, or None if parsing fails
        """
        logger.info("[MelodyGeneration] Parsing LLM response")

        # Extract JSON
        json_data = JSONParser.parse_json(response_text)

        if not json_data:
            logger.error("[MelodyGeneration] Failed to extract JSON from response")
            return None

        # Validate with Pydantic
        try:
            structure = MelodyStructure(**json_data)
            logger.info(f"[MelodyGeneration] Successfully parsed: key={structure.key}, "
                       f"notes={len(structure.melody)}")
            return structure
        except ValidationError as e:
            logger.error(f"[MelodyGeneration] Validation error: {e}")
            logger.debug(f"JSON data: {json_data}")
            return None
