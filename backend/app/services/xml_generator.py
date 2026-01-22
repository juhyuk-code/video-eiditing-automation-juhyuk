"""FCP7 XML generator for Adobe Premiere Pro."""

import logging
import uuid
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from ..models.analysis import Chapter
from ..services.audio import EditRegion

logger = logging.getLogger(__name__)

# Constants for timeline
TIMEBASE = 30  # 30 fps timebase
NTSC = False


class XMLGenerator:
    """Generate FCP7 XML timelines for Adobe Premiere Pro."""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        timebase: int = TIMEBASE,
        ntsc: bool = NTSC,
    ):
        """Initialize the XML generator.

        Args:
            width: Video width
            height: Video height
            timebase: Frames per second
            ntsc: Whether to use NTSC timing
        """
        self.width = width
        self.height = height
        self.timebase = timebase
        self.ntsc = ntsc

    def generate_timeline(
        self,
        video_filename: str,
        duration: float,
        edit_regions: list[EditRegion],
        chapters: Optional[list[Chapter]] = None,
        sequence_name: str = "Edited Timeline",
    ) -> str:
        """Generate FCP7 XML timeline.

        Args:
            video_filename: Name of the source video file (relative path)
            duration: Total duration in seconds
            edit_regions: Regions of content to include
            chapters: Optional chapter markers
            sequence_name: Name for the sequence

        Returns:
            XML string
        """
        # Create root element
        xmeml = ET.Element("xmeml", version="5")

        # Create project
        project = ET.SubElement(xmeml, "project")
        ET.SubElement(project, "name").text = sequence_name

        # Create children container
        children = ET.SubElement(project, "children")

        # Create sequence
        sequence = ET.SubElement(children, "sequence")
        sequence_id = f"sequence-{uuid.uuid4().hex[:8]}"
        sequence.set("id", sequence_id)

        ET.SubElement(sequence, "name").text = sequence_name
        ET.SubElement(sequence, "duration").text = str(self._seconds_to_frames(duration))

        # Rate
        rate = ET.SubElement(sequence, "rate")
        ET.SubElement(rate, "timebase").text = str(self.timebase)
        ET.SubElement(rate, "ntsc").text = "TRUE" if self.ntsc else "FALSE"

        # Timecode
        timecode = ET.SubElement(sequence, "timecode")
        tc_rate = ET.SubElement(timecode, "rate")
        ET.SubElement(tc_rate, "timebase").text = str(self.timebase)
        ET.SubElement(tc_rate, "ntsc").text = "TRUE" if self.ntsc else "FALSE"
        ET.SubElement(timecode, "string").text = "00:00:00:00"
        ET.SubElement(timecode, "frame").text = "0"
        ET.SubElement(timecode, "displayformat").text = "NDF"

        # Media
        media = ET.SubElement(sequence, "media")

        # Video track
        video = ET.SubElement(media, "video")
        video_format = ET.SubElement(video, "format")
        sample_characteristics = ET.SubElement(video_format, "samplecharacteristics")
        sc_rate = ET.SubElement(sample_characteristics, "rate")
        ET.SubElement(sc_rate, "timebase").text = str(self.timebase)
        ET.SubElement(sc_rate, "ntsc").text = "TRUE" if self.ntsc else "FALSE"
        ET.SubElement(sample_characteristics, "width").text = str(self.width)
        ET.SubElement(sample_characteristics, "height").text = str(self.height)
        ET.SubElement(sample_characteristics, "pixelaspectratio").text = "square"
        ET.SubElement(sample_characteristics, "fielddominance").text = "none"

        # Video track with clips
        video_track = ET.SubElement(video, "track")

        # Calculate timeline position
        timeline_position = 0

        for i, region in enumerate(edit_regions):
            clip_id = f"clipitem-{uuid.uuid4().hex[:8]}"
            clipitem = self._create_clipitem(
                parent=video_track,
                clip_id=clip_id,
                name=f"Clip {i + 1}",
                video_filename=video_filename,
                start_frame=timeline_position,
                end_frame=timeline_position + self._seconds_to_frames(region.duration),
                in_frame=self._seconds_to_frames(region.start),
                out_frame=self._seconds_to_frames(region.end),
                is_video=True,
            )
            timeline_position += self._seconds_to_frames(region.duration)

        # Add chapter markers if provided
        if chapters:
            # Markers need to go on the sequence
            for chapter in chapters:
                marker = ET.SubElement(sequence, "marker")
                ET.SubElement(marker, "name").text = chapter.title
                ET.SubElement(marker, "comment").text = chapter.summary
                ET.SubElement(marker, "in").text = str(self._seconds_to_frames(chapter.start))
                ET.SubElement(marker, "out").text = "-1"

        # Audio track
        audio = ET.SubElement(media, "audio")
        audio_format = ET.SubElement(audio, "format")
        audio_sc = ET.SubElement(audio_format, "samplecharacteristics")
        ET.SubElement(audio_sc, "depth").text = "16"
        ET.SubElement(audio_sc, "samplerate").text = "48000"

        audio_track = ET.SubElement(audio, "track")

        # Reset timeline position for audio
        timeline_position = 0

        for i, region in enumerate(edit_regions):
            clip_id = f"clipitem-audio-{uuid.uuid4().hex[:8]}"
            clipitem = self._create_clipitem(
                parent=audio_track,
                clip_id=clip_id,
                name=f"Clip {i + 1}",
                video_filename=video_filename,
                start_frame=timeline_position,
                end_frame=timeline_position + self._seconds_to_frames(region.duration),
                in_frame=self._seconds_to_frames(region.start),
                out_frame=self._seconds_to_frames(region.end),
                is_video=False,
            )
            timeline_position += self._seconds_to_frames(region.duration)

        # Convert to string
        xml_str = ET.tostring(xmeml, encoding="unicode")

        # Add XML declaration
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + xml_str

        return xml_str

    def _create_clipitem(
        self,
        parent: ET.Element,
        clip_id: str,
        name: str,
        video_filename: str,
        start_frame: int,
        end_frame: int,
        in_frame: int,
        out_frame: int,
        is_video: bool = True,
    ) -> ET.Element:
        """Create a clip item element.

        Args:
            parent: Parent element
            clip_id: Unique clip ID
            name: Clip name
            video_filename: Source video filename
            start_frame: Start frame on timeline
            end_frame: End frame on timeline
            in_frame: In point in source
            out_frame: Out point in source
            is_video: Whether this is a video clip (vs audio)

        Returns:
            Created clipitem element
        """
        clipitem = ET.SubElement(parent, "clipitem", id=clip_id)
        ET.SubElement(clipitem, "name").text = name
        ET.SubElement(clipitem, "enabled").text = "TRUE"
        ET.SubElement(clipitem, "start").text = str(start_frame)
        ET.SubElement(clipitem, "end").text = str(end_frame)
        ET.SubElement(clipitem, "in").text = str(in_frame)
        ET.SubElement(clipitem, "out").text = str(out_frame)

        # Rate
        rate = ET.SubElement(clipitem, "rate")
        ET.SubElement(rate, "timebase").text = str(self.timebase)
        ET.SubElement(rate, "ntsc").text = "TRUE" if self.ntsc else "FALSE"

        # File reference - using relative path (../stream.mp4)
        file_elem = ET.SubElement(clipitem, "file", id=f"file-{uuid.uuid4().hex[:8]}")
        ET.SubElement(file_elem, "name").text = Path(video_filename).name
        ET.SubElement(file_elem, "pathurl").text = f"file://../{video_filename}"

        # Media info
        file_media = ET.SubElement(file_elem, "media")

        if is_video:
            file_video = ET.SubElement(file_media, "video")
            ET.SubElement(file_video, "duration").text = str(out_frame)
            video_sc = ET.SubElement(file_video, "samplecharacteristics")
            vs_rate = ET.SubElement(video_sc, "rate")
            ET.SubElement(vs_rate, "timebase").text = str(self.timebase)
            ET.SubElement(video_sc, "width").text = str(self.width)
            ET.SubElement(video_sc, "height").text = str(self.height)
        else:
            file_audio = ET.SubElement(file_media, "audio")
            ET.SubElement(file_audio, "channelcount").text = "2"
            audio_sc = ET.SubElement(file_audio, "samplecharacteristics")
            ET.SubElement(audio_sc, "depth").text = "16"
            ET.SubElement(audio_sc, "samplerate").text = "48000"

        return clipitem

    def _seconds_to_frames(self, seconds: float) -> int:
        """Convert seconds to frames.

        Args:
            seconds: Time in seconds

        Returns:
            Frame count
        """
        return int(seconds * self.timebase)

    def save(self, xml_content: str, output_path: Path) -> Path:
        """Save XML content to file.

        Args:
            xml_content: XML string
            output_path: Path to save to

        Returns:
            Path to saved file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(xml_content, encoding="utf-8")
        logger.info(f"Saved timeline to {output_path}")
        return output_path
