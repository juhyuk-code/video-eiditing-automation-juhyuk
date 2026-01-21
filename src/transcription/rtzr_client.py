"""Return Zero (RTZR) STT API client.

Based on the RTZR STT OpenAPI documentation:
https://developers.rtzr.ai/docs/en/

API Base URL: https://openapi.vito.ai
"""

import asyncio
import os
import time
from pathlib import Path

import httpx

from src.models.transcript import Segment, Transcript, Word


class RTZRClient:
    """Client for Return Zero STT API."""

    BASE_URL = "https://openapi.vito.ai"
    AUTH_ENDPOINT = "/v1/authenticate"
    TRANSCRIBE_ENDPOINT = "/v1/transcribe"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        """Initialize the RTZR client.

        Args:
            client_id: RTZR API client ID (or set RTZR_CLIENT_ID env var).
            client_secret: RTZR API client secret (or set RTZR_CLIENT_SECRET env var).
        """
        self.client_id = client_id or os.environ.get("RTZR_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("RTZR_CLIENT_SECRET", "")

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "RTZR credentials required. Set RTZR_CLIENT_ID and RTZR_CLIENT_SECRET "
                "environment variables or pass them to the constructor."
            )

        self._token: str | None = None
        self._token_expires: float = 0

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        """Get or refresh the JWT token.

        Args:
            client: HTTP client to use.

        Returns:
            Valid JWT token.
        """
        # Return cached token if still valid (with 60s buffer)
        if self._token and time.time() < self._token_expires - 60:
            return self._token

        response = await client.post(
            f"{self.BASE_URL}{self.AUTH_ENDPOINT}",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()

        data = response.json()
        self._token = data["access_token"]
        # Token typically expires in 1 hour
        self._token_expires = time.time() + data.get("expires_in", 3600)

        return self._token

    async def transcribe(
        self,
        audio_path: Path,
        model: str = "sommers",
        language: str = "ko",
        use_word_timestamps: bool = True,
        use_diarization: bool = False,
        progress_callback: callable | None = None,
    ) -> Transcript:
        """Transcribe an audio file.

        Args:
            audio_path: Path to the audio file.
            model: Model to use ('sommers' for Korean, 'whisper' for multilingual).
            language: Language code ('ko' for Korean, 'en' for English).
            use_word_timestamps: Include word-level timestamps.
            use_diarization: Enable speaker diarization.
            progress_callback: Optional callback for progress updates.

        Returns:
            Transcript object with segments and words.

        Raises:
            RuntimeError: If transcription fails.
        """
        async with httpx.AsyncClient(timeout=300.0) as client:
            token = await self._get_token(client)

            # Submit transcription job
            if progress_callback:
                progress_callback("Uploading audio file...")

            with open(audio_path, "rb") as f:
                files = {"file": (audio_path.name, f, "audio/wav")}
                data = {
                    "config": self._build_config(
                        model=model,
                        language=language,
                        use_word_timestamps=use_word_timestamps,
                        use_diarization=use_diarization,
                    ),
                }

                response = await client.post(
                    f"{self.BASE_URL}{self.TRANSCRIBE_ENDPOINT}",
                    headers={"Authorization": f"Bearer {token}"},
                    files=files,
                    data=data,
                )
                response.raise_for_status()

            result = response.json()
            transcribe_id = result["id"]

            if progress_callback:
                progress_callback(f"Transcription job submitted: {transcribe_id}")

            # Poll for completion
            transcript_data = await self._poll_for_completion(
                client, token, transcribe_id, progress_callback
            )

            return self._parse_transcript(transcript_data)

    def _build_config(
        self,
        model: str,
        language: str,
        use_word_timestamps: bool,
        use_diarization: bool,
    ) -> str:
        """Build the config JSON string for the API request."""
        import json

        config = {
            "model_name": model,
            "use_word_timestamp": use_word_timestamps,
            "paragraph_splitter": {"min_interval": 5000},  # 5 seconds
        }

        if use_diarization:
            config["use_diarization"] = True

        return json.dumps(config)

    async def _poll_for_completion(
        self,
        client: httpx.AsyncClient,
        token: str,
        transcribe_id: str,
        progress_callback: callable | None,
        poll_interval: float = 3.0,
        max_wait: float = 7200.0,  # 2 hours max
    ) -> dict:
        """Poll the API until transcription is complete.

        Args:
            client: HTTP client to use.
            token: JWT token.
            transcribe_id: ID of the transcription job.
            progress_callback: Optional callback for progress updates.
            poll_interval: Seconds between polls.
            max_wait: Maximum seconds to wait.

        Returns:
            Transcript data from the API.

        Raises:
            RuntimeError: If transcription fails or times out.
        """
        start_time = time.time()
        status = "transcribing"

        while status in ("transcribing", "queued"):
            if time.time() - start_time > max_wait:
                raise RuntimeError(f"Transcription timed out after {max_wait}s")

            await asyncio.sleep(poll_interval)

            response = await client.get(
                f"{self.BASE_URL}{self.TRANSCRIBE_ENDPOINT}/{transcribe_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()

            data = response.json()
            status = data.get("status", "unknown")

            if progress_callback:
                elapsed = int(time.time() - start_time)
                progress_callback(f"Status: {status} (elapsed: {elapsed}s)")

        if status == "completed":
            return data
        else:
            raise RuntimeError(f"Transcription failed with status: {status}")

    def _parse_transcript(self, data: dict) -> Transcript:
        """Parse API response into Transcript object.

        Args:
            data: API response data.

        Returns:
            Transcript object.
        """
        results = data.get("results", {})
        utterances = results.get("utterances", [])

        segments = []
        total_duration = 0.0
        language_counts = {"ko": 0, "en": 0}

        for utt in utterances:
            start_ms = utt.get("start_at", 0)
            end_ms = utt.get("end_at", start_ms + 1000)
            text = utt.get("msg", "")

            start = start_ms / 1000.0
            end = end_ms / 1000.0
            total_duration = max(total_duration, end)

            # Parse words if available
            words = []
            for word_data in utt.get("words", []):
                word_start = word_data.get("start_at", start_ms) / 1000.0
                word_end = word_data.get("end_at", end_ms) / 1000.0
                word_text = word_data.get("text", "")

                # Detect language (simple heuristic)
                lang = self._detect_word_language(word_text)
                if lang:
                    language_counts[lang] = language_counts.get(lang, 0) + 1

                words.append(
                    Word(
                        text=word_text,
                        start=word_start,
                        end=word_end,
                        confidence=word_data.get("confidence", 1.0),
                        language=lang,
                    )
                )

            # Determine dominant language for segment
            segment_lang = self._detect_segment_language(text)

            segments.append(
                Segment(
                    text=text,
                    start=start,
                    end=end,
                    words=words,
                    language=segment_lang,
                )
            )

        # Calculate language breakdown
        total_words = sum(language_counts.values())
        language_breakdown = {}
        if total_words > 0:
            for lang, count in language_counts.items():
                language_breakdown[lang] = round(count / total_words * 100, 1)

        return Transcript(
            segments=segments,
            duration=total_duration,
            language_breakdown=language_breakdown,
        )

    @staticmethod
    def _detect_word_language(text: str) -> str | None:
        """Simple language detection for a word.

        Args:
            text: Word text.

        Returns:
            'ko' for Korean, 'en' for English, or None.
        """
        # Check for Korean characters (Hangul range)
        for char in text:
            if "\uac00" <= char <= "\ud7af" or "\u1100" <= char <= "\u11ff":
                return "ko"
        # Check for English letters
        if text.isascii() and text.isalpha():
            return "en"
        return None

    @staticmethod
    def _detect_segment_language(text: str) -> str | None:
        """Detect dominant language for a text segment.

        Args:
            text: Segment text.

        Returns:
            'ko' or 'en' based on character majority.
        """
        korean_count = 0
        english_count = 0

        for char in text:
            if "\uac00" <= char <= "\ud7af" or "\u1100" <= char <= "\u11ff":
                korean_count += 1
            elif char.isascii() and char.isalpha():
                english_count += 1

        if korean_count > english_count:
            return "ko"
        elif english_count > korean_count:
            return "en"
        return None


def transcribe_sync(
    audio_path: Path,
    client_id: str | None = None,
    client_secret: str | None = None,
    **kwargs,
) -> Transcript:
    """Synchronous wrapper for transcription.

    Args:
        audio_path: Path to the audio file.
        client_id: RTZR API client ID.
        client_secret: RTZR API client secret.
        **kwargs: Additional arguments for RTZRClient.transcribe().

    Returns:
        Transcript object.
    """
    client = RTZRClient(client_id=client_id, client_secret=client_secret)
    return asyncio.run(client.transcribe(audio_path, **kwargs))
