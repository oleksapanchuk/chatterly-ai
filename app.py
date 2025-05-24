import time

import uvicorn
from fastapi import FastAPI, HTTPException, Depends

from dto.audio_moderation_response import AudioModerationResponse
from dto.base_requests import TextRequest, AudioRequest, ImageRequest
from dto.moderation_request import ModerationRequest
from dto.moderation_response import ModerationResponse
from security.security import verify_salt
from services.audio_transcription.audio_transcription_service import AudioTranscriptionService, TranscriptionResult
from services.service import process_all_content_types
from services.text_service import process_text_array
from shared.gpt_text_analysis_result import GptTextAnalysisResult
from shared.logger_config import get_logger

app = FastAPI(
    title="Chatterly ~ Content Moderation API",
    description="API for moderating text, audio, and image content",
    version="1.0.0"
)

# Setup logger with colored output
logger = get_logger(__name__)

audio_transcription_service = AudioTranscriptionService()


@app.post("/process-text", response_model=GptTextAnalysisResult)
async def process_text(request: TextRequest, salt: str = Depends(verify_salt)):
    logger.info(f"Processing text request with salt verification")
    try:
        logger.debug(f"Text content length: {len(request.text) if request.text else 0}")
        result = process_text_array([request.text])
        logger.info("Text processing completed successfully")
        return result
    except ValueError as e:
        logger.warning(f"Invalid text request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")


@app.post("/process-audio", response_model=TranscriptionResult)
async def process_audio(request: AudioRequest, salt: str = Depends(verify_salt)):
    """
    Process audio content for transcription

    - Transcribes audio from the provided URL using Deepgram API
    - Returns the transcribed text and metadata
    """
    logger.info(f"Processing audio transcription request")
    try:
        logger.debug(f"Audio URL: {request.audio_url}")
        result = audio_transcription_service.transcribe_audio_url(request.audio_url)
        logger.info("Audio transcription completed successfully")
        return result
    except ValueError as e:
        logger.warning(f"Invalid audio request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")


@app.post("/process-audio-moderation", response_model=AudioModerationResponse)
async def process_audio_moderation(request: AudioRequest, salt: str = Depends(verify_salt)):
    logger.info("Processing audio moderation request")
    try:
        logger.debug(f"Audio URL for moderation: {request.audio_url}")
        transcription_result = audio_transcription_service.transcribe_audio_url(request.audio_url)

        if not transcription_result.success:
            logger.error(f"Audio transcription failed: {transcription_result.error}")
            raise HTTPException(status_code=500, detail=f"Error transcribing audio: {transcription_result.error}")

        logger.debug(f"Transcribed text length: {len(transcription_result.text)}")
        moderation_result = process_text_array([transcription_result.text])
        
        logger.info("Audio moderation completed successfully")
        return AudioModerationResponse(
            transcribed_text=transcription_result.text,
            moderation_result=moderation_result
        )
    except ValueError as e:
        logger.warning(f"Invalid audio moderation request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing audio for moderation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing audio for moderation: {str(e)}")


@app.post("/process-image")
async def process_image(request: ImageRequest, salt: str = Depends(verify_salt)):
    logger.warning("Deprecated endpoint /process-image accessed")
    raise HTTPException(status_code=400, detail='Method not supported. Use /moderate-content instead.')


@app.post("/moderate-content", response_model=ModerationResponse)
async def process_image(
        request: ModerationRequest,
        salt: str = Depends(verify_salt)
):
    logger.info("Processing content moderation request")
    try:
        start_time = time.time()
        
        logger.debug(f"Request details - Text array: {len(request.text_array) if request.text_array else 0} items, "
                    f"Image URLs: {len(request.image_urls) if request.image_urls else 0} items, "
                    f"Audio URLs: {len(request.audio_urls) if request.audio_urls else 0} items")

        result = process_all_content_types(
            request.text_array,
            request.image_urls,
            request.audio_urls
        )

        processing_time = int((time.time() - start_time) * 1000)
        result.processing_time_ms = processing_time
        
        logger.info(f"Content moderation completed successfully in {processing_time}ms. Is harmful: {result.is_harmful}")
        return result

    except Exception as e:
        logger.error(f"Error processing content: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing content: {str(e)}")


if __name__ == "__main__":
    logger.info("Starting Chatterly Content Moderation API...")
    logger.info("Application will be available at http://0.0.0.0:8000")
    logger.info("API documentation will be available at http://0.0.0.0:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000)
