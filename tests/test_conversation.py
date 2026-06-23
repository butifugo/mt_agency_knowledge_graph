"""Conversation state — <<STATE>> extraction, merge semantics, and stage clamping."""
from src.chat_api.conversation import (
    extract_handoff,
    extract_state,
    init_state,
    merge_state,
    strip_handoff_block,
    strip_state_block,
)
from src.chat_api.personas import get_persona

PERSONA = get_persona("community-planning-guide")


def test_extract_handoff_parses_json_block():
    raw = (
        "Funding is really the grants advisor's specialty.\n"
        "<<FOLLOWUPS>>\nq?\n<</FOLLOWUPS>>\n"
        '<<STATE>>\n{"stage":"ground"}\n<</STATE>>\n'
        '<<HANDOFF>>{"to":"funding-grants-advisor","label":"Bring in the Funding & Grants Advisor"}<</HANDOFF>>'
    )
    h = extract_handoff(raw)
    assert h == {"to": "funding-grants-advisor", "label": "Bring in the Funding & Grants Advisor"}


def test_extract_handoff_tolerates_bare_id_and_absence():
    assert extract_handoff("x <<HANDOFF>>site-selection-advisor<</HANDOFF>>") == {
        "to": "site-selection-advisor",
        "label": "",
    }
    assert extract_handoff("no handoff here") is None
    assert extract_handoff("<<HANDOFF>>\n<</HANDOFF>>") is None  # empty


def test_strip_handoff_block_removes_it():
    txt = "Visible answer [1]. <<HANDOFF>>{\"to\":\"x\"}<</HANDOFF>>"
    assert "HANDOFF" not in strip_handoff_block(txt)
    assert strip_handoff_block(txt).startswith("Visible answer")


def test_init_state_starts_at_first_stage():
    s = init_state(PERSONA)
    assert s["stage"] == "orient"
    assert s["branch"] is None
    assert s["slots"] == {} and s["artifact"] == {} and s["turn"] == 0


def test_extract_state_parses_block():
    raw = (
        "Answer text [1].\n<<FOLLOWUPS>>\nq?\n<</FOLLOWUPS>>\n"
        '<<STATE>>\n{"stage":"scope","branch":"build_plan","slots":{"community":"Red Lodge"}}\n<</STATE>>'
    )
    delta = extract_state(raw)
    assert delta["stage"] == "scope"
    assert delta["branch"] == "build_plan"
    assert delta["slots"]["community"] == "Red Lodge"


def test_extract_state_malformed_returns_empty():
    assert extract_state("no block here") == {}
    assert extract_state("<<STATE>>{not json}<</STATE>>") == {}


def test_strip_state_block_removes_it():
    assert strip_state_block("Hello.\n<<STATE>>{}<</STATE>>") == "Hello."


def test_merge_unions_slots_and_artifact_and_sets_branch():
    s0 = init_state(PERSONA)
    s1 = merge_state(s0, {"branch": "build_plan", "slots": {"community": "Red Lodge"}}, PERSONA)
    s2 = merge_state(
        s1,
        {"slots": {"plan_type": "growth_policy"}, "artifact": {"sections": ["Land use"]}},
        PERSONA,
    )
    assert s2["branch"] == "build_plan"
    assert s2["slots"] == {"community": "Red Lodge", "plan_type": "growth_policy"}
    assert s2["artifact"]["sections"] == ["Land use"]
    assert s2["turn"] == 2


def test_stage_advances_one_step_and_clamps_jumps():
    s = init_state(PERSONA)  # orient
    # orient→scope requires branch; provide it so the exit condition is met.
    s = merge_state(s, {"stage": "scope", "branch": "build_plan"}, PERSONA)
    assert s["stage"] == "scope"
    # illegal jump scope→fund_act (2 steps): clamps to the next stage (ground).
    # Slots are required by scope's exit condition; provide community + plan_type
    # so the gate allows the one-step clamp to ground rather than holding at scope.
    s = merge_state(
        s,
        {
            "stage": "fund_act",
            "slots": {"community": "Red Lodge", "plan_type": "growth_policy"},
        },
        PERSONA,
    )
    assert s["stage"] == "ground"


def test_stage_allows_backward_move():
    s = init_state(PERSONA)
    # orient→scope: provide branch so the exit condition is satisfied.
    s = merge_state(s, {"stage": "scope", "branch": "build_plan"}, PERSONA)
    assert s["stage"] == "scope"
    s = merge_state(s, {"stage": "orient"}, PERSONA)  # user changed their mind
    assert s["stage"] == "orient"


def test_empty_slot_values_are_ignored():
    s = merge_state(init_state(PERSONA), {"slots": {"community": ""}}, PERSONA)
    assert "community" not in s["slots"]


def test_action_items_list_replaces_and_empty_is_ignored():
    # The work plan's action_items is a list of objects the model re-emits in full each turn;
    # a new list REPLACES the prior one, and an empty list leaves the prior value untouched.
    s0 = init_state(PERSONA)
    items1 = [{"task": "Pull your Community Profile data", "owner": "Commerce", "cite": "[1]"}]
    s1 = merge_state(s0, {"artifact": {"action_items": items1}}, PERSONA)
    assert s1["artifact"]["action_items"] == items1

    items2 = items1 + [{"task": "Draft the land use chapter", "when": "weeks 2-4", "cite": "[2]"}]
    s2 = merge_state(s1, {"artifact": {"action_items": items2}}, PERSONA)
    assert s2["artifact"]["action_items"] == items2  # replaced, not appended-twice

    s3 = merge_state(s2, {"artifact": {"action_items": []}}, PERSONA)
    assert s3["artifact"]["action_items"] == items2  # empty delta ignored
