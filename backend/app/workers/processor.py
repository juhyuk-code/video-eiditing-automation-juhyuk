"""Stream processing Celery tasks."""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from celery import shared_task
from google.oauth2.credentials import Credentials
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

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

# Create sync engine for Celery tasks
_sync_database_url = settings.database_url.replace("+asyncpg", "+psycopg2")
_sync_engine = create_engine(_sync_database_url)


def _update_job_status(
    job_id: str,
    status: str,
    progress: int = 0,
    current_step: Optional[str] = None,
    error_message: Optional[str] = None,
    **kwargs,
):
    """Update job status in database.

    Args:
        job_id: Job ID
        status: New status
        progress: Progress percentage
        current_step: Current step description
        error_message: Error message if failed
        **kwargs: Additional fields to update
    """
    from ..db.models import Job

    with Session(_sync_engine) as session:
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            job.progress = progress
            job.current_step = current_step
            if error_message:
                job.error_message = error_message

            # Update additional fields
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)

            # Update timestamps
            if status == JobStatus.DOWNLOADING.value and not job.started_at:
                job.started_at = datetime.utcnow()
            if status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
                job.completed_at = datetime.utcnow()

            session.commit()
            logger.debug(f"[{job_id}] Updated status: {status} ({progress}%)")


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
    user_id: Optional[str] = None,
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
        user_id: User ID for database records

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
        _update_job_status(
            job_id,
            JobStatus.DOWNLOADING.value,
            progress=5,
            current_step="Downloading from Google Drive",
        )

        video_path = temp_dir / "stream.mp4"
        drive_service.download_file(stream_file_id, video_path)

        _update_job_status(job_id, JobStatus.DOWNLOADING.value, progress=15)

        # Step 2: Audio Processing (30%)
        logger.info(f"[{job_id}] Processing audio...")
        _update_job_status(
            job_id,
            JobStatus.PROCESSING_AUDIO.value,
            progress=20,
            current_step="Extracting and analyzing audio",
        )

        audio_path = temp_dir / "audio.wav"
        audio_processor.extract_audio(video_path, audio_path)

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

        _update_job_status(
            job_id,
            JobStatus.PROCESSING_AUDIO.value,
            progress=30,
            original_duration=duration,
            final_duration=final_duration,
            silence_removed=silence_removed,
        )

        # Step 3: Transcription (50%)
        logger.info(f"[{job_id}] Transcribing...")
        _update_job_status(
            job_id,
            JobStatus.TRANSCRIBING.value,
            progress=35,
            current_step="Transcribing audio (Return Zero)",
        )

        transcript = transcription_service.transcribe(audio_path)
        result["word_count"] = transcript.word_count
        result["language_breakdown"] = transcript.language_breakdown

        _update_job_status(
            job_id,
            JobStatus.TRANSCRIBING.value,
            progress=50,
            word_count=transcript.word_count,
            language_breakdown=transcript.language_breakdown,
        )

        # Step 4: Analysis (70%)
        logger.info(f"[{job_id}] Analyzing content...")
        _update_job_status(
            job_id,
            JobStatus.ANALYZING.value,
            progress=55,
            current_step="Analyzing content (Claude AI)",
        )

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

        _update_job_status(
            job_id,
            JobStatus.ANALYZING.value,
            progress=70,
            chapters_count=len(analysis.chapters),
            chapters_data=[ch.model_dump() for ch in analysis.chapters],
            title_ideas=[t.model_dump() for t in analysis.title_ideas],
            thumbnail_concepts=[t.model_dump() for t in analysis.thumbnail_concepts],
            tags=analysis.tags,
        )

        # Step 5: Generate Outputs (85%)
        logger.info(f"[{job_id}] Generating outputs...")
        _update_job_status(
            job_id,
            JobStatus.GENERATING.value,
            progress=75,
            current_step="Generating timeline and captions",
        )

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

        _update_job_status(job_id, JobStatus.GENERATING.value, progress=85)

        # Step 6: Upload to Google Drive (100%)
        logger.info(f"[{job_id}] Uploading outputs to Google Drive...")
        _update_job_status(
            job_id,
            JobStatus.UPLOADING.value,
            progress=90,
            current_step="Uploading to Google Drive",
        )

        # Create output folder in Google Drive
        output_folder_id = drive_service.create_folder("output", folder_id)
        result["output_folder_id"] = output_folder_id

        # Upload all files
        for file_path in output_dir.iterdir():
            if file_path.is_file():
                drive_service.upload_file(file_path, output_folder_id)

        result["progress"] = 100
        result["status"] = JobStatus.COMPLETED.value

        _update_job_status(
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            current_step="Complete",
            output_folder_id=output_folder_id,
        )

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

        _update_job_status(
            job_id,
            JobStatus.FAILED.value,
            progress=result.get("progress", 0),
            error_message=str(e),
        )

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
