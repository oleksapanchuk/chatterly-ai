import time
import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from dotenv import load_dotenv

from dto.audio_moderation_response import AudioModerationResponse
from dto.base_requests import TextRequest, AudioRequest, ImageRequest
from dto.moderation_request import ModerationRequest
from dto.moderation_response import ModerationResponse
from security.security import verify_salt
from services.audio_transcription.audio_transcription_service import AudioTranscriptionService, TranscriptionResult
from services.service import process_all_content_types
from services.text_service import process_text_array
from shared.gpt_text_analysis_result import GptTextAnalysisResult

# Нові імпорти для покращеної системи
from shared.enhanced_types import (
    EnhancedModerationRequest, EnhancedModerationResponse, 
    ProcessingConfig, ContentWeights, LayerWeights
)
from services.enhanced_moderation_service import EnhancedModerationService

# Завантаження конфігурації
load_dotenv()

app = FastAPI(
    title="Chatterly ~ Enhanced Content Moderation API",
    description="Advanced 3-layer AI-powered content moderation system",
    version="2.0.0"
)

# Ініціалізація сервісів
audio_transcription_service = AudioTranscriptionService()

# Нова покращена система модерації
enhanced_moderation_service = EnhancedModerationService(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    deepgram_api_key=os.getenv("DEEPGRAM_API_KEY")
)

# === НОВІ ENDPOINTS ДЛЯ ПОКРАЩЕНОЇ СИСТЕМИ ===

@app.post("/v2/moderate", response_model=EnhancedModerationResponse)
async def moderate_content_enhanced(
    request: EnhancedModerationRequest,
    salt: str = Depends(verify_salt)
):
    """
    Головний endpoint для модерації контенту через 3-шарову систему
    
    Підтримує:
    - Текст
    - Масив URL зображень
    - Масив URL аудіо файлів
    
    Повертає детальний аналіз з оцінками всіх шарів
    """
    try:
        # Обробка через покращену систему
        result = await enhanced_moderation_service.moderate_content(request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing content: {str(e)}")

@app.post("/v2/moderate-text", response_model=EnhancedModerationResponse)
async def moderate_text_only(
    text: str,
    harm_threshold: float = 70.0,
    confidence_threshold: float = 0.6,
    salt: str = Depends(verify_salt)
):
    """Спеціалізований endpoint для модерації тільки тексту"""
    try:
        config = ProcessingConfig(
            harm_threshold=harm_threshold,
            confidence_threshold=confidence_threshold
        )
        
        request = EnhancedModerationRequest(
            text_content=text,
            config=config
        )
        
        result = await enhanced_moderation_service.moderate_content(request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.post("/v2/moderate-image", response_model=EnhancedModerationResponse)
async def moderate_image_only(
    image_urls: List[str],
    harm_threshold: float = 70.0,
    salt: str = Depends(verify_salt)
):
    """Спеціалізований endpoint для модерації тільки зображень за URL"""
    try:
        config = ProcessingConfig(harm_threshold=harm_threshold)
        
        request = EnhancedModerationRequest(
            image_urls=image_urls,
            config=config
        )
        
        result = await enhanced_moderation_service.moderate_content(request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing images: {str(e)}")

@app.post("/v2/moderate-audio", response_model=EnhancedModerationResponse)
async def moderate_audio_only(
    audio_urls: List[str],
    harm_threshold: float = 70.0,
    salt: str = Depends(verify_salt)
):
    """Спеціалізований endpoint для модерації тільки аудіо за URL"""
    try:
        config = ProcessingConfig(harm_threshold=harm_threshold)
        
        request = EnhancedModerationRequest(
            audio_urls=audio_urls,
            config=config
        )
        
        result = await enhanced_moderation_service.moderate_content(request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@app.get("/v2/health")
async def get_system_health():
    """Отримати статус здоров'я системи"""
    try:
        health = enhanced_moderation_service.get_system_health()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system health: {str(e)}")

@app.get("/v2/capabilities")
async def get_processing_capabilities():
    """Отримати можливості обробки системи"""
    try:
        capabilities = enhanced_moderation_service.get_processing_capabilities()
        return capabilities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting capabilities: {str(e)}")

# === СТАРІ ENDPOINTS ДЛЯ ЗВОРОТНОЇ СУМІСНОСТІ ===

@app.post("/process-text", response_model=GptTextAnalysisResult)
async def process_text(request: TextRequest, salt: str = Depends(verify_salt)):
    try:
        result = process_text_array([request.text])
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

@app.post("/process-audio-moderation", response_model=AudioModerationResponse)
async def process_audio_moderation(request: AudioRequest, salt: str = Depends(verify_salt)):
    try:
        transcription_result = audio_transcription_service.transcribe_audio_url(request.audio_url)

        if not transcription_result.success:
            raise HTTPException(status_code=500, detail=f"Error transcribing audio: {transcription_result.error}")

        moderation_result = process_text_array([transcription_result.text])

        return AudioModerationResponse(
            transcribed_text=transcription_result.text,
            moderation_result=moderation_result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio for moderation: {str(e)}")

@app.post("/process-image")
async def process_image(request: ImageRequest, salt: str = Depends(verify_salt)):
    raise HTTPException(status_code=400, detail='Method not supported. Use /v2/moderate-image instead.')

@app.post("/moderate-content", response_model=ModerationResponse)
async def process_content_legacy(
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
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run("app:app", host=host, port=port, reload=reload)
