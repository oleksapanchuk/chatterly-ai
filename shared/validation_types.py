from enum import Enum
from typing import Optional

from pydantic import BaseModel

from shared.content_type import ContentType


class ContentCategory(str, Enum):
    HATE_SPEECH = "HATE_SPEECH"
    HARASSMENT = "HARASSMENT"
    SELF_HARM = "SELF_HARM"
    SEXUAL = "SEXUAL"
    VIOLENCE = "VIOLENCE"
    MISINFORMATION = "MISINFORMATION"
    SPAM = "SPAM"
    NONE = "NONE"


class SeverityLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ContentCategorySeverity(BaseModel):
    category: ContentCategory = ContentCategory.NONE
    severity: SeverityLevel = SeverityLevel.NONE
    confidence: float = 0.0
    details: Optional[str] = ""
    content_type: Optional[ContentType] = ContentType.UNKNOWN
    source: Optional[str] = None
