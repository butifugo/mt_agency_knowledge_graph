"""Persona registry: declarative guided-expert configs from ``personas/*.yaml``.

A persona is **configuration, not code** (see ``docs/guided-personas.spec.md``). It supplies
the system-prompt voice, retrieval scope, goals, and a stage machine; the chat API and the MCP
server load it by ``id``. Retrieval and the graph are untouched — this layer only shapes voice
and scope. Adding a persona = drop a YAML file in ``personas/``; no code change.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml

PERSONA_DIR = Path(__file__).resolve().parents[2] / "personas"

REQUIRED = ("id", "name", "voice", "scope", "goals", "flow")


class PersonaNotFound(KeyError):
    """Raised when a persona id has no backing YAML file."""


@dataclass
class Persona:
    """Thin typed view over a parsed persona YAML dict."""

    raw: Dict[str, Any]

    @property
    def id(self) -> str:
        return self.raw["id"]

    @property
    def name(self) -> str:
        return self.raw["name"]

    @property
    def audience(self) -> str:
        return self.raw.get("audience", "")

    @property
    def voice(self) -> str:
        return self.raw["voice"]

    @property
    def scope(self) -> Dict[str, Any]:
        return self.raw.get("scope") or {}

    @property
    def goals(self) -> List[str]:
        return self.raw.get("goals") or []

    @property
    def opening(self) -> str:
        return self.raw.get("opening", "")

    @property
    def starters(self) -> List[str]:
        return self.raw.get("starters") or []

    @property
    def mcp(self) -> Dict[str, Any]:
        return self.raw.get("mcp") or {}

    @property
    def stages(self) -> List[Dict[str, Any]]:
        return (self.raw.get("flow") or {}).get("stages") or []

    @property
    def stage_ids(self) -> List[str]:
        return [s["id"] for s in self.stages]

    @property
    def stage_goals(self) -> List[Dict[str, str]]:
        """Ordered ``[{id, goal}]`` for a UI progress tracker (the plan workspace)."""
        return [{"id": s.get("id", ""), "goal": s.get("goal", "")} for s in self.stages]

    @property
    def artifacts(self) -> Dict[str, List[str]]:
        """The deliverable field-sets keyed by branch (e.g. ``build_plan`` → field ids).

        These ordered field lists are the sections of the plan document the workspace renders.
        """
        return self.raw.get("artifacts") or {}

    @property
    def start_stage(self) -> str:
        flow = self.raw.get("flow") or {}
        return flow.get("start_stage") or (self.stage_ids[0] if self.stage_ids else "")

    def stage(self, stage_id: str) -> Dict[str, Any]:
        """Return a stage dict by id, falling back to the first stage if unknown."""
        for s in self.stages:
            if s.get("id") == stage_id:
                return s
        return self.stages[0] if self.stages else {"id": stage_id, "goal": "", "guidance": ""}


def _validate(data: Dict[str, Any], name: str) -> None:
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        raise ValueError(f"persona '{name}' missing required fields: {missing}")
    if not (data.get("flow") or {}).get("stages"):
        raise ValueError(f"persona '{name}' has no flow.stages")


@lru_cache(maxsize=None)
def get_persona(persona_id: str) -> Persona:
    """Load and cache a persona by id. Raises PersonaNotFound if the YAML is absent."""
    # Resolve and confine to PERSONA_DIR: persona_id arrives from the request/MCP client, so a
    # crafted value like "../config" must not escape the personas directory.
    path = (PERSONA_DIR / f"{persona_id}.yaml").resolve()
    if not path.is_relative_to(PERSONA_DIR.resolve()) or not path.exists():
        raise PersonaNotFound(f"No persona '{persona_id}' in {PERSONA_DIR}")
    data = yaml.safe_load(path.read_text())
    _validate(data, persona_id)
    return Persona(data)


@lru_cache(maxsize=1)
def list_personas() -> List[Dict[str, str]]:
    """Public catalog of available personas (id, name, audience)."""
    out: List[Dict[str, str]] = []
    for p in sorted(PERSONA_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(p.read_text())
            out.append(
                {
                    "id": data["id"],
                    "name": data.get("name", data["id"]),
                    "audience": data.get("audience", ""),
                }
            )
        except Exception:
            continue  # a malformed file shouldn't break the catalog
    return out
