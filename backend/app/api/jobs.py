"""Jobs API routes."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..db.database import get_db
from ..db.models import User, Job
from ..models.job import JobStatus

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(
    user_id: str,  # In production, from session/JWT
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all jobs for the user."""
    query = select(Job).where(Job.user_id == user_id)

    if status:
        query = query.where(Job.status == status)

    query = query.order_by(desc(Job.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return {
        "jobs": [
            {
                "id": job.id,
                "stream_name": job.stream_name,
                "stream_date": job.stream_date,
                "status": job.status,
                "progress": job.progress,
                "original_duration": job.original_duration,
                "final_duration": job.final_duration,
                "silence_removed": job.silence_removed,
                "chapters_count": job.chapters_count,
                "created_at": job.created_at,
                "completed_at": job.completed_at,
            }
            for job in jobs
        ],
        "total": len(jobs),
        "limit": limit,
        "offset": offset,
    }


@router.get("/current")
async def get_current_job(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get currently processing job."""
    result = await db.execute(
        select(Job)
        .where(Job.user_id == user_id)
        .where(Job.status.not_in([JobStatus.COMPLETED.value, JobStatus.FAILED.value]))
        .order_by(desc(Job.created_at))
        .limit(1)
    )
    job = result.scalar_one_or_none()

    if not job:
        return {"job": None}

    return {
        "job": {
            "id": job.id,
            "stream_name": job.stream_name,
            "status": job.status,
            "current_step": job.current_step,
            "progress": job.progress,
            "started_at": job.started_at,
        }
    }


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get job details."""
    result = await db.execute(
        select(Job).where(Job.id == job_id).where(Job.user_id == user_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job.id,
        "stream_name": job.stream_name,
        "stream_date": job.stream_date,
        "status": job.status,
        "current_step": job.current_step,
        "progress": job.progress,
        "error_message": job.error_message,
        "original_duration": job.original_duration,
        "final_duration": job.final_duration,
        "silence_removed": job.silence_removed,
        "output_folder_id": job.output_folder_id,
        "chapters_count": job.chapters_count,
        "chapters_data": job.chapters_data,
        "title_ideas": job.title_ideas,
        "thumbnail_concepts": job.thumbnail_concepts,
        "tags": job.tags,
        "word_count": job.word_count,
        "language_breakdown": job.language_breakdown,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
    }


@router.post("/{job_id}/reprocess")
async def reprocess_job(
    job_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Re-process a job."""
    result = await db.execute(
        select(Job).where(Job.id == job_id).where(Job.user_id == user_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get user credentials
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user or not user.google_access_token:
        raise HTTPException(status_code=400, detail="Google account not connected")

    # Queue new processing task
    from ..workers.processor import process_stream
    import uuid

    new_job_id = str(uuid.uuid4())

    process_stream.delay(
        job_id=new_job_id,
        stream_date=job.stream_date,
        folder_id=job.folder_id,
        stream_file_id=job.stream_file_id,
        google_credentials={
            "token": user.google_access_token,
            "refresh_token": user.google_refresh_token,
        },
        telegram_chat_id=user.telegram_chat_id,
        webcam_file_id=job.webcam_file_id,
        screen_file_id=job.screen_file_id,
    )

    # Create new job record
    new_job = Job(
        id=new_job_id,
        user_id=user_id,
        stream_name=job.stream_name,
        stream_date=job.stream_date,
        folder_id=job.folder_id,
        stream_file_id=job.stream_file_id,
        webcam_file_id=job.webcam_file_id,
        screen_file_id=job.screen_file_id,
        status=JobStatus.PENDING.value,
    )
    db.add(new_job)
    await db.commit()

    return {
        "message": "Job queued for re-processing",
        "new_job_id": new_job_id,
    }


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a job record."""
    result = await db.execute(
        select(Job).where(Job.id == job_id).where(Job.user_id == user_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await db.delete(job)
    await db.commit()

    return {"message": "Job deleted successfully"}
