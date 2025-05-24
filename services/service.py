import uuid
from typing import List, Optional

from sympy import true

from dto.moderation_response import ModerationResponse
from services.audio_service import process_audio_array
from services.image_service import process_image_array
from services.scoring_service import ScoringService
from services.text_service import process_text_array
from shared.moderation_result import ModerationResult
from shared.validation_types import ContentCategorySeverity, SeverityLevel
from shared.logger_config import get_logger

logger = get_logger(__name__)
scoring_service = ScoringService()


def process_all_content_types(
        text_array: Optional[List[str]] = [],
        image_urls: Optional[List[str]] = [],
        audio_urls: Optional[List[str]] = [],
        user_id: Optional[str] = None
) -> ModerationResponse:
    """Process all content types and return moderation results with scoring."""
    logger.info("Starting content processing for all types")
    
    text_results = []
    image_results = []
    audio_results = []
    detected_categories: List[ContentCategorySeverity] = []

    if text_array and len(text_array) > 0:
        logger.info(f"Processing {len(text_array)} text items")
        text_results = process_text_array(text_array)
        detected_categories.extend(_convert_text_results_to_categories(text_results))
        logger.info(f"Text processing completed. Found {len(text_results)} results")

    if image_urls and len(image_urls) > 0:
        logger.info(f"Processing {len(image_urls)} image URLs")
        image_results = process_image_array(image_urls)
        detected_categories.extend(_convert_image_results_to_categories(image_results))
        logger.info(f"Image processing completed. Found {len(image_results)} results")

    if audio_urls and len(audio_urls) > 0:
        logger.info(f"Processing {len(audio_urls)} audio URLs")
        audio__text_results = process_audio_array(audio_urls)
        logger.info(f"Audio transcription completed. Found {audio__text_results} results")
        audio_results = process_text_array(audio__text_results, True)
        detected_categories.extend(_convert_text_results_to_categories(audio_results))
        logger.info(f"Audio processing completed. Found {len(audio_results)} results")

    logger.info("Successfully processed all content types")

    # Sort categories by confidence in descending order
    detected_categories.sort(key=lambda x: x.confidence, reverse=True)
    logger.info(f"Sorted {len(detected_categories)} detected categories by confidence")

    # Calculate overall content score
    content_score = scoring_service.calculate_content_score(
        text_results=text_results,
        image_results=image_results,
        audio_results=audio_results
    )
    logger.debug(f"Calculated content score: {content_score}")

    # Determine if content is harmful based on score threshold
    is_harmful = content_score >= 25  # Consider content harmful if score is 25 or higher
    logger.info(f"Content assessment complete. Score: {content_score}, Is harmful: {is_harmful}")

    return ModerationResponse(
        request_id=str(uuid.uuid4()),
        is_harmful=is_harmful,
        categories=detected_categories,
        score=content_score,
        processing_time_ms=0  # This will be updated by the API endpoint
    )


def _convert_text_results_to_categories(results) -> List[ContentCategorySeverity]:
    """Convert text analysis results to ContentCategorySeverity list."""
    logger.debug(f"Converting {len(results)} text results to categories")
    categories = []
    for result in results:
        if result.is_harmful:
            for category in result.categories:
                categories.append(
                    ContentCategorySeverity(
                        category=category,
                        severity=result.severity,
                        confidence=result.confidence.get(category, 0.0),
                        details=result.explanation
                    )
                )
    logger.debug(f"Converted to {len(categories)} category entries")
    return categories


def _convert_image_results_to_categories(results: list[ModerationResult]) -> List[ContentCategorySeverity]:
    logger.debug(f"Converting {len(results)} image results to categories")
    categories = []
    CONFIDENCE_THRESHOLD = 0.7  # Only include categories with 70% or higher confidence
    
    for result in results:
        if result.is_harmful:
            logger.debug(f"Processing harmful image result with score: {result.score}")
            high_confidence_categories = {
                category: score for category, score in result.score.items() if score >= CONFIDENCE_THRESHOLD
            }
            
            for category, score in high_confidence_categories.items():
                categories.append(
                    ContentCategorySeverity(
                        category=category,
                        severity=_get_severity_from_score(score),  # Use confidence score to determine severity
                        confidence=score,
                        details=f"Image content flagged for {category} with {score:.2%} confidence"
                    )
                )
    
    logger.debug(f"Converted to {len(categories)} image category entries")
    return categories


def _get_severity_from_score(score: float) -> SeverityLevel:
    """Convert a score (0-1) to a severity level."""
    if score >= 0.9:
        return SeverityLevel.CRITICAL
    elif score >= 0.7:
        return SeverityLevel.HIGH
    elif score >= 0.4:
        return SeverityLevel.MEDIUM
    elif score >= 0.2:
        return SeverityLevel.LOW
    else:
        return SeverityLevel.NONE
