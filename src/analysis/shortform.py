"""Short-form content analysis for viral clip detection."""

from src.models.analysis import ContentSuggestions, ShortformAnalysis, ViralClip
from src.models.config import Settings
from src.models.transcript import Transcript

from .claude_client import ClaudeAnalyzer

SHORTFORM_SYSTEM_PROMPT = """You are an expert at identifying viral-worthy moments in financial/market analysis livestreams for short-form content (YouTube Shorts, TikTok, Instagram Reels).

You understand what makes content go viral:
- Strong hooks that grab attention in the first 2 seconds
- Bold predictions or contrarian takes
- Emotional reactions or surprising revelations
- Quotable one-liners or memorable statements
- Clear explanations of complex topics
- "I told you so" moments or validation of past predictions

The creator is a Korean/English bilingual who discusses cryptocurrency, stocks, and market analysis. Their audience wants actionable insights, bold takes, and entertaining market commentary.

Each clip should:
- Be self-contained with enough context for viewers to understand
- Have a clear hook at the beginning
- Maximum {max_duration} seconds (YouTube Shorts limit is 3 minutes)
- Not overlap with other clips

Always respond with valid JSON only, no additional text."""

SHORTFORM_USER_PROMPT = """Analyze this livestream transcript and identify at least {min_clips} viral-worthy moments for short-form content.

Look for these viral signals:
{viral_signals}

For each clip, provide:
- id: Clip identifier (clip_001, clip_002, etc.)
- start: Start time in seconds
- end: End time in seconds
- transcript: The exact transcript text for this clip
- category: One of [bold_prediction, insight, reaction, explanation, callout]
- viral_score: 0.0 to 1.0 rating of viral potential
- title_suggestions: 2-3 short-form title ideas (attention-grabbing, under 100 chars)
- hook: The opening line/hook that grabs attention
- context: Why this moment is clip-worthy (1 sentence)

Important:
- Clips must NOT overlap
- Each clip should have enough context to stand alone
- Prioritize moments with high energy, strong opinions, or surprising information
- Aim for clips between 30 seconds and {max_duration} seconds

Respond with this exact JSON structure:
```json
{{
  "clips": [
    {{
      "id": "clip_001",
      "start": number,
      "end": number,
      "transcript": "string",
      "category": "string",
      "viral_score": number,
      "title_suggestions": ["string"],
      "hook": "string",
      "context": "string"
    }}
  ],
  "suggestions": {{
    "title_ideas": ["string"],
    "tags": ["string"]
  }}
}}
```"""


def analyze_shortform(
    transcript: Transcript,
    settings: Settings,
    progress_callback: callable | None = None,
) -> ShortformAnalysis:
    """Analyze transcript for short-form viral content.

    Args:
        transcript: Full transcript of the livestream.
        settings: Application settings.
        progress_callback: Optional callback for progress updates.

    Returns:
        ShortformAnalysis with viral clips and suggestions.
    """
    if progress_callback:
        progress_callback("Identifying viral moments...")

    analyzer = ClaudeAnalyzer(
        api_key=settings.anthropic_api_key,
        model=settings.analysis.model,
    )

    shortform_settings = settings.analysis.shortform
    viral_signals = "\n".join(f"- {s}" for s in shortform_settings.viral_signals)

    user_prompt = SHORTFORM_USER_PROMPT.format(
        min_clips=shortform_settings.min_clips,
        max_duration=shortform_settings.max_clip_duration,
        viral_signals=viral_signals,
    )

    result = analyzer.analyze(
        transcript=transcript,
        system_prompt=SHORTFORM_SYSTEM_PROMPT.format(
            max_duration=shortform_settings.max_clip_duration
        ),
        user_prompt=user_prompt,
    )

    # Parse clips
    clips = []
    for clip_data in result.get("clips", []):
        clips.append(
            ViralClip(
                id=clip_data.get("id", f"clip_{len(clips)+1:03d}"),
                start=float(clip_data.get("start", 0)),
                end=float(clip_data.get("end", 0)),
                transcript=clip_data.get("transcript", ""),
                category=clip_data.get("category", "insight"),
                viral_score=float(clip_data.get("viral_score", 0.5)),
                title_suggestions=clip_data.get("title_suggestions", []),
                hook=clip_data.get("hook", ""),
                context=clip_data.get("context", ""),
            )
        )

    # Sort by viral score and limit
    clips.sort(key=lambda c: c.viral_score, reverse=True)
    max_clips = shortform_settings.max_clips
    if len(clips) > max_clips:
        clips = clips[:max_clips]

    # Re-sort by start time for timeline ordering
    clips.sort(key=lambda c: c.start)

    # Renumber clips
    for i, clip in enumerate(clips):
        clip.id = f"clip_{i+1:03d}"

    # Parse suggestions
    sugg_data = result.get("suggestions", {})
    suggestions = ContentSuggestions(
        title_ideas=sugg_data.get("title_ideas", []),
        tags=sugg_data.get("tags", []),
    )

    if progress_callback:
        total_duration = sum(c.duration for c in clips)
        progress_callback(
            f"Found {len(clips)} viral clips ({_format_duration(total_duration)} total)"
        )

    return ShortformAnalysis(
        clips=clips,
        suggestions=suggestions,
    )


def _format_duration(seconds: float) -> str:
    """Format duration in seconds to MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"
