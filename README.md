# 🌿 Flora

**Plant disease diagnosis agent** — upload a photo, get a diagnosis.

**Live demo:** https://flora-nine-kappa.vercel.app  
**Backend:** https://flora-production-90a7.up.railway.app

---

## What it does

Flora is an AI agent that diagnoses plant diseases from photos. Upload an image of a sick plant, optionally describe symptoms, and Flora runs a multi-step reasoning pipeline to identify the disease, retrieve treatment protocols, assess urgency, and escalate to a human agronomist when confidence is too low to act on.

It is not a chatbot wrapper around GPT. The agent decides which tools to call, in what order, based on what it knows — and a second LLM pass reviews every response before it reaches the user.

---

## Architecture

![Flora architecture](docs/flora_architecture.svg)

### Why this architecture

**Vision as a tool, not a pipeline step.** The agent calls `vision_analyze` only when appropriate. If a user sends "what causes root rot?" with no image, the agent answers from its knowledge base without wasting a vision call. This was a deliberate choice — hardcoding vision into every request would have been simpler but wrong.

**Supervisor layer.** The first version had no supervision and would confidently recommend treatment plans for ambiguous 0.6-confidence diagnoses. The supervisor catches overconfidence, missing escalations, and unsafe advice before the response reaches the user. This is directly analogous to what Clay Bavor describes in tau-bench: the solution to unreliable AI responses is often more AI.

**RAG over fine-tuning.** Treatment protocols change. Embedding 15 disease documents into a FAISS index and retrieving at query time means the knowledge base can be updated without retraining. The tradeoff is retrieval quality depends on embedding similarity — a disease with an unusual name may not retrieve correctly.

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | React, Vite, Tailwind-adjacent CSS |
| Backend | FastAPI, Python 3.13 |
| Agent | OpenAI gpt-4o, function calling |
| Vision | GPT-4V (via vision_analyze tool) |
| RAG | FAISS, text-embedding-ada-002 |
| Hosting | Vercel (frontend), Railway (backend) |

---

## Tool definitions

### `vision_analyze(image_base64, user_description)`
Sends the image to GPT-4V with a structured prompt. Returns disease name, confidence score (0–1), observed symptoms, plant type, and a flag for escalation. Forces a best-guess response — "unknown" only when confidence is genuinely below 0.3.

### `rag_lookup(disease_name, plant_type)`
Retrieves the most relevant document from a FAISS index of 15 disease knowledge base files. Returns treatment steps, prevention protocols, and source citation.

### `severity_assess(disease_name, confidence_score, symptoms)`
Rule-based risk scoring. Returns CRITICAL / HIGH / MEDIUM / LOW / NONE / UNKNOWN. CRITICAL diseases (Late Blight, Yellow Leaf Curl Virus) always escalate regardless of confidence. UNKNOWN returned when confidence < 0.5.

### `escalate(reason, case_summary)`
Logs the case for human review. Called automatically when confidence < 0.5 or severity is CRITICAL.

---

## Supervisor layer

After the agent loop completes, a second LLM call reviews the response against the tool results. It checks for:

- **OVERCONFIDENCE** — agent responds with certainty when vision confidence < 0.7
- **MISSING ESCALATION** — confidence < 0.5 but no escalation called
- **UNSAFE ADVICE** — specific numeric pesticide dosages without professional caveat
- **WRONG SEVERITY** — mismatch between vision confidence and severity label
- **HALLUCINATION** — treatment steps not grounded in RAG results

Returns `{ approved, flag_reason, severity, suggested_fix }`. In testing, the supervisor caught ~65% of overconfident responses that passed through the base agent.

---

## Known failure modes

**1. Bacterial Spot misclassified as Early Blight**  
GPT-4V hallucinates concentric rings on Bacterial Spot lesions. Both produce dark leaf spots but the patterns are visually distinct to an agronomist. Confidence scores are appropriately lower (0.6–0.7) but not always low enough to trigger escalation.

**2. Early Blight / Late Blight confusion on ambiguous images**  
Lighting and image angle significantly affect whether GPT-4V distinguishes the two. Late Blight has a more irregular lesion pattern, but under overexposure both look similar. The supervisor catches some of these via the WRONG_SEVERITY check.

**3. Non-plant images - resolved**  
Added `validate_image` pre-check tool that runs before `vision_analyze`.
Rejects non-plant images in a single low-resolution GPT-4V call, preventing
unnecessary downstream tool calls and hallucinated diagnoses.

---

## Local setup

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env           # add OPENAI_API_KEY
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

---

## What I'd build next

- **Image validation** pre-tool to reject non-plant inputs
- **Conversation memory** — follow-up questions lose context of the original diagnosis
- **Confidence calibration** — the 0.5 escalation threshold was set by intuition; A/B testing against agronomist ground truth would produce a better number
- **Streaming responses** — large RAG retrievals cause noticeable latency; streaming would improve perceived performance significantly
