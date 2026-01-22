"""Content analysis service using Claude API."""

import json
import logging
from typing import Optional

import anthropic

from ..models.transcript import Transcript
from ..models.analysis import (
    ContentAnalysis,
    Chapter,
    TitleIdea,
    ThumbnailConcept,
)

logger = logging.getLogger(__name__)

CHAPTER_DETECTION_PROMPT = """You are analyzing a livestream transcript to identify chapters/topics for YouTube.

The streamer discusses market analysis, trading, and financial topics in Korean and English.

Given this transcript, identify distinct chapters where the topic changes. Each chapter should:
- Be at least {min_duration} seconds long
- Have a clear, engaging title (mix of Korean and English titles is fine)
- Include a brief summary

Transcript with timestamps (format: [MM:SS] text):
{transcript}

Total duration: {duration_formatted}

Respond with JSON in this exact format:
{{
  "chapters": [
    {{
      "title": "Chapter title",
      "start": 0.0,
      "end": 180.5,
      "summary": "Brief description of what's discussed",
      "keywords": ["keyword1", "keyword2"]
    }}
  ]
}}

Rules:
- Maximum {max_chapters} chapters
- First chapter should start at 0
- Chapters should be continuous (no gaps)
- Last chapter should end near the total duration
- Titles should be engaging and clickable"""

CONTENT_SUGGESTIONS_PROMPT = """You are a YouTube content strategist analyzing a livestream about market analysis and trading.

The streamer creates content in Korean and English about crypto, stocks, and financial markets.

Based on this stream summary and chapters, generate content suggestions.

Stream Summary:
{summary}

Chapters:
{chapters}

Language breakdown: {language_breakdown}

Generate suggestions in this JSON format:
{{
  "title_ideas": [
    {{"title": "Engaging title here", "language": "en", "reasoning": "Why this works"}},
    {{"title": "한국어 제목", "language": "ko", "reasoning": "Why this works"}}
  ],
  "thumbnail_concepts": [
    {{"description": "Visual description", "text_overlay": "Bold text", "mood": "excited"}}
  ],
  "tags": ["tag1", "tag2", "tag3"],
  "summary": "2-3 sentence summary of the stream",
  "description_template": "YouTube description with placeholders for chapters"
}}

Rules:
- 5 title ideas (mix of Korean and English)
- 3 thumbnail concepts
- 10-15 relevant tags
- Description should include emoji and chapter placeholder"""


class AnalysisService:
    """Service for content analysis using Claude API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """Initialize the analysis service.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def analyze(
        self,
        transcript: Transcript,
        min_chapter_duration: int = 60,
        max_chapters: int = 20,
    ) -> ContentAnalysis:
        """Analyze transcript and generate content suggestions.

        Args:
            transcript: Transcript to analyze
            min_chapter_duration: Minimum chapter length in seconds
            max_chapters: Maximum number of chapters

        Returns:
            ContentAnalysis with chapters and suggestions
        """
        # Step 1: Detect chapters
        logger.info("Detecting chapters...")
        chapters = self._detect_chapters(transcript, min_chapter_duration, max_chapters)

        # Step 2: Generate content suggestions
        logger.info("Generating content suggestions...")
        suggestions = self._generate_suggestions(transcript, chapters)

        return ContentAnalysis(
            chapters=chapters,
            title_ideas=suggestions.get("title_ideas", []),
            thumbnail_concepts=suggestions.get("thumbnail_concepts", []),
            tags=suggestions.get("tags", []),
            summary=suggestions.get("summary", ""),
            description_template=suggestions.get("description_template", ""),
        )

    def _detect_chapters(
        self,
        transcript: Transcript,
        min_duration: int,
        max_chapters: int,
    ) -> list[Chapter]:
        """Detect chapters in the transcript.

        Args:
            transcript: Transcript to analyze
            min_duration: Minimum chapter duration
            max_chapters: Maximum chapters

        Returns:
            List of Chapter objects
        """
        # Format transcript with timestamps
        formatted_transcript = self._format_transcript_with_timestamps(transcript)

        # Format duration
        hours = int(transcript.duration // 3600)
        minutes = int((transcript.duration % 3600) // 60)
        seconds = int(transcript.duration % 60)
        duration_formatted = f"{hours}:{minutes:02d}:{seconds:02d}"

        prompt = CHAPTER_DETECTION_PROMPT.format(
            transcript=formatted_transcript,
            duration_formatted=duration_formatted,
            min_duration=min_duration,
            max_chapters=max_chapters,
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        content = response.content[0].text
        data = self._parse_json_response(content)

        chapters = []
        for ch in data.get("chapters", []):
            chapters.append(
                Chapter(
                    title=ch["title"],
                    start=float(ch["start"]),
                    end=float(ch["end"]),
                    summary=ch.get("summary", ""),
                    keywords=ch.get("keywords", []),
                )
            )

        logger.info(f"Detected {len(chapters)} chapters")
        return chapters

    def _generate_suggestions(
        self,
        transcript: Transcript,
        chapters: list[Chapter],
    ) -> dict:
        """Generate content suggestions.

        Args:
            transcript: Transcript
            chapters: Detected chapters

        Returns:
            Dict with suggestions
        """
        # Create summary from chapters
        chapter_summary = "\n".join(
            f"- {ch.to_youtube_format()}: {ch.summary}" for ch in chapters
        )

        # Get a brief text excerpt for context
        full_text = transcript.get_full_text()
        summary_text = full_text[:2000] + "..." if len(full_text) > 2000 else full_text

        # Format language breakdown
        lang_str = ", ".join(
            f"{lang}: {pct}%" for lang, pct in transcript.language_breakdown.items()
        )

        prompt = CONTENT_SUGGESTIONS_PROMPT.format(
            summary=summary_text,
            chapters=chapter_summary,
            language_breakdown=lang_str or "Mixed Korean/English",
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text
        data = self._parse_json_response(content)

        # Parse into proper objects
        title_ideas = [
            TitleIdea(
                title=t["title"],
                language=t.get("language", "en"),
                reasoning=t.get("reasoning"),
            )
            for t in data.get("title_ideas", [])
        ]

        thumbnail_concepts = [
            ThumbnailConcept(
                description=t["description"],
                text_overlay=t.get("text_overlay"),
                mood=t.get("mood"),
            )
            for t in data.get("thumbnail_concepts", [])
        ]

        return {
            "title_ideas": title_ideas,
            "thumbnail_concepts": thumbnail_concepts,
            "tags": data.get("tags", []),
            "summary": data.get("summary", ""),
            "description_template": data.get("description_template", ""),
        }

    def _format_transcript_with_timestamps(self, transcript: Transcript) -> str:
        """Format transcript with timestamps for the prompt.

        Args:
            transcript: Transcript to format

        Returns:
            Formatted string with [MM:SS] timestamps
        """
        lines = []
        for segment in transcript.segments:
            minutes = int(segment.start // 60)
            seconds = int(segment.start % 60)
            lines.append(f"[{minutes:02d}:{seconds:02d}] {segment.text}")

        return "\n".join(lines)

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from Claude's response.

        Args:
            content: Response text that may contain JSON

        Returns:
            Parsed JSON dict
        """
        # Try to find JSON in the response
        content = content.strip()

        # If wrapped in code blocks, extract
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()

        # Find JSON object
        start_brace = content.find("{")
        end_brace = content.rfind("}") + 1

        if start_brace != -1 and end_brace > start_brace:
            json_str = content[start_brace:end_brace]
            return json.loads(json_str)

        logger.warning("Could not parse JSON from response, returning empty dict")
        return {}
