from typing import List

from services.gpt_moderation.text_moderation import GptModerationService
from shared.gpt_text_analysis_result import GptTextAnalysisResult

gpt_moderation_service = GptModerationService()


def process_text_array(array: List[str]) -> list[GptTextAnalysisResult]:
    gpt_moderation_result: list[GptTextAnalysisResult] = []

    for text in array:
        gpt_moderation_result.append(gpt_moderation_service.analyze_content(text))
        print(
            f"\nModeration result for text: {text} is: {gpt_moderation_result}"
        )

    return gpt_moderation_result
