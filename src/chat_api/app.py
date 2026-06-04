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


class ChatRequest(BaseModel):
    question: str
    agency: Optional[str] = None


class Citation(BaseModel):
    title: str
    agency: str
    url: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    sources: List[Citation]
    agency: Optional[str] = None
    strategy: str
    provider: str = ""
    model: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="question is required")
    try:
        return synthesize(req.question.strip(), req.agency)
    except MissingAPIKey as exc:
        raise HTTPException(status_code=503, detail=str(exc))
