"""
Enhanced GPT Service for Layer 2 AI Analysis
Improved prompts and analysis for text and audio content
"""

import os
import time
from typing import Optional, Dict, List
import instructor
from dotenv import load_dotenv
from openai import OpenAI

from shared.enhanced_types import FilterResult, HarmCategory, ContentType

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))

class EnhancedGptService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model or DEFAULT_MODEL
        self.client = instructor.patch(OpenAI(api_key=self.api_key))
        
        # Category mapping from API response to our categories
        self.category_mapping = {
            "hate": HarmCategory.HATE_SPEECH,
            "harassment": HarmCategory.HARASSMENT,
            "violence": HarmCategory.VIOLENCE,
            "sexual": HarmCategory.SEXUAL_CONTENT,
            "self-harm": HarmCategory.SELF_HARM,
            "illegal": HarmCategory.ILLEGAL_ACTIVITY,
            "spam": HarmCategory.SPAM,
            "toxic": HarmCategory.TOXIC_BEHAVIOR,
            "profanity": HarmCategory.PROFANITY
        }
    
    def _create_enhanced_text_prompt(self, content_context: str = "general") -> str:
        """Create enhanced system prompt for text moderation"""
        return f"""
You are an expert content moderation AI specialized in detecting harmful content with high precision and nuanced understanding.

ANALYSIS CONTEXT: {content_context}

DETECT AND CATEGORIZE the following types of harmful content:

1. HATE SPEECH (hate): Content targeting individuals/groups based on protected characteristics
   - Racial, ethnic, religious, gender, sexual orientation slurs
   - Dehumanizing language or Nazi/extremist ideology
   - Incitement to hatred or discrimination

2. HARASSMENT (harassment): Personal attacks or coordinated harassment
   - Bullying, stalking, or intimidation tactics
   - Doxxing attempts or personal threats
   - Coordinated pile-on behavior

3. VIOLENCE (violence): Content promoting, glorifying, or threatening violence
   - Direct threats against individuals or groups
   - Instructions for violence or harm
   - Glorification of violent acts or events

4. SEXUAL CONTENT (sexual): Inappropriate sexual content
   - Explicit sexual descriptions or solicitation
   - Non-consensual intimate content
   - Sexual exploitation or grooming patterns

5. SELF-HARM (self-harm): Content encouraging self-destructive behavior
   - Suicide encouragement or instruction
   - Self-injury promotion or glorification
   - Eating disorder promotion

6. ILLEGAL ACTIVITY (illegal): Content promoting illegal activities
   - Drug trafficking or sales
   - Fraud, scams, or financial crimes
   - Weapons trafficking or illegal services

7. SPAM (spam): Unwanted commercial or repetitive content
   - Unsolicited advertising or MLM schemes
   - Repetitive posting or bot-like behavior
   - Fake engagement or manipulation tactics

8. TOXIC BEHAVIOR (toxic): Generally harmful social interactions
   - Excessive aggression or hostility
   - Bad faith arguments or trolling
   - Manipulation or gaslighting patterns

9. PROFANITY (profanity): Excessive or inappropriate language
   - Context-inappropriate profanity
   - Vulgar language in professional settings
   - Excessive cursing that degrades discourse

ANALYSIS INSTRUCTIONS:
- Consider CONTEXT and INTENT, not just word presence
- Account for SARCASM, HUMOR, and EDUCATIONAL use
- Be CULTURALLY AWARE of different communication styles
- Distinguish between DISCUSSING harmful content vs PROMOTING it
- Consider SEVERITY within each category (mild/moderate/severe)

CONFIDENCE SCORING:
- 0.9-1.0: Extremely confident, clear violation
- 0.7-0.8: High confidence, likely violation
- 0.5-0.6: Moderate confidence, borderline case
- 0.3-0.4: Low confidence, uncertain
- 0.0-0.2: Very low confidence, likely false positive

RESPONSE FORMAT:
Analyze the content and provide:
1. Boolean determination if content is harmful
2. List of detected categories with confidence scores
3. Brief explanation of reasoning
4. Specific flagged segments (if any)

Be precise, fair, and consider the human impact of your decisions.
"""
    
    def _create_audio_analysis_prompt(self, transcription: str) -> str:
        """Create specialized prompt for audio content analysis"""
        return f"""
You are analyzing AUDIO CONTENT that has been transcribed. Audio content has unique characteristics:

AUDIO-SPECIFIC CONSIDERATIONS:
- Transcription may contain errors or missing context
- Tone, emphasis, and emotion are lost in transcription
- Background noise may create transcription artifacts
- Multiple speakers may create confusion
- Partial sentences or unclear audio segments

TRANSCRIBED CONTENT:
"{transcription}"

Apply the same harmful content categories as text analysis, but with ADDITIONAL CONSIDERATION for:

AUDIO CONTEXT FACTORS:
- Transcription accuracy limitations
- Missing tonal and emotional context
- Potential speaker confusion or background interference
- Incomplete sentences due to audio quality

AUDIO-SPECIFIC PATTERNS:
- Heated arguments vs casual conversation
- Educational content vs promotion of harmful ideas
- Performance/entertainment vs genuine harmful intent
- Private conversation vs public broadcast intent

CONFIDENCE ADJUSTMENTS:
- Reduce confidence by 10-20% if transcription seems incomplete
- Consider alternative interpretations for unclear segments
- Account for missing emotional/tonal context
- Flag if content seems to be missing critical context

Provide analysis with audio-specific considerations in mind.
"""
    
    def analyze_text_content(self, text: str, layer1_data: Optional[Dict] = None) -> FilterResult:
        """Analyze text content with enhanced prompting"""
        start_time = time.time()
        
        if not text or not text.strip():
            return FilterResult(processing_time_ms=(time.time() - start_time) * 1000)
        
        try:
            # Prepare context based on Layer 1 findings
            context = "general"
            if layer1_data and layer1_data.get("banned_words_found"):
                context = f"text with pre-detected issues: {', '.join(layer1_data['banned_words_found'][:3])}"
            
            # Call OpenAI moderation API first for baseline
            moderation_result = self._call_openai_moderation(text)
            
            # Enhanced analysis with detailed prompt
            detailed_analysis = self._call_detailed_analysis(text, context)
            
            # Combine results intelligently
            combined_result = self._combine_analysis_results(
                moderation_result, detailed_analysis, start_time
            )
            
            return combined_result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return FilterResult(
                is_harmful=False,
                confidence=0.0,
                details=f"Analysis error: {str(e)}",
                processing_time_ms=processing_time
            )
    
    def analyze_audio_content(self, transcription: str, layer1_data: Optional[Dict] = None) -> FilterResult:
        """Analyze audio content via transcription with specialized prompting"""
        start_time = time.time()
        
        if not transcription or not transcription.strip():
            return FilterResult(processing_time_ms=(time.time() - start_time) * 1000)
        
        try:
            # Use specialized audio analysis prompt
            messages = [
                {"role": "system", "content": self._create_audio_analysis_prompt(transcription)},
                {"role": "user", "content": f"Analyze this transcribed audio content: {transcription}"}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=TEMPERATURE,
                max_retries=MAX_RETRIES
            )
            
            # Parse response and create FilterResult
            result = self._parse_ai_response(response.choices[0].message.content)
            result.processing_time_ms = (time.time() - start_time) * 1000
            
            # Adjust confidence for audio-specific factors
            if "transcription" in result.details.lower() or "unclear" in result.details.lower():
                result.confidence *= 0.8  # Reduce confidence for transcription uncertainty
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return FilterResult(
                is_harmful=False,
                confidence=0.0,
                details=f"Audio analysis error: {str(e)}",
                processing_time_ms=processing_time
            )
    
    def _call_openai_moderation(self, text: str) -> Dict:
        """Call OpenAI's built-in moderation API for baseline"""
        try:
            moderation = self.client.moderations.create(input=text)
            result = moderation.results[0]
            
            return {
                "flagged": result.flagged,
                "categories": result.categories.__dict__,
                "category_scores": result.category_scores.__dict__
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _call_detailed_analysis(self, text: str, context: str) -> Dict:
        """Call detailed analysis with enhanced prompt"""
        try:
            messages = [
                {"role": "system", "content": self._create_enhanced_text_prompt(context)},
                {"role": "user", "content": f"Analyze this content: {text}"}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=TEMPERATURE,
                max_retries=MAX_RETRIES
            )
            
            return {"content": response.choices[0].message.content}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _combine_analysis_results(self, moderation_result: Dict, detailed_analysis: Dict, start_time: float) -> FilterResult:
        """Intelligently combine OpenAI moderation and detailed analysis"""
        
        categories = []
        confidence_scores = []
        is_harmful = False
        details_parts = []
        
        # Process OpenAI moderation results
        if "categories" in moderation_result:
            for category, flagged in moderation_result["categories"].items():
                if flagged:
                    mapped_category = self._map_openai_category(category)
                    if mapped_category:
                        categories.append(mapped_category)
                        # Get confidence from category_scores
                        score = moderation_result.get("category_scores", {}).get(category, 0.5)
                        confidence_scores.append(score)
                        is_harmful = True
        
        # Process detailed analysis
        if "content" in detailed_analysis:
            detailed_result = self._parse_ai_response(detailed_analysis["content"])
            if detailed_result.is_harmful:
                categories.extend(detailed_result.categories)
                confidence_scores.append(detailed_result.confidence)
                is_harmful = True
                if detailed_result.details:
                    details_parts.append(f"Detailed: {detailed_result.details}")
        
        # Handle errors
        error_details = []
        if "error" in moderation_result:
            error_details.append(f"Moderation API: {moderation_result['error']}")
        if "error" in detailed_analysis:
            error_details.append(f"Detailed analysis: {detailed_analysis['error']}")
        
        if error_details:
            details_parts.extend(error_details)
        
        # Calculate final confidence
        final_confidence = max(confidence_scores) if confidence_scores else 0.0
        
        # Remove duplicates from categories
        unique_categories = list(set(categories))
        
        processing_time = (time.time() - start_time) * 1000
        
        return FilterResult(
            is_harmful=is_harmful,
            confidence=final_confidence,
            categories=unique_categories,
            details="; ".join(details_parts) if details_parts else None,
            processing_time_ms=processing_time
        )
    
    def _map_openai_category(self, openai_category: str) -> Optional[HarmCategory]:
        """Map OpenAI moderation categories to our HarmCategory enum"""
        mapping = {
            "hate": HarmCategory.HATE_SPEECH,
            "harassment": HarmCategory.HARASSMENT,
            "violence": HarmCategory.VIOLENCE,
            "sexual": HarmCategory.SEXUAL_CONTENT,
            "self-harm": HarmCategory.SELF_HARM,
        }
        return mapping.get(openai_category)
    
    def _parse_ai_response(self, response_content: str) -> FilterResult:
        """Parse AI response into FilterResult (simplified version)"""
        
        # Simple parsing logic - in production, you'd want more robust parsing
        is_harmful = any(keyword in response_content.lower() for keyword in 
                        ["harmful", "violation", "inappropriate", "flagged", "detected"])
        
        # Extract categories (simplified)
        detected_categories = []
        for category_name, category_enum in self.category_mapping.items():
            if category_name in response_content.lower():
                detected_categories.append(category_enum)
        
        # Extract confidence (simplified)
        confidence = 0.7 if is_harmful else 0.1  # Default values
        
        # Try to extract actual confidence from response
        import re
        confidence_match = re.search(r'confidence[:\s]*([0-9.]+)', response_content.lower())
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
                if confidence > 1.0:  # If given as percentage
                    confidence /= 100.0
            except:
                pass
        
        return FilterResult(
            is_harmful=is_harmful,
            confidence=confidence,
            categories=detected_categories,
            details=response_content[:200] + "..." if len(response_content) > 200 else response_content
        ) 