from typing import Optional

from pydantic import BaseModel, Field


class TranscriptionResult(BaseModel):
    text: str = Field(description="The transcribed text")
    confidence: float = Field(ge=0, le=1, description="Confidence score for the transcription")
    language: str = Field(description="Detected language of the audio")
    audio_duration: float = Field(description="Duration of the audio in seconds")
    success: bool = Field(description="Whether the transcription was successful")
    error: Optional[str] = Field(None, description="Error message if transcription failed")
