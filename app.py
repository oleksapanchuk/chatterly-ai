import time

from fastapi import FastAPI, HTTPException, Depends

from content_moderation_service import ContentModerationService, ContentAnalysisResult
from dto.audio_moderation_result import AudioModerationResult
from dto.base_requests import TextRequest, AudioRequest, ImageRequest
from dto.moderation_request import ModerationRequest
from dto.moderation_response import ModerationResponse
from security.security import verify_salt
from services.audio_transcription.audio_transcription_service import AudioTranscriptionService, TranscriptionResult
from services.service import process_all_content_types

app = FastAPI(
    title="Chatterly ~ Content Moderation API",
    description="API for moderating text, audio, and image content",
    version="1.0.0"
)

content_moderation_service = ContentModerationService()
audio_transcription_service = AudioTranscriptionService()


@app.post("/process-text", response_model=ContentAnalysisResult)
async def process_text(request: TextRequest, salt: str = Depends(verify_salt)):
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
    try:
        transcription_result = audio_transcription_service.transcribe_audio_url(request.audio_url)

        if not transcription_result.success:
            raise HTTPException(status_code=500, detail=f"Error transcribing audio: {transcription_result.error}")

        moderation_result = content_moderation_service.analyze_content(transcription_result.text)

        return AudioModerationResult(
            transcribed_text=transcription_result.text,
            moderation_result=moderation_result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio for moderation: {str(e)}")


@app.post("/process-image")
async def process_image(request: ImageRequest, salt: str = Depends(verify_salt)):
    raise HTTPException(status_code=400, detail='Method not supported. Use /moderate-content instead.')


@app.post("/moderate-content", response_model=ModerationResponse)
async def process_image(
        request: ModerationRequest,
        salt: str = Depends(verify_salt)
):
    try:
        start_time = time.time()

        result = process_all_content_types(
            request.text_array,
            request.image_urls,
            request.audio_urls
        )

        result.processing_time_ms = int((time.time() - start_time) * 1000)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing content: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
