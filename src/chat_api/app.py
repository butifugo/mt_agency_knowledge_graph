"""FastAPI app exposing /chat and /health for the widget.

Run (from repo root, venv active):
    uvicorn src.chat_api.app:app --port 8001 --reload
"""
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.chat_api.answer import MissingAPIKey, synthesize
from src.chat_api.config import get_settings
from src.chat_api.personas import PersonaNotFound, get_persona
from src.chat_api.retrieval import get_retriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the graph at startup so the first request isn't slow and a missing
    # graph fails fast and loudly.
    get_retriever()
    yield


app = FastAPI(title="Montana Agency Answer API", version="0.1.0", lifespan=lifespan)

# Local demo: a read-only public-info API. Permissive CORS keeps the sample page simple.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Turn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    agency: Optional[str] = None
    persona: Optional[str] = None          # null = single-turn generic assistant
    history: List[Turn] = []               # prior turns the client echoes back
    state: Optional[dict] = None           # last conversation state (guided personas)


class Citation(BaseModel):
    title: str
    agency: str
    url: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    sources: List[Citation]
    followups: List[str] = []
    agency: Optional[str] = None
    strategy: str
    provider: str = ""
    model: str = ""
    persona: Optional[str] = None
    stage: Optional[str] = None
    state: Optional[dict] = None
    artifact: Optional[dict] = None
    handoff: Optional[dict] = None       # {to, name, label} when an advisor recommends a colleague


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/personas/{persona_id}")
def persona_meta(persona_id: str):
    """Public persona metadata the widget needs to render its opening + starter chips."""
    try:
        p = get_persona(persona_id)
    except PersonaNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:  # malformed persona YAML
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "id": p.id,
        "name": p.name,
        "audience": p.audience,
        "opening": p.opening,
        "starters": p.starters,
        # The plan-workspace scaffold: ordered stages (progress tracker) and the per-branch
        # artifact field-sets (plan document sections). Additive — older clients ignore these.
        "stages": p.stage_goals,
        "artifacts": p.artifacts,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="question is required")
    try:
        return synthesize(
            req.question.strip(),
            agency=req.agency,
            persona=req.persona,
            history=[t.model_dump() for t in req.history],
            state=req.state,
        )
    except (PersonaNotFound, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except MissingAPIKey as exc:
        raise HTTPException(status_code=503, detail=str(exc))
