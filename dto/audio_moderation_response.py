from pydantic import BaseModel

from shared.gpt_text_analysis_result import GptTextAnalysisResult


class AudioModerationResponse(BaseModel):
    transcribed_text: str
    moderation_result: GptTextAnalysisResult
