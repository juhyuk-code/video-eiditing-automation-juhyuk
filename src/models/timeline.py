"""Timeline and editing data models."""

from pathlib import Path

from pydantic import BaseModel


class SilenceRegion(BaseModel):
    """A region of silence to be cut."""

    start: float  # seconds
    end: float  # seconds

    @property
    def duration(self) -> float:
        return self.end - self.start


class EditRegion(BaseModel):
    """A region of content to keep (non-silence)."""

    source_start: float  # start in source video
    source_end: float  # end in source video
    timeline_start: float  # start in output timeline (after cuts)

    @property
    def duration(self) -> float:
        return self.source_end - self.source_start

    @property
    def timeline_end(self) -> float:
        return self.timeline_start + self.duration


class MediaFile(BaseModel):
    """Reference to a media file."""

    path: Path
    duration: float  # seconds
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    has_audio: bool = True

    model_config = {"arbitrary_types_allowed": True}


class TimelineClip(BaseModel):
    """A clip on the timeline."""

    media: MediaFile
    source_in: float  # in point in source media
    source_out: float  # out point in source media
    timeline_in: float  # position on timeline
    track: int = 1  # track number (1-indexed)

    # Transform for short-form (9:16 layout)
    scale: float = 1.0
    position_x: float = 0.0  # center offset
    position_y: float = 0.0  # center offset

    model_config = {"arbitrary_types_allowed": True}

    @property
    def duration(self) -> float:
        return self.source_out - self.source_in

    @property
    def timeline_out(self) -> float:
        return self.timeline_in + self.duration


class TimelineMarker(BaseModel):
    """A marker on the timeline (chapter or clip boundary)."""

    time: float  # seconds
    name: str
    color: str = "blue"  # blue, green, red, yellow, etc.
    comment: str = ""


class Timeline(BaseModel):
    """Complete timeline representation."""

    name: str
    duration: float  # total duration in seconds
    fps: float = 30.0
    width: int = 1920
    height: int = 1080
    sample_rate: int = 48000

    video_clips: list[TimelineClip] = []
    audio_clips: list[TimelineClip] = []
    markers: list[TimelineMarker] = []

    model_config = {"arbitrary_types_allowed": True}

    def add_video_clip(self, clip: TimelineClip) -> None:
        """Add a video clip to the timeline."""
        self.video_clips.append(clip)
        self._update_duration()

    def add_audio_clip(self, clip: TimelineClip) -> None:
        """Add an audio clip to the timeline."""
        self.audio_clips.append(clip)
        self._update_duration()

    def add_marker(self, marker: TimelineMarker) -> None:
        """Add a marker to the timeline."""
        self.markers.append(marker)

    def _update_duration(self) -> None:
        """Update timeline duration based on clips."""
        max_video = max((c.timeline_out for c in self.video_clips), default=0)
        max_audio = max((c.timeline_out for c in self.audio_clips), default=0)
        self.duration = max(max_video, max_audio)
