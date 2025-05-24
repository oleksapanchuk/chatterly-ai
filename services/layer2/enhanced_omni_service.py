"""
Enhanced Omni Service for Layer 2 Image Analysis
Improved image moderation using OpenAI's Omni model with enhanced configuration
"""

import os
import time
import base64
from typing import Optional, Dict, List, Union
from io import BytesIO
from dotenv import load_dotenv
from openai import OpenAI
import aiohttp

from shared.enhanced_types import FilterResult, HarmCategory, ContentType

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class EnhancedOmniService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Enhanced sensitivity settings for different content types
        self.sensitivity_configs = {
            "high_sensitivity": {
                "sensitivity_threshold": 0.3,
                "analyze_text_in_image": True,
                "check_nsfw": True,
                "check_violence": True,
                "check_hate_symbols": True,
                "check_self_harm": True,
                "check_harassment": True
            },
            "standard": {
                "sensitivity_threshold": 0.5,
                "analyze_text_in_image": True,
                "check_nsfw": True,
                "check_violence": True,
                "check_hate_symbols": True,
                "check_self_harm": True,
                "check_harassment": True
            },
            "low_sensitivity": {
                "sensitivity_threshold": 0.7,
                "analyze_text_in_image": True,
                "check_nsfw": True,
                "check_violence": True,
                "check_hate_symbols": True,
                "check_self_harm": False,
                "check_harassment": False
            }
        }
        
        # Category mapping from Omni response to our categories
        self.category_mapping = {
            "sexual": HarmCategory.SEXUAL_CONTENT,
            "violence": HarmCategory.VIOLENCE,
            "hate": HarmCategory.HATE_SPEECH,
            "self-harm": HarmCategory.SELF_HARM,
            "harassment": HarmCategory.HARASSMENT,
            "illicit": HarmCategory.ILLEGAL_ACTIVITY
        }
    
    def analyze_image_content(
        self, 
        image_data: bytes, 
        layer1_data: Optional[Dict] = None,
        sensitivity_level: str = "standard"
    ) -> FilterResult:
        """
        Analyze image content using enhanced Omni moderation
        
        Args:
            image_data: Raw image bytes
            layer1_data: Data from Layer 1 analysis (hash matches, etc.)
            sensitivity_level: "high_sensitivity", "standard", or "low_sensitivity"
        """
        start_time = time.time()
        
        try:
            # Convert image bytes to base64 for API
            image_url = self._bytes_to_data_url(image_data)
            
            # Choose sensitivity configuration
            config = self.sensitivity_configs.get(sensitivity_level, self.sensitivity_configs["standard"])
            
            # Adjust sensitivity based on Layer 1 findings
            if layer1_data and layer1_data.get("hash_matches"):
                config = self.sensitivity_configs["high_sensitivity"]
            
            # Prepare input for Omni model
            input_data = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                        "details": config
                    }
                }
            ]
            
            # Call Omni moderation API
            response = self.client.moderations.create(
                model="omni-moderation-latest",
                input=input_data
            )
            
            # Process response
            result = self._process_omni_response(response, layer1_data)
            result.processing_time_ms = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return FilterResult(
                is_harmful=False,
                confidence=0.0,
                details=f"Image analysis error: {str(e)}",
                processing_time_ms=processing_time
            )
    
    def analyze_image_batch(
        self, 
        image_data_list: List[bytes],
        sensitivity_level: str = "standard"
    ) -> List[FilterResult]:
        """Analyze multiple images in batch for efficiency"""
        
        results = []
        for image_data in image_data_list:
            result = self.analyze_image_content(image_data, None, sensitivity_level)
            results.append(result)
        
        return results
    
    def _bytes_to_data_url(self, image_data: bytes) -> str:
        """Convert image bytes to data URL for API"""
        
        # Try to detect image format
        image_format = "jpeg"  # default
        
        # Simple format detection based on magic bytes
        if image_data.startswith(b'\x89PNG'):
            image_format = "png"
        elif image_data.startswith(b'\xFF\xD8\xFF'):
            image_format = "jpeg"
        elif image_data.startswith(b'GIF'):
            image_format = "gif"
        elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:12]:
            image_format = "webp"
        
        # Encode to base64
        base64_string = base64.b64encode(image_data).decode('utf-8')
        
        return f"data:image/{image_format};base64,{base64_string}"
    
    def _process_omni_response(self, response, layer1_data: Optional[Dict] = None) -> FilterResult:
        """Process Omni API response into FilterResult"""
        
        if not response.results:
            return FilterResult(is_harmful=False, confidence=0.0)
        
        result = response.results[0]
        
        categories = []
        confidence_scores = []
        is_harmful = result.flagged
        details_parts = []
        
        # Process flagged categories
        if hasattr(result, 'categories') and result.categories:
            for category_name in dir(result.categories):
                if not category_name.startswith('_'):
                    is_flagged = getattr(result.categories, category_name, False)
                    if is_flagged:
                        mapped_category = self.category_mapping.get(category_name)
                        if mapped_category:
                            categories.append(mapped_category)
        
        # Process category scores for confidence
        if hasattr(result, 'category_scores') and result.category_scores:
            for category_name in dir(result.category_scores):
                if not category_name.startswith('_'):
                    score = getattr(result.category_scores, category_name, 0.0)
                    if score > 0.1:  # Only consider scores above threshold
                        confidence_scores.append(score)
        
        # Add Layer 1 context to details
        if layer1_data:
            if layer1_data.get("hash_matches"):
                details_parts.append(f"Hash matches: {len(layer1_data['hash_matches'])}")
            if layer1_data.get("fast_filter_result"):
                fast_result = layer1_data["fast_filter_result"]
                if fast_result.get("is_harmful"):
                    details_parts.append(f"Layer 1 flagged: {fast_result.get('confidence', 0):.2f}")
        
        # Calculate overall confidence
        if confidence_scores:
            # Use max confidence but also consider number of categories
            base_confidence = max(confidence_scores)
            if len(categories) > 1:
                base_confidence = min(1.0, base_confidence * 1.1)  # Slight boost for multiple categories
            final_confidence = base_confidence
        else:
            final_confidence = 0.7 if is_harmful else 0.0
        
        # Enhanced confidence adjustment based on Layer 1 correlation
        if layer1_data and layer1_data.get("fast_filter_result", {}).get("is_harmful"):
            final_confidence = min(1.0, final_confidence * 1.15)  # Boost if Layer 1 also detected issues
        
        # Create details string
        details = None
        if details_parts:
            details = "; ".join(details_parts)
        elif is_harmful:
            details = f"Omni flagged {len(categories)} categories"
        
        return FilterResult(
            is_harmful=is_harmful,
            confidence=round(final_confidence, 3),
            categories=list(set(categories)),  # Remove duplicates
            details=details
        )
    
    def analyze_image_with_custom_prompt(
        self, 
        image_data: bytes, 
        custom_analysis_prompt: str,
        layer1_data: Optional[Dict] = None
    ) -> FilterResult:
        """
        Analyze image with custom prompt using vision model
        Useful for specialized analysis beyond standard moderation
        """
        start_time = time.time()
        
        try:
            # Convert to data URL
            image_url = self._bytes_to_data_url(image_data)
            
            # Use vision model for custom analysis
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Vision model
                messages=[
                    {
                        "role": "system",
                        "content": custom_analysis_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "Please analyze this image for potentially harmful content."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ]
            )
            
            # Parse custom analysis response
            analysis_text = response.choices[0].message.content
            result = self._parse_custom_analysis(analysis_text)
            result.processing_time_ms = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return FilterResult(
                is_harmful=False,
                confidence=0.0,
                details=f"Custom analysis error: {str(e)}",
                processing_time_ms=processing_time
            )
    
    def _parse_custom_analysis(self, analysis_text: str) -> FilterResult:
        """Parse custom analysis response into FilterResult"""
        
        # Simple parsing - in production you'd want more sophisticated parsing
        is_harmful = any(keyword in analysis_text.lower() for keyword in 
                        ["harmful", "inappropriate", "violation", "concerning", "flagged"])
        
        # Extract categories based on keywords
        categories = []
        for keyword, category in [
            ("sexual", HarmCategory.SEXUAL_CONTENT),
            ("violence", HarmCategory.VIOLENCE),
            ("hate", HarmCategory.HATE_SPEECH),
            ("harassment", HarmCategory.HARASSMENT),
            ("self-harm", HarmCategory.SELF_HARM)
        ]:
            if keyword in analysis_text.lower():
                categories.append(category)
        
        # Estimate confidence based on language strength
        confidence = 0.1
        if "clearly" in analysis_text.lower() or "obviously" in analysis_text.lower():
            confidence = 0.9
        elif "likely" in analysis_text.lower() or "appears" in analysis_text.lower():
            confidence = 0.7
        elif "possibly" in analysis_text.lower() or "might" in analysis_text.lower():
            confidence = 0.4
        elif is_harmful:
            confidence = 0.6
        
        return FilterResult(
            is_harmful=is_harmful,
            confidence=confidence,
            categories=categories,
            details=analysis_text[:300] + "..." if len(analysis_text) > 300 else analysis_text
        )
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats"""
        return ["jpeg", "jpg", "png", "gif", "webp", "bmp"]
    
    def validate_image_size(self, image_data: bytes, max_size_mb: float = 20.0) -> bool:
        """Validate image size is within acceptable limits"""
        size_mb = len(image_data) / (1024 * 1024)
        return size_mb <= max_size_mb

    def analyze_images_content(
        self, 
        image_urls: List[str], 
        layer1_data: Optional[Dict] = None,
        sensitivity_level: str = "standard"
    ) -> FilterResult:
        """
        Analyze multiple images from URLs using enhanced Omni moderation
        
        Args:
            image_urls: List of image URLs
            layer1_data: Data from Layer 1 analysis (hash matches, etc.)
            sensitivity_level: "high_sensitivity", "standard", or "low_sensitivity"
        """
        start_time = time.time()
        
        try:
            # Choose sensitivity configuration
            config = self.sensitivity_configs.get(sensitivity_level, self.sensitivity_configs["standard"])
            
            # Adjust sensitivity based on Layer 1 findings
            if layer1_data and layer1_data.get("hash_matches"):
                config = self.sensitivity_configs["high_sensitivity"]
            
            # Prepare input for Omni model with URLs
            input_data = []
            for url in image_urls:
                input_data.append({
                    "type": "image_url", 
                    "image_url": {
                        "url": url,
                        "details": config
                    }
                })
            
            # Call Omni moderation API
            response = self.client.moderations.create(
                model="omni-moderation-latest",
                input=input_data
            )
            
            # Process response (aggregate results from multiple images)
            result = self._process_omni_multi_response(response, layer1_data, image_urls)
            result.processing_time_ms = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return FilterResult(
                is_harmful=False,
                confidence=0.0,
                details=f"Images analysis error: {str(e)}",
                processing_time_ms=processing_time
            )
    
    def _process_omni_multi_response(self, response, layer1_data: Optional[Dict] = None, image_urls: List[str] = None) -> FilterResult:
        """Process Omni API response for multiple images into aggregated FilterResult"""
        
        if not response.results:
            return FilterResult(is_harmful=False, confidence=0.0)
        
        all_categories = []
        all_confidence_scores = []
        is_any_harmful = False
        details_parts = []
        
        # Process each image result
        for i, result in enumerate(response.results):
            url = image_urls[i] if image_urls and i < len(image_urls) else f"Image {i+1}"
            
            if result.flagged:
                is_any_harmful = True
                details_parts.append(f"{url}: flagged")
            
            # Process flagged categories
            if hasattr(result, 'categories') and result.categories:
                for category_name in dir(result.categories):
                    if not category_name.startswith('_'):
                        is_flagged = getattr(result.categories, category_name, False)
                        if is_flagged:
                            mapped_category = self.category_mapping.get(category_name)
                            if mapped_category:
                                all_categories.append(mapped_category)
            
            # Process category scores
            if hasattr(result, 'category_scores') and result.category_scores:
                for category_name in dir(result.category_scores):
                    if not category_name.startswith('_'):
                        score = getattr(result.category_scores, category_name, 0.0)
                        if score > 0.1:
                            all_confidence_scores.append(score)
        
        # Add Layer 1 context to details
        if layer1_data:
            if layer1_data.get("hash_matches"):
                details_parts.append(f"Hash matches: {len(layer1_data['hash_matches'])}")
            if layer1_data.get("fast_filter_result"):
                fast_result = layer1_data["fast_filter_result"]
                if fast_result.get("is_harmful"):
                    details_parts.append(f"Layer 1 flagged: {fast_result.get('confidence', 0):.2f}")
        
        # Calculate overall confidence
        if all_confidence_scores:
            # Use max confidence but also consider number of categories and images
            base_confidence = max(all_confidence_scores)
            if len(set(all_categories)) > 1:
                base_confidence = min(1.0, base_confidence * 1.1)
            final_confidence = base_confidence
        else:
            final_confidence = 0.7 if is_any_harmful else 0.0
        
        # Enhanced confidence adjustment based on Layer 1 correlation
        if layer1_data and layer1_data.get("fast_filter_result", {}).get("is_harmful"):
            final_confidence = min(1.0, final_confidence * 1.15)
        
        # Create details string
        details = None
        if details_parts:
            details = "; ".join(details_parts)
        elif is_any_harmful:
            details = f"Omni flagged {len(set(all_categories))} categories across {len(response.results)} images"
        
        return FilterResult(
            is_harmful=is_any_harmful,
            confidence=round(final_confidence, 3),
            categories=list(set(all_categories)),  # Remove duplicates
            details=details
        ) 