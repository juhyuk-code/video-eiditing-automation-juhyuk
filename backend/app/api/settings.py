"""Settings API routes."""

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db.database import get_db
from ..db.models import User, Settings as SettingsModel

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    """Settings update request."""

    watch_folder_id: Optional[str] = None
    silence_threshold_db: Optional[float] = None
    silence_min_duration: Optional[float] = None
    silence_padding: Optional[float] = None
    min_chapter_duration: Optional[int] = None
    max_chapters: Optional[int] = None
    notify_on_detected: Optional[bool] = None
    notify_on_started: Optional[bool] = None
    notify_on_completed: Optional[bool] = None
    notify_on_failed: Optional[bool] = None


class TelegramConnect(BaseModel):
    """Telegram connection request."""

    chat_id: str


@router.get("")
async def get_settings(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get user settings."""
    result = await db.execute(
        select(SettingsModel).where(SettingsModel.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Get user for telegram status
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    return {
        "watch_folder_id": settings.watch_folder_id,
        "silence_threshold_db": settings.silence_threshold_db,
        "silence_min_duration": settings.silence_min_duration,
        "silence_padding": settings.silence_padding,
        "min_chapter_duration": settings.min_chapter_duration,
        "max_chapters": settings.max_chapters,
        "notify_on_detected": settings.notify_on_detected,
        "notify_on_started": settings.notify_on_started,
        "notify_on_completed": settings.notify_on_completed,
        "notify_on_failed": settings.notify_on_failed,
        "telegram_connected": user.telegram_chat_id is not None if user else False,
        "telegram_chat_id": user.telegram_chat_id if user else None,
    }


@router.put("")
async def update_settings(
    user_id: str,
    updates: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update user settings."""
    result = await db.execute(
        select(SettingsModel).where(SettingsModel.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.commit()

    return {"message": "Settings updated successfully"}


@router.post("/telegram/connect")
async def connect_telegram(
    user_id: str,
    data: TelegramConnect,
    db: AsyncSession = Depends(get_db),
):
    """Connect Telegram for notifications."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.telegram_chat_id = data.chat_id
    await db.commit()

    # Send test message
    from ..services.telegram import TelegramService
    from ..config import get_settings

    settings = get_settings()
    telegram = TelegramService(settings.telegram_bot_token)

    success = telegram.send_message_sync(
        data.chat_id,
        "🎉 <b>Stream Automation connected!</b>\n\nYou'll receive notifications when streams are detected and processed.",
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to send test message")

    return {"message": "Telegram connected successfully"}


@router.delete("/telegram/disconnect")
async def disconnect_telegram(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Telegram."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.telegram_chat_id = None
    await db.commit()

    return {"message": "Telegram disconnected successfully"}


@router.post("/telegram/test")
async def test_telegram(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Send a test Telegram notification."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.telegram_chat_id:
        raise HTTPException(status_code=400, detail="Telegram not connected")

    from ..services.telegram import TelegramService
    from ..config import get_settings

    settings = get_settings()
    telegram = TelegramService(settings.telegram_bot_token)

    success = telegram.send_message_sync(
        user.telegram_chat_id,
        "🧪 <b>Test notification</b>\n\nIf you see this, notifications are working!",
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send test message")

    return {"message": "Test notification sent"}
