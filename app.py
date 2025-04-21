# --------------------------------------------------------------
# Content Moderation API Server
# --------------------------------------------------------------

import os
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional
from content_moderation_service import ContentModerationService, ContentAnalysisResult
from audio_transcription_service import AudioTranscriptionService, TranscriptionResult
from image_processing_service import ImageProcessingService, ImageProcessingResult

# Initialize FastAPI app
app = FastAPI(
    title="Content Moderation API",
    description="API for moderating text, audio, and image content",
    version="1.0.0"
)

# Initialize services
content_moderation_service = ContentModerationService()
audio_transcription_service = AudioTranscriptionService()
image_processing_service = ImageProcessingService()

# Environment variables
API_SALT = os.getenv("API_SALT", "default_salt")  # Salt for API protection

# --------------------------------------------------------------
# Request and Response Models
# --------------------------------------------------------------

class TextRequest(BaseModel):
    """Request model for text content"""
    text: str

class AudioRequest(BaseModel):
    """Request model for audio content"""
    audio_url: str

class ImageRequest(BaseModel):
    """Request model for image content"""
    image_url: str

class AudioModerationResult(BaseModel):
    """Response model for audio moderation"""
    transcribed_text: str
    moderation_result: ContentAnalysisResult

# --------------------------------------------------------------
# Security Dependencies
# --------------------------------------------------------------

def verify_salt(x_api_salt: Optional[str] = Header(None)):
    """Verify the API salt to protect from abuse"""
    if API_SALT != "default_salt" and (not x_api_salt or x_api_salt != API_SALT):
        raise HTTPException(status_code=403, detail="Invalid API salt")
    return x_api_salt

# --------------------------------------------------------------
# API Endpoints
# --------------------------------------------------------------

@app.post("/process-text", response_model=ContentAnalysisResult)
async def process_text(request: TextRequest, salt: str = Depends(verify_salt)):
    """
    Process and moderate text content

    - Analyzes text for harmful content
    - Returns detailed analysis results
    """
    try:
        result = content_moderation_service.analyze_content(request.text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.post("/process-audio", response_model=TranscriptionResult)
async def process_audio(request: AudioRequest, salt: str = Depends(verify_salt)):
    """
    Process audio content for transcription

    - Transcribes audio from the provided URL using Deepgram API
    - Returns the transcribed text and metadata
    """
    try:
        result = audio_transcription_service.transcribe_audio_url(request.audio_url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@app.post("/process-audio-moderation", response_model=AudioModerationResult)
async def process_audio_moderation(request: AudioRequest, salt: str = Depends(verify_salt)):
    """
    Process audio content for transcription and content moderation

    - Transcribes audio from the provided URL
    - Analyzes the transcribed text for harmful content
    - Returns both the transcribed text and moderation results
    """
    try:
        # Step 1: Transcribe the audio
        transcription_result = audio_transcription_service.transcribe_audio_url(request.audio_url)

        if not transcription_result.success:
            raise HTTPException(status_code=500, detail=f"Error transcribing audio: {transcription_result.error}")

        # Step 2: Analyze the transcribed text
        moderation_result = content_moderation_service.analyze_content(transcription_result.text)

        # Step 3: Return combined result
        return AudioModerationResult(
            transcribed_text=transcription_result.text,
            moderation_result=moderation_result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio for moderation: {str(e)}")

@app.post("/process-image", response_model=ImageProcessingResult)
async def process_image(request: ImageRequest, salt: str = Depends(verify_salt)):
    """
    Process and moderate image content

    - Downloads the image from the provided URL
    - Generates a detailed description of the image
    - Analyzes the description for harmful content
    - Returns both the description and moderation results
    """
    try:
        # Process the image and get moderation results
        result = image_processing_service.process_image_url(request.image_url)

        if not result.success:
            raise HTTPException(status_code=500, detail=f"Error processing image: {result.error}")

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# --------------------------------------------------------------
# Server Startup
# --------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
