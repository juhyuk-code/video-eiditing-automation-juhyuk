"""Transcript models for speech-to-text results."""

from typing import Optional
from pydantic import BaseModel, Field


class Word(BaseModel):
    """A single word with timing information."""

    text: str
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Segment(BaseModel):
    """A segment of transcribed speech."""

    text: str
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    words: list[Word] = Field(default_factory=list)
    language: Optional[str] = Field(None, description="Detected language code (ko, en)")
    speaker: Optional[str] = None


class Transcript(BaseModel):
    """Full transcript with segments and metadata."""

    segments: list[Segment] = Field(default_factory=list)
    duration: float = Field(..., description="Total duration in seconds")
    language_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Percentage of each language (e.g., {'ko': 72.5, 'en': 27.5})",
    )
    word_count: int = 0

    def get_full_text(self) -> str:
        """Get the full transcript as plain text."""
        return " ".join(seg.text for seg in self.segments)

    def to_srt(self, offset: float = 0.0) -> str:
        """Convert transcript to SRT format."""
        lines = []
        for i, segment in enumerate(self.segments, 1):
            start = self._format_srt_time(segment.start + offset)
            end = self._format_srt_time(segment.end + offset)
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(segment.text)
            lines.append("")
        return "\n".join(lines)

    def to_vtt(self, offset: float = 0.0) -> str:
        """Convert transcript to WebVTT format."""
        lines = ["WEBVTT", ""]
        for i, segment in enumerate(self.segments, 1):
            start = self._format_vtt_time(segment.start + offset)
            end = self._format_vtt_time(segment.end + offset)
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(segment.text)
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format seconds as SRT timestamp (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_vtt_time(seconds: float) -> str:
        """Format seconds as VTT timestamp (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
