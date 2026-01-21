"""FCP7 XML generator for Adobe Premiere import.

Adobe Premiere Pro can import Final Cut Pro 7 XML format natively.
This module generates FCP7 XML timelines with:
- Multiple video/audio tracks
- Clip references with in/out points
- Markers for chapters
- Transform effects for 9:16 layout
"""

import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from src.models.analysis import LongformAnalysis, ShortformAnalysis
from src.models.config import Settings
from src.models.timeline import EditRegion, MediaFile


def generate_longform_xml(
    full_stream: MediaFile,
    edit_regions: list[EditRegion],
    analysis: LongformAnalysis,
    settings: Settings,
    output_path: Path,
) -> Path:
    """Generate FCP7 XML for long-form content.

    Args:
        full_stream: Full stream video file info.
        edit_regions: Regions to keep (silences removed).
        analysis: Long-form analysis with chapters.
        settings: Application settings.
        output_path: Path for the output XML file.

    Returns:
        Path to the generated XML file.
    """
    fps = settings.premiere.fps
    sample_rate = settings.premiere.sample_rate

    # Calculate timeline duration
    timeline_duration = sum(r.duration for r in edit_regions)

    # Create XML structure
    root = _create_xmeml_root()
    project = ET.SubElement(root, "project")
    ET.SubElement(project, "name").text = output_path.stem

    # Create bin for media
    children = ET.SubElement(project, "children")

    # Create sequence
    sequence = ET.SubElement(children, "sequence")
    ET.SubElement(sequence, "name").text = "Long-Form Timeline"
    ET.SubElement(sequence, "duration").text = str(int(timeline_duration * fps))

    # Rate
    rate = ET.SubElement(sequence, "rate")
    ET.SubElement(rate, "timebase").text = str(int(fps))
    ET.SubElement(rate, "ntsc").text = "FALSE"

    # Timecode
    timecode = ET.SubElement(sequence, "timecode")
    tc_rate = ET.SubElement(timecode, "rate")
    ET.SubElement(tc_rate, "timebase").text = str(int(fps))
    ET.SubElement(tc_rate, "ntsc").text = "FALSE"
    ET.SubElement(timecode, "string").text = settings.premiere.timecode_start
    ET.SubElement(timecode, "frame").text = "0"
    ET.SubElement(timecode, "displayformat").text = "NDF"

    # Media
    media = ET.SubElement(sequence, "media")

    # Video tracks
    video = ET.SubElement(media, "video")
    _add_format(video, full_stream.width, full_stream.height, fps)

    # Video track 1 - main video
    track1 = ET.SubElement(video, "track")
    file_id = f"file-{uuid.uuid4().hex[:8]}"

    for region in edit_regions:
        _add_clip_item(
            track1,
            file_id=file_id,
            file_path=full_stream.path,
            source_in=region.source_start,
            source_out=region.source_end,
            timeline_in=region.timeline_start,
            fps=fps,
            width=full_stream.width,
            height=full_stream.height,
            has_audio=True,
        )

    # Audio tracks
    audio = ET.SubElement(media, "audio")
    _add_audio_format(audio, sample_rate)

    # Audio track 1
    audio_track = ET.SubElement(audio, "track")
    for region in edit_regions:
        _add_audio_clip_item(
            audio_track,
            file_id=file_id,
            file_path=full_stream.path,
            source_in=region.source_start,
            source_out=region.source_end,
            timeline_in=region.timeline_start,
            fps=fps,
            sample_rate=sample_rate,
        )

    # Add chapter markers
    for chapter in analysis.chapters:
        # Find the timeline position for this chapter's source time
        timeline_pos = _source_to_timeline_time(chapter.start, edit_regions)
        if timeline_pos is not None:
            _add_marker(
                sequence,
                time=timeline_pos,
                name=chapter.title,
                comment=chapter.summary,
                fps=fps,
            )

    # Write XML
    output_path.parent.mkdir(parents=True, exist_ok=True)
    xml_str = _prettify(root)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

    return output_path


def generate_shortform_xml(
    webcam: MediaFile,
    screen: MediaFile,
    full_stream: MediaFile,
    analysis: ShortformAnalysis,
    edit_regions: list[EditRegion],
    settings: Settings,
    output_path: Path,
) -> Path:
    """Generate FCP7 XML for short-form content.

    Args:
        webcam: Webcam video file info.
        screen: Screen recording file info.
        full_stream: Full stream for audio.
        analysis: Short-form analysis with clips.
        edit_regions: Regions to map source times to timeline times.
        settings: Application settings.
        output_path: Path for the output XML file.

    Returns:
        Path to the generated XML file.
    """
    fps = settings.premiere.fps
    sample_rate = settings.premiere.sample_rate
    shortform_settings = settings.video.shortform

    # Parse resolution
    width, height = map(int, shortform_settings.resolution.split("x"))
    webcam_ratio = shortform_settings.webcam_height_ratio

    # Calculate total timeline duration (all clips in sequence)
    total_duration = sum(clip.duration for clip in analysis.clips)

    # Create XML structure
    root = _create_xmeml_root()
    project = ET.SubElement(root, "project")
    ET.SubElement(project, "name").text = output_path.stem

    children = ET.SubElement(project, "children")

    # Create sequence
    sequence = ET.SubElement(children, "sequence")
    ET.SubElement(sequence, "name").text = "Short-Form Timeline"
    ET.SubElement(sequence, "duration").text = str(int(total_duration * fps))

    # Rate
    rate = ET.SubElement(sequence, "rate")
    ET.SubElement(rate, "timebase").text = str(int(fps))
    ET.SubElement(rate, "ntsc").text = "FALSE"

    # Timecode
    timecode = ET.SubElement(sequence, "timecode")
    tc_rate = ET.SubElement(timecode, "rate")
    ET.SubElement(tc_rate, "timebase").text = str(int(fps))
    ET.SubElement(tc_rate, "ntsc").text = "FALSE"
    ET.SubElement(timecode, "string").text = "00:00:00:00"
    ET.SubElement(timecode, "frame").text = "0"
    ET.SubElement(timecode, "displayformat").text = "NDF"

    # Media
    media = ET.SubElement(sequence, "media")

    # Video tracks
    video = ET.SubElement(media, "video")
    _add_format(video, width, height, fps)

    # Video track 1 - Webcam (top)
    track1 = ET.SubElement(video, "track")
    webcam_file_id = f"file-webcam-{uuid.uuid4().hex[:8]}"

    # Video track 2 - Screen (bottom)
    track2 = ET.SubElement(video, "track")
    screen_file_id = f"file-screen-{uuid.uuid4().hex[:8]}"

    # Calculate positions for 9:16 layout
    webcam_height = int(height * webcam_ratio)
    screen_height = height - webcam_height
    webcam_y_offset = (height / 2) - (webcam_height / 2)  # Top position
    screen_y_offset = -((height / 2) - (screen_height / 2))  # Bottom position

    timeline_position = 0.0
    for i, clip in enumerate(analysis.clips):
        # Webcam clip (top)
        _add_clip_item(
            track1,
            file_id=webcam_file_id,
            file_path=webcam.path,
            source_in=clip.start,
            source_out=clip.end,
            timeline_in=timeline_position,
            fps=fps,
            width=webcam.width,
            height=webcam.height,
            has_audio=False,
            scale_x=width / webcam.width,
            scale_y=webcam_height / webcam.height,
            position_y=webcam_y_offset,
        )

        # Screen clip (bottom)
        _add_clip_item(
            track2,
            file_id=screen_file_id,
            file_path=screen.path,
            source_in=clip.start,
            source_out=clip.end,
            timeline_in=timeline_position,
            fps=fps,
            width=screen.width,
            height=screen.height,
            has_audio=False,
            scale_x=width / screen.width,
            scale_y=screen_height / screen.height,
            position_y=screen_y_offset,
        )

        # Add clip marker
        _add_marker(
            sequence,
            time=timeline_position,
            name=f"Clip {i+1}: {clip.category}",
            comment=clip.hook,
            fps=fps,
        )

        timeline_position += clip.duration

    # Audio track - from full stream
    audio = ET.SubElement(media, "audio")
    _add_audio_format(audio, sample_rate)

    audio_track = ET.SubElement(audio, "track")
    audio_file_id = f"file-audio-{uuid.uuid4().hex[:8]}"

    timeline_position = 0.0
    for clip in analysis.clips:
        _add_audio_clip_item(
            audio_track,
            file_id=audio_file_id,
            file_path=full_stream.path,
            source_in=clip.start,
            source_out=clip.end,
            timeline_in=timeline_position,
            fps=fps,
            sample_rate=sample_rate,
        )
        timeline_position += clip.duration

    # Write XML
    output_path.parent.mkdir(parents=True, exist_ok=True)
    xml_str = _prettify(root)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

    return output_path


def _create_xmeml_root() -> ET.Element:
    """Create the root XMEML element."""
    root = ET.Element("xmeml")
    root.set("version", "5")
    return root


def _add_format(video: ET.Element, width: int, height: int, fps: float) -> None:
    """Add video format element."""
    format_elem = ET.SubElement(video, "format")
    sample_chars = ET.SubElement(format_elem, "samplecharacteristics")
    ET.SubElement(sample_chars, "width").text = str(width)
    ET.SubElement(sample_chars, "height").text = str(height)
    ET.SubElement(sample_chars, "pixelaspectratio").text = "square"

    rate = ET.SubElement(sample_chars, "rate")
    ET.SubElement(rate, "timebase").text = str(int(fps))
    ET.SubElement(rate, "ntsc").text = "FALSE"


def _add_audio_format(audio: ET.Element, sample_rate: int) -> None:
    """Add audio format element."""
    format_elem = ET.SubElement(audio, "format")
    sample_chars = ET.SubElement(format_elem, "samplecharacteristics")
    ET.SubElement(sample_chars, "samplerate").text = str(sample_rate)
    ET.SubElement(sample_chars, "depth").text = "16"


def _add_clip_item(
    track: ET.Element,
    file_id: str,
    file_path: Path,
    source_in: float,
    source_out: float,
    timeline_in: float,
    fps: float,
    width: int,
    height: int,
    has_audio: bool = True,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    position_x: float = 0.0,
    position_y: float = 0.0,
) -> ET.Element:
    """Add a video clip item to a track."""
    clipitem = ET.SubElement(track, "clipitem")
    ET.SubElement(clipitem, "name").text = file_path.stem

    duration_frames = int((source_out - source_in) * fps)
    ET.SubElement(clipitem, "duration").text = str(duration_frames)

    # Rate
    rate = ET.SubElement(clipitem, "rate")
    ET.SubElement(rate, "timebase").text = str(int(fps))
    ET.SubElement(rate, "ntsc").text = "FALSE"

    # In/Out points
    ET.SubElement(clipitem, "in").text = str(int(source_in * fps))
    ET.SubElement(clipitem, "out").text = str(int(source_out * fps))
    ET.SubElement(clipitem, "start").text = str(int(timeline_in * fps))
    ET.SubElement(clipitem, "end").text = str(int((timeline_in + source_out - source_in) * fps))

    # File reference
    file_elem = ET.SubElement(clipitem, "file")
    file_elem.set("id", file_id)
    ET.SubElement(file_elem, "name").text = file_path.name
    ET.SubElement(file_elem, "pathurl").text = f"file://localhost{file_path.absolute()}"

    # File rate
    file_rate = ET.SubElement(file_elem, "rate")
    ET.SubElement(file_rate, "timebase").text = str(int(fps))
    ET.SubElement(file_rate, "ntsc").text = "FALSE"

    # Media
    file_media = ET.SubElement(file_elem, "media")
    file_video = ET.SubElement(file_media, "video")
    video_chars = ET.SubElement(file_video, "samplecharacteristics")
    ET.SubElement(video_chars, "width").text = str(width)
    ET.SubElement(video_chars, "height").text = str(height)

    if has_audio:
        file_audio = ET.SubElement(file_media, "audio")
        audio_chars = ET.SubElement(file_audio, "samplecharacteristics")
        ET.SubElement(audio_chars, "samplerate").text = "48000"
        ET.SubElement(audio_chars, "depth").text = "16"

    # Transform effects (for 9:16 layout)
    if scale_x != 1.0 or scale_y != 1.0 or position_x != 0.0 or position_y != 0.0:
        _add_motion_effect(clipitem, scale_x, scale_y, position_x, position_y)

    return clipitem


def _add_audio_clip_item(
    track: ET.Element,
    file_id: str,
    file_path: Path,
    source_in: float,
    source_out: float,
    timeline_in: float,
    fps: float,
    sample_rate: int,
) -> ET.Element:
    """Add an audio clip item to a track."""
    clipitem = ET.SubElement(track, "clipitem")
    ET.SubElement(clipitem, "name").text = file_path.stem

    duration_frames = int((source_out - source_in) * fps)
    ET.SubElement(clipitem, "duration").text = str(duration_frames)

    # Rate
    rate = ET.SubElement(clipitem, "rate")
    ET.SubElement(rate, "timebase").text = str(int(fps))
    ET.SubElement(rate, "ntsc").text = "FALSE"

    # In/Out points
    ET.SubElement(clipitem, "in").text = str(int(source_in * fps))
    ET.SubElement(clipitem, "out").text = str(int(source_out * fps))
    ET.SubElement(clipitem, "start").text = str(int(timeline_in * fps))
    ET.SubElement(clipitem, "end").text = str(int((timeline_in + source_out - source_in) * fps))

    # File reference
    file_elem = ET.SubElement(clipitem, "file")
    file_elem.set("id", file_id)

    # Source track
    source_track = ET.SubElement(clipitem, "sourcetrack")
    ET.SubElement(source_track, "mediatype").text = "audio"
    ET.SubElement(source_track, "trackindex").text = "1"

    return clipitem


def _add_motion_effect(
    clipitem: ET.Element,
    scale_x: float,
    scale_y: float,
    position_x: float,
    position_y: float,
) -> None:
    """Add motion/transform effect to a clip."""
    effect = ET.SubElement(clipitem, "effect")
    ET.SubElement(effect, "name").text = "Basic Motion"
    ET.SubElement(effect, "effectid").text = "basic"
    ET.SubElement(effect, "effecttype").text = "motion"

    # Scale
    if scale_x != 1.0 or scale_y != 1.0:
        scale_param = ET.SubElement(effect, "parameter")
        ET.SubElement(scale_param, "parameterid").text = "scale"
        ET.SubElement(scale_param, "name").text = "Scale"
        ET.SubElement(scale_param, "value").text = str(min(scale_x, scale_y) * 100)

    # Position
    if position_x != 0.0:
        pos_x_param = ET.SubElement(effect, "parameter")
        ET.SubElement(pos_x_param, "parameterid").text = "centerX"
        ET.SubElement(pos_x_param, "name").text = "Center X"
        ET.SubElement(pos_x_param, "value").text = str(position_x)

    if position_y != 0.0:
        pos_y_param = ET.SubElement(effect, "parameter")
        ET.SubElement(pos_y_param, "parameterid").text = "centerY"
        ET.SubElement(pos_y_param, "name").text = "Center Y"
        ET.SubElement(pos_y_param, "value").text = str(position_y)


def _add_marker(
    sequence: ET.Element,
    time: float,
    name: str,
    comment: str,
    fps: float,
    color: str = "blue",
) -> None:
    """Add a marker to the sequence."""
    marker = ET.SubElement(sequence, "marker")
    ET.SubElement(marker, "name").text = name
    ET.SubElement(marker, "comment").text = comment
    ET.SubElement(marker, "in").text = str(int(time * fps))
    ET.SubElement(marker, "out").text = "-1"


def _source_to_timeline_time(
    source_time: float,
    edit_regions: list[EditRegion],
) -> float | None:
    """Convert source time to timeline time accounting for edits.

    Args:
        source_time: Time in the source video.
        edit_regions: List of edit regions.

    Returns:
        Timeline time, or None if the source time was cut.
    """
    for region in edit_regions:
        if region.source_start <= source_time <= region.source_end:
            # Time is within this region
            offset_in_region = source_time - region.source_start
            return region.timeline_start + offset_in_region

    return None


def _prettify(elem: ET.Element) -> str:
    """Return a pretty-printed XML string."""
    rough_string = ET.tostring(elem, encoding="unicode")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
