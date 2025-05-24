"""
Fast Filter Service - Layer 1 Coordinator
Orchestrates fast pre-filtering for all content types
"""

import time
import asyncio
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor
import io
import aiohttp

from shared.enhanced_types import (
    ContentType, Layer1Result, FilterResult, HarmCategory,
    EnhancedModerationRequest, ProcessingConfig
)
from .fast_text_filter import FastTextFilter
from .image_hash_detector import ImageHashDetector

# Audio transcription import
try:
    import deepgram
    from deepgram import DeepgramClient, PrerecordedOptions, FileSource
    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False

class FastFilterService:
    def __init__(self, deepgram_api_key: Optional[str] = None):
        # Initialize filters
        self.text_filter = FastTextFilter()
        self.image_detector = ImageHashDetector()
        
        # Audio transcription setup
        self.deepgram_client = None
        if DEEPGRAM_AVAILABLE and deepgram_api_key:
            try:
                self.deepgram_client = DeepgramClient(deepgram_api_key)
            except Exception as e:
                print(f"Warning: Could not initialize Deepgram client: {e}")
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    async def process_content(self, request: EnhancedModerationRequest) -> Dict[ContentType, Layer1Result]:
        """
        Process all content types in parallel using fast filters
        Returns Layer1Result for each content type present
        """
        tasks = []
        content_types = []
        
        # Schedule text processing
        if request.text_content:
            tasks.append(self._process_text_async(request.text_content))
            content_types.append(ContentType.TEXT)
        
        # Schedule image processing from URLs
        if request.image_urls and len(request.image_urls) > 0:
            tasks.append(self._process_images_async(request.image_urls))
            content_types.append(ContentType.IMAGE)
        
        # Schedule audio processing from URLs
        if request.audio_urls and len(request.audio_urls) > 0:
            tasks.append(self._process_audios_async(request.audio_urls))
            content_types.append(ContentType.AUDIO)
        
        # Execute all tasks in parallel
        results = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        layer1_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle errors gracefully
                error_result = Layer1Result(
                    content_type=content_types[i],
                    fast_filter_result=FilterResult(
                        is_harmful=False,
                        confidence=0.0,
                        details=f"Processing error: {str(result)}"
                    )
                )
                layer1_results[content_types[i]] = error_result
            else:
                layer1_results[content_types[i]] = result
        
        return layer1_results
    
    async def _process_text_async(self, text_content: str) -> Layer1Result:
        """Process text content asynchronously"""
        loop = asyncio.get_event_loop()
        
        # Run text filtering in thread pool
        filter_result = await loop.run_in_executor(
            self.executor, 
            self.text_filter.filter_text, 
            text_content
        )
        
        # Extract banned words for reporting
        banned_words = []
        if filter_result.details and "Banned words found:" in filter_result.details:
            words_part = filter_result.details.split("Banned words found: ")[1]
            banned_words = [word.strip() for word in words_part.split(",")]
        
        return Layer1Result(
            content_type=ContentType.TEXT,
            fast_filter_result=filter_result,
            preprocessed_content=self._preprocess_text(text_content),
            banned_words_found=banned_words
        )
    
    async def _process_image_async(self, image_content: bytes) -> Layer1Result:
        """Process image content asynchronously"""
        loop = asyncio.get_event_loop()
        
        # Run image analysis in thread pool
        filter_result = await loop.run_in_executor(
            self.executor,
            self.image_detector.analyze_image,
            image_content
        )
        
        # Get hash matches for reporting
        hash_matches = []
        if filter_result.details and "Hash matches found:" in filter_result.details:
            matches_part = filter_result.details.split("Hash matches found: ")[1]
            hash_matches = [match.strip() for match in matches_part.split(",")]
        
        return Layer1Result(
            content_type=ContentType.IMAGE,
            fast_filter_result=filter_result,
            hash_matches=hash_matches
        )
    
    async def _process_audio_async(self, audio_content: bytes) -> Layer1Result:
        """Process audio content asynchronously"""
        start_time = time.time()
        
        transcription = None
        filter_result = FilterResult()
        
        try:
            # Transcribe audio using Deepgram
            if self.deepgram_client:
                transcription = await self._transcribe_audio_deepgram(audio_content)
            else:
                # Fallback: create a placeholder result
                transcription = "[Audio transcription not available - Deepgram not configured]"
            
            # If we have transcription, apply text filtering to it
            if transcription and transcription != "[Audio transcription not available - Deepgram not configured]":
                filter_result = self.text_filter.filter_text(transcription)
                # Adjust categories for audio context
                if filter_result.categories:
                    filter_result.details = f"Transcribed: '{transcription[:100]}...' - {filter_result.details}"
            
        except Exception as e:
            filter_result = FilterResult(
                is_harmful=False,
                confidence=0.0,
                details=f"Audio processing error: {str(e)}"
            )
        
        processing_time = (time.time() - start_time) * 1000
        filter_result.processing_time_ms = processing_time
        
        return Layer1Result(
            content_type=ContentType.AUDIO,
            fast_filter_result=filter_result,
            transcription=transcription
        )
    
    async def _transcribe_audio_deepgram(self, audio_content: bytes) -> str:
        """Transcribe audio using Deepgram API"""
        try:
            # Prepare audio source
            source = FileSource(
                buffer=audio_content,
                mimetype="audio/wav"  # Adjust based on actual audio format
            )
            
            # Configure transcription options
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                language="en",  # You can make this configurable
                profanity_filter=False,  # We want to detect profanity, not filter it
                punctuate=True,
                paragraphs=True
            )
            
            # Perform transcription
            response = await self.deepgram_client.listen.asyncprerecorded.v("1").transcribe_file(
                source, options
            )
            
            # Extract transcribed text
            if response.results and response.results.channels:
                channel = response.results.channels[0]
                if channel.alternatives:
                    return channel.alternatives[0].transcript
            
            return ""
            
        except Exception as e:
            raise Exception(f"Deepgram transcription failed: {str(e)}")
    
    def _preprocess_text(self, text: str) -> str:
        """Basic text preprocessing for downstream analysis"""
        if not text:
            return ""
        
        # Basic cleaning
        cleaned = text.strip()
        
        # Remove excessive whitespace
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Normalize case for certain patterns
        # (but preserve original case for AI analysis)
        
        return cleaned
    
    def add_custom_banned_words(self, category: str, words: List[str]):
        """Add custom banned words to text filter"""
        self.text_filter.add_custom_words(category, words)
    
    def add_harmful_image_hash(self, image_hash: str, category: HarmCategory, confidence: float = 0.9):
        """Add harmful image hash to detector"""
        self.image_detector.add_harmful_hash(image_hash, category, confidence)
    
    def load_harmful_image_database(self, hash_database: Dict[str, tuple]):
        """Load harmful image database"""
        self.image_detector.load_harmful_hashes_from_db(hash_database)
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics for Layer 1 processing"""
        return {
            "text_filter_loaded": self.text_filter is not None,
            "image_detector_loaded": self.image_detector is not None,
            "deepgram_available": self.deepgram_client is not None,
            "thread_pool_active": not self.executor._shutdown,
            "harmful_hashes_count": len(self.image_detector.harmful_hashes)
        }
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
    
    async def _download_content(self, url: str, max_size: int = 50 * 1024 * 1024) -> bytes:
        """Download content from URL with size limit"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: Could not download from {url}")
                    
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > max_size:
                        raise Exception(f"Content too large: {content_length} bytes (max {max_size})")
                    
                    # Download with size checking
                    content = bytearray()
                    async for chunk in response.content.iter_chunked(8192):
                        content.extend(chunk)
                        if len(content) > max_size:
                            raise Exception(f"Content exceeds size limit: {max_size} bytes")
                    
                    return bytes(content)
        except Exception as e:
            raise Exception(f"Failed to download from {url}: {str(e)}")
    
    async def _process_images_async(self, image_urls: List[str]) -> Layer1Result:
        """Process multiple images from URLs"""
        start_time = time.time()
        all_hash_matches = []
        max_harm_score = 0.0
        is_harmful = False
        all_categories = []
        combined_details = []
        
        for i, url in enumerate(image_urls):
            try:
                # Download image with 20MB limit
                image_data = await self._download_content(url, 20 * 1024 * 1024)
                
                # Process image
                loop = asyncio.get_event_loop()
                filter_result = await loop.run_in_executor(
                    self.executor,
                    self.image_detector.analyze_image,
                    image_data
                )
                
                # Track results
                if filter_result.is_harmful:
                    is_harmful = True
                    all_categories.extend(filter_result.categories)
                
                if filter_result.confidence > max_harm_score:
                    max_harm_score = filter_result.confidence
                
                # Extract hash matches
                if filter_result.details and "Hash matches found:" in filter_result.details:
                    matches_part = filter_result.details.split("Hash matches found: ")[1]
                    matches = [match.strip() for match in matches_part.split(",")]
                    all_hash_matches.extend(matches)
                
                combined_details.append(f"Image {i+1} ({url}): {filter_result.details}")
                
            except Exception as e:
                combined_details.append(f"Image {i+1} ({url}): Error - {str(e)}")
        
        processing_time = (time.time() - start_time) * 1000
        
        return Layer1Result(
            content_type=ContentType.IMAGE,
            fast_filter_result=FilterResult(
                is_harmful=is_harmful,
                confidence=max_harm_score,
                categories=list(set(all_categories)),
                details="; ".join(combined_details),
                processing_time_ms=processing_time
            ),
            hash_matches=all_hash_matches
        )
    
    async def _process_audios_async(self, audio_urls: List[str]) -> Layer1Result:
        """Process multiple audio files from URLs"""
        start_time = time.time()
        all_transcriptions = []
        is_harmful = False
        max_harm_score = 0.0
        all_categories = []
        combined_details = []
        
        for i, url in enumerate(audio_urls):
            try:
                # Download audio with 50MB limit
                audio_data = await self._download_content(url, 50 * 1024 * 1024)
                
                # Transcribe and analyze
                transcription = None
                if self.deepgram_client:
                    transcription = await self._transcribe_audio_deepgram(audio_data)
                    all_transcriptions.append(f"Audio {i+1}: {transcription}")
                else:
                    transcription = "[Audio transcription not available - Deepgram not configured]"
                    all_transcriptions.append(f"Audio {i+1}: {transcription}")
                
                # Apply text filtering to transcription
                if transcription and transcription != "[Audio transcription not available - Deepgram not configured]":
                    filter_result = self.text_filter.filter_text(transcription)
                    
                    if filter_result.is_harmful:
                        is_harmful = True
                        all_categories.extend(filter_result.categories)
                    
                    if filter_result.confidence > max_harm_score:
                        max_harm_score = filter_result.confidence
                    
                    combined_details.append(f"Audio {i+1} ({url}): {filter_result.details}")
                else:
                    combined_details.append(f"Audio {i+1} ({url}): No transcription available")
                
            except Exception as e:
                combined_details.append(f"Audio {i+1} ({url}): Error - {str(e)}")
        
        processing_time = (time.time() - start_time) * 1000
        
        return Layer1Result(
            content_type=ContentType.AUDIO,
            fast_filter_result=FilterResult(
                is_harmful=is_harmful,
                confidence=max_harm_score,
                categories=list(set(all_categories)),
                details="; ".join(combined_details),
                processing_time_ms=processing_time
            ),
            transcription="; ".join(all_transcriptions)
        ) 