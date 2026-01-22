"""Stream processing Celery tasks."""

import logging
import shutil
from pathlib import Path
from typing import Optional

from celery import shared_task
from google.oauth2.credentials import Credentials

from ..config import get_settings
from ..models.job import JobStatus
from ..services.google_drive import GoogleDriveService
from ..services.audio import AudioProcessor
from ..services.transcription import TranscriptionService
from ..services.analysis import AnalysisService
from ..services.xml_generator import XMLGenerator
from ..services.telegram import TelegramService

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(bind=True, max_retries=3)
def process_stream(
    self,
    job_id: str,
    stream_date: str,
    folder_id: str,
    stream_file_id: str,
    google_credentials: dict,
    telegram_chat_id: Optional[str] = None,
    webcam_file_id: Optional[str] = None,
    screen_file_id: Optional[str] = None,
) -> dict:
    """Process a stream: download, transcribe, analyze, generate outputs.

    Args:
        job_id: Job ID for tracking
        stream_date: Stream date (YYYYMMDD or YYYYMMDD-N)
        folder_id: Google Drive folder ID
        stream_file_id: Google Drive stream file ID
        google_credentials: OAuth credentials dict
        telegram_chat_id: Optional Telegram chat ID for notifications
        webcam_file_id: Optional webcam file ID
        screen_file_id: Optional screen file ID

    Returns:
        Dict with job results
    """
    # Initialize services
    credentials = Credentials(
        token=google_credentials.get("token"),
        refresh_token=google_credentials.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )

    drive_service = GoogleDriveService(credentials)
    audio_processor = AudioProcessor(
        threshold_db=settings.silence_threshold_db,
        min_silence_duration=settings.silence_min_duration,
        padding=settings.silence_padding,
    )
    transcription_service = TranscriptionService(
        client_id=settings.rtzr_client_id,
        client_secret=settings.rtzr_client_secret,
        api_url=settings.rtzr_api_url,
    )
    analysis_service = AnalysisService(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
    )
    xml_generator = XMLGenerator()
    telegram_service = TelegramService(settings.telegram_bot_token)

    # Create temp directory for this job
    temp_dir = Path(settings.temp_dir) / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "job_id": job_id,
        "status": JobStatus.PENDING.value,
        "progress": 0,
    }

    try:
        # Notify start
        if telegram_chat_id:
            telegram_service.send_message_sync(
                telegram_chat_id,
                telegram_service.format_processing_started(stream_date),
            )

        # Step 1: Download (15%)
        logger.info(f"[{job_id}] Downloading stream file...")
        result["status"] = JobStatus.DOWNLOADING.value
        result["progress"] = 5

        video_path = temp_dir / "stream.mp4"
        drive_service.download_file(stream_file_id, video_path)
        result["progress"] = 15

        # Step 2: Audio Processing (30%)
        logger.info(f"[{job_id}] Processing audio...")
        result["status"] = JobStatus.PROCESSING_AUDIO.value

        audio_path = temp_dir / "audio.wav"
        audio_processor.extract_audio(video_path, audio_path)
        result["progress"] = 20

        # Get duration
        duration = audio_processor.get_duration(video_path)
        result["original_duration"] = duration

        # Detect silences
        silences = audio_processor.detect_silences(audio_path)
        edit_regions = audio_processor.get_edit_regions(duration, silences)

        silence_removed = audio_processor.calculate_silence_removed(duration, edit_regions)
        final_duration = duration - silence_removed

        result["final_duration"] = final_duration
        result["silence_removed"] = silence_removed
        result["progress"] = 30

        # Step 3: Transcription (50%)
        logger.info(f"[{job_id}] Transcribing...")
        result["status"] = JobStatus.TRANSCRIBING.value

        transcript = transcription_service.transcribe(audio_path)
        result["word_count"] = transcript.word_count
        result["language_breakdown"] = transcript.language_breakdown
        result["progress"] = 50

        # Step 4: Analysis (70%)
        logger.info(f"[{job_id}] Analyzing content...")
        result["status"] = JobStatus.ANALYZING.value

        analysis = analysis_service.analyze(
            transcript,
            min_chapter_duration=settings.min_chapter_duration,
            max_chapters=settings.max_chapters,
        )

        result["chapters_count"] = len(analysis.chapters)
        result["chapters_data"] = [ch.model_dump() for ch in analysis.chapters]
        result["title_ideas"] = [t.model_dump() for t in analysis.title_ideas]
        result["thumbnail_concepts"] = [t.model_dump() for t in analysis.thumbnail_concepts]
        result["tags"] = analysis.tags
        result["progress"] = 70

        # Step 5: Generate Outputs (85%)
        logger.info(f"[{job_id}] Generating outputs...")
        result["status"] = JobStatus.GENERATING.value

        output_dir = temp_dir / "output"
        output_dir.mkdir(exist_ok=True)

        # Generate timeline XML
        xml_content = xml_generator.generate_timeline(
            video_filename="stream.mp4",
            duration=duration,
            edit_regions=edit_regions,
            chapters=analysis.chapters,
            sequence_name=f"Stream {stream_date}",
        )
        xml_generator.save(xml_content, output_dir / "timeline.xml")

        # Generate captions
        srt_content = transcript.to_srt()
        (output_dir / "captions.srt").write_text(srt_content, encoding="utf-8")

        vtt_content = transcript.to_vtt()
        (output_dir / "captions.vtt").write_text(vtt_content, encoding="utf-8")

        # Generate chapters.txt
        chapters_txt = analysis.get_chapters_text()
        (output_dir / "chapters.txt").write_text(chapters_txt, encoding="utf-8")

        # Generate suggestions.md
        suggestions_md = analysis.to_suggestions_md()
        (output_dir / "suggestions.md").write_text(suggestions_md, encoding="utf-8")

        # Save transcript files
        import json
        transcript_data = {
            "segments": [s.model_dump() for s in transcript.segments],
            "duration": transcript.duration,
            "language_breakdown": transcript.language_breakdown,
            "word_count": transcript.word_count,
        }
        (output_dir / "transcript.json").write_text(
            json.dumps(transcript_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_dir / "transcript.txt").write_text(
            transcript.get_full_text(),
            encoding="utf-8",
        )

        result["progress"] = 85

        # Step 6: Upload to Google Drive (100%)
        logger.info(f"[{job_id}] Uploading outputs to Google Drive...")
        result["status"] = JobStatus.UPLOADING.value

        # Create output folder in Google Drive
        output_folder_id = drive_service.create_folder("output", folder_id)
        result["output_folder_id"] = output_folder_id

        # Upload all files
        for file_path in output_dir.iterdir():
            if file_path.is_file():
                drive_service.upload_file(file_path, output_folder_id)

        result["progress"] = 100
        result["status"] = JobStatus.COMPLETED.value

        # Send completion notification
        if telegram_chat_id:
            output_link = drive_service.get_folder_link(output_folder_id)
            telegram_service.send_message_sync(
                telegram_chat_id,
                telegram_service.format_processing_complete(
                    stream_name=stream_date,
                    original_duration=telegram_service.format_duration(duration),
                    final_duration=telegram_service.format_duration(final_duration),
                    silence_removed=telegram_service.format_duration(silence_removed),
                    chapters_count=len(analysis.chapters),
                    title_count=len(analysis.title_ideas),
                    output_link=output_link,
                ),
            )

        logger.info(f"[{job_id}] Processing complete!")

    except Exception as e:
        logger.exception(f"[{job_id}] Processing failed: {e}")
        result["status"] = JobStatus.FAILED.value
        result["error_message"] = str(e)

        # Send failure notification
        if telegram_chat_id:
            telegram_service.send_message_sync(
                telegram_chat_id,
                telegram_service.format_processing_failed(
                    stream_name=stream_date,
                    error_message=str(e)[:200],  # Truncate long errors
                ),
            )

        # Retry if applicable
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"[{job_id}] Cleaned up temp directory")
        except Exception as e:
            logger.warning(f"[{job_id}] Failed to cleanup temp directory: {e}")

    return result
