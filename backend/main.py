from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware 
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
from agent import run_agent 
from fastapi import HTTPException

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

@app.get("/traces")
async def get_traces():
    traces_dir = Path("traces")
    if not traces_dir.exists():
        return []
    traces = []
    sorted_traces = sorted(traces_dir.glob("*.json"), reverse=True)

    for curr_trace_file in sorted_traces: 
        curr_trace = json.loads(curr_trace_file.read_text())
        traces.append({
            "request_id": curr_trace["request_id"],
            "timestamp": curr_trace["timestamp"],
            "image_present": curr_trace["image_present"],
            "tools_called": [step["tool"] for step in curr_trace["steps"]],
            "total_latency_ms": curr_trace["total_latency_ms"],
            "supervisor_approved": curr_trace["supervisor"]["approved"]
        })
    
    return traces 

@app.get("/traces/{request_id}")
async def get_trace(request_id: str):
    trace_file = Path("traces") / f"{request_id}.json"
    if not trace_file.exists():
        raise HTTPException(status_code=404, detail="Trace not found")
    return json.loads(trace_file.read_text())

        