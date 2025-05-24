from typing import List

from services.audio_transcription.audio_transcription_service import AudioTranscriptionService
from shared.logger_config import get_logger

logger = get_logger(__name__)
transcription_service = AudioTranscriptionService()


def process_audio_array(audio_urls: List[str]):
    logger.info(f"Processing audio array with {len(audio_urls)} URLs")
    transcribed_text: list[str] = []

    for i, audio_url in enumerate(audio_urls):
        logger.debug(f"Processing audio URL {i + 1}/{len(audio_urls)}: {audio_url}")
        result = transcription_service.transcribe_audio_url(audio_url)

        if result is not None and result.success:
            transcribed_text.append(result.text)
            logger.info(f"Successfully transcribed audio {i + 1}: {len(result.text)} characters")
        else:
            transcribed_text.append("")
            error_msg = result.error if result else "Unknown error"
            logger.warning(f"Failed to transcribe audio {i + 1}: {error_msg}")

    logger.info(f"Completed audio processing. {len([t for t in transcribed_text if t])} successful transcriptions")
    return transcribed_text
