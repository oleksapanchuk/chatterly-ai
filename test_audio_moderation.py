import requests
import json

def test_audio_moderation():
    """Test the audio moderation endpoint"""
    
    # Base URL for the API
    base_url = "http://localhost:8000"
    
    # Test audio URL (replace with a valid audio URL for actual testing)
    test_audio_url = "https://example.com/sample-audio.mp3"
    
    # Request payload
    payload = {
        "audio_url": test_audio_url
    }
    
    # Headers (add API salt if required)
    headers = {
        "Content-Type": "application/json"
        # "X-API-Salt": "your_api_salt_here"  # Uncomment and set if needed
    }
    
    try:
        # Make the request to the audio moderation endpoint
        response = requests.post(
            f"{base_url}/process-audio-moderation",
            headers=headers,
            data=json.dumps(payload)
        )
        
        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            print("Audio Moderation Test Successful!")
            print("\nTranscribed Text:")
            print(result["transcribed_text"])
            print("\nModeration Result:")
            print(json.dumps(result["moderation_result"], indent=2))
            
            # Check if content is harmful
            is_harmful = result["moderation_result"]["is_harmful"]
            print(f"\nContent is {'harmful' if is_harmful else 'safe'}")
            
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Audio Moderation API...")
    test_audio_moderation()