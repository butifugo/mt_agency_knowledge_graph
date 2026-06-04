"""Answer synthesis: retrieve passages, ground the prompt, return a cited answer.

Provider-agnostic — the LLM call goes through ``providers.get_provider()`` (default set by
CHAT_PROVIDER). ``format_sources``, ``build_messages`` and ``extract_cited`` are pure and
unit-tested without any API call.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from src.chat_api.config import get_settings
from src.chat_api.providers import MissingAPIKey, get_provider  # re-exported for callers
from src.chat_api.retrieval import get_retriever

MAX_CONTENT_CHARS = 1500  # per-source content cap fed to the model

SYSTEM_INSTRUCTIONS = (
    "You are a helpful assistant for Montana state government public information. "
    "Answer the user's question using ONLY the provided sources. Do not use web search "
    "results or any knowledge beyond the provided sources, and never invent facts or links. "
    "Cite sources inline with bracketed numbers like [1] or [2] that refer to the numbered "
    "Source list. If the sources do not contain the answer, say you don't have that "
    "information and suggest the user check the relevant agency website."
)


def format_sources(results: List[Dict[str, Any]], max_sources: int) -> List[Dict[str, Any]]:
    """Turn RAGResult.results into citation-ready sources with grounding text."""
    sources: List[Dict[str, Any]] = []
    for doc in results:
        chunks = doc.get("chunks") or []
        content = "\n".join(c["content"] for c in chunks if c.get("content")).strip()
        if not content:
            continue  # a source with no text can't ground or be cited
        sources.append(
            {
                "title": doc.get("title") or "(untitled)",
                "agency": doc.get("agency") or "",
                "url": doc.get("source_url") or "",
                "snippet": " ".join(content.split())[:200],
                "content": content[:MAX_CONTENT_CHARS],
            }
        )
        if len(sources) >= max_sources:
            break
    return sources


def build_messages(question: str, sources: List[Dict[str, Any]]) -> Tuple[str, str]:
    """Build neutral (system_text, user_text). Providers format these for their own API."""
    src_block = "\n\n".join(
        f"[{i}] {s['title']} ({s['agency']}) — {s['url']}\n{s['content']}"
        for i, s in enumerate(sources, 1)
    )
    user = f"Sources:\n{src_block}\n\nQuestion: {question}"
    return SYSTEM_INSTRUCTIONS, user


def _public(source: Dict[str, Any]) -> Dict[str, Any]:
    return {k: source[k] for k in ("title", "agency", "url", "snippet")}


def extract_cited(answer_text: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return the sources actually referenced by [n] markers in the answer."""
    nums = {int(n) for n in re.findall(r"\[(\d+)\]", answer_text)}
    return [_public(s) for i, s in enumerate(sources, 1) if i in nums]


def synthesize(question: str, agency: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve, ground, and synthesize a cited answer using the configured provider."""
    settings = get_settings()
    retriever = get_retriever()
    top_k = settings["top_k"]

    rag = retriever.retrieve(
        question, top_k=top_k * 3 if agency else top_k, return_chunks=True
    )
    results = rag.results
    if agency:
        results = [d for d in results if d.get("agency") == agency] or rag.results

    sources = format_sources(results, top_k)
    if not sources:
        return {
            "answer": "I couldn't find relevant Montana agency content for that question.",
            "citations": [],
            "sources": [],
            "agency": agency,
            "strategy": rag.search_strategy,
            "provider": settings["provider"],
            "model": "",
        }

    provider = get_provider()  # may raise ValueError (unknown provider)
    system_text, user_text = build_messages(question, sources)
    answer = provider.complete(system_text, user_text)  # may raise MissingAPIKey

    cited = extract_cited(answer, sources) or [_public(s) for s in sources]
    return {
        "answer": answer,
        "citations": cited,
        "sources": [_public(s) for s in sources],
        "agency": agency,
        "strategy": rag.search_strategy,
        "provider": provider.name,
        "model": provider.model,
    }
