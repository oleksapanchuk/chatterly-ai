from typing import List

from pydantic import BaseModel, Field

from shared.validation_types import ContentCategory, SeverityLevel


class GptTextAnalysisResult(BaseModel):
    is_harmful: bool = Field(description="Whether the content contains harmful elements")
    categories: List[ContentCategory] = Field(description="Categories of harmful content detected")
    severity: SeverityLevel = Field(description="Overall severity level of harmful content")
    confidence: dict[ContentCategory, float] = Field(description="Confidence score for each category")
    flagged_segments: List[str] = Field(default=[], description="Specific segments of text that were flagged")
    recommendation: str = Field(description="Recommendation for handling the content")
    explanation: str = Field(description="Explanation of why the content was flagged or not")
