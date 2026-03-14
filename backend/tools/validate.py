from openai import OpenAI
from dotenv import load_dotenv
import json
import base64

load_dotenv()
client = OpenAI()

required_fields = {
    "is_plant": False,
    "reason": ""
}

SYSTEM_PROMPT = """
You are an expert at identifying plants. Analyze the provided image and return ONLY a JSON object with exactly these fields:
- "is_plant": boolean, True if the image contains a plant or plant material, False if the image doesn't
- "reason": string, briefly describe what plant material is visible ONLY if the image contains a plant or plant material and is_plant is True

Return ONLY the JSON object. No explanation, no markdown, no preamble.
"""


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def validate_image(image_base64: str) -> dict:
    messages = [
        {
            "role": "system", 
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": "low"
                    }
                }
            ]
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages = messages,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content 
    content_json = json.loads(content)

    for curr_field in required_fields:
        if curr_field not in content_json:
            content_json[curr_field] = required_fields[curr_field]
    
    return content_json