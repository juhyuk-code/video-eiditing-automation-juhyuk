"""File watcher Celery task for detecting new streams."""

import logging
from typing import Optional

from celery import shared_task

from ..config import get_settings
from .processor import process_stream

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory cache of processed folders (in production, use database)
_processed_folders: set[str] = set()


@shared_task
def watch_for_streams(
    watch_folder_id: Optional[str] = None,
    google_credentials: Optional[dict] = None,
    telegram_chat_id: Optional[str] = None,
) -> dict:
    """Watch Google Drive for new stream folders.

    This task is called periodically by Celery Beat.

    Args:
        watch_folder_id: Google Drive folder ID to watch
        google_credentials: OAuth credentials dict
        telegram_chat_id: Telegram chat ID for notifications

    Returns:
        Dict with watch results
    """
    # In production, these would come from the database based on user settings
    # For now, we'll skip if not provided
    if not watch_folder_id or not google_credentials:
        logger.debug("Watcher skipped: missing credentials or folder ID")
        return {"status": "skipped", "reason": "no_credentials"}

    from google.oauth2.credentials import Credentials
    from ..services.google_drive import GoogleDriveService
    from ..services.telegram import TelegramService

    try:
        credentials = Credentials(
            token=google_credentials.get("token"),
            refresh_token=google_credentials.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
        )

        drive_service = GoogleDriveService(credentials)
        telegram_service = TelegramService(settings.telegram_bot_token)

        # Get all stream folders
        folders = drive_service.get_stream_folders(watch_folder_id)

        new_streams = []
        for folder in folders:
            folder_id = folder["id"]
            folder_name = folder["name"]

            # Skip if already has output folder
            if folder["has_output"]:
                logger.debug(f"Skipping {folder_name}: already processed")
                continue

            # Skip if we've already queued it
            if folder_id in _processed_folders:
                logger.debug(f"Skipping {folder_name}: already in queue")
                continue

            # Check for stream file
            files = drive_service.get_stream_files(folder_id)
            if not files["stream"]:
                logger.debug(f"Skipping {folder_name}: no stream file")
                continue

            # Check if file is ready (upload complete)
            if not drive_service.is_file_ready(files["stream"]["id"]):
                logger.debug(f"Skipping {folder_name}: file still uploading")
                continue

            # New stream detected!
            logger.info(f"New stream detected: {folder_name}")
            _processed_folders.add(folder_id)

            # Notify via Telegram
            if telegram_chat_id:
                telegram_service.send_message_sync(
                    telegram_chat_id,
                    telegram_service.format_stream_detected(folder_name),
                )

            # Queue processing task
            import uuid
            job_id = str(uuid.uuid4())

            process_stream.delay(
                job_id=job_id,
                stream_date=folder_name,
                folder_id=folder_id,
                stream_file_id=files["stream"]["id"],
                google_credentials=google_credentials,
                telegram_chat_id=telegram_chat_id,
                webcam_file_id=files["webcam"]["id"] if files["webcam"] else None,
                screen_file_id=files["screen"]["id"] if files["screen"] else None,
            )

            new_streams.append({
                "job_id": job_id,
                "folder_name": folder_name,
                "folder_id": folder_id,
            })

        return {
            "status": "success",
            "folders_checked": len(folders),
            "new_streams": new_streams,
        }

    except Exception as e:
        logger.exception(f"Watcher failed: {e}")
        return {"status": "error", "error": str(e)}


def clear_processed_cache():
    """Clear the in-memory processed folders cache.

    Useful for testing or allowing re-processing.
    """
    global _processed_folders
    _processed_folders = set()
