"""Silence detection using FFmpeg."""

import re
import subprocess
from pathlib import Path

from src.models.timeline import EditRegion, SilenceRegion


def detect_silences(
    audio_path: Path,
    threshold_db: float = -40.0,
    min_duration: float = 0.5,
) -> list[SilenceRegion]:
    """Detect silence regions in audio file.

    Args:
        audio_path: Path to the audio file.
        threshold_db: Silence threshold in dB (default -40dB).
        min_duration: Minimum silence duration in seconds (default 0.5s).

    Returns:
        List of SilenceRegion objects.

    Raises:
        RuntimeError: If FFmpeg fails.
    """
    cmd = [
        "ffmpeg",
        "-i",
        str(audio_path),
        "-af",
        f"silencedetect=noise={threshold_db}dB:d={min_duration}",
        "-f",
        "null",
        "-",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    # FFmpeg outputs to stderr even on success
    output = result.stderr

    # Parse silence detection output
    # Format: [silencedetect @ 0x...] silence_start: 1.234
    #         [silencedetect @ 0x...] silence_end: 5.678 | silence_duration: 4.444
    silence_regions = []

    start_pattern = r"silence_start:\s*([\d.]+)"
    end_pattern = r"silence_end:\s*([\d.]+)"

    starts = re.findall(start_pattern, output)
    ends = re.findall(end_pattern, output)

    for start, end in zip(starts, ends):
        silence_regions.append(
            SilenceRegion(start=float(start), end=float(end))
        )

    return silence_regions


def generate_edit_regions(
    silences: list[SilenceRegion],
    total_duration: float,
    padding: float = 0.1,
) -> list[EditRegion]:
    """Generate edit regions (content to keep) from silence regions.

    Args:
        silences: List of silence regions to cut.
        total_duration: Total duration of the source media.
        padding: Seconds of padding to keep around speech.

    Returns:
        List of EditRegion objects representing content to keep.
    """
    if not silences:
        # No silences, keep everything
        return [
            EditRegion(
                source_start=0.0,
                source_end=total_duration,
                timeline_start=0.0,
            )
        ]

    # Sort silences by start time
    silences = sorted(silences, key=lambda s: s.start)

    edit_regions = []
    timeline_position = 0.0
    current_position = 0.0

    for silence in silences:
        # Adjust silence boundaries with padding
        silence_start = max(0, silence.start + padding)
        silence_end = min(total_duration, silence.end - padding)

        # Skip if padding eliminated the silence
        if silence_end <= silence_start:
            continue

        # Content before this silence
        if current_position < silence_start:
            region = EditRegion(
                source_start=current_position,
                source_end=silence_start,
                timeline_start=timeline_position,
            )
            edit_regions.append(region)
            timeline_position += region.duration

        current_position = silence_end

    # Content after last silence
    if current_position < total_duration:
        edit_regions.append(
            EditRegion(
                source_start=current_position,
                source_end=total_duration,
                timeline_start=timeline_position,
            )
        )

    return edit_regions


def get_total_silence_duration(silences: list[SilenceRegion]) -> float:
    """Calculate total silence duration.

    Args:
        silences: List of silence regions.

    Returns:
        Total duration of all silences in seconds.
    """
    return sum(s.duration for s in silences)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string like "1:23:45" or "12:34".
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
