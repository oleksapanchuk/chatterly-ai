from pydantic import BaseModel

from content_moderation_service import ContentAnalysisResult


class AudioModerationResult(BaseModel):
    transcribed_text: str
    moderation_result: ContentAnalysisResult
