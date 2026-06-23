"""Answer synthesis: retrieve passages, ground the prompt, return a cited answer.

Provider-agnostic — the LLM call goes through ``providers.get_provider()`` (default set by
CHAT_PROVIDER). ``format_sources``, ``build_messages`` and ``extract_cited`` are pure and
unit-tested without any API call.
"""
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from src.chat_api.config import get_settings
from src.chat_api.conversation import (
    extract_handoff,
    extract_state,
    merge_state,
    strip_handoff_block,
    strip_state_block,
)
from src.chat_api.personas import Persona, PersonaNotFound, get_persona, list_personas
from src.chat_api.providers import History, MissingAPIKey, get_provider  # re-exported for callers
from src.chat_api.retrieval import build_node_filter, get_retriever

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
    "FOLLOW-UPS: End every reply with 1-3 short questions the user is likely to ask next, "
    "written in the user's OWN first-person voice — as if THEY are asking you (e.g. \"How do "
    "I renew my license?\", \"What documents do I need?\"), never questions you ask them. Only "
    "include ones the sources can actually answer. Put them ONLY inside this block (one per "
    "line, no numbering):\n"
    f"{FOLLOWUP_OPEN}\n"
    "How do I…?\n"
    "What do I need to…?\n"
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


def _user_block(question: str, sources: List[Dict[str, Any]]) -> str:
    """The grounded user turn: the numbered Source list followed by the question."""
    src_block = "\n\n".join(
        f"[{i}] {s['title']} ({s['agency']}) — {s['url']}\n{s['content']}"
        for i, s in enumerate(sources, 1)
    )
    return f"Sources:\n{src_block}\n\nQuestion: {question}"


def build_messages(question: str, sources: List[Dict[str, Any]]) -> Tuple[str, str]:
    """Build neutral (system_text, user_text). Providers format these for their own API."""
    return SYSTEM_INSTRUCTIONS, _user_block(question, sources)


def _team_roster(persona: Persona) -> str:
    """A one-line-per-colleague roster (every other persona) for handoff awareness."""
    lines = []
    for p in list_personas():
        if p["id"] == persona.id:
            continue
        tag = " ".join((p.get("audience") or "").split())[:120]
        lines.append(f"- {p['name']} (id: {p['id']})" + (f" — {tag}" if tag else ""))
    return "\n".join(lines)


def _conversation_paradigm(persona: Persona) -> str:
    """Cross-cutting conversation style applied to every advisor, every turn.

    Centralized here (not duplicated into each persona's ``voice``) so the whole team shares one
    natural-flow paradigm: conversational tone, citations woven inline, first-person suggestions,
    and collaboration — naming a colleague and offering a one-tap handoff when a topic is theirs.
    """
    roster = _team_roster(persona)
    parts = [
        "HOW YOU TALK (every reply):\n"
        "- Sound like a real advisor talking across the table — not a brochure, not a form. "
        "React to what they just said in a few words, then move it forward. Warm, plain, "
        "specific; contractions are good; vary your rhythm. Never bureaucratic, never a wall of bullets.\n"
        "- Keep it to ~2-4 sentences (or a couple of quick bullets). Say one genuinely useful thing, "
        "then ask ONE natural question to keep going — converse, don't interrogate.\n"
        "- Weave citations into the sentence right after the claim they support, like a natural "
        "footnote — e.g. \"A growth policy starts from your community profile data [1], so let's "
        "pull yours.\" Don't stack [1][2][3] at the end, and never write \"According to Source 1.\"",
        "SUGGESTIONS ARE THE USER'S OWN NEXT PROMPTS (this matters — get it right):\n"
        "- The <<FOLLOWUPS>> are suggested prompts the USER taps to send YOU next, written as the "
        "user speaking, in their first-person voice. Make them suggestive and actionable — a request "
        "or question that moves things forward — and ground them in what you're discussing right now "
        "(use their community/plan when you know it). Keep each short (~3-8 words).\n"
        "- DO, in the user's voice: \"Outline the sections for my growth policy\", \"Help me find "
        "funding for this\", \"Pull Red Lodge's profile data\", \"What data do I already have?\"\n"
        "- DON'T write them from YOUR side and DON'T use bland templates. Never \"Would you like "
        "to…\", \"Do you want me to…\", \"I can help you…\", and never a generic \"How do I…?\" stub. "
        "They are the user's words to you, not your questions to them. Only suggest things your "
        "sources can actually answer.",
        "THE DELIVERABLE IS A WORK PLAN — END IT WITH ACTION ITEMS:\n"
        "- Alongside the narrative artifact fields, build an `action_items` list inside the "
        "<<STATE>> artifact object: the concrete, ordered next steps the user should take to move "
        "forward. Start it once you're grounded in sources and keep refining it; by the time you "
        "wrap up it should be the user's real to-do list.\n"
        "- Each action item is an object: {\"task\":\"…\",\"owner\":\"…\",\"when\":\"…\",\"cite\":\"[n]\"}.\n"
        "  • task — a short imperative step in plain language (\"Adopt the growth policy by "
        "resolution\", \"Pull your Community Profile data\").\n"
        "  • owner — who acts: an office, board, or program NAMED in the sources, or \"you\" / "
        "\"your community\" when it's theirs. Never invent an office or contact.\n"
        "  • when — rough sequence or timing (\"first\", \"before drafting\", \"next funding "
        "cycle\"). Omit it rather than guess a date or deadline.\n"
        "  • cite — the [n] source the step is grounded in, when one applies; omit for a purely "
        "procedural step the user owns.\n"
        "- Emit the FULL action_items list every time you change it (it REPLACES the prior list, it "
        "does not append). Keep it to the handful of steps that actually matter, and ground each in "
        "the sources wherever you can — same grounding rule as the rest of the answer.",
    ]
    if roster:
        parts.append(
            "YOU'RE PART OF A TEAM OF ADVISORS:\n"
            "Your colleagues on the Community Planning Platform:\n" + roster + "\n"
            "- When the conversation moves into a colleague's lane, say so naturally and offer to "
            "bring them in by name (e.g. \"The funding side is really the Funding & Grants Advisor's "
            "specialty — want me to bring them in?\"). Don't guess outside your lane; hand off.\n"
            "- To offer a handoff, add this OPTIONAL block LAST, after <<STATE>> — at most one, and "
            "only when you genuinely recommend switching:\n"
            "<<HANDOFF>>{\"to\":\"<colleague persona id>\",\"label\":\"Bring in the <Colleague Name>\"}<</HANDOFF>>"
        )
    return "\n\n".join(parts)


def build_persona_system(persona: Persona, state: Optional[Dict[str, Any]]) -> str:
    """Assemble a persona's system prompt: voice + shared paradigm + goals + state + stage guidance.

    Replaces ``SYSTEM_INSTRUCTIONS`` for a persona turn. The persona's ``voice`` carries its
    identity + the grounding/citation/``<<FOLLOWUPS>>``/``<<STATE>>`` contract; the shared
    conversation paradigm shapes tone/citations/handoff across the whole team; and the per-turn
    part says where we are in the flow and what the active stage should accomplish.
    """
    stage_id = (state or {}).get("stage") or persona.start_stage
    st = persona.stage(stage_id)
    summary = {
        "stage": stage_id,
        "branch": (state or {}).get("branch"),
        "slots": (state or {}).get("slots") or {},
        "artifact_fields_done": sorted(((state or {}).get("artifact") or {}).keys()),
    }
    parts = [
        persona.voice.strip(),
        _conversation_paradigm(persona),
        "YOUR GOALS (in order):\n" + "\n".join(f"- {g}" for g in persona.goals),
        "CONVERSATION STATE (authoritative — do not contradict it):\n"
        + json.dumps(summary, ensure_ascii=False),
        f"ACTIVE STAGE — {stage_id}: {st.get('goal', '')}\n{(st.get('guidance') or '').strip()}",
        "Advance at most one stage this turn, and only once the stage's needs are met. End every "
        "reply with the <<FOLLOWUPS>> block, then the <<STATE>> block, then an optional <<HANDOFF>> "
        "block — exactly as instructed.",
    ]
    return "\n\n".join(p for p in parts if p)


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


def synthesize(
    question: str,
    agency: Optional[str] = None,
    persona: Optional[str] = None,
    history: History = None,
    state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Retrieve, ground, and synthesize a cited answer using the configured provider.

    With ``persona`` set, the answer is shaped by the persona's voice + stage machine, retrieval
    is narrowed by ``persona.scope``, and a merged conversation ``state`` is returned for the
    client to echo back. With ``persona=None`` this behaves exactly as the single-turn assistant.
    """
    settings = get_settings()
    retriever = get_retriever()
    top_k = settings["top_k"]

    persona_obj = get_persona(persona) if persona else None  # may raise PersonaNotFound
    scope = persona_obj.scope if persona_obj else {}
    eff_agency = agency or scope.get("agency")
    node_filter = build_node_filter(eff_agency, scope.get("url_contains"))

    rag = retriever.retrieve(question, top_k=top_k, return_chunks=True, node_filter=node_filter)
    sources = format_sources(rag.results, top_k)
    if not sources and node_filter:
        # Nothing in scope for this query — answer from the whole graph rather than go silent.
        rag = retriever.retrieve(question, top_k=top_k, return_chunks=True)
        sources = format_sources(rag.results, top_k)

    base: Dict[str, Any] = {
        "agency": eff_agency,
        "strategy": rag.search_strategy,
        "persona": persona_obj.id if persona_obj else None,
    }
    if not sources:
        empty = {
            "answer": "I couldn't find relevant Montana agency content for that question.",
            "citations": [],
            "sources": [],
            "followups": [],
            "provider": settings["provider"],
            "model": "",
            "stage": (state or {}).get("stage"),
            "state": state,
            "artifact": (state or {}).get("artifact"),
        }
        empty.update(base)
        return empty

    provider = get_provider()  # may raise ValueError (unknown provider)
    if persona_obj:
        system_text = build_persona_system(persona_obj, state)
    else:
        system_text = SYSTEM_INSTRUCTIONS
    user_text = _user_block(question, sources)
    raw = provider.complete(system_text, user_text, history)  # may raise MissingAPIKey

    answer, followups = split_followups(raw)
    answer = strip_handoff_block(strip_state_block(answer))
    answer = strip_invalid_citations(answer, len(sources))

    cited = extract_cited(answer, sources) or [_public(s) for s in sources]
    out = {
        "answer": answer,
        "citations": cited,
        "sources": [_public(s) for s in sources],
        "followups": followups,
        "provider": provider.name,
        "model": provider.model,
    }
    out.update(base)

    if persona_obj:
        new_state = merge_state(state, extract_state(raw), persona_obj)
        out["state"] = new_state
        out["stage"] = new_state["stage"]
        out["artifact"] = new_state["artifact"]
        out["handoff"] = _resolve_handoff(extract_handoff(raw), persona_obj)
    else:
        out["state"] = out["stage"] = out["artifact"] = out["handoff"] = None
    return out


def _resolve_handoff(
    handoff: Optional[Dict[str, str]], persona: Persona
) -> Optional[Dict[str, str]]:
    """Validate a model-proposed handoff: target must be a real, different persona.

    Returns ``{to, name, label}`` for the client, or ``None`` if the target is unknown or is
    the current advisor (the model occasionally suggests handing off to itself)."""
    if not handoff or not handoff.get("to"):
        return None
    to = handoff["to"]
    if to == persona.id:
        return None
    try:
        target = get_persona(to)
    except PersonaNotFound:
        return None
    return {
        "to": target.id,
        "name": target.name,
        "label": handoff.get("label") or f"Bring in the {target.name}",
    }
