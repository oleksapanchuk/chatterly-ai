from typing import List

from sympy import false

from services.gpt_moderation.prompts import prompt_for_text, prompt_for_audio
from services.gpt_moderation.text_moderation import GptModerationService
from shared.gpt_text_analysis_result import GptTextAnalysisResult
from shared.logger_config import get_logger

logger = get_logger(__name__)
gpt_moderation_service = GptModerationService()


def process_text_array(array: List[str], is_audio: bool = false) -> list[GptTextAnalysisResult]:
    logger.info(f"Processing text array with {len(array)} items")
    gpt_moderation_result: list[GptTextAnalysisResult] = []

    system_prompt = prompt_for_audio if is_audio else prompt_for_text

    for i, text in enumerate(array):
        result = gpt_moderation_service.analyze_content(text, system_prompt)
        gpt_moderation_result.append(result)

    logger.info(f"Completed text processing. {len(gpt_moderation_result)} results generated")
    return gpt_moderation_result
