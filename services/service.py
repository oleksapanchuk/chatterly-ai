import uuid
from typing import List, Optional

from dto.moderation_response import ModerationResponse
from services.audio_service import process_audio_array
from services.image_service import process_image_array
from services.text_service import process_text_array
from shared.validation_types import ContentCategory, SeverityLevel


def process_all_content_types(
        text_array: Optional[List[str]],
        image_urls: Optional[List[str]],
        audio_urls: Optional[List[str]],
):
    is_harmful: bool = False
    calculated_confidence: float = 0.0
    severity_level: SeverityLevel = SeverityLevel.NONE
    detected_categories: List[ContentCategory] = []
    overall_recommendation: str = ""

    if text_array:
        process_text_array(text_array)

    if image_urls:
        process_image_array(image_urls)

    if audio_urls:
        process_audio_array(audio_urls)

    is_harmful = True
    calculated_confidence = 0.9
    severity_level = SeverityLevel.LOW
    detected_categories.append(ContentCategory.SEXUAL)
    overall_recommendation = "Content appears harmful"

    return ModerationResponse(
        request_id=str(uuid.uuid4()),
        is_harmful=is_harmful,
        categories=detected_categories,
        confidence=calculated_confidence,
        severity=severity_level,
        overall_recommendation=overall_recommendation,
        processing_time_ms=0
    )
