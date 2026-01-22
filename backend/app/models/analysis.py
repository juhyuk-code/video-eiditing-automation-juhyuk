"""Analysis models for Claude API results."""

from typing import Optional
from pydantic import BaseModel, Field


class Chapter(BaseModel):
    """A chapter/topic segment in the stream."""

    title: str = Field(..., description="Chapter title for YouTube")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    summary: str = Field(default="", description="Brief summary of the chapter")
    keywords: list[str] = Field(default_factory=list)

    def to_youtube_format(self) -> str:
        """Format chapter for YouTube description."""
        hours = int(self.start // 3600)
        minutes = int((self.start % 3600) // 60)
        seconds = int(self.start % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d} {self.title}"
        return f"{minutes}:{seconds:02d} {self.title}"


class TitleIdea(BaseModel):
    """A suggested title for the video."""

    title: str
    language: str = Field(default="en", description="Language code (en, ko)")
    reasoning: Optional[str] = Field(None, description="Why this title works")


class ThumbnailConcept(BaseModel):
    """A suggested thumbnail concept."""

    description: str = Field(..., description="Visual description of the thumbnail")
    text_overlay: Optional[str] = Field(None, description="Suggested text to overlay")
    mood: Optional[str] = Field(None, description="Emotional tone (excited, serious, etc.)")


class ContentAnalysis(BaseModel):
    """Full content analysis results."""

    # Chapters
    chapters: list[Chapter] = Field(default_factory=list)

    # Suggestions
    title_ideas: list[TitleIdea] = Field(default_factory=list)
    thumbnail_concepts: list[ThumbnailConcept] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    # Description
    summary: str = Field(default="", description="2-3 sentence stream summary")
    description_template: str = Field(default="", description="YouTube description template")

    def get_chapters_text(self) -> str:
        """Get chapters formatted for YouTube."""
        return "\n".join(ch.to_youtube_format() for ch in self.chapters)

    def to_suggestions_md(self) -> str:
        """Generate suggestions.md content."""
        lines = ["# Stream Content Suggestions", ""]

        # Title Ideas
        lines.append("## Title Ideas")
        for i, idea in enumerate(self.title_ideas, 1):
            lines.append(f'{i}. "{idea.title}"')
        lines.append("")

        # Thumbnail Concepts
        lines.append("## Thumbnail Concepts")
        for i, concept in enumerate(self.thumbnail_concepts, 1):
            lines.append(f"{i}. {concept.description}")
            if concept.text_overlay:
                lines.append(f"   - Text: \"{concept.text_overlay}\"")
        lines.append("")

        # YouTube Chapters
        lines.append("## YouTube Chapters")
        lines.append(self.get_chapters_text())
        lines.append("")

        # Tags
        lines.append("## Tags")
        lines.append(", ".join(self.tags))
        lines.append("")

        # Description Template
        lines.append("## Description Template")
        lines.append(self.description_template)
        lines.append("")

        # Summary
        lines.append("## Stream Summary")
        lines.append(self.summary)

        return "\n".join(lines)
