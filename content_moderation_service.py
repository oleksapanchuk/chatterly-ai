# --------------------------------------------------------------
# Content Moderation Service
# --------------------------------------------------------------

import os
import instructor
from pydantic import BaseModel, Field
from openai import OpenAI
from enum import Enum
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Requires OpenAI API key
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

# --------------------------------------------------------------
# Pydantic Models for Content Analysis
# --------------------------------------------------------------

class ContentCategory(str, Enum):
    """Categories of potentially harmful content"""
    HATE_SPEECH = "hate_speech"
    HARASSMENT = "harassment"
    SELF_HARM = "self_harm"
    SEXUAL = "sexual"
    VIOLENCE = "violence"
    MISINFORMATION = "misinformation"
    SPAM = "spam"
    NONE = "none"

class SeverityLevel(str, Enum):
    """Severity levels for harmful content"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ContentAnalysisResult(BaseModel):
    """Model for content analysis results"""
    is_harmful: bool = Field(description="Whether the content contains harmful elements")
    categories: List[ContentCategory] = Field(description="Categories of harmful content detected")
    severity: SeverityLevel = Field(description="Overall severity level of harmful content")
    confidence: float = Field(ge=0, le=1, description="Confidence score for the analysis")
    flagged_segments: List[str] = Field(default=[], description="Specific segments of text that were flagged")
    recommendation: str = Field(description="Recommendation for handling the content")
    explanation: str = Field(description="Explanation of why the content was flagged or not")

# --------------------------------------------------------------
# Content Moderation Service
# --------------------------------------------------------------

class ContentModerationService:
    """Service for analyzing and moderating content"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the content moderation service"""
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it as OPENAI_API_KEY environment variable or pass it to the constructor.")
        
        self.model = model or DEFAULT_MODEL
        self.client = instructor.patch(OpenAI(api_key=self.api_key))
        
    def _create_system_prompt(self) -> str:
        """Create the system prompt for content analysis"""
        return """
        You are an AI content moderation assistant. Your task is to analyze text content for potentially harmful elements.
        
        You should identify content that may contain:
        - Hate speech or discrimination based on race, gender, religion, etc.
        - Harassment, bullying, or personal attacks
        - Self-harm or suicide content
        - Sexually explicit or inappropriate content
        - Violence or threats
        - Misinformation or deliberately misleading content
        - Spam or unwanted commercial content
        
        For each analysis, provide:
        1. Whether the content is harmful
        2. Categories of harmful content detected
        3. Overall severity level
        4. Confidence score for your analysis
        5. Specific segments of text that were flagged (if any)
        6. Recommendation for handling the content
        7. Explanation of your analysis
        
        Be objective and thorough in your analysis. If you're uncertain about any aspect, reflect that in your confidence score.
        """
    
    def analyze_content(self, text: str) -> ContentAnalysisResult:
        """
        Analyze text content for potentially harmful elements
        
        Args:
            text (str): The text content to analyze
            
        Returns:
            ContentAnalysisResult: Analysis results with categorization and recommendations
            
        Raises:
            Exception: If the API call fails after maximum retries
        """
        if not text or not text.strip():
            raise ValueError("Text content cannot be empty")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_model=ContentAnalysisResult,
                temperature=TEMPERATURE,
                max_retries=MAX_RETRIES,
                messages=[
                    {
                        "role": "system",
                        "content": self._create_system_prompt(),
                    },
                    {"role": "user", "content": text}
                ]
            )
            return response
        except Exception as e:
            # Log the error and raise a more user-friendly exception
            print(f"Error analyzing content: {str(e)}")
            raise Exception(f"Failed to analyze content: {str(e)}")
    
    def is_content_safe(self, text: str) -> bool:
        """
        Quick check if content is safe (convenience method)
        
        Args:
            text (str): The text content to analyze
            
        Returns:
            bool: True if content is safe, False otherwise
        """
        result = self.analyze_content(text)
        return not result.is_harmful

# --------------------------------------------------------------
# Usage Example
# --------------------------------------------------------------

def example_usage():
    # Example text to analyze
    safe_text = "Hello world! This is a friendly message."
    harmful_text = "I hate everyone from that country. They should all be eliminated."
    
    # Create service
    moderation_service = ContentModerationService()
    
    # Analyze content
    safe_result = moderation_service.analyze_content(safe_text)
    harmful_result = moderation_service.analyze_content(harmful_text)
    
    # Print results
    print("Safe text analysis:")
    print(safe_result.model_dump_json(indent=2))
    
    print("\nHarmful text analysis:")
    print(harmful_result.model_dump_json(indent=2))

if __name__ == "__main__":
    example_usage()