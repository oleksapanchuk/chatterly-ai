import uuid
from typing import List, Optional

from dto.moderation_response import ModerationResponse
from services.audio_service import process_audio_array
from services.content_decision_service import ContentDecisionService
from services.image_service import process_image_array
from services.improved_scoring_service import ImprovedScoringService
from services.scoring_service import ScoringService
from services.text_service import process_text_array
from shared.action_threshold_config import ActionThresholdConfig
from shared.content_type import ContentType
from shared.gpt_text_analysis_result import GptTextAnalysisResult
from shared.logger_config import get_logger
from shared.moderation_result import ModerationResult
from shared.scoring_configuration import ScoringConfiguration
from shared.validation_types import ContentCategorySeverity, SeverityLevel

logger = get_logger(__name__)

USE_IMPROVED_SCORING = True


def process_all_content_types(
        text_array: Optional[List[str]] = [],
        image_urls: Optional[List[str]] = [],
        audio_urls: Optional[List[str]] = [],
        user_id: Optional[str] = None,
        scoring_config: Optional[ScoringConfiguration] = None,
        action_threshold_config: Optional[ActionThresholdConfig] = None
) -> ModerationResponse:
    """Process all content types and return moderation results with scoring and action decision."""
    logger.info("Starting content processing for all types")

    # Initialize scoring service with custom configuration if provided
    if USE_IMPROVED_SCORING:
        current_scoring_service = ImprovedScoringService(scoring_config)
        logger.info("Using improved probabilistic scoring service")
        if scoring_config:
            logger.info("Using custom scoring configuration")
    else:
        current_scoring_service = ScoringService()
        logger.info("Using legacy severity-based scoring service")
        if scoring_config:
            logger.warning("Custom scoring configuration ignored - legacy scoring service doesn't support it")

    # Initialize decision service with custom thresholds if provided
    decision_service = ContentDecisionService(action_threshold_config)
    if action_threshold_config:
        logger.info("Using custom action threshold configuration")
        logger.debug(f"Custom thresholds: {action_threshold_config.to_dict()}")
    else:
        logger.debug("Using default action threshold configuration")

    text_results = []
    image_results = []
    audio_results = []
    detected_categories: List[ContentCategorySeverity] = []

    if text_array and len(text_array) > 0:
        logger.info(f"Processing {len(text_array)} text items")
        text_results = process_text_array(text_array)
        detected_categories.extend(_convert_text_results_to_categories(text_results, ContentType.TEXT, text_array))
        logger.info(f"Text processing completed. Found {len(text_results)} results")

    if image_urls and len(image_urls) > 0:
        logger.info(f"Processing {len(image_urls)} image URLs")
        image_results = process_image_array(image_urls)
        detected_categories.extend(_convert_image_results_to_categories(image_results, image_urls))
        logger.info(f"Image processing completed. Found {len(image_results)} results")

    if audio_urls and len(audio_urls) > 0:
        logger.info(f"Processing {len(audio_urls)} audio URLs")
        audio_text_results = process_audio_array(audio_urls)
        logger.info(f"Audio transcription completed. Found {len(audio_text_results)} results")
        audio_results = process_text_array(audio_text_results, True)
        detected_categories.extend(_convert_audio_results_to_categories(audio_results, audio_urls))
        logger.info(f"Audio processing completed. Found {len(audio_results)} results")

    logger.info("Successfully processed all content types")

    # Sort categories by confidence in descending order
    detected_categories.sort(key=lambda x: x.confidence, reverse=True)
    logger.info(f"Sorted {len(detected_categories)} detected categories by confidence")

    # Calculate overall content score
    content_score = current_scoring_service.calculate_content_score(
        text_results=text_results,
        image_results=image_results,
        audio_results=audio_results
    )
    logger.debug(f"Calculated content score: {content_score}")

    # Determine action based on score
    action = decision_service.decide_action(content_score)
    logger.info(f"Decision service determined action: {action.value} for score {content_score}")

    # Determine if content is harmful based on score threshold
    is_harmful = content_score >= 25  # Consider content harmful if score is 25 or higher
    logger.info(
        f"Content assessment complete. Score: {content_score}, Is harmful: {is_harmful}, Action: {action.value}")

    return ModerationResponse(
        request_id=str(uuid.uuid4()),
        is_harmful=is_harmful,
        categories=detected_categories,
        score=content_score,
        action=action,
        processing_time_ms=0  # This will be updated by the API endpoint
    )


def _convert_text_results_to_categories(results, content_type: ContentType = ContentType.TEXT,
                                        sources: List[str] = None) -> List[
    ContentCategorySeverity]:
    """Convert text analysis results to ContentCategorySeverity list."""
    logger.debug(f"Converting {len(results)} {content_type} results to categories")
    categories = []
    for i, result in enumerate(results):
        if result.is_harmful:
            source_text = sources[i] if sources and i < len(sources) else None
            for category in result.categories:
                categories.append(
                    ContentCategorySeverity(
                        category=category,
                        severity=result.severity,
                        confidence=result.confidence.get(category, 0.0),
                        details=result.explanation,
                        content_type=content_type,
                        source=source_text
                    )
                )
    logger.debug(f"Converted to {len(categories)} {content_type} category entries")
    return categories


def _convert_image_results_to_categories(results: list[ModerationResult], urls: List[str]) -> List[
    ContentCategorySeverity]:
    logger.debug(f"Converting {len(results)} image results to categories")
    categories = []
    CONFIDENCE_THRESHOLD = 0.7  # Only include categories with 70% or higher confidence

    for i, result in enumerate(results):
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
                        details=f"Image content flagged for {category} with {score:.2%} confidence",
                        content_type=ContentType.IMAGE,
                        source=urls[i] if i < len(urls) else None
                    )
                )

    logger.debug(f"Converted to {len(categories)} image category entries")
    return categories


def _convert_audio_results_to_categories(results: List[GptTextAnalysisResult], urls: List[str]) -> List[
    ContentCategorySeverity]:
    """Convert audio analysis results to ContentCategorySeverity list with URL tracking."""
    logger.debug(f"Converting {len(results)} audio results to categories")
    categories = []
    for i, result in enumerate(results):
        if result.is_harmful:
            for category in result.categories:
                categories.append(
                    ContentCategorySeverity(
                        category=category,
                        severity=result.severity,
                        confidence=result.confidence.get(category, 0.0),
                        details=result.explanation,
                        content_type=ContentType.AUDIO,
                        source=urls[i] if i < len(urls) else None
                    )
                )
    logger.debug(f"Converted to {len(categories)} audio category entries")
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
