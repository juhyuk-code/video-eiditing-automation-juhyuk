"""Analysis result data models."""

from pydantic import BaseModel


class Chapter(BaseModel):
    """A chapter/topic segment for long-form content."""

    title: str
    start: float  # seconds
    end: float  # seconds
    summary: str = ""
    keywords: list[str] = []

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_youtube_format(self) -> str:
        """Format as YouTube chapter timestamp."""
        hours = int(self.start // 3600)
        minutes = int((self.start % 3600) // 60)
        seconds = int(self.start % 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d} {self.title}"
        return f"{minutes}:{seconds:02d} {self.title}"


class ViralClip(BaseModel):
    """A viral-worthy clip for short-form content."""

    id: str  # e.g., "clip_001"
    start: float  # seconds
    end: float  # seconds
    transcript: str
    category: str  # bold_prediction, insight, reaction, explanation, callout
    viral_score: float  # 0.0 to 1.0
    title_suggestions: list[str] = []
    hook: str = ""  # opening hook/quote
    context: str = ""  # why this moment is clip-worthy

    @property
    def duration(self) -> float:
        return self.end - self.start


class ContentSuggestions(BaseModel):
    """Title, thumbnail, and tag suggestions."""

    title_ideas: list[str] = []
    thumbnail_concepts: list[str] = []
    tags: list[str] = []
    description_template: str = ""


class LongformAnalysis(BaseModel):
    """Complete analysis for long-form content."""

    chapters: list[Chapter]
    suggestions: ContentSuggestions
    summary: str = ""
    key_topics: list[str] = []

    def to_chapters_txt(self) -> str:
        """Generate YouTube chapters format."""
        return "\n".join(ch.to_youtube_format() for ch in self.chapters)


class ShortformAnalysis(BaseModel):
    """Complete analysis for short-form content."""

    clips: list[ViralClip]
    suggestions: ContentSuggestions

    @property
    def total_clips(self) -> int:
        return len(self.clips)

    @property
    def total_duration(self) -> float:
        return sum(clip.duration for clip in self.clips)
