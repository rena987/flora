TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "validate_image",
            "description": """ALWAYS call this first when a user inputs an image before you call vision_analyze.
            if validate_image returns is_plant=False, explain politely that you can only diagnose plant diseases 
            and stop.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_base64": {
                        "type": "string",
                        "description": "encoded image"
                    }
                },
                "required": ["image_base64"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "vision_analyze",
            "description": """ALWAYS call this first when a user describes any plant symptoms or problems, 
            even without an image. skip if user already knows the plant's disease or problem. 
            skip if user expresses complete uncertainty with no specific symptoms, call escalate instead. Call immediately — 
            do not ask the user for an image first.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_base64": {
                        "type": "string",
                        "description": "encoded image"
                    },
                    "user_description": {
                        "type": "string",
                        "description": "what the user said about the plant"
                    }
                },
                "required": ["user_description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rag_lookup",
            "description": """DEFINITELY call this after vision_analyze has returned a confirmed disease. 
            However, AWLWAYS call if we need treatment protocols or care information.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "disease_name": {
                        "type": "string",
                        "description": "name of a diasease like Powdery Mildew, Rust, Downy Mildew, etc"
                    },
                    "plant_type": {
                        "type": "string",
                        "description": "name of plant type like Boxwood, Rose, Hydrangea, etc"
                    }
                },
                "required": ["disease_name", "plant_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "severity_assess",
            "description": """DEFINITELY call this after vision_analyze has returned a confirmed disease name. 
            However, ALWAYS call if diagnosis is made to determine urgency and risk level.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "disease_name": {
                        "type": "string",
                        "description": "name of a diasease like Powdery Mildew, Rust, Downy Mildew, etc"
                    },
                    "confidence_score": {
                        "type": "number",
                        "description": "number betwene 0 and 1"
                    },
                    "symptoms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "array of strings that describe symptoms of disease like white to grayish spots, patches on leaves, etc"
                    }
                },
                "required": ["disease_name", "confidence_score", "symptoms"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate",
            "description": """ALWAYS call this when user expresses complete uncertainty with no identifiable symptoms (e.g. 
            I have no idea what's wrong), when confidence from vision_analyze is below 0.5, or when situation is critical. 
             Do not call vision_analyze first in these cases.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "reason for uncertainty like confidence is very low"
                    },
                    "case_summary": {
                        "type": "string",
                        "description": "summary of plant's symptoms and history of these diagnoses"
                    }
                },
                "required": ["reason", "case_summary"]
            }
        }
    }
]

if __name__ == "__main__":
    print(len(TOOLS))