"""
Enhanced Moderation Service - Main Coordinator
Orchestrates the complete 3-layer moderation pipeline
"""

import time
import asyncio
import os
from typing import Optional, Dict, List
from dotenv import load_dotenv

from shared.enhanced_types import (
    EnhancedModerationRequest, EnhancedModerationResponse,
    ContentType, ProcessingConfig, Layer3Result
)
from services.layer1.fast_filter_service import FastFilterService
from services.layer2.ai_analysis_service import AIAnalysisService
from services.enhanced_scoring_service import EnhancedScoringService

load_dotenv()

class EnhancedModerationService:
    """
    Main moderation service coordinating all three processing layers:
    - Layer 1: Fast pre-filtering (banned words, image hashes, audio transcription)
    - Layer 2: AI-powered analysis (GPT-4o, Omni, enhanced prompts)
    - Layer 3: Mathematical scoring and final decision
    """
    
    def __init__(
        self, 
        openai_api_key: Optional[str] = None,
        deepgram_api_key: Optional[str] = None
    ):
        # Initialize all services
        self.layer1_service = FastFilterService(deepgram_api_key=deepgram_api_key)
        self.layer2_service = AIAnalysisService(openai_api_key=openai_api_key)
        self.layer3_service = EnhancedScoringService()
        
        # Performance tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.error_requests = 0
    
    async def moderate_content(self, request: EnhancedModerationRequest) -> EnhancedModerationResponse:
        """
        Main moderation method - processes content through all three layers
        
        Pipeline:
        1. Layer 1: Fast filtering and preprocessing
        2. Layer 2: AI-powered deep analysis  
        3. Layer 3: Mathematical scoring and final decision
        
        Args:
            request: EnhancedModerationRequest with content and configuration
            
        Returns:
            EnhancedModerationResponse with comprehensive analysis results
        """
        start_time = time.time()
        self.total_requests += 1
        
        errors = []
        warnings = []
        
        try:
            # Validate request
            validation_errors = self._validate_request(request)
            if validation_errors:
                errors.extend(validation_errors)
                return self._create_error_response(request, errors, start_time)
            
            # LAYER 1: Fast filtering
            layer1_results = {}
            if request.config.enable_layer1_fast_filter:
                try:
                    layer1_results = await self.layer1_service.process_content(request)
                except Exception as e:
                    warnings.append(f"Layer 1 processing warning: {str(e)}")
                    layer1_results = {}
            
            # LAYER 2: AI analysis
            layer2_results = {}
            if request.config.enable_layer2_ai_analysis:
                try:
                    layer2_results = await self.layer2_service.process_content(request, layer1_results)
                except Exception as e:
                    warnings.append(f"Layer 2 processing warning: {str(e)}")
                    layer2_results = {}
            
            # LAYER 3: Mathematical scoring
            try:
                layer3_result = self.layer3_service.calculate_comprehensive_score(
                    layer1_results, layer2_results, request.config
                )
            except Exception as e:
                errors.append(f"Layer 3 scoring error: {str(e)}")
                # Create fallback result
                layer3_result = Layer3Result(
                    overall_harm_score=0.0,
                    is_harmful=False,
                    harm_categories=[],
                    confidence=0.0,
                    calculation_details="Error in scoring calculation"
                )
            
            # Create successful response
            processing_time = (time.time() - start_time) * 1000
            self.successful_requests += 1
            
            return EnhancedModerationResponse(
                request_id=request.request_id,
                overall_result=layer3_result,
                layer1_results=layer1_results,
                layer2_results=layer2_results,
                processing_time_ms=processing_time,
                errors=errors,
                warnings=warnings,
                timestamp=time.time()
            )
            
        except Exception as e:
            self.error_requests += 1
            errors.append(f"Critical processing error: {str(e)}")
            return self._create_error_response(request, errors, start_time)
    
    async def moderate_text_only(self, text: str, config: Optional[ProcessingConfig] = None) -> EnhancedModerationResponse:
        """Convenience method for text-only moderation"""
        request = EnhancedModerationRequest(
            text_content=text,
            config=config or ProcessingConfig()
        )
        return await self.moderate_content(request)
    
    async def moderate_image_only(self, image_data: bytes, config: Optional[ProcessingConfig] = None) -> EnhancedModerationResponse:
        """Convenience method for image-only moderation"""
        request = EnhancedModerationRequest(
            image_content=image_data,
            config=config or ProcessingConfig()
        )
        return await self.moderate_content(request)
    
    async def moderate_audio_only(self, audio_data: bytes, config: Optional[ProcessingConfig] = None) -> EnhancedModerationResponse:
        """Convenience method for audio-only moderation"""
        request = EnhancedModerationRequest(
            audio_content=audio_data,
            config=config or ProcessingConfig()
        )
        return await self.moderate_content(request)
    
    async def moderate_multimodal(
        self,
        text: Optional[str] = None,
        image_data: Optional[bytes] = None,
        audio_data: Optional[bytes] = None,
        config: Optional[ProcessingConfig] = None
    ) -> EnhancedModerationResponse:
        """Convenience method for multimodal content moderation"""
        request = EnhancedModerationRequest(
            text_content=text,
            image_content=image_data,
            audio_content=audio_data,
            config=config or ProcessingConfig()
        )
        return await self.moderate_content(request)
    
    def _validate_request(self, request: EnhancedModerationRequest) -> List[str]:
        """Validate moderation request"""
        errors = []
        
        # Check if any content is provided
        if not any([
            request.text_content, 
            request.image_urls and len(request.image_urls) > 0, 
            request.audio_urls and len(request.audio_urls) > 0
        ]):
            errors.append("No content provided for moderation")
        
        # Validate text content
        if request.text_content is not None:
            if len(request.text_content.strip()) == 0:
                errors.append("Text content is empty")
            elif len(request.text_content) > 100000:  # 100KB limit
                errors.append("Text content exceeds maximum length")
        
        # Validate image URLs
        if request.image_urls is not None and len(request.image_urls) > 0:
            if len(request.image_urls) > 10:  # Max 10 images
                errors.append("Too many image URLs (maximum 10)")
            for url in request.image_urls:
                if not url or not isinstance(url, str):
                    errors.append("Invalid image URL format")
                elif not url.startswith(('http://', 'https://')):
                    errors.append(f"Invalid image URL: {url}")
        
        # Validate audio URLs
        if request.audio_urls is not None and len(request.audio_urls) > 0:
            if len(request.audio_urls) > 5:  # Max 5 audio files
                errors.append("Too many audio URLs (maximum 5)")
            for url in request.audio_urls:
                if not url or not isinstance(url, str):
                    errors.append("Invalid audio URL format")
                elif not url.startswith(('http://', 'https://')):
                    errors.append(f"Invalid audio URL: {url}")
        
        # Validate configuration
        if request.config.harm_threshold < 0 or request.config.harm_threshold > 100:
            errors.append("Harm threshold must be between 0 and 100")
        
        if request.config.confidence_threshold < 0 or request.config.confidence_threshold > 1:
            errors.append("Confidence threshold must be between 0 and 1")
        
        return errors
    
    def _create_error_response(
        self, 
        request: EnhancedModerationRequest, 
        errors: List[str], 
        start_time: float
    ) -> EnhancedModerationResponse:
        """Create error response"""
        processing_time = (time.time() - start_time) * 1000
        
        return EnhancedModerationResponse(
            request_id=request.request_id,
            overall_result=Layer3Result(
                overall_harm_score=0.0,
                is_harmful=False,
                harm_categories=[],
                confidence=0.0,
                calculation_details="Processing failed due to errors"
            ),
            layer1_results={},
            layer2_results={},
            processing_time_ms=processing_time,
            errors=errors,
            warnings=[],
            timestamp=time.time()
        )
    
    # Configuration and management methods
    
    def update_banned_words(self, category: str, words: List[str]):
        """Add custom banned words to Layer 1 text filter"""
        self.layer1_service.add_custom_banned_words(category, words)
    
    def add_harmful_image_hash(self, image_hash: str, category, confidence: float = 0.9):
        """Add harmful image hash to Layer 1 detector"""
        self.layer1_service.add_harmful_image_hash(image_hash, category, confidence)
    
    def load_harmful_image_database(self, hash_database: Dict[str, tuple]):
        """Load harmful image hash database"""
        self.layer1_service.load_harmful_image_database(hash_database)
    
    def get_system_health(self) -> Dict[str, any]:
        """Get comprehensive system health status"""
        return {
            "system_status": "operational",
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "error_requests": self.error_requests,
            "success_rate": (self.successful_requests / max(1, self.total_requests)) * 100,
            "layer1_stats": self.layer1_service.get_performance_stats(),
            "layer2_stats": self.layer2_service.get_performance_stats(),
            "layer3_loaded": self.layer3_service is not None,
            "timestamp": time.time()
        }
    
    def get_supported_content_types(self) -> List[str]:
        """Get list of supported content types"""
        return [ContentType.TEXT.value, ContentType.IMAGE.value, ContentType.AUDIO.value]
    
    def get_processing_capabilities(self) -> Dict[str, any]:
        """Get detailed processing capabilities"""
        return {
            "text_processing": {
                "banned_words_detection": True,
                "profanity_filtering": True,
                "gpt_analysis": True,
                "custom_prompts": True,
                "max_length": 100000
            },
            "image_processing": {
                "hash_detection": True,
                "omni_moderation": True,
                "custom_vision_analysis": True,
                "supported_formats": self.layer2_service.omni_service.get_supported_formats(),
                "max_size_mb": 20
            },
            "audio_processing": {
                "transcription": True,
                "deepgram_integration": self.layer1_service.deepgram_client is not None,
                "post_transcription_analysis": True,
                "max_size_mb": 50
            },
            "scoring": {
                "mathematical_model": True,
                "category_weighting": True,
                "confidence_scoring": True,
                "detailed_explanations": True
            }
        }
    
    async def batch_moderate(self, requests: List[EnhancedModerationRequest]) -> List[EnhancedModerationResponse]:
        """Process multiple moderation requests in parallel"""
        if not requests:
            return []
        
        # Process requests in parallel with reasonable concurrency limit
        batch_size = min(len(requests), 10)  # Limit concurrent requests
        
        results = []
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self.moderate_content(req) for req in batch],
                return_exceptions=True
            )
            
            # Handle any exceptions in batch processing
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    error_response = self._create_error_response(
                        batch[j], 
                        [f"Batch processing error: {str(result)}"], 
                        time.time()
                    )
                    results.append(error_response)
                else:
                    results.append(result)
        
        return results 