"""Persona registry — loading, validation, and the Community Planning Guide config."""
import pytest

from src.chat_api.personas import PersonaNotFound, get_persona, list_personas


def test_community_planning_guide_loads_with_expected_shape():
    p = get_persona("community-planning-guide")
    assert p.id == "community-planning-guide"
    assert p.scope["agency"] == "commerce"
    assert "Community-Planning-Platform" in p.scope["url_contains"]
    assert p.start_stage == "orient"
    assert p.stage_ids == ["orient", "scope", "ground", "scaffold", "fund_act", "complete"]
    assert p.goals and p.opening and p.starters
    assert p.mcp["tool_name"] == "community_planning_guide"


def test_stage_lookup_falls_back_to_first_for_unknown():
    p = get_persona("community-planning-guide")
    assert p.stage("orient")["id"] == "orient"
    assert p.stage("nonexistent")["id"] == "orient"  # graceful fallback


def test_unknown_persona_raises():
    with pytest.raises(PersonaNotFound):
        get_persona("no-such-persona")


def test_persona_id_cannot_escape_directory():
    # A crafted id must not read files outside personas/ (e.g. repo-root config.yaml).
    with pytest.raises(PersonaNotFound):
        get_persona("../config")


def test_catalog_includes_the_guide():
    ids = {row["id"] for row in list_personas()}
    assert "community-planning-guide" in ids


def test_every_persona_artifact_includes_action_items():
    # The deliverable is a work plan: every branch must carry an action_items field so the
    # interview always drives toward a concrete, checkable to-do list.
    for row in list_personas():
        p = get_persona(row["id"])
        assert p.artifacts, f"{p.id} declares no artifacts"
        for branch, fields in p.artifacts.items():
            assert "action_items" in fields, f"{p.id}/{branch} is missing action_items"
