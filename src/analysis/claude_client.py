"""Claude API client for content analysis."""

import json
import os

from anthropic import Anthropic

from src.models.transcript import Transcript


class ClaudeAnalyzer:
    """Claude API client for analyzing livestream content."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        """Initialize the Claude analyzer.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var).
            model: Claude model to use.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment "
                "variable or pass it to the constructor."
            )

        self.model = model
        self.client = Anthropic(api_key=self.api_key)

    def analyze(
        self,
        transcript: Transcript,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> dict:
        """Send analysis request to Claude.

        Args:
            transcript: Transcript to analyze.
            system_prompt: System prompt for Claude.
            user_prompt: User prompt with specific instructions.
            max_tokens: Maximum response tokens.

        Returns:
            Parsed JSON response from Claude.
        """
        # Prepare transcript text with timestamps
        transcript_text = self._format_transcript_for_analysis(transcript)

        full_user_prompt = f"{user_prompt}\n\n## TRANSCRIPT\n\n{transcript_text}"

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": full_user_prompt},
            ],
        )

        # Extract text content
        content = response.content[0].text

        # Parse JSON from response
        return self._extract_json(content)

    def _format_transcript_for_analysis(self, transcript: Transcript) -> str:
        """Format transcript with timestamps for Claude analysis.

        Args:
            transcript: Transcript to format.

        Returns:
            Formatted transcript string.
        """
        lines = []
        for seg in transcript.segments:
            timestamp = self._format_timestamp(seg.start)
            lang_tag = f"[{seg.language}]" if seg.language else ""
            lines.append(f"[{timestamp}] {lang_tag} {seg.text}")
        return "\n".join(lines)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds as MM:SS or HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from Claude's response.

        Args:
            text: Response text that may contain JSON.

        Returns:
            Parsed JSON dict.

        Raises:
            ValueError: If no valid JSON found.
        """
        # Try to find JSON in code blocks
        import re

        # Look for ```json ... ``` blocks
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Look for ``` ... ``` blocks
        code_match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try parsing the entire text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Look for { ... } pattern
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract JSON from response: {text[:500]}...")
