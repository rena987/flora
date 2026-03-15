from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.responses import StreamingResponse
from openai import OpenAI
from supervisor import review_response
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
from agent import run_agent, run_agent_tools
from fastapi import HTTPException

app = FastAPI()
client = OpenAI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    message: str = "I have uploaded a plant image. Please analyze it using vision_analyze to diagnose any diseases."
    image_base64: Optional[str] = None 
    history: Optional[list] = None # list of {role, content}

@app.post("/chat")
async def chat(request: ChatRequest):
    result = run_agent(request.message, request.image_base64)
    return result 

async def generate(request: ChatRequest):
    history = request.history or []
    messages, trace = run_agent_tools(request.message, request.image_base64, history)

    clean_messages = []
    for m in messages:
        if isinstance(m, dict):
            clean_messages.append(m)
        else:
            clean_messages.append(m.model_dump())

    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=clean_messages,
        stream=True
    )

    full_response = ""
    for chunk in stream: 
        delta = chunk.choices[0].delta.content 
        if delta:
            full_response += delta 
            yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"
    
    trace["supervisor"] = review_response(full_response, trace)
    trace["total_latency_ms"] = sum(s["latency_ms"] for s in trace["steps"])
    traces_dir = Path("traces")
    traces_dir.mkdir(exist_ok = True)
    (traces_dir / f"{trace['request_id']}.json").write_text(json.dumps(trace, indent=2))

    yield f"data: {json.dumps({'type': 'done', 'trace': trace, 'supervisor': trace['supervisor']})}\n\n"

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(generate(request), media_type="text/event-stream")

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

        