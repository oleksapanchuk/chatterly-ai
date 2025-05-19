from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class UserReputationLevel(str, Enum):
    EXCELLENT = "EXCELLENT"  # Score > 90
    GOOD = "GOOD"  # Score 70-90
    NEUTRAL = "NEUTRAL"  # Score 40-70
    WARNING = "WARNING"  # Score 20-40
    PROBLEMATIC = "PROBLEMATIC"  # Score < 20


class UserBanStatus(str, Enum):
    NONE = "NONE"
    TEMPORARY = "TEMPORARY"
    PERMANENT = "PERMANENT"


class UserReputation(BaseModel):
    user_id: str = Field(description="Unique identifier for the user")
    reputation_score: float = Field(
        ge=0,
        le=100,
        default=70,
        description="User's reputation score (0-100)"
    )
    reputation_level: UserReputationLevel = Field(
        default=UserReputationLevel.NEUTRAL,
        description="Current reputation level"
    )
    ban_status: UserBanStatus = Field(
        default=UserBanStatus.NONE,
        description="Current ban status"
    )
    ban_end_date: Optional[datetime] = Field(
        default=None,
        description="End date for temporary bans"
    )
    violation_history: List[dict] = Field(
        default_factory=list,
        description="History of content violations"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )
