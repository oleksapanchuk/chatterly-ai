from enum import Enum
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field
from dataclasses import dataclass
import time

class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"

class ProcessingLayer(Enum):
    LAYER_1_FAST_FILTER = "layer_1_fast_filter"
    LAYER_2_AI_ANALYSIS = "layer_2_ai_analysis"
    LAYER_3_SCORING = "layer_3_scoring"

class HarmCategory(Enum):
    PROFANITY = "profanity"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SEXUAL_CONTENT = "sexual_content"
    HARASSMENT = "harassment"
    SELF_HARM = "self_harm"
    ILLEGAL_ACTIVITY = "illegal_activity"
    SPAM = "spam"
    TOXIC_BEHAVIOR = "toxic_behavior"

class FilterResult(BaseModel):
    is_harmful: bool = False
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    categories: List[HarmCategory] = Field(default_factory=list)
    details: Optional[str] = None
    processing_time_ms: float = 0.0

class Layer1Result(BaseModel):
    content_type: ContentType
    fast_filter_result: FilterResult
    preprocessed_content: Optional[str] = None
    hash_matches: List[str] = Field(default_factory=list)
    banned_words_found: List[str] = Field(default_factory=list)
    transcription: Optional[str] = None

class Layer2Result(BaseModel):
    content_type: ContentType
    ai_analysis_result: FilterResult
    model_used: str
    prompt_used: Optional[str] = None
    raw_response: Optional[str] = None

class Layer3Result(BaseModel):
    overall_harm_score: float = Field(ge=0.0, le=100.0, default=0.0)
    is_harmful: bool = False
    harm_categories: List[HarmCategory] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    layer_scores: Dict[str, float] = Field(default_factory=dict)
    calculation_details: Optional[str] = None

@dataclass
class ContentWeights:
    """Weights for different content types in final scoring"""
    text_weight: float = 0.4
    image_weight: float = 0.35
    audio_weight: float = 0.25
    
    def normalize(self):
        """Ensure weights sum to 1.0"""
        total = self.text_weight + self.image_weight + self.audio_weight
        if total > 0:
            self.text_weight /= total
            self.image_weight /= total
            self.audio_weight /= total

@dataclass
class LayerWeights:
    """Weights for different processing layers"""
    layer1_weight: float = 0.3  # Fast filters
    layer2_weight: float = 0.7  # AI analysis
    
    def normalize(self):
        total = self.layer1_weight + self.layer2_weight
        if total > 0:
            self.layer1_weight /= total
            self.layer2_weight /= total

class ProcessingConfig(BaseModel):
    content_weights: ContentWeights = Field(default_factory=ContentWeights)
    layer_weights: LayerWeights = Field(default_factory=LayerWeights)
    harm_threshold: float = Field(ge=0.0, le=100.0, default=70.0)
    confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.6)
    enable_layer1_fast_filter: bool = True
    enable_layer2_ai_analysis: bool = True
    max_processing_time_ms: float = 30000.0

class EnhancedModerationRequest(BaseModel):
    text_content: Optional[str] = None
    image_urls: Optional[List[str]] = Field(default_factory=list)
    audio_urls: Optional[List[str]] = Field(default_factory=list)
    config: ProcessingConfig = Field(default_factory=ProcessingConfig)
    request_id: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

class EnhancedModerationResponse(BaseModel):
    request_id: Optional[str] = None
    overall_result: Layer3Result
    layer1_results: Dict[ContentType, Layer1Result] = Field(default_factory=dict)
    layer2_results: Dict[ContentType, Layer2Result] = Field(default_factory=dict)
    processing_time_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time) 