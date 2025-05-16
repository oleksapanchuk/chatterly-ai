from typing import List, Optional

from pydantic import BaseModel, Field

from shared.validation_types import ContentCategory, SeverityLevel


class ModerationResponse(BaseModel):
    request_id: str = Field(description="Unique identifier for the request")
    is_harmful: bool = Field(description="Whether the content contains harmful elements")
    categories: List[ContentCategory] = Field(description="Categories of harmful content detected")
    severity: SeverityLevel = Field(description="Overall severity level of harmful content")
    confidence: float = Field(ge=0, le=1, description="Confidence score for the analysis")
    overall_recommendation: str = Field(description="Overall recommendation for handling the content")
    processing_time_ms: int
