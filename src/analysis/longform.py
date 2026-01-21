"""Long-form content analysis for chapters and suggestions."""

from src.models.analysis import Chapter, ContentSuggestions, LongformAnalysis
from src.models.config import Settings
from src.models.transcript import Transcript

from .claude_client import ClaudeAnalyzer

LONGFORM_SYSTEM_PROMPT = """You are an expert content analyst specializing in financial and market analysis livestreams. Your job is to analyze transcripts and identify:

1. Topic chapters/segments for YouTube chapter markers
2. Key themes and topics discussed
3. Title ideas optimized for YouTube search and clicks
4. Thumbnail concepts that would attract viewers

The content is from a Korean/English bilingual creator who discusses cryptocurrency, stocks, and market analysis. The audience is interested in trading insights, market predictions, and financial education.

Always respond with valid JSON only, no additional text."""

LONGFORM_USER_PROMPT = """Analyze this livestream transcript and provide:

1. **Chapters**: Identify major topic changes for YouTube chapter markers. Each chapter should be at least {min_duration} seconds long. Include:
   - title: Concise chapter title (in the dominant language of that section, or English if mixed)
   - start: Start time in seconds
   - end: End time in seconds
   - summary: Brief 1-2 sentence summary
   - keywords: 3-5 relevant keywords

2. **Suggestions**: Provide content optimization suggestions:
   - title_ideas: 5 YouTube title ideas (attention-grabbing, SEO-optimized)
   - thumbnail_concepts: 3 thumbnail visual concepts
   - tags: 10-15 relevant YouTube tags
   - description_template: A template for the video description

3. **Summary**: A 2-3 sentence overview of the entire stream content.

4. **Key Topics**: List of 5-10 main topics discussed.

Respond with this exact JSON structure:
```json
{{
  "chapters": [
    {{
      "title": "string",
      "start": number,
      "end": number,
      "summary": "string",
      "keywords": ["string"]
    }}
  ],
  "suggestions": {{
    "title_ideas": ["string"],
    "thumbnail_concepts": ["string"],
    "tags": ["string"],
    "description_template": "string"
  }},
  "summary": "string",
  "key_topics": ["string"]
}}
```"""


def analyze_longform(
    transcript: Transcript,
    settings: Settings,
    progress_callback: callable | None = None,
) -> LongformAnalysis:
    """Analyze transcript for long-form content optimization.

    Args:
        transcript: Full transcript of the livestream.
        settings: Application settings.
        progress_callback: Optional callback for progress updates.

    Returns:
        LongformAnalysis with chapters and suggestions.
    """
    if progress_callback:
        progress_callback("Analyzing long-form content structure...")

    analyzer = ClaudeAnalyzer(
        api_key=settings.anthropic_api_key,
        model=settings.analysis.model,
    )

    min_duration = settings.analysis.longform.min_chapter_duration
    user_prompt = LONGFORM_USER_PROMPT.format(min_duration=min_duration)

    result = analyzer.analyze(
        transcript=transcript,
        system_prompt=LONGFORM_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    # Parse chapters
    chapters = []
    for ch_data in result.get("chapters", []):
        chapters.append(
            Chapter(
                title=ch_data.get("title", "Untitled"),
                start=float(ch_data.get("start", 0)),
                end=float(ch_data.get("end", 0)),
                summary=ch_data.get("summary", ""),
                keywords=ch_data.get("keywords", []),
            )
        )

    # Limit chapters
    max_chapters = settings.analysis.longform.max_chapters
    if len(chapters) > max_chapters:
        chapters = chapters[:max_chapters]

    # Parse suggestions
    sugg_data = result.get("suggestions", {})
    suggestions = ContentSuggestions(
        title_ideas=sugg_data.get("title_ideas", []),
        thumbnail_concepts=sugg_data.get("thumbnail_concepts", []),
        tags=sugg_data.get("tags", []),
        description_template=sugg_data.get("description_template", ""),
    )

    if progress_callback:
        progress_callback(f"Found {len(chapters)} chapters")

    return LongformAnalysis(
        chapters=chapters,
        suggestions=suggestions,
        summary=result.get("summary", ""),
        key_topics=result.get("key_topics", []),
    )
