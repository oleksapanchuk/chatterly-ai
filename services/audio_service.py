from typing import List

from services.audio_transcription.audio_transcription_service import AudioTranscriptionService

transcription_service = AudioTranscriptionService()


def process_audio_array(audio_urls: List[str]):
    transcribed_text: list[str] = []

    for audio_url in audio_urls:
        result = transcription_service.transcribe_audio_url(audio_url)

        if result is not None and result.success:
            transcribed_text.append(result.text)
        else:
            transcribed_text.append("")

        print(f"\nTranscribed text for {audio_url}: {result.text}")

    return transcribed_text
