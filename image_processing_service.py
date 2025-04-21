# --------------------------------------------------------------
# Image Processing Service
# --------------------------------------------------------------

import os
import requests
from io import BytesIO
import base64
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI
from content_moderation_service import ContentModerationService, ContentAnalysisResult

# Load environment variables
load_dotenv()

# Constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Requires OpenAI API key
DEFAULT_MODEL = os.getenv("DEFAULT_VISION_MODEL", "gpt-4-vision-preview")
MAX_RETRIES = int(os.getenv("IMAGE_PROCESS_MAX_RETRIES", "2"))
RETRY_DELAY = float(os.getenv("IMAGE_PROCESS_RETRY_DELAY", "1.0"))

# --------------------------------------------------------------
# Pydantic Models for Image Processing Results
# --------------------------------------------------------------

class ImageProcessingResult(BaseModel):
    """Model for image processing results"""
    description: str = Field(description="The generated description of the image")
    moderation_result: ContentAnalysisResult = Field(description="Content moderation results for the image")
    success: bool = Field(description="Whether the image processing was successful")
    error: Optional[str] = Field(None, description="Error message if processing failed")

# --------------------------------------------------------------
# Image Processing Service
# --------------------------------------------------------------

class ImageProcessingService:
    """Service for processing and analyzing images using OpenAI's vision capabilities"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the image processing service"""
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it as OPENAI_API_KEY environment variable or pass it to the constructor.")

        self.model = model or DEFAULT_MODEL
        self.client = OpenAI(api_key=self.api_key)
        self.content_moderation_service = ContentModerationService(api_key=self.api_key)

    def download_image(self, image_url: str) -> bytes:
        """
        Download image from URL

        Args:
            image_url (str): URL of the image to download

        Returns:
            bytes: Image data

        Raises:
            Exception: If the download fails
        """
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.content
        except Exception as e:
            raise Exception(f"Failed to download image from {image_url}: {str(e)}")

    def encode_image_to_base64(self, image_data: bytes) -> str:
        """
        Encode image data to base64

        Args:
            image_data (bytes): Image data

        Returns:
            str: Base64 encoded image
        """
        return base64.b64encode(image_data).decode('utf-8')

    def generate_image_description(self, image_data: bytes) -> str:
        """
        Generate a description of the image using OpenAI's vision capabilities

        Args:
            image_data (bytes): Image data

        Returns:
            str: Description of the image

        Raises:
            Exception: If the API call fails
        """
        base64_image = self.encode_image_to_base64(image_data)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that describes images in detail. Please provide a comprehensive description of the image, including all visible elements, actions, text, and potentially sensitive or harmful content. Please analyze this image and tell me if it contains any content that might be inappropriate for minors. Please analyze this image and tell me if it contains any content that might be inappropriate for minors."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Please describe this image in detail:"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            # Extract the description from the response
            description = response.choices[0].message.content
            return description
            
        except Exception as e:
            raise Exception(f"Failed to generate image description: {str(e)}")
    
    def process_image_url(self, image_url: str) -> ImageProcessingResult:
        """
        Process image from a URL
        
        Args:
            image_url (str): URL of the image to process
            
        Returns:
            ImageProcessingResult: Processing results including description and moderation
            
        Raises:
            Exception: If the processing fails after maximum retries
        """
        if not image_url or not image_url.strip():
            raise ValueError("Image URL cannot be empty")
        
        # Try to process with retries
        for attempt in range(MAX_RETRIES):
            try:
                # Step 1: Download the image
                image_data = self.download_image(image_url)
                
                # Step 2: Generate a description of the image
                description = self.generate_image_description(image_data)
                
                # Step 3: Analyze the description for harmful content
                moderation_result = self.content_moderation_service.analyze_content(description)
                
                return ImageProcessingResult(
                    description=description,
                    moderation_result=moderation_result,
                    success=True,
                    error=None
                )
                
            except Exception as e:
                if attempt == MAX_RETRIES - 1:  # Last attempt
                    # Log the error and return a failure result
                    print(f"Error processing image: {str(e)}")
                    return ImageProcessingResult(
                        description="",
                        moderation_result=ContentAnalysisResult(
                            is_harmful=False,
                            categories=[],
                            severity="none",
                            confidence=0.0,
                            flagged_segments=[],
                            recommendation="Failed to process image",
                            explanation=f"Error: {str(e)}"
                        ),
                        success=False,
                        error=f"Failed to process image: {str(e)}"
                    )
                else:
                    # Wait before retrying
                    import time
                    time.sleep(1)  # Simple backoff strategy

# --------------------------------------------------------------
# Usage Example
# --------------------------------------------------------------

def example_usage():
    # Example image URL to process
    image_url = "https://example.com/sample-image.jpg"
    
    # Create service
    image_processing_service = ImageProcessingService()
    
    # Process image
    result = image_processing_service.process_image_url(image_url)
    
    # Print results
    print("Image processing result:")
    print(f"Success: {result.success}")
    if result.success:
        print(f"Description: {result.description}")
        print(f"Is harmful: {result.moderation_result.is_harmful}")
        print(f"Categories: {result.moderation_result.categories}")
        print(f"Severity: {result.moderation_result.severity}")
        print(f"Recommendation: {result.moderation_result.recommendation}")
    else:
        print(f"Error: {result.error}")

if __name__ == "__main__":
    example_usage()