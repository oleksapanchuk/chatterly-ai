from typing import Optional, List

from pydantic import BaseModel, Field


class ModerationRequest(BaseModel):
    text_array: Optional[List[str]] = Field(default=None, description="List of text content to moderate")
    image_urls: Optional[List[str]] = Field(default=None, description="List of image URLs to moderate")
    audio_urls: Optional[List[str]] = Field(default=None, description="List of audio URLs to moderate")

    class Config:
        schema_extra = {
            "example": {
                "text_array": ["Sample text to moderate", "Another sample text to moderate"],
                "image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
                "audio_urls": ["https://example.com/audio1.mp3"]
            }
        }
