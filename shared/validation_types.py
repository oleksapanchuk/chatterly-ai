from enum import Enum


class ContentCategory(str, Enum):
    HATE_SPEECH = "hate_speech"
    HARASSMENT = "harassment"
    SELF_HARM = "self_harm"
    SEXUAL = "sexual"
    VIOLENCE = "violence"
    MISINFORMATION = "misinformation"
    SPAM = "spam"
    NONE = "none"


class SeverityLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
