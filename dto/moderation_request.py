from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field
from shared.scoring_configuration import ScoringConfiguration


class ModerationRequest(BaseModel):
    text_array: Optional[List[str]] = Field(default=None, description="List of text content to moderate")
    image_urls: Optional[List[str]] = Field(default=None, description="List of image URLs to moderate")
    audio_urls: Optional[List[str]] = Field(default=None, description="List of audio URLs to moderate")
    scoring_config: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Optional custom scoring configuration. If not provided, default values will be used."
    )

    def get_scoring_configuration(self) -> Optional[ScoringConfiguration]:
        """Convert scoring_config dict to ScoringConfiguration object."""
        if not self.scoring_config:
            return None
        try:
            return ScoringConfiguration.from_dict(self.scoring_config)
        except Exception as e:
            # If configuration is invalid, return None to use defaults
            return None

    class Config:
        json_schema_extra = {
            "example": {
                "text_array": ["Sample text to moderate", "Another sample text to moderate"],
                "image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
                "audio_urls": ["https://example.com/audio1.mp3"],
                "scoring_config": {
                    "category_base_risk": {
                        "HATE_SPEECH": 90,
                        "HARASSMENT": 80,
                        "VIOLENCE": 85,
                        "SELF_HARM": 95,
                        "SEXUAL": 65,
                        "MISINFORMATION": 50,
                        "SPAM": 30
                    },
                    "content_type_modifiers": {
                        "text": 0,
                        "image": 15,
                        "audio": 8
                    }
                }
            }
        }
