from typing import List

from pydantic import BaseModel, Field

from shared.validation_types import ContentCategorySeverity
from shared.content_action import ContentAction


class ModerationResponse(BaseModel):
    request_id: str = Field(..., description="Unique identifier for this moderation request")
    is_harmful: bool = Field(..., description="Whether the content contains harmful material")
    categories: List[ContentCategorySeverity] = Field(default=[], description="List of detected harmful categories")
    score: float = Field(..., description="Overall content moderation score (0-100)")
    action: ContentAction = Field(..., description="Recommended action based on the score")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
