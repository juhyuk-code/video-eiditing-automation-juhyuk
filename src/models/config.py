"""Configuration settings model."""

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class PathSettings(BaseModel):
    """Path configuration."""

    output_dir: Path = Path("./output")
    temp_dir: Path = Path("./temp")


class SilenceSettings(BaseModel):
    """Silence detection configuration."""

    threshold_db: float = -40.0
    min_duration: float = 0.5  # seconds
    padding: float = 0.1  # seconds to keep around speech


class TranscriptionSettings(BaseModel):
    """Transcription configuration."""

    provider: str = "returnzero"
    language_hints: list[str] = ["ko", "en"]


class LongformAnalysisSettings(BaseModel):
    """Long-form analysis configuration."""

    min_chapter_duration: int = 60  # seconds
    max_chapters: int = 20


class ShortformAnalysisSettings(BaseModel):
    """Short-form analysis configuration."""

    min_clips: int = 10
    max_clip_duration: int = 180  # seconds (3 min YouTube Shorts limit)
    max_clips: int = 30
    viral_signals: list[str] = Field(
        default=[
            "bold market predictions",
            "contrarian takes",
            "price calls",
            "I told you so moments",
            "surprising insights",
            "emotional reactions",
        ]
    )


class AnalysisSettings(BaseModel):
    """Analysis configuration."""

    model: str = "claude-sonnet-4-20250514"
    longform: LongformAnalysisSettings = LongformAnalysisSettings()
    shortform: ShortformAnalysisSettings = ShortformAnalysisSettings()


class ShortformVideoSettings(BaseModel):
    """Short-form video layout configuration."""

    resolution: str = "1080x1920"
    webcam_position: str = "top"  # top or bottom
    webcam_height_ratio: float = 0.4  # 40% of frame


class VideoSettings(BaseModel):
    """Video configuration."""

    shortform: ShortformVideoSettings = ShortformVideoSettings()


class PremiereSettings(BaseModel):
    """Adobe Premiere export configuration."""

    fps: float = 30.0
    sample_rate: int = 48000
    timecode_start: str = "00:00:00:00"


class CaptionSettings(BaseModel):
    """Caption configuration."""

    formats: list[str] = ["srt", "vtt"]


class Settings(BaseSettings):
    """Main application settings."""

    paths: PathSettings = PathSettings()
    silence: SilenceSettings = SilenceSettings()
    transcription: TranscriptionSettings = TranscriptionSettings()
    analysis: AnalysisSettings = AnalysisSettings()
    video: VideoSettings = VideoSettings()
    premiere: PremiereSettings = PremiereSettings()
    captions: CaptionSettings = CaptionSettings()

    # API Keys (from environment)
    rtzr_api_key: str = ""
    anthropic_api_key: str = ""

    model_config = {
        "env_prefix": "",
        "env_nested_delimiter": "__",
        "extra": "ignore",
    }

    @classmethod
    def load_from_yaml(cls, path: Path) -> "Settings":
        """Load settings from a YAML file."""
        import yaml

        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls(**data)
