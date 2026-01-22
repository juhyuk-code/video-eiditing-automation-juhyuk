"""Transcription service using Return Zero (RTZR) API."""

import logging
import time
from pathlib import Path

import httpx

from ..models.transcript import Transcript, Segment, Word

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcription using Return Zero API."""

    def __init__(self, client_id: str, client_secret: str, api_url: str = "https://openapi.vito.ai"):
        """Initialize the transcription service.

        Args:
            client_id: Return Zero client ID
            client_secret: Return Zero client secret
            api_url: Base URL for the API
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = api_url
        self._access_token = None
        self._token_expires_at = 0

    def _get_access_token(self) -> str:
        """Get or refresh the access token."""
        current_time = time.time()

        if self._access_token and current_time < self._token_expires_at - 60:
            return self._access_token

        logger.info("Refreshing Return Zero access token")

        with httpx.Client() as client:
            response = client.post(
                f"{self.api_url}/v1/authenticate",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()

        self._access_token = data["access_token"]
        # Token typically expires in 6 hours, but we'll refresh earlier
        self._token_expires_at = current_time + 3600 * 5

        return self._access_token

    def transcribe(self, audio_path: Path, language: str = "ko") -> Transcript:
        """Transcribe an audio file.

        Args:
            audio_path: Path to the audio file
            language: Primary language code ('ko' or 'en')

        Returns:
            Transcript object with segments and words
        """
        token = self._get_access_token()

        # Upload the file and create transcription job
        logger.info(f"Uploading audio file for transcription: {audio_path}")
        transcribe_id = self._create_transcription(token, audio_path, language)

        # Poll for completion
        logger.info(f"Waiting for transcription to complete (ID: {transcribe_id})")
        result = self._wait_for_completion(token, transcribe_id)

        # Parse the result into our Transcript model
        transcript = self._parse_result(result)

        logger.info(
            f"Transcription complete: {transcript.word_count} words, "
            f"{len(transcript.segments)} segments"
        )

        return transcript

    def _create_transcription(self, token: str, audio_path: Path, language: str) -> str:
        """Create a transcription job.

        Args:
            token: Access token
            audio_path: Path to the audio file
            language: Language code

        Returns:
            Transcription ID
        """
        headers = {"Authorization": f"Bearer {token}"}

        # Configuration for transcription
        config = {
            "use_diarization": False,  # We don't need speaker diarization
            "use_multi_channel": False,
            "model": "sommers",  # Korean-optimized model
        }

        with httpx.Client(timeout=300.0) as client:
            with open(audio_path, "rb") as f:
                response = client.post(
                    f"{self.api_url}/v1/transcribe",
                    headers=headers,
                    data={"config": str(config)},
                    files={"file": (audio_path.name, f, "audio/wav")},
                )
            response.raise_for_status()
            data = response.json()

        return data["id"]

    def _wait_for_completion(
        self, token: str, transcribe_id: str, poll_interval: int = 5, timeout: int = 3600
    ) -> dict:
        """Wait for transcription to complete.

        Args:
            token: Access token
            transcribe_id: ID of the transcription job
            poll_interval: Seconds between status checks
            timeout: Maximum time to wait in seconds

        Returns:
            Transcription result data
        """
        headers = {"Authorization": f"Bearer {token}"}
        start_time = time.time()

        with httpx.Client() as client:
            while True:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Transcription timed out after {timeout}s")

                response = client.get(
                    f"{self.api_url}/v1/transcribe/{transcribe_id}",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                status = data.get("status")

                if status == "completed":
                    return data
                elif status == "failed":
                    raise RuntimeError(f"Transcription failed: {data.get('message', 'Unknown error')}")

                logger.debug(f"Transcription status: {status}")
                time.sleep(poll_interval)

    def _parse_result(self, result: dict) -> Transcript:
        """Parse Return Zero result into Transcript model.

        Args:
            result: Raw API result

        Returns:
            Transcript object
        """
        segments = []
        total_duration = 0
        total_words = 0
        language_durations = {"ko": 0.0, "en": 0.0}

        utterances = result.get("results", {}).get("utterances", [])

        for utterance in utterances:
            words = []
            segment_text_parts = []

            for word_data in utterance.get("words", []):
                word = Word(
                    text=word_data["text"],
                    start=word_data["start_at"] / 1000.0,  # Convert ms to seconds
                    end=word_data["end_at"] / 1000.0,
                    confidence=word_data.get("confidence", 1.0),
                )
                words.append(word)
                segment_text_parts.append(word_data["text"])
                total_words += 1

            if words:
                segment = Segment(
                    text=" ".join(segment_text_parts),
                    start=words[0].start,
                    end=words[-1].end,
                    words=words,
                    language=self._detect_segment_language(segment_text_parts),
                )
                segments.append(segment)

                # Track language duration
                duration = segment.end - segment.start
                if segment.language:
                    language_durations[segment.language] = (
                        language_durations.get(segment.language, 0) + duration
                    )
                total_duration = max(total_duration, segment.end)

        # Calculate language breakdown percentages
        language_breakdown = {}
        if total_duration > 0:
            for lang, duration in language_durations.items():
                percentage = (duration / total_duration) * 100
                if percentage > 0:
                    language_breakdown[lang] = round(percentage, 1)

        return Transcript(
            segments=segments,
            duration=total_duration,
            language_breakdown=language_breakdown,
            word_count=total_words,
        )

    def _detect_segment_language(self, words: list[str]) -> str:
        """Simple language detection based on character ranges.

        Args:
            words: List of words in the segment

        Returns:
            Language code ('ko' or 'en')
        """
        text = " ".join(words)
        korean_chars = sum(1 for c in text if "\uac00" <= c <= "\ud7af" or "\u1100" <= c <= "\u11ff")
        total_alpha = sum(1 for c in text if c.isalpha())

        if total_alpha == 0:
            return "ko"  # Default to Korean

        korean_ratio = korean_chars / total_alpha
        return "ko" if korean_ratio > 0.3 else "en"
