# --------------------------------------------------------------
# Test Image Processing Service
# --------------------------------------------------------------

import os
from dotenv import load_dotenv
from image_processing_service import ImageProcessingService

# Load environment variables
load_dotenv()

def test_image_processing():
    """Test the image processing service with a sample image"""
    
    # Sample image URL (use a publicly accessible image)
    # This is a sample image from Unsplash (a free image service)
    image_url = "https://images.unsplash.com/photo-1579546929518-9e396f3cc809"
    
    print(f"Testing image processing with URL: {image_url}")
    
    # Create service
    image_processing_service = ImageProcessingService()
    
    try:
        # Process image
        result = image_processing_service.process_image_url(image_url)
        
        # Print results
        print("\nImage processing result:")
        print(f"Success: {result.success}")
        
        if result.success:
            print("\nImage Description:")
            print(result.description)
            
            print("\nModeration Results:")
            print(f"Is harmful: {result.moderation_result.is_harmful}")
            print(f"Categories: {result.moderation_result.categories}")
            print(f"Severity: {result.moderation_result.severity}")
            print(f"Confidence: {result.moderation_result.confidence}")
            
            if result.moderation_result.flagged_segments:
                print("\nFlagged Segments:")
                for segment in result.moderation_result.flagged_segments:
                    print(f"- {segment}")
            
            print(f"\nRecommendation: {result.moderation_result.recommendation}")
            print(f"\nExplanation: {result.moderation_result.explanation}")
        else:
            print(f"Error: {result.error}")
            
        return result.success
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_image_processing()
    print(f"\nTest {'passed' if success else 'failed'}")