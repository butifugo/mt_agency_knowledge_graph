"""Pluggable LLM providers for the front-end answer bot.

The synthesis step is the ONLY place that talks to an LLM. Swap providers by setting
``CHAT_PROVIDER`` in .env (e.g. ``perplexity`` or ``anthropic``); the backend (retrieval,
graph, MCP) is untouched. Adding a provider = one small class + one registry entry.
"""
import os
from typing import Dict, List, Optional

import httpx

# A prior conversation turn: {"role": "user"|"assistant", "content": str}. Personas pass these
# so the model has multi-turn context; the single-turn assistant passes None (no change).
History = Optional[List[Dict[str, str]]]

MAX_TOKENS = 1536  # headroom so the trailing <<FOLLOWUPS>> block isn't truncated
_PLACEHOLDER = "your-"  # unedited value in .env.example


class MissingAPIKey(RuntimeError):
    """Raised when the selected provider's API key is not configured."""


def _key(env_name: str) -> str:
    value = os.getenv(env_name, "").strip()
    return "" if value.startswith(_PLACEHOLDER) else value


class LLMProvider:
    name = "base"
    model = ""

    def complete(self, system_text: str, user_text: str, history: History = None) -> str:
        raise NotImplementedError


class PerplexityProvider(LLMProvider):
    """Perplexity Sonar (OpenAI-compatible chat completions API)."""

    name = "perplexity"
    endpoint = "https://api.perplexity.ai/chat/completions"

    def __init__(self) -> None:
        self.api_key = _key("PERPLEXITY_API_KEY")
        self.model = os.getenv("PERPLEXITY_MODEL", "sonar-pro").strip()
        # Optional: lock Sonar's own web search to Montana sites (comma-separated hosts).
        self.search_domains = [
            d.strip() for d in os.getenv("PERPLEXITY_SEARCH_DOMAINS", "").split(",") if d.strip()
        ]

    def build_payload(self, system_text: str, user_text: str, history: History = None) -> dict:
        messages = [{"role": "system", "content": system_text}]
        messages += [{"role": h["role"], "content": h["content"]} for h in (history or [])]
        messages.append({"role": "user", "content": user_text})
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": MAX_TOKENS,
            "temperature": 0.1,
        }
        if self.search_domains:
            payload["search_domain_filter"] = self.search_domains
        return payload

    def complete(self, system_text: str, user_text: str, history: History = None) -> str:
        if not self.api_key:
            raise MissingAPIKey(
                "PERPLEXITY_API_KEY is not set. Add it to .env (CHAT_PROVIDER=perplexity)."
            )
        resp = httpx.post(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=self.build_payload(system_text, user_text, history),
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


class AnthropicProvider(LLMProvider):
    """Anthropic Claude (kept available for switch-back)."""

    name = "anthropic"

    def __init__(self) -> None:
        self.api_key = _key("ANTHROPIC_API_KEY")
        self.model = (
            os.getenv("ANTHROPIC_MODEL") or os.getenv("CHAT_MODEL") or "claude-haiku-4-5"
        ).strip()

    def complete(self, system_text: str, user_text: str, history: History = None) -> str:
        if not self.api_key:
            raise MissingAPIKey(
                "ANTHROPIC_API_KEY is not set. Add it to .env (CHAT_PROVIDER=anthropic)."
            )
        import anthropic  # imported lazily so this provider is optional

        messages = [{"role": h["role"], "content": h["content"]} for h in (history or [])]
        messages.append({"role": "user", "content": user_text})
        client = anthropic.Anthropic(api_key=self.api_key)
        message = client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=[{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
        )
        return "".join(
            b.text for b in message.content if getattr(b, "type", None) == "text"
        ).strip()


_REGISTRY = {
    "perplexity": PerplexityProvider,
    "anthropic": AnthropicProvider,
}


def get_provider(name: str = None) -> LLMProvider:
    """Return a provider instance. Defaults to the configured CHAT_PROVIDER."""
    if name is None:
        from src.chat_api.config import get_settings

        name = get_settings()["provider"]
    name = name.lower()
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown CHAT_PROVIDER '{name}'. Options: {sorted(_REGISTRY)}"
        )
    return cls()
