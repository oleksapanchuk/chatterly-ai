import os
from typing import Optional

import instructor
from dotenv import load_dotenv
from openai import OpenAI

from shared.gpt_text_analysis_result import GptTextAnalysisResult
from shared.logger_config import get_logger

load_dotenv()

logger = get_logger(__name__)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))


class GptModerationService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            logger.critical("OpenAI API key is missing")
            raise ValueError(
                "OpenAI API key is required. Set it as OPENAI_API_KEY environment variable or pass it to the constructor.")

        self.model = model or DEFAULT_MODEL
        self.client = instructor.patch(OpenAI(api_key=self.api_key))
        logger.info(f"GptModerationService initialized with model: {self.model}")

    def _create_system_prompt(self) -> str:
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
        4. Confidence score for each detected content category (between 0 and 1)
        5. Specific segments of text that were flagged (if any)
        6. Recommendation for handling the content
        7. Explanation of your analysis

        Be objective and thorough in your analysis. Make sure to provide confidence scores for each category identified. If you're uncertain about any aspect, reflect lower confidence scores for those categories.
        """

    def analyze_content(self, text: str) -> GptTextAnalysisResult:
        logger.debug(f"Starting GPT content analysis for text of length: {len(text)}")
        
        if not text or not text.strip():
            logger.error("Empty text provided for analysis")
            raise ValueError("Text content cannot be empty")

        try:
            logger.debug(f"Sending request to OpenAI with model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                response_model=GptTextAnalysisResult,
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
            
            logger.info(f"GPT analysis completed. Is harmful: {response.is_harmful}, Categories: {response.categories}, Severity: {response.severity}")
            logger.debug(f"Analysis confidence scores: {response.confidence}")
            
            return response
        except Exception as e:
            logger.error(f"Error analyzing content with GPT: {str(e)}", exc_info=True)
            raise Exception(f"Failed to analyze content: {str(e)}")
