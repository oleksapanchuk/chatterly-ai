from typing import List

from services.gpt_moderation.text_moderation import GptModerationService
from shared.gpt_text_analysis_result import GptTextAnalysisResult
from shared.logger_config import get_logger

logger = get_logger(__name__)
gpt_moderation_service = GptModerationService()


def process_text_array(array: List[str]) -> list[GptTextAnalysisResult]:
    logger.info(f"Processing text array with {len(array)} items")
    gpt_moderation_result: list[GptTextAnalysisResult] = []

    for i, text in enumerate(array):
        logger.debug(f"Processing text item {i + 1}/{len(array)}: {text[:100]}{'...' if len(text) > 100 else ''}")
        result = gpt_moderation_service.analyze_content(text)
        gpt_moderation_result.append(result)
        logger.debug(f"Text moderation result - Is harmful: {result.is_harmful}, Categories: {result.categories}")

    logger.info(f"Completed text processing. {len(gpt_moderation_result)} results generated")
    return gpt_moderation_result
