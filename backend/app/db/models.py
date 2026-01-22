"""SQLAlchemy database models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    google_id = Column(String(255), unique=True, nullable=False)
    google_access_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    telegram_chat_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    settings = relationship("Settings", back_populates="user", uselist=False)
    jobs = relationship("Job", back_populates="user")


class Settings(Base):
    """User settings model."""

    __tablename__ = "settings"

    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        primary_key=True,
    )

    # Google Drive
    watch_folder_id = Column(String(255), nullable=True)

    # Silence detection
    silence_threshold_db = Column(Float, default=-40.0)
    silence_min_duration = Column(Float, default=0.5)
    silence_padding = Column(Float, default=0.1)

    # Chapter detection
    min_chapter_duration = Column(Integer, default=60)
    max_chapters = Column(Integer, default=20)

    # Notifications
    notify_on_detected = Column(Boolean, default=True)
    notify_on_started = Column(Boolean, default=True)
    notify_on_completed = Column(Boolean, default=True)
    notify_on_failed = Column(Boolean, default=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="settings")


class Job(Base):
    """Processing job model."""

    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    stream_name = Column(String(255), nullable=False)

    # Status
    status = Column(String(50), nullable=False, default="pending")
    current_step = Column(String(100), nullable=True)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Input files
    stream_date = Column(String(8), nullable=False)
    folder_id = Column(String(255), nullable=True)
    stream_file_id = Column(String(255), nullable=True)
    webcam_file_id = Column(String(255), nullable=True)
    screen_file_id = Column(String(255), nullable=True)

    # Duration info
    original_duration = Column(Float, nullable=True)
    final_duration = Column(Float, nullable=True)
    silence_removed = Column(Float, nullable=True)

    # Output info
    output_folder_id = Column(String(255), nullable=True)

    # Results
    chapters_count = Column(Integer, nullable=True)
    chapters_data = Column(JSON, nullable=True)
    title_ideas = Column(JSON, nullable=True)
    thumbnail_concepts = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    # Transcript info
    word_count = Column(Integer, nullable=True)
    language_breakdown = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="jobs")
    logs = relationship("JobLog", back_populates="job")


class JobLog(Base):
    """Job log entry model."""

    __tablename__ = "job_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    job_id = Column(UUID(as_uuid=False), ForeignKey("jobs.id"), nullable=False)
    level = Column(String(20), nullable=False)  # info, warning, error
    step = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="logs")
