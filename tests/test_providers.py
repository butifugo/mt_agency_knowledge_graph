"""Provider abstraction tests (no network calls).

Verifies provider selection and that the Perplexity request payload is well-formed.
The live round-trip is exercised by scripts/perplexity_smoke.py / eval with a real key.
"""
import pytest

from src.chat_api.providers import (
    AnthropicProvider,
    PerplexityProvider,
    get_provider,
)


def test_get_provider_by_name():
    assert isinstance(get_provider("perplexity"), PerplexityProvider)
    assert isinstance(get_provider("anthropic"), AnthropicProvider)


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_provider("bogus")


def test_perplexity_defaults_to_sonar_pro_and_builds_openai_payload():
    p = get_provider("perplexity")
    assert p.model == "sonar-pro"  # not affected by CHAT_MODEL (which is Claude's)
    payload = p.build_payload("SYSTEM", "USER")
    assert payload["model"] == "sonar-pro"
    assert payload["messages"][0] == {"role": "system", "content": "SYSTEM"}
    assert payload["messages"][1] == {"role": "user", "content": "USER"}


def test_anthropic_model_is_not_used_for_perplexity():
    # Even though .env may set CHAT_MODEL=claude-haiku-4-5, Perplexity uses its own default.
    assert get_provider("perplexity").model == "sonar-pro"


def test_perplexity_payload_threads_history_between_system_and_user():
    p = get_provider("perplexity")
    history = [
        {"role": "user", "content": "prior question"},
        {"role": "assistant", "content": "prior answer"},
    ]
    msgs = p.build_payload("SYS", "NOW", history)["messages"]
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
    assert msgs[0]["content"] == "SYS"
    assert msgs[-1]["content"] == "NOW"
