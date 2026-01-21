"""Audio processing module."""

from .extractor import extract_audio, get_video_info
from .silence import detect_silences, generate_edit_regions

__all__ = [
    "extract_audio",
    "get_video_info",
    "detect_silences",
    "generate_edit_regions",
]
