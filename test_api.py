# --------------------------------------------------------------
# Test Script for Content Moderation API
# --------------------------------------------------------------

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_URL = "http://localhost:8000"
API_SALT = os.getenv("API_SALT", "default_salt")

# Test data
safe_text = "Hello world! This is a friendly message."
harmful_text = "I hate everyone from that country. They should all be eliminated."
test_audio_url = "https://example.com/audio/sample.mp3"
test_image_url = "https://example.com/images/sample.jpg"

# Headers
headers = {
    "Content-Type": "application/json",
    "X-API-Salt": API_SALT
}

def test_process_text():
    """Test the text processing endpoint"""
    print("\n=== Testing /process-text endpoint ===")
    
    # Test with safe text
    print("\nTesting with safe text...")
    response = requests.post(
        f"{API_URL}/process-text",
        headers=headers,
        json={"text": safe_text}
    )
    
    if response.status_code == 200:
        print(f"Status: {response.status_code} OK")
        result = response.json()
        print(f"Is harmful: {result['is_harmful']}")
        print(f"Severity: {result['severity']}")
        print(f"Confidence: {result['confidence']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    
    # Test with harmful text
    print("\nTesting with harmful text...")
    response = requests.post(
        f"{API_URL}/process-text",
        headers=headers,
        json={"text": harmful_text}
    )
    
    if response.status_code == 200:
        print(f"Status: {response.status_code} OK")
        result = response.json()
        print(f"Is harmful: {result['is_harmful']}")
        print(f"Severity: {result['severity']}")
        print(f"Categories: {', '.join(result['categories'])}")
        print(f"Confidence: {result['confidence']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_process_audio():
    """Test the audio processing endpoint"""
    print("\n=== Testing /process-audio endpoint ===")
    
    response = requests.post(
        f"{API_URL}/process-audio",
        headers=headers,
        json={"audio_url": test_audio_url}
    )
    
    if response.status_code == 200:
        print(f"Status: {response.status_code} OK")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_process_image():
    """Test the image processing endpoint"""
    print("\n=== Testing /process-image endpoint ===")
    
    response = requests.post(
        f"{API_URL}/process-image",
        headers=headers,
        json={"image_url": test_image_url}
    )
    
    if response.status_code == 200:
        print(f"Status: {response.status_code} OK")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_invalid_salt():
    """Test API with invalid salt"""
    print("\n=== Testing with invalid salt ===")
    
    invalid_headers = {
        "Content-Type": "application/json",
        "X-API-Salt": "invalid_salt"
    }
    
    response = requests.post(
        f"{API_URL}/process-text",
        headers=invalid_headers,
        json={"text": safe_text}
    )
    
    print(f"Status: {response.status_code}")
    print(response.text)

if __name__ == "__main__":
    print("Running Content Moderation API tests...")
    print("Make sure the API server is running on http://localhost:8000")
    
    # Run tests
    test_process_text()
    test_process_audio()
    test_process_image()
    
    # Only test invalid salt if a custom salt is set
    if API_SALT != "default_salt":
        test_invalid_salt()
    
    print("\nTests completed.")