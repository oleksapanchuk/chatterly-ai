from typing import List

from services.omni_moderation.omni_image_moderation import get_image_moderation_response
from shared.moderation_result import ModerationResult


def process_image_array(image_urls: List[str]):
    omni_moderation_result: list[ModerationResult] = get_image_moderation_response(image_urls)


    return omni_moderation_result
