import os

from dotenv import load_dotenv
from openai import OpenAI

from services.omni_moderation.omni_utils import get_omni_moderation_results, map_moderation_response_to_json

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


def get_image_moderation_response(urls: list[str]):
    if not urls:
        raise ValueError("At least one URL must be provided")

    results = []

    for url in urls:
        input_list = []

        input_list.append({
            "type": "image_url",
            "image_url": {
                "url": url,
                "details": {
                    "sensitivity_threshold": 0.7,
                    "analyze_text_in_image": True,
                    "check_nsfw": True,
                    "check_violence": True,
                    "check_hate_symbols": True
                }
            }
        })

        response = client.moderations.create(
            model="omni-moderation-latest",
            input=input_list,
        )

        results.append({"url": url, "response": response})

    return get_omni_moderation_results(map_moderation_response_to_json(results))
