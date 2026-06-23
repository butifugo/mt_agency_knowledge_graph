"""Persona synthesis — real retrieval + a fake provider (no network).

Proves the persona path scopes retrieval to the Community Planning Platform, advances
conversation state from the model's <<STATE>> block, builds the artifact, and strips the
control blocks from the visible answer — while the generic path stays unchanged (AC-5).
"""
from src.chat_api import answer as A

CANNED = (
    "For a growth policy, start with your community profile data and the standard sections [1].\n\n"
    "<<FOLLOWUPS>>\nWhich community is this for?\n<</FOLLOWUPS>>\n"
    "<<STATE>>\n"
    '{"stage":"scope","branch":"build_plan","slots":{"plan_type":"growth_policy"},'
    '"artifact":{"sections":["Land use","Housing","Transportation"]}}\n'
    "<</STATE>>"
)


class _FakeProvider:
    name = "fake"
    model = "fake-1"

    def __init__(self, capture):
        self._capture = capture

    def complete(self, system_text, user_text, history=None):
        self._capture["system"] = system_text
        self._capture["history"] = history
        return CANNED


def test_persona_synthesis_scopes_advances_state_and_builds_artifact(retriever, monkeypatch):
    cap = {}
    monkeypatch.setattr(A, "get_provider", lambda: _FakeProvider(cap))

    out = A.synthesize(
        "How do I start a growth policy?",
        persona="community-planning-guide",
        history=[],
        state=None,
    )

    assert out["persona"] == "community-planning-guide"
    assert out["stage"] == "scope"
    assert out["state"]["branch"] == "build_plan"
    assert out["state"]["slots"]["plan_type"] == "growth_policy"
    assert out["artifact"]["sections"] == ["Land use", "Housing", "Transportation"]
    # control blocks stripped from the visible answer
    assert "<<STATE>>" not in out["answer"]
    assert "<<FOLLOWUPS>>" not in out["answer"]
    # scoped to commerce Community Planning Platform content (AC-2)
    assert out["agency"] == "commerce"
    assert out["sources"], "expected scoped CPP sources"
    for s in out["sources"]:
        assert s["agency"] == "commerce"
        assert "community-planning-platform" in s["url"].lower()
    # the persona voice + active-stage guidance reached the model
    assert "Business Location Guide" in cap["system"]
    assert "ACTIVE STAGE" in cap["system"]


def test_generic_path_unchanged_returns_null_persona(retriever, monkeypatch):
    monkeypatch.setattr(A, "get_provider", lambda: _FakeProvider({}))
    out = A.synthesize("pesticide licensing")
    assert out["persona"] is None
    assert out["stage"] is None
    assert out["state"] is None
    assert out["artifact"] is None


def test_second_turn_threads_prior_state_and_history(retriever, monkeypatch):
    cap = {}
    monkeypatch.setattr(A, "get_provider", lambda: _FakeProvider(cap))
    prior = {
        "persona": "community-planning-guide",
        "stage": "orient",
        "branch": None,
        "slots": {},
        "artifact": {},
        "turn": 1,
    }
    out = A.synthesize(
        "It's for Red Lodge",
        persona="community-planning-guide",
        history=[{"role": "user", "content": "growth policy"}, {"role": "assistant", "content": "..."}],
        state=prior,
    )
    assert cap["history"], "prior turns must reach the provider"
    assert out["state"]["turn"] == 2  # incremented from prior
