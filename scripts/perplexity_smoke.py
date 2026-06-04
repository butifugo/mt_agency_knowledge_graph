"""Live answer smoke — calls synthesize() with the configured provider (reads .env).

    .venv/bin/python scripts/perplexity_smoke.py

Uses whatever CHAT_PROVIDER points at (perplexity by default). Requires that provider's
API key in .env. Makes a real LLM call.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.chat_api.answer import synthesize

QUESTIONS = [
    "How do I get a commercial pesticide applicator license in Montana?",
    "How do I file an insurance complaint in Montana?",
]


def main() -> None:
    for q in QUESTIONS:
        r = synthesize(q)
        print("=" * 80)
        print(f"[{r['provider']}:{r['model']}]  retrieval={r['strategy']}")
        print(f"Q: {q}")
        print(f"A: {r['answer']}\n")
        print("Citations:")
        for c in r["citations"]:
            print(f"  - {c['title']} → {c['url']}")
        print()


if __name__ == "__main__":
    main()
