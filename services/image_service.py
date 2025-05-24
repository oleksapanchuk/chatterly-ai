from typing import List

from services.omni_moderation.omni_image_moderation import get_image_moderation_response
from shared.logger_config import get_logger
from shared.moderation_result import ModerationResult

logger = get_logger(__name__)


def process_image_array(image_urls: List[str]):
    logger.info(f"Processing image array with {len(image_urls)} URLs")
    omni_moderation_result: list[ModerationResult] = get_image_moderation_response(image_urls)

    harmful_count = len([r for r in omni_moderation_result if r.is_harmful])
    logger.info(f"Completed image processing. {harmful_count}/{len(omni_moderation_result)} images flagged as harmful")

    return omni_moderation_result
