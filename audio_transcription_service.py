# --------------------------------------------------------------
# Audio Transcription Service
# --------------------------------------------------------------

import os
import requests
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")  # Requires Deepgram API key
MAX_RETRIES = int(os.getenv("AUDIO_TRANSCRIBE_MAX_RETRIES", "2"))

# --------------------------------------------------------------
# Pydantic Models for Transcription Results
# --------------------------------------------------------------

class TranscriptionResult(BaseModel):
    """Model for transcription results"""
    text: str = Field(description="The transcribed text")
    confidence: float = Field(ge=0, le=1, description="Confidence score for the transcription")
    language: str = Field(description="Detected language of the audio")
    audio_duration: float = Field(description="Duration of the audio in seconds")
    success: bool = Field(description="Whether the transcription was successful")
    error: Optional[str] = Field(None, description="Error message if transcription failed")

# --------------------------------------------------------------
# Audio Transcription Service
# --------------------------------------------------------------

class AudioTranscriptionService:
    """Service for transcribing audio content using Deepgram API"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the audio transcription service"""
        self.api_key = api_key or DEEPGRAM_API_KEY
        if not self.api_key:
            raise ValueError("Deepgram API key is required. Set it as DEEPGRAM_API_KEY environment variable or pass it to the constructor.")

        self.base_url = "https://api.deepgram.com/v1/listen"
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }

    def transcribe_audio_url(self, audio_url: str) -> TranscriptionResult:
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

        # Parameters for Deepgram API
        params = {
            "url": audio_url,
            "model": "general",
            "language": "en,uk",  # Support both English and Ukrainian
            "detect_language": True,
            "punctuate": True,
            "diarize": False
        }

        # Try to transcribe with retries
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=params
                )

                response.raise_for_status()  # Raise exception for HTTP errors

                # Parse the response
                data = response.json()

                # Extract the transcription results
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
                if attempt == MAX_RETRIES - 1:  # Last attempt
                    # Log the error and raise a more user-friendly exception
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
                    # Wait before retrying
                    import time
                    time.sleep(1)  # Simple backoff strategy

# --------------------------------------------------------------
# Usage Example
# --------------------------------------------------------------

def example_usage():
    # Example audio URL to transcribe
    audio_url = "https://example.com/sample-audio.mp3"

    # Create service
    transcription_service = AudioTranscriptionService()

    # Transcribe audio
    result = transcription_service.transcribe_audio_url(audio_url)

    # Print results
    print("Transcription result:")
    print(result.model_dump_json(indent=2))

if __name__ == "__main__":
    example_usage()
