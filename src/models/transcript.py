"""Transcript data models."""

from pydantic import BaseModel


class Word(BaseModel):
    """A single word with timing information."""

    text: str
    start: float  # seconds
    end: float  # seconds
    confidence: float = 1.0
    language: str | None = None  # 'ko' or 'en'


class Segment(BaseModel):
    """A segment of speech (typically a sentence or phrase)."""

    text: str
    start: float  # seconds
    end: float  # seconds
    words: list[Word] = []
    language: str | None = None  # dominant language for segment
    speaker: str | None = None  # for future multi-speaker support


class Transcript(BaseModel):
    """Complete transcript of a video."""

    segments: list[Segment]
    duration: float  # total duration in seconds
    language_breakdown: dict[str, float] = {}  # language -> percentage

    @property
    def full_text(self) -> str:
        """Get the complete transcript as plain text."""
        return " ".join(seg.text for seg in self.segments)

    @property
    def word_count(self) -> int:
        """Get total word count."""
        return sum(len(seg.words) for seg in self.segments)

    def get_text_for_range(self, start: float, end: float) -> str:
        """Get transcript text for a specific time range."""
        texts = []
        for seg in self.segments:
            if seg.end < start:
                continue
            if seg.start > end:
                break
            # Segment overlaps with range
            if seg.words:
                # Use word-level precision
                words_in_range = [
                    w.text for w in seg.words if w.start >= start and w.end <= end
                ]
                if words_in_range:
                    texts.append(" ".join(words_in_range))
            else:
                texts.append(seg.text)
        return " ".join(texts)

    def to_srt(self, offset: float = 0.0) -> str:
        """Convert transcript to SRT format."""
        lines = []
        for i, seg in enumerate(self.segments, 1):
            start_time = self._format_srt_time(seg.start + offset)
            end_time = self._format_srt_time(seg.end + offset)
            lines.append(str(i))
            lines.append(f"{start_time} --> {end_time}")
            lines.append(seg.text)
            lines.append("")
        return "\n".join(lines)

    def to_vtt(self, offset: float = 0.0) -> str:
        """Convert transcript to WebVTT format."""
        lines = ["WEBVTT", ""]
        for i, seg in enumerate(self.segments, 1):
            start_time = self._format_vtt_time(seg.start + offset)
            end_time = self._format_vtt_time(seg.end + offset)
            lines.append(str(i))
            lines.append(f"{start_time} --> {end_time}")
            lines.append(seg.text)
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
        """Format seconds as WebVTT timestamp (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
