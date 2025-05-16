# Content Moderation Service

A service for analyzing text content for potentially harmful elements using OpenAI's API, with a REST API server for easy integration.

## Features

- Analyzes text and audio content for various types of harmful content:
  - Hate speech
  - Harassment
  - Self-harm
  - Sexual content
  - Violence
  - Misinformation
  - Spam
- Provides structured analysis results with:
  - Harmful content detection
  - Content categorization
  - Severity assessment
  - Confidence scores
  - Flagged text segments
  - Handling recommendations
  - Detailed explanations
- Configurable via environment variables
- Built-in error handling and retry logic

## Setup

1. Install required packages:

   Using pip:
   ```
   pip install openai instructor pydantic python-dotenv fastapi uvicorn requests
   ```

   Using conda:
   ```
   conda install -c conda-forge openai pydantic python-dotenv fastapi uvicorn requests
   pip install instructor
   ```

   Note: The `instructor` package may not be available in conda repositories, so we install it using pip after setting up the conda environment.

   Important: When using conda, always specify the channel with `-c conda-forge`. Do not use `-c fastapi` as "fastapi" is a package name, not a channel name. The correct format is `conda install -c conda-forge fastapi`, not `conda install -c fastapi`.

2. Create a `.env` file in the project root with your OpenAI API key and other configuration:
   ```
   OPENAI_API_KEY=your_api_key_here
   DEFAULT_MODEL=gpt-4o
   MAX_RETRIES=3
   TEMPERATURE=0
   ```

## Usage

### Basic Usage

```python
from content_moderation_service import ContentModerationService

# Create an instance of the service
moderation_service = ContentModerationService()

# Analyze text content
text = "Hello world! This is a friendly message."
result = moderation_service.analyze_content(text)

# Check if content is harmful
is_harmful = result.is_harmful
print(f"Is harmful: {is_harmful}")

# Get detailed analysis
print(f"Categories: {result.categories}")
print(f"Severity: {result.severity}")
print(f"Confidence: {result.confidence}")
print(f"Recommendation: {result.recommendation}")
```

### Audio Content Moderation

The service can also analyze audio content by first transcribing it and then analyzing the transcribed text:

```python
from services.audio_transcription.audio_transcription_service import AudioTranscriptionService
from content_moderation_service import ContentModerationService

# Create instances of the services
transcription_service = AudioTranscriptionService()
moderation_service = ContentModerationService()

# Transcribe audio
transcription_result = transcription_service.transcribe_audio_url("https://example.com/audio.mp3")

# Analyze transcribed text
if transcription_result.success:
    moderation_result = moderation_service.analyze_content(transcription_result.text)

    # Check if content is safe
    is_safe = not moderation_result.is_harmful
    print(f"Transcribed text: {transcription_result.text}")
    print(f"Content is {'safe' if is_safe else 'harmful'}")
```

### Quick Safety Check

```python
from content_moderation_service import ContentModerationService

moderation_service = ContentModerationService()

# Quick check if content is safe
text = "Hello world! This is a friendly message."
is_safe = moderation_service.is_content_safe(text)
print(f"Is content safe: {is_safe}")
```

### Custom Configuration

```python
from content_moderation_service import ContentModerationService

# Use custom API key and model
moderation_service = ContentModerationService(
    api_key="your_api_key_here",
    model="gpt-3.5-turbo"
)

# Analyze content
result = moderation_service.analyze_content("Your text here")
```

## Example

See `test_content_moderation.py` for a complete example of how to use the service.

## Response Structure

The `analyze_content` method returns a `ContentAnalysisResult` object with the following properties:

- `is_harmful` (bool): Whether the content contains harmful elements
- `categories` (List[ContentCategory]): Categories of harmful content detected
- `severity` (SeverityLevel): Overall severity level of harmful content
- `confidence` (float): Confidence score for the analysis (0-1)
- `flagged_segments` (List[str]): Specific segments of text that were flagged
- `recommendation` (str): Recommendation for handling the content
- `explanation` (str): Explanation of why the content was flagged or not

## API Server

The project includes a FastAPI server that exposes the content moderation functionality through REST API endpoints.

### Setup

1. Update your `.env` file to include API salt for security (optional):
   ```
   OPENAI_API_KEY=your_api_key_here
   DEFAULT_MODEL=gpt-4o
   MAX_RETRIES=3
   TEMPERATURE=0
   API_SALT=your_secret_salt_here
   ```

### Running the Server

Run the server with:

```bash
python app.py
```

Or using uvicorn directly:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at http://localhost:8000.

### API Documentation

Once the server is running, you can access the auto-generated API documentation at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

### API Endpoints

#### 1. Process Text

- **URL**: `/process-text`
- **Method**: POST
- **Headers**:
  - `Content-Type: application/json`
  - `X-API-Salt: your_salt_here` (optional, if API_SALT is configured)
- **Request Body**:
  ```json
  {
    "text": "Text content to analyze"
  }
  ```
- **Response**: ContentAnalysisResult object

#### 2. Process Audio (Transcription)

- **URL**: `/process-audio`
- **Method**: POST
- **Headers**:
  - `Content-Type: application/json`
  - `X-API-Salt: your_salt_here` (optional, if API_SALT is configured)
- **Request Body**:
  ```json
  {
    "audio_url": "URL to audio file"
  }
  ```
- **Response**: TranscriptionResult object

#### 3. Process Audio with Moderation

- **URL**: `/process-audio-moderation`
- **Method**: POST
- **Headers**:
  - `Content-Type: application/json`
  - `X-API-Salt: your_salt_here` (optional, if API_SALT is configured)
- **Request Body**:
  ```json
  {
    "audio_url": "URL to audio file"
  }
  ```
- **Response**: 
  ```json
  {
    "transcribed_text": "The transcribed text from the audio",
    "moderation_result": {
      "is_harmful": false,
      "categories": ["none"],
      "severity": "none",
      "confidence": 0.95,
      "flagged_segments": [],
      "recommendation": "Content appears safe",
      "explanation": "The content does not contain harmful elements"
    }
  }
  ```

#### 4. Process Image (Placeholder)

- **URL**: `/process-image`
- **Method**: POST
- **Headers**:
  - `Content-Type: application/json`
  - `X-API-Salt: your_salt_here` (optional, if API_SALT is configured)
- **Request Body**:
  ```json
  {
    "image_url": "URL to image file"
  }
  ```
- **Response**: Placeholder response

### Testing the API

Test scripts are provided to verify the API functionality:

```bash
# Test text moderation API
python test_api.py

# Test audio moderation API
python test_audio_moderation.py
```

Make sure the server is running before executing the test scripts.
