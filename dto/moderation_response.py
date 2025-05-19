from typing import List

from pydantic import BaseModel, Field

from shared.validation_types import ContentCategorySeverity


class ModerationResponse(BaseModel):
    request_id: str = Field(description="Unique identifier for the request")
    is_harmful: bool = Field(description="Whether the content contains harmful elements")
    categories: List[ContentCategorySeverity] = Field(description="Categories of harmful content detected")
    score: float = Field(ge=0, le=100, description="Harmfulness score for the content")
    processing_time_ms: int
