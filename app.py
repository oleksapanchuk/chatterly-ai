import time

import uvicorn
from fastapi import FastAPI, HTTPException, Depends

from dto.moderation_request import ModerationRequest
from dto.moderation_response import ModerationResponse
from security.security import verify_salt
from services.service import process_all_content_types
from shared.logger_config import get_logger

app = FastAPI(
    title="Chatterly ~ Content Moderation API",
    description="API for moderating text, audio, and image content",
    version="1.0.0"
)

logger = get_logger(__name__)


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

        scoring_config = request.get_scoring_configuration()
        if scoring_config:
            logger.info("Using custom scoring configuration from request")
            logger.debug(f"Custom scoring config: {scoring_config.to_dict()}")
        else:
            logger.debug("Using default scoring configuration")

        action_threshold_config = request.get_action_threshold_configuration()
        if action_threshold_config:
            logger.info("Using custom action threshold configuration from request")
            logger.debug(f"Custom action thresholds: {action_threshold_config.to_dict()}")
        else:
            logger.debug("Using default action threshold configuration")

        result = process_all_content_types(
            request.text_array,
            request.image_urls,
            request.audio_urls,
            scoring_config=scoring_config,
            action_threshold_config=action_threshold_config
        )

        processing_time = int((time.time() - start_time) * 1000)
        result.processing_time_ms = processing_time

        logger.info(f"Content moderation completed successfully in {processing_time}ms. "
                    f"Score: {result.score}, Action: {result.action.value}, Is harmful: {result.is_harmful}")
        return result

    except Exception as e:
        logger.error(f"Error processing content: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing content: {str(e)}")


if __name__ == "__main__":
    logger.info("Starting Chatterly Content Moderation API...")
    logger.info("Application will be available at http://0.0.0.0:8000")
    logger.info("API documentation will be available at http://0.0.0.0:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000)
