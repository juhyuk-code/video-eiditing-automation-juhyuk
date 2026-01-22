"""Audio processing service using FFmpeg."""

import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SilenceRegion:
    """A detected silence region."""

    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class EditRegion:
    """A region of content to keep (non-silence)."""

    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


class AudioProcessor:
    """Service for audio extraction and silence detection."""

    def __init__(
        self,
        threshold_db: float = -40.0,
        min_silence_duration: float = 0.5,
        padding: float = 0.1,
    ):
        """Initialize the audio processor.

        Args:
            threshold_db: Volume threshold for silence detection (default -40 dB)
            min_silence_duration: Minimum silence duration to detect (default 0.5s)
            padding: Padding to keep around speech (default 0.1s)
        """
        self.threshold_db = threshold_db
        self.min_silence_duration = min_silence_duration
        self.padding = padding

    def extract_audio(self, video_path: Path, output_path: Path) -> Path:
        """Extract audio from video file.

        Args:
            video_path: Path to the video file
            output_path: Path for the output audio file

        Returns:
            Path to the extracted audio file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Extract audio as 16kHz mono WAV (optimal for speech recognition)
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # PCM 16-bit
            "-ar", "16000",  # 16kHz sample rate
            "-ac", "1",  # Mono
            "-y",  # Overwrite output
            str(output_path),
        ]

        logger.info(f"Extracting audio from {video_path}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {result.stderr}")

        logger.info(f"Audio extracted to {output_path}")
        return output_path

    def get_duration(self, file_path: Path) -> float:
        """Get the duration of a media file in seconds.

        Args:
            file_path: Path to the media file

        Returns:
            Duration in seconds
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(file_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFprobe error: {result.stderr}")

        data = json.loads(result.stdout)
        return float(data["format"]["duration"])

    def detect_silences(self, audio_path: Path) -> list[SilenceRegion]:
        """Detect silence regions in an audio file.

        Args:
            audio_path: Path to the audio file

        Returns:
            List of SilenceRegion objects
        """
        cmd = [
            "ffmpeg",
            "-i", str(audio_path),
            "-af", f"silencedetect=noise={self.threshold_db}dB:d={self.min_silence_duration}",
            "-f", "null",
            "-",
        ]

        logger.info(f"Detecting silences in {audio_path}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse silence detection output from stderr
        silences = []
        silence_start = None

        for line in result.stderr.split("\n"):
            # Match silence_start
            start_match = re.search(r"silence_start: ([\d.]+)", line)
            if start_match:
                silence_start = float(start_match.group(1))

            # Match silence_end
            end_match = re.search(r"silence_end: ([\d.]+)", line)
            if end_match and silence_start is not None:
                silence_end = float(end_match.group(1))
                silences.append(SilenceRegion(start=silence_start, end=silence_end))
                silence_start = None

        logger.info(f"Detected {len(silences)} silence regions")
        return silences

    def get_edit_regions(
        self, duration: float, silences: list[SilenceRegion]
    ) -> list[EditRegion]:
        """Convert silence regions to edit regions (content to keep).

        Args:
            duration: Total duration of the audio
            silences: List of detected silence regions

        Returns:
            List of EditRegion objects representing content to keep
        """
        if not silences:
            return [EditRegion(start=0, end=duration)]

        regions = []
        current_pos = 0

        for silence in silences:
            # Add padding to silence boundaries
            silence_start = max(0, silence.start - self.padding)
            silence_end = min(duration, silence.end + self.padding)

            # If there's content before this silence, keep it
            if silence_start > current_pos:
                regions.append(
                    EditRegion(
                        start=current_pos,
                        end=silence_start + self.padding,  # Keep a bit of the padding
                    )
                )

            current_pos = silence_end - self.padding  # Start next region a bit early

        # Add final region if there's content after the last silence
        if current_pos < duration:
            regions.append(EditRegion(start=current_pos, end=duration))

        # Merge overlapping regions and filter tiny ones
        merged = self._merge_regions(regions)
        filtered = [r for r in merged if r.duration >= 0.1]

        logger.info(f"Generated {len(filtered)} edit regions")
        return filtered

    def _merge_regions(self, regions: list[EditRegion]) -> list[EditRegion]:
        """Merge overlapping or adjacent regions."""
        if not regions:
            return []

        # Sort by start time
        sorted_regions = sorted(regions, key=lambda r: r.start)
        merged = [sorted_regions[0]]

        for region in sorted_regions[1:]:
            last = merged[-1]
            # If regions overlap or are adjacent, merge them
            if region.start <= last.end:
                merged[-1] = EditRegion(start=last.start, end=max(last.end, region.end))
            else:
                merged.append(region)

        return merged

    def calculate_silence_removed(
        self, duration: float, edit_regions: list[EditRegion]
    ) -> float:
        """Calculate total silence removed.

        Args:
            duration: Original duration
            edit_regions: Regions of content kept

        Returns:
            Seconds of silence removed
        """
        kept_duration = sum(r.duration for r in edit_regions)
        return duration - kept_duration
