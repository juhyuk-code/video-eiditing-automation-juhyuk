"""Celery application configuration."""

from celery import Celery

from ..config import get_settings

settings = get_settings()

celery_app = Celery(
    "stream_automation",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.processor", "app.workers.watcher"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600 * 2,  # 2 hour hard limit
    task_soft_time_limit=3600 * 1.5,  # 1.5 hour soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    task_acks_late=True,  # Acknowledge after task completes
)

# Beat schedule for periodic tasks (file watcher)
celery_app.conf.beat_schedule = {
    "watch-for-new-streams": {
        "task": "app.workers.watcher.watch_for_streams",
        "schedule": settings.watcher_interval_seconds,
    },
}
