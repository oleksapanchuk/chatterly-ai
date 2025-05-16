import os
from typing import Optional

import requests
from dotenv import load_dotenv

from shared.transcription_result import TranscriptionResult

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
MAX_RETRIES = int(os.getenv("AUDIO_TRANSCRIBE_MAX_RETRIES", "2"))


class AudioTranscriptionService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or DEEPGRAM_API_KEY
        if not self.api_key:
            raise ValueError(
                "Deepgram API key is required. Set it as DEEPGRAM_API_KEY environment variable or pass it to the constructor.")

        self.base_url = "https://api.deepgram.com/v1/listen"
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }

    def transcribe_audio_url(self, audio_url: str) -> TranscriptionResult | None:
        """
        Transcribe audio from a URL using Deepgram API

        Args:
            audio_url (str): URL of the audio file to transcribe

        Returns:
            TranscriptionResult: Transcription results

        Raises:
            Exception: If the API call fails after maximum retries
        """
        if not audio_url or not audio_url.strip():
            raise ValueError("Audio URL cannot be empty")

        params = {
            "url": audio_url,
            "model": "general",
            "language": "en,uk",
            "detect_language": True,
            "punctuate": True,
            "diarize": False
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=params
                )

                response.raise_for_status()

                data = response.json()

                results = data.get("results", {})
                channels = results.get("channels", [{}])[0]
                alternatives = channels.get("alternatives", [{}])[0]
                transcript = alternatives.get("transcript", "")
                confidence = alternatives.get("confidence", 0.0)

                # Get metadata
                metadata = results.get("metadata", {})
                duration = metadata.get("duration", 0.0)
                detected_language = metadata.get("detected_language", "unknown")

                return TranscriptionResult(
                    text=transcript,
                    confidence=confidence,
                    language=detected_language,
                    audio_duration=duration,
                    success=True,
                    error=None
                )

            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    print(f"Error transcribing audio: {str(e)}")
                    return TranscriptionResult(
                        text="",
                        confidence=0.0,
                        language="unknown",
                        audio_duration=0.0,
                        success=False,
                        error=f"Failed to transcribe audio: {str(e)}"
                    )
                else:
                    import time
                    print(f"Error transcribing audio: {str(e)}")
                    time.sleep(1)
                    return None

        print("Error transcribing audio: Maximum retries exceeded")
        return None
