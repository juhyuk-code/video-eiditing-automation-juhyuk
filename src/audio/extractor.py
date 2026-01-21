"""Audio extraction from video files using FFmpeg."""

import json
import subprocess
from pathlib import Path

from src.models.timeline import MediaFile


def get_video_info(video_path: Path) -> MediaFile:
    """Get video file information using ffprobe.

    Args:
        video_path: Path to the video file.

    Returns:
        MediaFile with video metadata.

    Raises:
        RuntimeError: If ffprobe fails.
    """
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    data = json.loads(result.stdout)

    # Extract video stream info
    video_stream = None
    has_audio = False
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        if stream.get("codec_type") == "audio":
            has_audio = True

    if video_stream is None:
        raise RuntimeError(f"No video stream found in {video_path}")

    # Get duration from format or stream
    duration = float(data.get("format", {}).get("duration", 0))
    if duration == 0 and video_stream.get("duration"):
        duration = float(video_stream["duration"])

    # Get framerate
    fps = 30.0
    if video_stream.get("r_frame_rate"):
        try:
            num, den = video_stream["r_frame_rate"].split("/")
            fps = float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            pass

    return MediaFile(
        path=video_path,
        duration=duration,
        width=video_stream.get("width", 1920),
        height=video_stream.get("height", 1080),
        fps=fps,
        has_audio=has_audio,
    )


def extract_audio(
    video_path: Path,
    output_path: Path,
    sample_rate: int = 16000,
    mono: bool = True,
) -> Path:
    """Extract audio from video file.

    Args:
        video_path: Path to the video file.
        output_path: Path for the output audio file.
        sample_rate: Audio sample rate (default 16kHz for transcription).
        mono: Convert to mono (default True for transcription).

    Returns:
        Path to the extracted audio file.

    Raises:
        RuntimeError: If FFmpeg fails.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vn",  # No video
        "-acodec",
        "pcm_s16le",  # PCM 16-bit little-endian
        "-ar",
        str(sample_rate),
    ]

    if mono:
        cmd.extend(["-ac", "1"])

    cmd.extend([
        "-y",  # Overwrite output
        str(output_path),
    ])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")

    return output_path
