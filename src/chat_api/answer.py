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

FOLLOWUP_OPEN = "<<FOLLOWUPS>>"
FOLLOWUP_CLOSE = "<</FOLLOWUPS>>"

SYSTEM_INSTRUCTIONS = (
    "You are a warm, helpful assistant for Montana state government public information. "
    "Your job is to be genuinely useful to residents and to move them one step closer to "
    "what they need.\n\n"
    "GROUNDING: Answer using ONLY the provided sources. Do not use outside knowledge or web "
    "results, and never invent facts, URLs, phone numbers, prices, business names, places, or "
    "procedures. Cite sources inline with bracketed numbers like [1] or [2]. Only ever use "
    "numbers that appear in the Source list (1 to N) — never cite a number higher than the last "
    "source.\n\n"
    "WHEN THE SOURCES DON'T FIT: If the provided sources are not actually about what the person "
    "asked, do NOT answer from outside knowledge and do NOT describe specifics that aren't in the "
    "sources. Instead, say plainly that you don't have Montana state-agency information on that "
    "specific topic, and point them to the agency most likely to help. An honest 'I don't have "
    "that' is always better than a confident guess.\n\n"
    "BE HELPFUL, NOT A DEAD END: When the sources ARE relevant but the person's wording doesn't "
    "match exactly, don't just say you don't know — share the most relevant information and "
    "resources the sources DO contain, point them to the agency, program, or page most likely to "
    "handle their need, and be clear about what you found versus what you couldn't confirm. "
    "Always offer a useful next step.\n\n"
    "FORMAT: Write in clean, simple Markdown — short paragraphs, **bold** for key terms, and "
    "bullet or numbered lists for steps or options. Be concise and scannable: aim for a few "
    "short paragraphs or a short list, not an exhaustive essay. Always leave room to finish "
    "with the follow-up block below.\n\n"
    "FOLLOW-UPS: After your answer, suggest 2-3 short follow-up questions that the provided "
    "sources can actually answer, to help the person go further. Put them at the very end inside "
    "this exact block and nowhere else (one question per line, no numbering):\n"
    f"{FOLLOWUP_OPEN}\n"
    "First follow-up question?\n"
    "Second follow-up question?\n"
    f"{FOLLOWUP_CLOSE}"
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


def strip_invalid_citations(text: str, n_sources: int) -> str:
    """Drop ``[n]`` markers that point past the Source list (keep 1..n_sources).

    The prompt asks the model not to over-cite, but models still occasionally emit
    e.g. ``[7]`` with 6 sources. We remove those at the API boundary so the answer
    string itself is trustworthy, then tidy the spacing a dropped marker leaves behind.
    """
    def repl(m: "re.Match") -> str:
        n = int(m.group(1))
        return m.group(0) if 1 <= n <= n_sources else ""

    text = re.sub(r"\[(\d+)\]", repl, text)
    text = re.sub(r"[ \t]+([.,;:)])", r"\1", text)  # " ." left by a dropped marker
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def split_followups(text: str) -> Tuple[str, List[str]]:
    """Split a model reply into (clean answer, follow-up questions).

    The model is asked to append a ``<<FOLLOWUPS>>…<</FOLLOWUPS>>`` block; we strip
    it from the visible answer and return up to three questions. Tolerates a missing
    closing marker and stray bullet/number prefixes.
    """
    body, sep, tail = text.partition(FOLLOWUP_OPEN)
    if not sep:
        return text.strip(), []
    tail = tail.split(FOLLOWUP_CLOSE, 1)[0]
    followups = []
    for line in tail.splitlines():
        q = re.sub(r"^[\s\-*\d.)]+", "", line).strip()
        if q:
            followups.append(q)
    return body.strip(), followups[:3]


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
            "followups": [],
            "agency": agency,
            "strategy": rag.search_strategy,
            "provider": settings["provider"],
            "model": "",
        }

    provider = get_provider()  # may raise ValueError (unknown provider)
    system_text, user_text = build_messages(question, sources)
    raw = provider.complete(system_text, user_text)  # may raise MissingAPIKey
    answer, followups = split_followups(raw)
    answer = strip_invalid_citations(answer, len(sources))

    cited = extract_cited(answer, sources) or [_public(s) for s in sources]
    return {
        "answer": answer,
        "citations": cited,
        "sources": [_public(s) for s in sources],
        "followups": followups,
        "agency": agency,
        "strategy": rag.search_strategy,
        "provider": provider.name,
        "model": provider.model,
    }
