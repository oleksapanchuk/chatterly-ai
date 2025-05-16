from shared.moderation_result import ModerationResult
from shared.validation_types import ContentCategory


def get_omni_moderation_results(result):
    data: list[ModerationResult] = []

    for item in result:
        current_item = item['results'][0]

        if not current_item['flagged']:
            data.append(
                ModerationResult(
                    is_harmful=False,
                    categories=[],
                    score={}
                )
            )
            continue

        data.append(
            ModerationResult(
                is_harmful=True,
                categories=get_categories(current_item['categories']),
                score=get_content_moderation_score(current_item['category_scores'])
            )
        )

    print(data)

    return data


def get_categories(categories: dict[str, bool]):
    actual_categories: list[ContentCategory] = []

    for category, value in categories.items():
        if value:
            actual_categories.append(get_content_moderation_category(category))

    return actual_categories


def get_content_moderation_category(name: str):
    mapping = {
        'harassment': ContentCategory.HARASSMENT,
        'harassment_threatening': ContentCategory.HARASSMENT,
        'hate': ContentCategory.HATE_SPEECH,
        'hate_threatening': ContentCategory.HATE_SPEECH,
        'violence': ContentCategory.VIOLENCE,
        'violence_graphic': ContentCategory.VIOLENCE,
        'illicit_violent': ContentCategory.VIOLENCE,
        'self_harm': ContentCategory.SELF_HARM,
        'self_harm_instructions': ContentCategory.SELF_HARM,
        'self_harm_intent': ContentCategory.SELF_HARM,
        'sexual': ContentCategory.SEXUAL,
        'sexual_minors': ContentCategory.SEXUAL,
        'illicit': ContentCategory.MISINFORMATION,
    }

    return mapping.get(name, ContentCategory.NONE)


def get_content_moderation_score(category_scores: dict[str, float]):
    actual_score: dict[ContentCategory, float] = {}

    for category, value in category_scores.items():
        actual_score[get_content_moderation_category(category)] = value

    return actual_score

def map_moderation_response_to_json(results: list):
    mapped_results = []

    for result in results:
        url = result["url"]
        response = result["response"]

        mapped_response = {
            "url": url,
            "id": response.id,
            "model": response.model,
            "results": []
        }

        for res in response.results:
            mapped_result = {
                "categories": {
                    **res.categories.__dict__
                },
                "category_scores": {
                    **res.category_scores.__dict__
                },
                "flagged": res.flagged
            }
            mapped_response["results"].append(mapped_result)

        mapped_results.append(mapped_response)

    return mapped_results