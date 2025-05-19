import uuid
from typing import List, Optional

from dto.moderation_response import ModerationResponse
from services.audio_service import process_audio_array
from services.image_service import process_image_array
from services.text_service import process_text_array
from shared.validation_types import ContentCategorySeverity


def process_all_content_types(
        text_array: Optional[List[str]],
        image_urls: Optional[List[str]],
        audio_urls: Optional[List[str]],
):
    image_result: list[ModerationResponse] = []

    detected_categories: List[ContentCategorySeverity] = []
    overall_recommendation: str = ""

    if text_array:
        process_text_array(text_array)

    if image_urls:
        image_result = process_image_array(image_urls)

    if audio_urls:
        process_audio_array(audio_urls)

    is_harmful = True
    score = 0.9
    detected_categories.append(ContentCategorySeverity())

    return ModerationResponse(
        request_id=str(uuid.uuid4()),
        is_harmful=is_harmful,
        categories=detected_categories,
        score=score,
        processing_time_ms=0
    )
