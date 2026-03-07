from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware 
from pydantic import BaseModel
from typing import Optional
from agent import run_agent 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    message: str = "I have uploaded a plant image. Please analyze it using vision_analyze to diagnose any diseases."
    image_base64: Optional[str] = None 

@app.post("/chat")
async def chat(request: ChatRequest):
    result = run_agent(request.message, request.image_base64)
    return result 
