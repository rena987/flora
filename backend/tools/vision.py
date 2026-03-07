from openai import OpenAI
from dotenv import load_dotenv
import json
import base64

load_dotenv()
client = OpenAI()

required_fields = {
    "disease": "unknown",
    "confidence": 0.0,
    "symptoms_observed": [],
    "plant_type": "unknown",
    "visual_confidence_note": "Unable to analyze",
    "needs_escalation": True
}

SYSTEM_PROMPT = """
You are a plant disease diagnosis expert. Analyze the provided image and return ONLY a JSON object with exactly these fields:
- "disease": string, the name of the disease or "healthy" or "unknown"
- "confidence": float between 0 and 1
- "symptoms_observed": array of strings describing what you see
- "plant_type": string, the type of plant
- "visual_confidence_note": string, one sentence explaining your confidence level
- "needs_escalation": boolean, true if confidence is below 0.5 or disease is unidentifiable

Known diseases to identify include: Early Blight, Late Blight, Septoria Leaf Spot, 
Bacterial Spot, Leaf Mold, Target Spot, Powdery Mildew, Rust, Root Rot. 
If symptoms match one of these, use that name. Only return "unknown" if truly unidentifiable.

Known types of plants to identify: Potato, Tomato

Return ONLY the JSON object. No explanation, no markdown, no preamble.

"""

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_image(image_base64: str, user_description: str) -> dict:
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
                        "detail": "high"
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

if __name__ == "__main__":
    img_path = "test_images/tomato_early_blight.jpg"
    encoded_img = encode_image(img_path)
    output_json = analyze_image(encoded_img, "I think my plant is sick")
    print("Tomato Early Blight: ", output_json)

    img_path = "test_images/tomato_late_blight.jpg"
    encoded_img = encode_image(img_path)
    output_json = analyze_image(encoded_img, "I think my plant is sick")
    print("Tomato Late Blight: ", output_json)

    img_path = "test_images/potato_early_blight.jpg"
    encoded_img = encode_image(img_path)
    output_json = analyze_image(encoded_img, "I think my plant is sick")
    print("Potato Early Blight: ", output_json)

    img_path = "test_images/tomato_septoria_leaf_spot.jpg"
    encoded_img = encode_image(img_path)
    output_json = analyze_image(encoded_img, "I think my plant is sick")
    print("Tomato Septoria Leaf Spot: ", output_json)

    img_path = "test_images/tomato_healthy.jpg"
    encoded_img = encode_image(img_path)
    output_json = analyze_image(encoded_img, "I think my plant is sick")
    print("Tomato Healthy: ", output_json)



# KNOWN LIMITATION: Bacterial spot with large yellow patches is misclassified 
# as Early Blight with high confidence (0.85). Model hallucinates concentric 
# rings not present in image. This is a known LLM hallucination pattern — 
# the supervisor layer is designed to catch these overconfident diagnoses.
# See: Clay Bavor tau-bench paper on agent reliability.


# KNOWN LIMITATION 2: tomato_early_blight.jpg misclassified as Late Blight (0.8).
# Early vs Late Blight are visually similar in advanced stages — model conflates them.
# Supervisor layer and human escalation exist for exactly this reason.