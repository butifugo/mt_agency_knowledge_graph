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
    "You are a friendly Montana state-government help assistant having a quick back-and-forth "
    "with a resident. Talk like a helpful person, not a brochure or a form letter.\n\n"
    "ANSWER FIRST: Open with the actual help — the most useful answer plus the specific "
    "resource that gets them there (a page, form, program, or office), linked as an inline "
    "citation [1]. NEVER open by stating what you don't know or can't confirm — just help. If "
    "the sources only partly cover it, give what they do offer and the best next step, briefly, "
    "without dwelling on the gap.\n\n"
    "KEEP IT SHORT & CONVERSATIONAL: Usually 2-4 sentences or a few quick bullets — one step at "
    "a time, the way a person would chat. Don't dump everything at once; let the conversation "
    "unfold through the follow-ups.\n\n"
    "GROUNDING: Use ONLY the provided sources. Cite inline as [1], [2] mapping to the Source "
    "list (only numbers 1 to N, never higher). Never invent facts, links, phone numbers, prices, "
    "names, or procedures. If the sources genuinely don't cover the question, don't guess — in "
    "one short, friendly sentence point them to the agency most likely to help, then ask a "
    "follow-up. (Keep that pointer at the end, never as your opening.)\n\n"
    "FORMAT: Plain, simple Markdown; bold a key term or link when it helps. Always leave room to "
    "finish with the follow-up block.\n\n"
    "FOLLOW-UPS: End every reply with 1-3 short questions that move the conversation forward and "
    "that the sources can actually answer. Put them ONLY inside this block (one per line, no "
    "numbering):\n"
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
