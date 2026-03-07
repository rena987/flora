from openai import OpenAI
from tools import schemas 
from dotenv import load_dotenv
import json
import base64

from tools.vision import analyze_image 
from tools.rag import build_index, retrieve
from supervisor import review_response
from tools.severity import assess_severity

build_index()
load_dotenv()
client = OpenAI()

SYSTEM_PROMPT = """Flora is an expert plant disease diagnosis agent. 
She always calls vision_analyze immediately when a user describes plant symptoms, 
even if no image is provided yet — the tool handles missing images gracefully. However, 
if user describes complete uncertainty with no symptoms, then skips vision_analyze and calls
escalate first. Besides that, she never diagnoses from text alone without calling vision_analyze first. 
If confidence is below 0.5 she must escalate. 
She is warm, clear, and avoids overwhelming users with jargon."""

mock_tool_results = {
    "vision_analyze": {
        "disease": "early_blight",
        "confidence": 0.87,
        "symptoms_observed": ["dark concentric spots", "yellowing around lesions"],
        "plant_type": "tomato",
        "visual_confidence_note": "clear fungal pattern visible on lower leaves"
    },
    "rag_lookup": {
        "disease": "early_blight",
        "treatment_steps": [
            "Remove and destroy affected leaves immediately",
            "Apply copper-based fungicide every 7-10 days",
            "Avoid overhead watering to reduce moisture on leaves",
            "Ensure adequate plant spacing for airflow"
        ],
        "prevention": "Rotate crops annually, use disease-resistant varieties",
        "sources": ["PlantVillage Protocol v2.1"]
    },
    "severity_assess": {
        "risk_level": "HIGH",
        "urgency": "Act within 48 hours",
        "spread_risk": "Can spread to neighboring plants via spores",
        "recommendation": "Immediate treatment required"
    },
    "escalate": {
        "status": "escalated",
        "case_id": "FLORA-2024-001",
        "message": "Your case has been flagged for review by a certified agronomist",
        "estimated_response": "Within 24 hours"
    }
}

def run_agent(user_message: str, image_base64: str = None) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    tool_summary = {
        "tools_called": [],
        "vision_result": None, 
        "severity_result": None
    }

    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=schemas.TOOLS,
            tool_choice="auto"
        )
        
        if not response.choices[0].message.tool_calls:
            final_response = response.choices[0].message.content
            return {
                "response": final_response,
                "vision_result": tool_summary["vision_result"],
                "severity_result": tool_summary["severity_result"],
                "tools_called": tool_summary["tools_called"],
                "supervisor": review_response(final_response, tool_summary)
            }

        all_tool_calls = response.choices[0].message.tool_calls
        messages.append(response.choices[0].message)
        for tool_call in all_tool_calls: 
            tool_name = tool_call.function.name
            tool_summary["tools_called"].append(tool_name)
            tool_args = json.loads(tool_call.function.arguments)

            if tool_name == "vision_analyze":
                tool_result = analyze_image(
                    image_base64 or "",
                    tool_args.get("user_description", "")
                )
                tool_summary["vision_result"] = tool_result
            elif tool_name == "rag_lookup":
                tool_result = retrieve(
                    tool_args.get("disease_name", ""),
                    tool_args.get("plant_type", "")
                )
            elif tool_name == "severity_assess":
                tool_result = assess_severity(
                    tool_args.get("disease_name", ""),
                    tool_args.get("confidence_score", 0.0),
                    tool_args.get("symptoms", [])
                )
                tool_summary["severity_result"] = tool_result
            else:
                tool_result = mock_tool_results[tool_name]

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            })
    


if __name__ == "__main__":
    with open("test_images/tomato_early_blight.jpg", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    result = run_agent("my tomato plant has dark spots", img_b64)
    print("RESPONSE:", result["response"])
    print("ANALYSIS OF IMAGE: ", result["vision_result"])
    print("ANALYSIS OF SEVERITY: ", result["severity_result"])
    print("SUPERVISOR:", result["supervisor"])
    print("TOOLS CALLED:", result["tools_called"])


    