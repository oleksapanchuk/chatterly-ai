from typing import List

from pydantic import BaseModel

from shared.validation_types import ContentCategory


class ModerationResult(BaseModel):
    is_harmful: bool
    categories: List[str]
    score: dict[ContentCategory, float]
