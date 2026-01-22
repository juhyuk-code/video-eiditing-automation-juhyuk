"""Job models for processing streams."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job processing status."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING_AUDIO = "processing_audio"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    """Model for creating a new job."""

    stream_date: str = Field(..., description="YYYYMMDD or YYYYMMDD-N format")
    folder_id: str = Field(..., description="Google Drive folder ID")
    stream_file_id: str = Field(..., description="Google Drive stream file ID")
    webcam_file_id: Optional[str] = None
    screen_file_id: Optional[str] = None


class JobUpdate(BaseModel):
    """Model for updating job status."""

    status: Optional[JobStatus] = None
    current_step: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    error_message: Optional[str] = None
    original_duration: Optional[float] = None
    final_duration: Optional[float] = None
    silence_removed: Optional[float] = None
    output_folder_id: Optional[str] = None
    chapters_count: Optional[int] = None
    chapters_data: Optional[list] = None
    title_ideas: Optional[list] = None
    thumbnail_concepts: Optional[list] = None
    tags: Optional[list] = None
    word_count: Optional[int] = None
    language_breakdown: Optional[dict] = None


class Job(BaseModel):
    """Full job model."""

    id: str
    user_id: str
    stream_name: str
    stream_date: str

    # Status
    status: JobStatus = JobStatus.PENDING
    current_step: Optional[str] = None
    progress: int = 0
    error_message: Optional[str] = None

    # Input files
    folder_id: str
    stream_file_id: str
    webcam_file_id: Optional[str] = None
    screen_file_id: Optional[str] = None

    # Duration info
    original_duration: Optional[float] = None
    final_duration: Optional[float] = None
    silence_removed: Optional[float] = None

    # Output info
    output_folder_id: Optional[str] = None

    # Results
    chapters_count: Optional[int] = None
    chapters_data: Optional[list] = None
    title_ideas: Optional[list] = None
    thumbnail_concepts: Optional[list] = None
    tags: Optional[list] = None

    # Transcript info
    word_count: Optional[int] = None
    language_breakdown: Optional[dict] = None

    # Timestamps
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
