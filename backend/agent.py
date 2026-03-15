from openai import OpenAI
from tools import schemas 
from dotenv import load_dotenv
import json
import base64
import uuid 
import time 
from datetime import datetime, timezone
from pathlib import Path

from tools.vision import analyze_image 
from tools.rag import build_index, retrieve
from supervisor import review_response
from tools.severity import assess_severity
from tools.validate import validate_image

load_dotenv()
client = OpenAI()

SYSTEM_PROMPT = """Flora is an expert plant disease diagnosis agent.
RULE 0: If an image is attached, you MUST call validate_image before vision_analyze. If validate_image returns is_plant=false, explain politely that you can only diagnose plant diseases and stop
RULE 1: After validate_image confirms is_plant=true, you MUST call vision_analyze next.
RULE 2: Never diagnose from text alone without calling vision_analyze first.
RULE 3: If confidence is below 0.5, you must also call escalate.
RULE 4: Only escalate without vision if the user explicitly says they have no image and no symptoms.
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
    build_index()
    original_message = user_message 
    if image_base64:
        user_message = f"[IMAGE ATTACHED - you MUST call vision_analyze immediately] {user_message}"
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    trace = {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "image_present": image_base64 is not None,
        "user_message": original_message,
        "steps": [],
        "supervisor": None,
        "total_latency_ms": 0
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
            trace["supervisor"] = review_response(final_response, trace)
            trace["total_latency_ms"] = sum(s["latency_ms"] for s in trace["steps"])
            traces_dir = Path("traces")
            traces_dir.mkdir(exist_ok=True)
            (traces_dir / f"{trace['request_id']}.json").write_text(json.dumps(trace, indent=2))
            return {
                "response": final_response,
                "vision_result": next((s["output"] for s in trace["steps"] if s["tool"] == "vision_analyze"), None),
                "severity_result": next((s["output"] for s in trace["steps"] if s["tool"] == "severity_assess"), None),
                "tools_called": [s["tool"] for s in trace["steps"]],
                "supervisor": trace["supervisor"],
                "trace": trace
            }

        all_tool_calls = response.choices[0].message.tool_calls
        messages.append(response.choices[0].message)
        for tool_call in all_tool_calls: 
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            start = time.perf_counter()

            if tool_name == "validate_image":
                tool_result = validate_image(
                    image_base64 or ""
                )
            elif tool_name == "vision_analyze":
                tool_result = analyze_image(
                    image_base64 or "",
                    tool_args.get("user_description", "")
                )
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
            else:
                tool_result = mock_tool_results[tool_name]

            latency_ms = round((time.perf_counter() - start) * 1000)
            trace["steps"].append({
                "tool": tool_name,
                "inputs": tool_args,
                "output": tool_result,
                "latency_ms": latency_ms,
                "status": "success"
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            })
    
def run_agent_tools(user_message: str, image_base64: str = None, history: list = None) -> dict:
    build_index()
    if history is None: 
        history = []
    
    original_message = user_message 
    if image_base64:
        user_message = f"[IMAGE ATTACHED - you MUST call vision_analyze immediately] {user_message}"
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_message}
    ]
    trace = {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "image_present": image_base64 is not None,
        "user_message": original_message,
        "steps": [],
        "supervisor": None,
        "total_latency_ms": 0
    }

    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=schemas.TOOLS,
            tool_choice="auto"
        )
        
        if not response.choices[0].message.tool_calls:
            return messages, trace

        all_tool_calls = response.choices[0].message.tool_calls
        messages.append(response.choices[0].message)
        for tool_call in all_tool_calls: 
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            start = time.perf_counter()

            if tool_name == "validate_image":
                tool_result = validate_image(
                    image_base64 or ""
                )
            elif tool_name == "vision_analyze":
                tool_result = analyze_image(
                    image_base64 or "",
                    tool_args.get("user_description", "")
                )
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
            else:
                tool_result = mock_tool_results[tool_name]

            latency_ms = round((time.perf_counter() - start) * 1000)
            trace["steps"].append({
                "tool": tool_name,
                "inputs": tool_args,
                "output": tool_result,
                "latency_ms": latency_ms,
                "status": "success"
            })

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


    