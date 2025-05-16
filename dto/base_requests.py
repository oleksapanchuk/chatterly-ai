from pydantic import BaseModel


class TextRequest(BaseModel):
    text: str


class AudioRequest(BaseModel):
    audio_url: str


class ImageRequest(BaseModel):
    image_url: str
