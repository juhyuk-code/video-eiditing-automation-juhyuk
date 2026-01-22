"""Google Drive service for file watching and management."""

import io
import re
import logging
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

logger = logging.getLogger(__name__)

# Regex patterns for folder names
DATE_PATTERN = re.compile(r"^(\d{8})(-\d+)?$")  # YYYYMMDD or YYYYMMDD-N


class GoogleDriveService:
    """Service for interacting with Google Drive."""

    def __init__(self, credentials: Credentials):
        """Initialize the Google Drive service.

        Args:
            credentials: Google OAuth2 credentials
        """
        self.service = build("drive", "v3", credentials=credentials)

    def get_stream_folders(self, parent_folder_id: str) -> list[dict]:
        """Get all stream folders (YYYYMMDD or YYYYMMDD-N format) in the parent folder.

        Args:
            parent_folder_id: ID of the StreamAutomation folder

        Returns:
            List of folder metadata dicts with id, name, and whether it has output/
        """
        # Query for folders in the parent
        query = f"'{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

        results = (
            self.service.files()
            .list(q=query, fields="files(id, name)", pageSize=100)
            .execute()
        )

        folders = []
        for item in results.get("files", []):
            # Check if folder name matches YYYYMMDD or YYYYMMDD-N pattern
            if DATE_PATTERN.match(item["name"]):
                has_output = self._has_output_folder(item["id"])
                folders.append(
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "has_output": has_output,
                    }
                )

        return folders

    def _has_output_folder(self, folder_id: str) -> bool:
        """Check if a folder has an 'output' subfolder.

        Args:
            folder_id: ID of the folder to check

        Returns:
            True if output/ subfolder exists
        """
        query = f"'{folder_id}' in parents and name = 'output' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = (
            self.service.files()
            .list(q=query, fields="files(id)", pageSize=1)
            .execute()
        )
        return len(results.get("files", [])) > 0

    def get_stream_files(self, folder_id: str) -> dict[str, Optional[dict]]:
        """Get stream files (stream.*, webcam.*, screen.*) in a folder.

        Args:
            folder_id: ID of the stream folder

        Returns:
            Dict with keys 'stream', 'webcam', 'screen' and file metadata or None
        """
        query = f"'{folder_id}' in parents and trashed = false"
        results = (
            self.service.files()
            .list(q=query, fields="files(id, name, size, mimeType)", pageSize=50)
            .execute()
        )

        files = {"stream": None, "webcam": None, "screen": None}

        for item in results.get("files", []):
            name_lower = item["name"].lower()
            if name_lower.startswith("stream."):
                files["stream"] = item
            elif name_lower.startswith("webcam."):
                files["webcam"] = item
            elif name_lower.startswith("screen."):
                files["screen"] = item

        return files

    def is_file_ready(self, file_id: str, min_stable_seconds: int = 60) -> bool:
        """Check if a file has finished uploading (size is stable).

        Note: This is a simplified check. For production, you'd want to
        track file sizes over time to detect stability.

        Args:
            file_id: ID of the file to check
            min_stable_seconds: Not used in this simple implementation

        Returns:
            True if file appears ready (has a size)
        """
        try:
            file_meta = (
                self.service.files()
                .get(fileId=file_id, fields="size")
                .execute()
            )
            # If we can get the size, file is probably done uploading
            return "size" in file_meta and int(file_meta["size"]) > 0
        except Exception as e:
            logger.warning(f"Error checking file readiness: {e}")
            return False

    def download_file(self, file_id: str, destination: Path) -> Path:
        """Download a file from Google Drive.

        Args:
            file_id: ID of the file to download
            destination: Local path to save the file

        Returns:
            Path to the downloaded file
        """
        request = self.service.files().get_media(fileId=file_id)

        destination.parent.mkdir(parents=True, exist_ok=True)

        with open(destination, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download progress: {int(status.progress() * 100)}%")

        logger.info(f"Downloaded file to {destination}")
        return destination

    def create_folder(self, name: str, parent_id: str) -> str:
        """Create a folder in Google Drive.

        Args:
            name: Name of the folder
            parent_id: ID of the parent folder

        Returns:
            ID of the created folder
        """
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }

        folder = self.service.files().create(body=file_metadata, fields="id").execute()
        logger.info(f"Created folder '{name}' with ID: {folder['id']}")
        return folder["id"]

    def upload_file(
        self, local_path: Path, folder_id: str, filename: Optional[str] = None
    ) -> str:
        """Upload a file to Google Drive.

        Args:
            local_path: Local path to the file
            folder_id: ID of the destination folder
            filename: Optional name for the file (defaults to local filename)

        Returns:
            ID of the uploaded file
        """
        filename = filename or local_path.name

        # Determine mime type
        mime_type = self._get_mime_type(local_path)

        file_metadata = {"name": filename, "parents": [folder_id]}

        media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)

        file = (
            self.service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        logger.info(f"Uploaded '{filename}' with ID: {file['id']}")
        return file["id"]

    def _get_mime_type(self, path: Path) -> str:
        """Get MIME type for a file based on extension."""
        mime_types = {
            ".xml": "application/xml",
            ".srt": "text/plain",
            ".vtt": "text/vtt",
            ".txt": "text/plain",
            ".json": "application/json",
            ".md": "text/markdown",
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".mkv": "video/x-matroska",
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
        }
        return mime_types.get(path.suffix.lower(), "application/octet-stream")

    def get_file_link(self, file_id: str) -> str:
        """Get a shareable link to a file.

        Args:
            file_id: ID of the file

        Returns:
            URL to view the file
        """
        return f"https://drive.google.com/file/d/{file_id}/view"

    def get_folder_link(self, folder_id: str) -> str:
        """Get a shareable link to a folder.

        Args:
            folder_id: ID of the folder

        Returns:
            URL to view the folder
        """
        return f"https://drive.google.com/drive/folders/{folder_id}"
