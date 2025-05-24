"""
AI Analysis Service - Layer 2 Coordinator
Orchestrates AI-powered analysis for all content types using enhanced models
"""

import time
import asyncio
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor

from shared.enhanced_types import (
    ContentType, Layer2Result, FilterResult, HarmCategory,
    EnhancedModerationRequest, Layer1Result
)
from .enhanced_gpt_service import EnhancedGptService
from .enhanced_omni_service import EnhancedOmniService

class AIAnalysisService:
    def __init__(self, openai_api_key: Optional[str] = None):
        # Initialize AI services
        self.gpt_service = EnhancedGptService(api_key=openai_api_key)
        self.omni_service = EnhancedOmniService(api_key=openai_api_key)
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    async def process_content(
        self, 
        request: EnhancedModerationRequest,
        layer1_results: Dict[ContentType, Layer1Result]
    ) -> Dict[ContentType, Layer2Result]:
        """
        Process all content types using AI models in parallel
        
        Args:
            request: The moderation request with content
            layer1_results: Results from Layer 1 fast filtering
        
        Returns:
            Dictionary of Layer2Result for each content type
        """
        tasks = []
        content_types = []
        
        # Schedule text analysis
        if request.text_content:
            layer1_data = self._extract_layer1_data(layer1_results.get(ContentType.TEXT))
            tasks.append(self._analyze_text_async(request.text_content, layer1_data))
            content_types.append(ContentType.TEXT)
        
        # Schedule image analysis from URLs
        if request.image_urls and len(request.image_urls) > 0:
            layer1_data = self._extract_layer1_data(layer1_results.get(ContentType.IMAGE))
            tasks.append(self._analyze_images_async(request.image_urls, layer1_data))
            content_types.append(ContentType.IMAGE)
        
        # Schedule audio analysis (via transcription from Layer 1)
        if request.audio_urls and len(request.audio_urls) > 0:
            layer1_data = self._extract_layer1_data(layer1_results.get(ContentType.AUDIO))
            tasks.append(self._analyze_audio_async(layer1_data))
            content_types.append(ContentType.AUDIO)
        
        # Execute all tasks in parallel
        results = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        layer2_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle errors gracefully
                error_result = Layer2Result(
                    content_type=content_types[i],
                    ai_analysis_result=FilterResult(
                        is_harmful=False,
                        confidence=0.0,
                        details=f"AI analysis error: {str(result)}"
                    ),
                    model_used="error",
                    raw_response=str(result)
                )
                layer2_results[content_types[i]] = error_result
            else:
                layer2_results[content_types[i]] = result
        
        return layer2_results
    
    async def _analyze_text_async(self, text_content: str, layer1_data: Optional[Dict]) -> Layer2Result:
        """Analyze text content using enhanced GPT service"""
        loop = asyncio.get_event_loop()
        
        # Run GPT analysis in thread pool
        filter_result = await loop.run_in_executor(
            self.executor,
            self.gpt_service.analyze_text_content,
            text_content,
            layer1_data
        )
        
        return Layer2Result(
            content_type=ContentType.TEXT,
            ai_analysis_result=filter_result,
            model_used="gpt-4o-enhanced",
            prompt_used="Enhanced text moderation with context awareness",
            raw_response=filter_result.details
        )
    
    async def _analyze_images_async(self, image_urls: List[str], layer1_data: Optional[Dict]) -> Layer2Result:
        """Analyze image content using enhanced Omni service"""
        loop = asyncio.get_event_loop()
        
        # Determine sensitivity level based on Layer 1 findings
        sensitivity_level = "standard"
        if layer1_data and layer1_data.get("hash_matches"):
            sensitivity_level = "high_sensitivity"
        elif layer1_data and layer1_data.get("fast_filter_result", {}).get("is_harmful"):
            sensitivity_level = "high_sensitivity"
        
        # Run Omni analysis in thread pool
        filter_result = await loop.run_in_executor(
            self.executor,
            self.omni_service.analyze_images_content,
            image_urls,
            layer1_data,
            sensitivity_level
        )
        
        return Layer2Result(
            content_type=ContentType.IMAGE,
            ai_analysis_result=filter_result,
            model_used="omni-moderation-latest",
            prompt_used=f"Enhanced image moderation with {sensitivity_level} sensitivity",
            raw_response=filter_result.details
        )
    
    async def _analyze_audio_async(self, layer1_data: Optional[Dict]) -> Layer2Result:
        """Analyze audio content via transcription using enhanced GPT service"""
        
        # Extract transcription from Layer 1 results
        transcription = None
        if layer1_data and "transcription" in layer1_data:
            transcription = layer1_data["transcription"]
        
        if not transcription or transcription == "[Audio transcription not available - Deepgram not configured]":
            # No transcription available
            return Layer2Result(
                content_type=ContentType.AUDIO,
                ai_analysis_result=FilterResult(
                    is_harmful=False,
                    confidence=0.0,
                    details="No transcription available for AI analysis"
                ),
                model_used="none",
                prompt_used="N/A",
                raw_response="No transcription available"
            )
        
        loop = asyncio.get_event_loop()
        
        # Run audio transcription analysis in thread pool
        filter_result = await loop.run_in_executor(
            self.executor,
            self.gpt_service.analyze_audio_content,
            transcription,
            layer1_data
        )
        
        return Layer2Result(
            content_type=ContentType.AUDIO,
            ai_analysis_result=filter_result,
            model_used="gpt-4o-audio-enhanced",
            prompt_used="Enhanced audio content analysis with transcription context",
            raw_response=filter_result.details
        )
    
    def _extract_layer1_data(self, layer1_result: Optional[Layer1Result]) -> Optional[Dict]:
        """Extract relevant data from Layer 1 result for Layer 2 processing"""
        if not layer1_result:
            return None
        
        data = {
            "fast_filter_result": {
                "is_harmful": layer1_result.fast_filter_result.is_harmful,
                "confidence": layer1_result.fast_filter_result.confidence,
                "categories": [cat.value for cat in layer1_result.fast_filter_result.categories],
                "details": layer1_result.fast_filter_result.details
            }
        }
        
        # Add content-specific data
        if layer1_result.content_type == ContentType.TEXT:
            data["banned_words_found"] = layer1_result.banned_words_found
            data["preprocessed_content"] = layer1_result.preprocessed_content
        
        elif layer1_result.content_type == ContentType.IMAGE:
            data["hash_matches"] = layer1_result.hash_matches
        
        elif layer1_result.content_type == ContentType.AUDIO:
            data["transcription"] = layer1_result.transcription
        
        return data
    
    async def analyze_with_custom_models(
        self,
        request: EnhancedModerationRequest,
        custom_text_prompt: Optional[str] = None,
        custom_image_prompt: Optional[str] = None
    ) -> Dict[ContentType, Layer2Result]:
        """Analyze content with custom prompts for specialized use cases"""
        
        results = {}
        
        # Custom text analysis
        if request.text_content and custom_text_prompt:
            # You could implement custom text analysis here
            pass
        
        # Custom image analysis
        if request.image_content and custom_image_prompt:
            try:
                filter_result = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.omni_service.analyze_image_with_custom_prompt,
                    request.image_content,
                    custom_image_prompt,
                    None
                )
                
                results[ContentType.IMAGE] = Layer2Result(
                    content_type=ContentType.IMAGE,
                    ai_analysis_result=filter_result,
                    model_used="gpt-4o-vision-custom",
                    prompt_used=custom_image_prompt[:100] + "...",
                    raw_response=filter_result.details
                )
            except Exception as e:
                results[ContentType.IMAGE] = Layer2Result(
                    content_type=ContentType.IMAGE,
                    ai_analysis_result=FilterResult(
                        is_harmful=False,
                        confidence=0.0,
                        details=f"Custom analysis error: {str(e)}"
                    ),
                    model_used="error",
                    raw_response=str(e)
                )
        
        return results
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics for Layer 2 processing"""
        return {
            "gpt_service_loaded": self.gpt_service is not None,
            "omni_service_loaded": self.omni_service is not None,
            "thread_pool_active": not self.executor._shutdown,
            "supported_image_formats": self.omni_service.get_supported_formats(),
            "gpt_model": getattr(self.gpt_service, 'model', 'unknown'),
        }
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False) 