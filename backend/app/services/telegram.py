"""Telegram notification service."""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending Telegram notifications."""

    def __init__(self, bot_token: str):
        """Initialize the Telegram service.

        Args:
            bot_token: Telegram bot token
        """
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_preview: bool = True,
    ) -> bool:
        """Send a message to a Telegram chat.

        Args:
            chat_id: Telegram chat ID
            text: Message text (supports HTML formatting)
            parse_mode: Parse mode (HTML or Markdown)
            disable_preview: Whether to disable link previews

        Returns:
            True if message was sent successfully
        """
        if not self.bot_token:
            logger.warning("Telegram bot token not configured, skipping notification")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": disable_preview,
                    },
                )
                response.raise_for_status()
                logger.info(f"Sent Telegram notification to {chat_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False

    def send_message_sync(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_preview: bool = True,
    ) -> bool:
        """Send a message synchronously (for use in Celery workers).

        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Parse mode
            disable_preview: Whether to disable link previews

        Returns:
            True if message was sent successfully
        """
        if not self.bot_token:
            logger.warning("Telegram bot token not configured, skipping notification")
            return False

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": disable_preview,
                    },
                )
                response.raise_for_status()
                logger.info(f"Sent Telegram notification to {chat_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False

    # Pre-formatted message templates

    def format_stream_detected(self, stream_name: str) -> str:
        """Format 'stream detected' notification."""
        return f"""📁 <b>New stream detected!</b>

Stream: <code>{stream_name}</code>
Status: Queued for processing

Processing will begin shortly."""

    def format_processing_started(self, stream_name: str) -> str:
        """Format 'processing started' notification."""
        return f"""🎬 <b>Processing started</b>

Stream: <code>{stream_name}</code>
Started: Just now

You'll be notified when complete."""

    def format_processing_complete(
        self,
        stream_name: str,
        original_duration: str,
        final_duration: str,
        silence_removed: str,
        chapters_count: int,
        title_count: int,
        output_link: str,
        dashboard_link: Optional[str] = None,
    ) -> str:
        """Format 'processing complete' notification."""
        text = f"""✅ <b>Processing complete!</b>

Stream: <code>{stream_name}</code>
Duration: {original_duration} → {final_duration}
Silences removed: {silence_removed}

📺 <b>Results:</b>
• {chapters_count} chapters detected
• {title_count} title ideas generated
• Timeline ready for Premiere import

📂 <a href="{output_link}">View outputs</a>"""

        if dashboard_link:
            text += f"\n\n🔗 <a href=\"{dashboard_link}\">Open dashboard</a>"

        return text

    def format_processing_failed(
        self,
        stream_name: str,
        error_message: str,
        dashboard_link: Optional[str] = None,
    ) -> str:
        """Format 'processing failed' notification."""
        text = f"""❌ <b>Processing failed</b>

Stream: <code>{stream_name}</code>
Error: {error_message}

Please try re-processing or check the logs."""

        if dashboard_link:
            text += f"\n\n🔗 <a href=\"{dashboard_link}\">View details</a>"

        return text

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string (e.g., "1:32:45" or "14:23")
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
