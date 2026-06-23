"""Acceptance gates for the community-planning-guide persona (v1 gates AC-1/AC-2/AC-3).

See docs/guided-personas.spec.md §6.

AC-1 (flow): scripted 5-turn end-to-end drives orient → scope → ground → scaffold → fund_act;
  no multi-step jumps; state round-trips; branch persists.
AC-2 (scope): off-scope query returns only Community-Planning-Platform sources; no agency leak.
AC-3 (artifact completeness): build_plan branch reaching 'complete' has sections, ≥1 funding
  entry, and a non-null next_office.

All tests are hermetic: fake provider, real retriever (graph fixture from conftest.py).

Hardening note — slot-condition gate gap:
  The spec (§2.4) says stages advance "only when the exit condition's slots are present."
  merge_state / _clamp_stage enforce *at most one step per turn* but do NOT enforce that the
  exit-condition slots are filled before a single-step advance is permitted.  A model that emits
  {"stage":"ground"} without having set community/plan_type WILL advance. This is a real
  implementation gap.  test_ac1_slot_condition_not_enforced_KNOWN_GAP documents and proves the
  gap in place of a spurious passing assertion.
"""

import json

import pytest

from src.chat_api import answer as A
from src.chat_api.conversation import init_state, merge_state
from src.chat_api.personas import get_persona

PERSONA_ID = "community-planning-guide"


# ─── Fake provider helpers ────────────────────────────────────────────────────

def _make_canned(stage, branch=None, slots=None, artifact=None, answer="Test answer [1]."):
    """Return a canned provider response emitting the given STATE delta."""
    state_payload = {"stage": stage}
    if branch is not None:
        state_payload["branch"] = branch
    if slots:
        state_payload["slots"] = slots
    if artifact:
        state_payload["artifact"] = artifact

    return (
        f"{answer}\n\n"
        "<<FOLLOWUPS>>\nWhat's next?\n<</FOLLOWUPS>>\n"
        f"<<STATE>>\n{json.dumps(state_payload)}\n<</STATE>>"
    )


class _SequencedProvider:
    """Returns a different canned response each call, advancing through ``responses``."""

    name = "fake"
    model = "fake-1"

    def __init__(self, responses):
        self._responses = list(responses)
        self._idx = 0
        self.calls = []  # captures (system_text, user_text, history) per call

    def complete(self, system_text, user_text, history=None):
        self.calls.append((system_text, user_text, history))
        resp = self._responses[self._idx]
        self._idx += 1
        return resp


# ─── AC-1: 5-turn scripted end-to-end ────────────────────────────────────────

class TestAC1Flow:
    """AC-1 — scripted 5-turn conversation drives orient→scope→ground→scaffold→fund_act."""

    def _five_turn_responses(self):
        """Canned model responses for each of the 5 turns."""
        return [
            # Turn 1: model identifies branch, advances to scope
            _make_canned(
                stage="scope",
                branch="build_plan",
                slots={},
                answer="Great — let's build your planning document [1].",
            ),
            # Turn 2: model collects slots, advances to ground
            _make_canned(
                stage="ground",
                slots={"community": "Red Lodge", "plan_type": "growth_policy"},
                answer="Red Lodge growth policy — I've pulled the CPP guidance [1].",
            ),
            # Turn 3: model confirms direction, advances to scaffold
            _make_canned(
                stage="scaffold",
                artifact={"purpose": "Guide Red Lodge growth to 2040"},
                answer="Here's the CPP template for a growth policy [1].",
            ),
            # Turn 4: model builds artifact core, advances to fund_act
            _make_canned(
                stage="fund_act",
                artifact={"sections": ["Land Use", "Housing", "Transportation"],
                           "required_data": ["Community Profile", "Census data"]},
                answer="Your scaffold is taking shape [1].",
            ),
            # Turn 5: funding surfaced, advances to complete
            _make_canned(
                stage="complete",
                artifact={"funding": ["CDBG", "Montana Ready Communities"],
                           "next_office": "Commerce CPP office (406-841-2770)"},
                answer="Here are the programs that match your project [1].",
            ),
        ]

    def test_ac1_five_turn_stage_sequence(self, retriever, monkeypatch):
        """Each of the 5 turns advances exactly one stage; final stage is fund_act."""
        provider = _SequencedProvider(self._five_turn_responses())
        monkeypatch.setattr(A, "get_provider", lambda: provider)

        expected_stages = ["scope", "ground", "scaffold", "fund_act", "complete"]
        state = None
        history = []

        for turn_num, (question, expected_stage) in enumerate(
            zip(
                [
                    "I need to build a planning document",
                    "It's for Red Lodge — a growth policy",
                    "Yes, that's the right direction",
                    "Let's build the scaffold",
                    "What funding is available?",
                ],
                expected_stages,
            ),
            start=1,
        ):
            out = A.synthesize(
                question,
                persona=PERSONA_ID,
                history=history,
                state=state,
            )
            new_stage = out["stage"]
            assert new_stage == expected_stage, (
                f"Turn {turn_num}: expected stage '{expected_stage}', got '{new_stage}'"
            )
            # State round-trip: the returned state carries the new stage
            assert out["state"]["stage"] == expected_stage, (
                f"Turn {turn_num}: state['stage'] should match out['stage']"
            )
            state = out["state"]
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": out["answer"]})

    def test_ac1_branch_set_at_orient_and_persists(self, retriever, monkeypatch):
        """Branch is set on Turn 1 (orient) and persists unchanged through all turns."""
        provider = _SequencedProvider(self._five_turn_responses())
        monkeypatch.setattr(A, "get_provider", lambda: provider)

        state = None
        history = []
        questions = [
            "I need to build a planning document",
            "It's for Red Lodge — a growth policy",
            "Yes, that's the right direction",
            "Let's build the scaffold",
            "What funding is available?",
        ]
        for i, q in enumerate(questions, 1):
            out = A.synthesize(q, persona=PERSONA_ID, history=history, state=state)
            if i == 1:
                assert out["state"]["branch"] == "build_plan", (
                    "Branch must be set on Turn 1 (orient → scope)"
                )
            else:
                assert out["state"]["branch"] == "build_plan", (
                    f"Turn {i}: branch must persist as 'build_plan' once set"
                )
            state = out["state"]
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": out["answer"]})

    def test_ac1_no_multi_step_jump(self, retriever, monkeypatch):
        """Server clamps a 2+-step forward jump to at most one step.

        This is the clamping behaviour proven in test_conversation.py:test_stage_advances_one_step.
        Tested here via the synthesize() path to confirm the clamp holds end-to-end.
        """
        # Canned response attempts to jump orient → ground (2 steps, illegal)
        illegal_jump = _make_canned(
            stage="ground",  # from orient, should be clamped to scope
            branch="build_plan",
        )
        monkeypatch.setattr(A, "get_provider", lambda: _SequencedProvider([illegal_jump]))

        out = A.synthesize(
            "I want to build a growth policy",
            persona=PERSONA_ID,
            history=[],
            state=None,  # start at orient
        )
        # orient + 2 = ground → clamped to orient + 1 = scope
        assert out["stage"] == "scope", (
            f"Illegal 2-step jump from 'orient' must be clamped to 'scope'; got '{out['stage']}'"
        )

    def test_ac1_state_turn_counter_increments(self, retriever, monkeypatch):
        """state.turn increments by 1 each synthesize() call."""
        responses = self._five_turn_responses()[:3]
        provider = _SequencedProvider(responses)
        monkeypatch.setattr(A, "get_provider", lambda: provider)

        state = None
        history = []
        for expected_turn, question in enumerate(
            ["First", "Second", "Third"], start=1
        ):
            out = A.synthesize(question, persona=PERSONA_ID, history=history, state=state)
            assert out["state"]["turn"] == expected_turn, (
                f"Expected turn={expected_turn}, got {out['state']['turn']}"
            )
            state = out["state"]
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": out["answer"]})

    def test_ac1_history_reaches_provider(self, retriever, monkeypatch):
        """Prior history is threaded to the provider on every non-first turn."""
        responses = self._five_turn_responses()[:2]
        provider = _SequencedProvider(responses)
        monkeypatch.setattr(A, "get_provider", lambda: provider)

        out1 = A.synthesize("First question", persona=PERSONA_ID, history=[], state=None)
        state1 = out1["state"]

        out2 = A.synthesize(
            "Second question",
            persona=PERSONA_ID,
            history=[
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": out1["answer"]},
            ],
            state=state1,
        )
        # provider.calls[1] is the second call; history arg is index 2
        _, _, history_passed = provider.calls[1]
        assert history_passed, "Prior history must be passed to provider on Turn 2+"
        assert any(m["role"] == "assistant" for m in history_passed), (
            "Prior assistant turn must appear in threaded history"
        )


# ─── AC-1 slot-condition gate (was: known gap, now: enforced) ─────────────────

class TestAC1SlotConditionGate:
    """Verifies that _clamp_stage enforces exit-condition slots (spec §2.4).

    The spec requires: 'stages advance at most one step per turn AND only when the
    exit condition's slots are present; the server clamps illegal jumps back to the
    highest legal stage.'

    Both halves are tested:
      - Advance blocked when exit slots absent (held at current stage).
      - Advance permitted once exit slots are present.
    """

    def test_ac1_scope_to_ground_blocked_without_slots(self):
        """scope→ground must be clamped (held at scope) when community/plan_type absent.

        This was the AC-1 blocker.  The fix adds slot-gating to _clamp_stage so a
        single-step forward advance from a slot-gated stage is only allowed when the
        exit conditions are satisfied in the merged state.
        """
        p = get_persona(PERSONA_ID)
        s = init_state(p)
        # Advance orient→scope normally (branch set satisfies orient exit condition).
        s = merge_state(s, {"stage": "scope", "branch": "build_plan"}, p)
        assert s["stage"] == "scope"

        # Attempt scope→ground WITHOUT filling community or plan_type.
        s_after = merge_state(s, {"stage": "ground"}, p)
        assert s_after["stage"] == "scope", (
            f"scope→ground must be held at 'scope' when exit-condition slots are absent; "
            f"got '{s_after['stage']}'"
        )

    def test_ac1_scope_to_ground_permitted_with_slots(self):
        """scope→ground must be allowed once community AND plan_type slots are present."""
        p = get_persona(PERSONA_ID)
        s = init_state(p)
        s = merge_state(s, {"stage": "scope", "branch": "build_plan"}, p)
        assert s["stage"] == "scope"

        # Advance with the required slots present in the same delta.
        s_after = merge_state(
            s,
            {
                "stage": "ground",
                "slots": {"community": "Red Lodge", "plan_type": "growth_policy"},
            },
            p,
        )
        assert s_after["stage"] == "ground", (
            f"scope→ground must be permitted when community + plan_type are present; "
            f"got '{s_after['stage']}'"
        )

    def test_ac1_scope_to_ground_permitted_with_business_need(self):
        """business_need satisfies the scope exit condition for the evaluate_community branch."""
        p = get_persona(PERSONA_ID)
        s = init_state(p)
        s = merge_state(s, {"stage": "scope", "branch": "evaluate_community"}, p)

        s_after = merge_state(
            s,
            {
                "stage": "ground",
                "slots": {
                    "community": "Billings",
                    "business_need": "manufacturing facility",
                },
            },
            p,
        )
        assert s_after["stage"] == "ground", (
            f"scope→ground must be permitted with community + business_need; "
            f"got '{s_after['stage']}'"
        )

    def test_ac1_orient_to_scope_blocked_without_branch(self):
        """orient→scope must be held at orient when branch is absent."""
        p = get_persona(PERSONA_ID)
        s = init_state(p)  # orient, no branch
        s_after = merge_state(s, {"stage": "scope"}, p)  # no branch in delta either
        assert s_after["stage"] == "orient", (
            f"orient→scope must be held at 'orient' when branch is absent; "
            f"got '{s_after['stage']}'"
        )

    def test_ac1_orient_to_scope_permitted_with_branch(self):
        """orient→scope must be permitted once branch is set."""
        p = get_persona(PERSONA_ID)
        s = init_state(p)
        s_after = merge_state(s, {"stage": "scope", "branch": "build_plan"}, p)
        assert s_after["stage"] == "scope", (
            f"orient→scope must be permitted when branch is set; got '{s_after['stage']}'"
        )


# ─── AC-2: scope-leak negative test ──────────────────────────────────────────

class TestAC2ScopeIsolation:
    """AC-2 — off-scope query returns only CPP sources; no out-of-scope agency leaks."""

    def test_ac2_off_scope_query_returns_only_cpp_sources(self, retriever, monkeypatch):
        """Querying 'pesticide applicator licensing' (agriculture/DLI territory) with the
        community-planning-guide persona must return only Community-Planning-Platform sources.

        The node_filter built from persona.scope is applied at the candidate level — every
        node in the ranked pool must pass the filter — so even a topically irrelevant query
        returns CPP-domain results rather than leaking to other agencies.
        """
        monkeypatch.setattr(
            A,
            "get_provider",
            lambda: _SequencedProvider(
                [_make_canned("scope", branch="build_plan")]
            ),
        )

        out = A.synthesize(
            "pesticide applicator licensing",
            persona=PERSONA_ID,
            history=[],
            state=None,
        )

        assert out["sources"], (
            "Scoped retrieval returned no sources — CPP corpus may be missing from the graph"
        )
        for src in out["sources"]:
            assert src["agency"] == "commerce", (
                f"Scope leak: expected agency='commerce', got '{src['agency']}' "
                f"for URL {src['url']!r}"
            )
            assert "community-planning-platform" in src["url"].lower(), (
                f"Scope leak: URL does not contain 'community-planning-platform': {src['url']!r}"
            )

    def test_ac2_no_dli_or_agriculture_sources_in_persona_result(self, retriever, monkeypatch):
        """Agencies DLI and agriculture must not appear in persona-scoped results."""
        monkeypatch.setattr(
            A,
            "get_provider",
            lambda: _SequencedProvider(
                [_make_canned("scope", branch="build_plan")]
            ),
        )

        out = A.synthesize(
            "pesticide license renewal requirements",
            persona=PERSONA_ID,
            history=[],
            state=None,
        )

        leaked = [
            s for s in out.get("sources", [])
            if s.get("agency") in ("dli", "agriculture", "labor")
        ]
        assert not leaked, (
            f"Scope leak: out-of-scope agencies found in sources: {leaked}"
        )


# ─── AC-3: artifact completeness at complete ─────────────────────────────────

class TestAC3ArtifactCompleteness:
    """AC-3 — by 'complete', the build_plan artifact has sections, ≥1 funding, and next_office."""

    def _complete_branch_responses(self):
        """Drive the build_plan branch all the way to 'complete'."""
        return [
            # Turn 1: orient → scope, branch=build_plan
            _make_canned(
                stage="scope",
                branch="build_plan",
                answer="Happy to help build a growth policy [1].",
            ),
            # Turn 2: scope → ground, slots filled
            _make_canned(
                stage="ground",
                slots={"community": "Lewistown", "plan_type": "growth_policy"},
                answer="Here's the CPP page for growth policy [1].",
            ),
            # Turn 3: ground → scaffold, artifact core populated
            _make_canned(
                stage="scaffold",
                artifact={
                    "purpose": "Guide Lewistown growth",
                    "required_data": ["Community Profile", "Parcel data"],
                    "sections": [
                        "Introduction",
                        "Land Use Element",
                        "Housing Element",
                        "Transportation Element",
                        "Economic Development Element",
                    ],
                    "template": "https://commerce.mt.gov/Infrastructure-Planning/Community-Planning-Platform/Plan",
                },
                answer="Here's the scaffold for Lewistown's growth policy [1].",
            ),
            # Turn 4: scaffold → fund_act
            _make_canned(
                stage="fund_act",
                artifact={},
                answer="Let's find the right programs [1].",
            ),
            # Turn 5: fund_act → complete, funding and next_office populated
            _make_canned(
                stage="complete",
                artifact={
                    "funding": [
                        "Community Development Block Grant (CDBG)",
                        "Montana Ready Communities",
                    ],
                    "next_office": (
                        "Department of Commerce — Community Development Division, "
                        "406-841-2770, CommerceEDD@mt.gov"
                    ),
                    "sources": [
                        "https://commerce.mt.gov/Infrastructure-Planning/Community-Planning-Platform/Plans/Growth-Policy"
                    ],
                },
                answer="Here's your completed plan scaffold and next steps [1].",
            ),
        ]

    def test_ac3_artifact_has_sections_at_complete(self, retriever, monkeypatch):
        """build_plan artifact must have a non-empty 'sections' list at complete."""
        provider = _SequencedProvider(self._complete_branch_responses())
        monkeypatch.setattr(A, "get_provider", lambda: provider)

        state = None
        history = []
        questions = [
            "I need to build a planning document",
            "Lewistown — growth policy",
            "Yes, that's the right plan",
            "Build the scaffold",
            "What funding fits this?",
        ]
        for q in questions:
            out = A.synthesize(q, persona=PERSONA_ID, history=history, state=state)
            state = out["state"]
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": out["answer"]})

        assert out["stage"] == "complete", f"Expected 'complete', got '{out['stage']}'"
        artifact = out["artifact"]
        assert artifact.get("sections"), (
            "AC-3 FAIL: artifact.sections must be populated by 'complete'; got: "
            f"{artifact.get('sections')!r}"
        )
        assert len(artifact["sections"]) >= 1

    def test_ac3_artifact_has_funding_at_complete(self, retriever, monkeypatch):
        """build_plan artifact must have at least one grounded funding program at complete."""
        provider = _SequencedProvider(self._complete_branch_responses())
        monkeypatch.setattr(A, "get_provider", lambda: provider)

        state = None
        history = []
        questions = [
            "I need to build a planning document",
            "Lewistown — growth policy",
            "Yes, that's the right plan",
            "Build the scaffold",
            "What funding fits this?",
        ]
        for q in questions:
            out = A.synthesize(q, persona=PERSONA_ID, history=history, state=state)
            state = out["state"]
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": out["answer"]})

        assert out["stage"] == "complete"
        artifact = out["artifact"]
        funding = artifact.get("funding")
        assert funding and len(funding) >= 1, (
            f"AC-3 FAIL: artifact.funding must have ≥1 entry at complete; got: {funding!r}"
        )
        # Grounding check: at least one program name from the CPP source list must appear
        # (the canned responses use the spec's named programs — this proves the merge path
        # carries them through, not that a live LLM invented them)
        known_programs = {"cdbg", "montana ready communities", "montana main street", "slipa"}
        found = any(
            any(prog in entry.lower() for prog in known_programs)
            for entry in funding
        )
        assert found, (
            f"AC-3 FAIL: funding entries don't match any known CPP program: {funding}"
        )

    def test_ac3_artifact_has_next_office_at_complete(self, retriever, monkeypatch):
        """build_plan artifact must have a non-null next_office at complete."""
        provider = _SequencedProvider(self._complete_branch_responses())
        monkeypatch.setattr(A, "get_provider", lambda: provider)

        state = None
        history = []
        questions = [
            "I need to build a planning document",
            "Lewistown — growth policy",
            "Yes, that's the right plan",
            "Build the scaffold",
            "What funding fits this?",
        ]
        for q in questions:
            out = A.synthesize(q, persona=PERSONA_ID, history=history, state=state)
            state = out["state"]
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": out["answer"]})

        assert out["stage"] == "complete"
        artifact = out["artifact"]
        next_office = artifact.get("next_office")
        assert next_office, (
            f"AC-3 FAIL: artifact.next_office must be non-null at complete; got: {next_office!r}"
        )
        assert isinstance(next_office, str) and len(next_office) > 5

    def test_ac3_artifact_accumulates_across_all_turns(self, retriever, monkeypatch):
        """artifact fields from earlier turns persist into the complete stage (union semantics)."""
        provider = _SequencedProvider(self._complete_branch_responses())
        monkeypatch.setattr(A, "get_provider", lambda: provider)

        state = None
        history = []
        questions = [
            "I need to build a planning document",
            "Lewistown — growth policy",
            "Yes, that's the right plan",
            "Build the scaffold",
            "What funding fits this?",
        ]
        for q in questions:
            out = A.synthesize(q, persona=PERSONA_ID, history=history, state=state)
            state = out["state"]
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": out["answer"]})

        assert out["stage"] == "complete"
        artifact = out["artifact"]
        # All fields from turns 3/4/5 must be present (merge/union, not replace)
        for field in ("sections", "funding", "next_office", "purpose"):
            assert artifact.get(field), (
                f"AC-3 FAIL: artifact['{field}'] missing at complete — "
                "earlier-turn fields must survive the merge into later turns"
            )
