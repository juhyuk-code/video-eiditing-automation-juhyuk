"""Transcript formatting utilities."""

from pathlib import Path

from src.models.transcript import Transcript


def format_transcript_to_srt(
    transcript: Transcript,
    output_path: Path,
    offset: float = 0.0,
) -> Path:
    """Write transcript to SRT file.

    Args:
        transcript: Transcript to format.
        output_path: Path for the output SRT file.
        offset: Time offset in seconds (for clips).

    Returns:
        Path to the written file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = transcript.to_srt(offset=offset)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def format_transcript_to_vtt(
    transcript: Transcript,
    output_path: Path,
    offset: float = 0.0,
) -> Path:
    """Write transcript to WebVTT file.

    Args:
        transcript: Transcript to format.
        output_path: Path for the output VTT file.
        offset: Time offset in seconds (for clips).

    Returns:
        Path to the written file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = transcript.to_vtt(offset=offset)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def extract_transcript_for_clip(
    transcript: Transcript,
    start: float,
    end: float,
) -> Transcript:
    """Extract a portion of transcript for a clip.

    Args:
        transcript: Full transcript.
        start: Clip start time in seconds.
        end: Clip end time in seconds.

    Returns:
        New Transcript object for the clip.
    """
    from src.models.transcript import Segment, Word

    clip_segments = []

    for seg in transcript.segments:
        # Skip segments outside the clip range
        if seg.end < start or seg.start > end:
            continue

        # Adjust segment times relative to clip start
        new_start = max(0, seg.start - start)
        new_end = min(end - start, seg.end - start)

        # Filter words to clip range and adjust times
        new_words = []
        for word in seg.words:
            if word.start >= start and word.end <= end:
                new_words.append(
                    Word(
                        text=word.text,
                        start=word.start - start,
                        end=word.end - start,
                        confidence=word.confidence,
                        language=word.language,
                    )
                )

        # Get text for this segment within the clip
        if new_words:
            text = " ".join(w.text for w in new_words)
        else:
            text = seg.text

        clip_segments.append(
            Segment(
                text=text,
                start=new_start,
                end=new_end,
                words=new_words,
                language=seg.language,
            )
        )

    return Transcript(
        segments=clip_segments,
        duration=end - start,
        language_breakdown=transcript.language_breakdown,
    )
