from openai import OpenAI
from rich.json import JSON

client = OpenAI(api_key='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')

response = client.moderations.create(
    model="omni-moderation-latest",
    input=[
        {"type": "text", "text": "...text to classify goes here..."},
        {
            "type": "image_url",
            "image_url": {
                "url": "https://drive.google.com/uc?export=download&id=1tdVGIuRFPkU0NFin0F_WR5WZUTKKy_sP",
                # can also use base64 encoded image URLs
                # "url": "data:image/jpeg;base64,abcdefg..."
            }
        },
    ],
)

data = response.model_dump()

result = data["results"][0]

category_scores = result["category_scores"]
# Filter and print only the entries where the value > 0.5
filtered = {k: v for k, v in category_scores.items() if v > 0.5}
print(filtered)

print(response.model_dump_json())