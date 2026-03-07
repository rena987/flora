from openai import OpenAI
from tools import schemas 
from dotenv import load_dotenv
import json
import base64

load_dotenv()
client = OpenAI()

required_fields = {
    "approved": True,
    "flag_reason": "",
    "severity": "APPROVED",
    "suggested_fix": ""
}

SUPERVISOR_PROMPT = """

You are a strict QA reviewer for Flora, a plant disease diagnosis agent. 
Your job is to review Flora's response before it reaches the user.

You will be given:
1. Flora's response to the user
2. The actual tool results that Flora's response was based on

Check for these specific issues:
- HALLUCINATION: Flora states treatment steps or facts not present in the tool results
- OVERCONFIDENCE: Flora gives a confident diagnosis when confidence score was below 0.7
- MISSING ESCALATION: Flora did not recommend expert review when confidence was below 0.5
- UNSAFE ADVICE: Flora recommended specific numeric dosages (e.g. "50ml per liter", 
  "2 tablespoons") or made medical claims. General fungicide recommendations 
  without specific measurements are acceptable and should NOT be flagged.
- WRONG SEVERITY: Flora's urgency does not match the risk level from severity_assess

Only flag genuine issues. Minor wording differences or general treatment 
recommendations are acceptable. When in doubt, approve.

Respond with ONLY a JSON object with exactly these fields:
- "approved": boolean
- "flag_reason": string, empty string if approved
- "severity": "APPROVED", "WARNING", or "CRITICAL"
- "suggested_fix": string, empty string if approved

"""

def review_response(agent_response: str, tool_results: dict) -> dict: 
    review_prompt = f"""
        Flora's response to review: {agent_response}

        Actual tool results: {json.dumps(tool_results, indent=2)}

        Review this response carefully.    

    """

    messages = [
        {"role": "system", "content": SUPERVISOR_PROMPT},
        {"role": "user", "content": review_prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    
    for field in required_fields:
        if field not in result: 
            result[field] = required_fields[field]
    
    return result 


if __name__ == "__main__":
    good_response = "Your tomato plant has Early Blight. Remove affected leaves and apply copper fungicide every 7-10 days."
    tool_results = {
        "vision": {"disease": "Early Blight", "confidence": 0.87},
        "severity": {"risk_level": "HIGH", "urgency": "Act within 48 hours"}
    }
    print("Case 1: ", review_response(good_response, tool_results))

    bad_response = "Your plant definitely has Early Blight, no doubt about it. Apply 50ml of fungicide per liter of water immediately."
    tool_results = {
        "vision": {"disease": "Early Blight", "confidence": 0.35},
        "severity": {"risk_level": "UNKNOWN"}
    }
    print("Case 2: ", review_response(bad_response, tool_results))