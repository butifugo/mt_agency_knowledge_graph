"""Conversation state for guided personas (see ``docs/guided-personas.spec.md``).

State is computed by the server and echoed by the client each turn — there is **no
server-side session store**. The model emits a ``<<STATE>>{json}<</STATE>>`` block alongside
its answer; we extract and merge it, clamping illegal stage jumps. This mirrors the
``<<FOLLOWUPS>>`` extraction in ``answer.py``.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from src.chat_api.personas import Persona

STATE_OPEN = "<<STATE>>"
STATE_CLOSE = "<</STATE>>"
HANDOFF_OPEN = "<<HANDOFF>>"
HANDOFF_CLOSE = "<</HANDOFF>>"

# Primary: a fully delimited block. Fallback: an unterminated block (model dropped the close).
_STATE_RE = re.compile(re.escape(STATE_OPEN) + r"\s*(.*?)\s*" + re.escape(STATE_CLOSE), re.DOTALL)
_STATE_OPEN_RE = re.compile(re.escape(STATE_OPEN) + r"\s*(.*)", re.DOTALL)
_HANDOFF_RE = re.compile(re.escape(HANDOFF_OPEN) + r"\s*(.*?)\s*" + re.escape(HANDOFF_CLOSE), re.DOTALL)
_HANDOFF_OPEN_RE = re.compile(re.escape(HANDOFF_OPEN) + r"\s*(.*)", re.DOTALL)


def init_state(persona: Persona) -> Dict[str, Any]:
    """A fresh conversation state for a persona, parked at its start stage."""
    return {
        "persona": persona.id,
        "stage": persona.start_stage,
        "branch": None,
        "slots": {},
        "artifact": {},
        "turn": 0,
    }


def extract_state(text: str) -> Dict[str, Any]:
    """Parse the model's ``<<STATE>>{json}<</STATE>>`` delta. ``{}`` if absent/malformed."""
    m = _STATE_RE.search(text) or _STATE_OPEN_RE.search(text)
    if not m:
        return {}
    blob = m.group(1).split(STATE_CLOSE, 1)[0].strip()
    try:
        data = json.loads(blob)
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def strip_state_block(text: str) -> str:
    """Remove any ``<<STATE>>`` block from visible text (defensive — usually already gone)."""
    text = _STATE_RE.sub("", text)
    text = _STATE_OPEN_RE.sub("", text)  # unterminated block
    return text.strip()


def extract_handoff(text: str) -> Optional[Dict[str, str]]:
    """Parse an optional ``<<HANDOFF>>{"to":...,"label":...}<</HANDOFF>>`` block.

    The advisor emits this only when it recommends bringing in a fellow advisor. Returns
    ``{"to", "label"}`` (label may be ""), or ``None`` if absent/empty/malformed. The target
    id is validated against the registry by the caller (``answer.synthesize``).
    """
    m = _HANDOFF_RE.search(text) or _HANDOFF_OPEN_RE.search(text)
    if not m:
        return None
    blob = m.group(1).split(HANDOFF_CLOSE, 1)[0].strip()
    if not blob:
        return None
    try:
        data = json.loads(blob)
        if isinstance(data, dict) and data.get("to"):
            return {"to": str(data["to"]).strip(), "label": str(data.get("label") or "").strip()}
    except (ValueError, TypeError):
        pass
    # Tolerate a bare persona id instead of JSON.
    return {"to": blob.split()[0].strip(), "label": ""}


def strip_handoff_block(text: str) -> str:
    """Remove any ``<<HANDOFF>>`` block from visible text (defensive — usually already gone)."""
    text = _HANDOFF_RE.sub("", text)
    text = _HANDOFF_OPEN_RE.sub("", text)  # unterminated block
    return text.strip()


def merge_state(
    prev: Optional[Dict[str, Any]], delta: Dict[str, Any], persona: Persona
) -> Dict[str, Any]:
    """Merge a model state delta into the prior state. The server is authoritative.

    - ``slots`` / ``artifact``: shallow union (delta wins per key; empties ignored).
    - ``branch``: set when the delta provides a non-empty value.
    - ``stage``: advance at most one step forward AND only when the current stage's
      exit-condition slots are present; backward moves allowed; illegal jumps clamped.
    """
    state = init_state(persona) if not prev else json.loads(json.dumps(prev))
    state["persona"] = persona.id

    slots = state.get("slots") or {}
    for k, v in (delta.get("slots") or {}).items():
        if v not in (None, "", []):
            slots[k] = v
    state["slots"] = slots

    artifact = state.get("artifact") or {}
    for k, v in (delta.get("artifact") or {}).items():
        if v not in (None, "", []):
            artifact[k] = v
    state["artifact"] = artifact

    if delta.get("branch"):
        state["branch"] = delta["branch"]

    # Pass the now-merged slots and branch so _clamp_stage can evaluate exit conditions.
    state["stage"] = _clamp_stage(
        state.get("stage"),
        delta.get("stage"),
        persona,
        slots=state["slots"],
        branch=state.get("branch"),
    )
    state["turn"] = int(state.get("turn") or 0) + 1
    return state


# ---------------------------------------------------------------------------
# Stage exit-condition slot requirements (spec §2.4).
#
# Maps stage_id → callable(slots, branch) -> bool  that returns True when the
# stage's exit conditions are satisfied and a forward advance is permitted.
#
# Only slot-gated stages need an entry.  Stages with conversational/model-judged
# exits (ground, scaffold, fund_act, complete) are left out so they are never
# over-constrained — once in them the model may advance as soon as the content
# warrants it.
#
# orient: exits when `branch` is set (branch lives in state, not slots).
# scope:  exits when `community` AND (`plan_type` OR `business_need`) are in slots.
# ---------------------------------------------------------------------------
_STAGE_EXIT_SATISFIED: Dict[str, Any] = {
    "orient": lambda slots, branch: bool(branch),
    "scope": lambda slots, branch: bool(
        slots.get("community")
        and (slots.get("plan_type") or slots.get("business_need"))
    ),
}


def _clamp_stage(
    current: Optional[str],
    requested: Optional[str],
    persona: Persona,
    *,
    slots: Optional[Dict[str, Any]] = None,
    branch: Optional[str] = None,
) -> str:
    """Allow stay / one-step-forward (if exit conditions met) / any-backward; clamp illegal jumps.

    Two rules (spec §2.4):
      1. Forward advance is at most ONE step per turn.
      2. A forward advance is only permitted when the CURRENT stage's exit conditions are
         satisfied (slot-gated stages only; conversational stages advance freely).

    If either rule is violated the stage stays at the highest legal value.
    """
    ids = persona.stage_ids
    if not ids:
        return requested or current or ""
    cur = current if current in ids else ids[0]
    if not requested or requested not in ids:
        return cur
    ci, ri = ids.index(cur), ids.index(requested)

    # Backward movement is always allowed (user changed community/plan type, etc.).
    if ri <= ci:
        return requested

    # Forward: must be exactly one step AND exit conditions satisfied.
    _slots = slots or {}
    exit_ok = _STAGE_EXIT_SATISFIED.get(cur, lambda s, b: True)(_slots, branch)

    if ri > ci + 1:
        # Multi-step jump: clamp to the next stage IF exit conditions are met,
        # otherwise hold at the current stage.
        return ids[ci + 1] if exit_ok else cur

    # Exactly one step forward: permitted only when exit conditions are met.
    return requested if exit_ok else cur
