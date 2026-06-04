"""Answer-quality evaluation (Círdan's gate).

Scores the gold question set on:
  - retrieval relevance  — does a relevant, correctly-sourced doc appear in the top-K?
  - citeability          — do results carry real (http) source URLs?
  - citation integrity   — (only with ANTHROPIC_API_KEY) every URL the answer cites is one
                           of the sources we actually provided (no invented links).

Importable (used by the gate test) and runnable:
    .venv/bin/python -m eval.evaluate
"""
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.chat_api.providers import get_provider
from src.chat_api.retrieval import get_retriever

GOLD_PATH = ROOT / "eval" / "gold_questions.yaml"
TOP_K = 8
RELEVANCE_BAR = 0.66  # go/no-go threshold for retrieval relevance hit-rate


def load_gold() -> List[Dict[str, Any]]:
    with open(GOLD_PATH) as f:
        return yaml.safe_load(f)["questions"]


def _doc_text(doc: Dict[str, Any]) -> str:
    chunks = doc.get("chunks") or []
    snippet = " ".join(c.get("content", "") for c in chunks)
    return f"{doc.get('title', '')} {doc.get('source_url', '')} {snippet}".lower()


def score_retrieval(retriever, gold: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for item in gold:
        r = retriever.retrieve(item["q"], top_k=TOP_K, return_chunks=True)
        res = r.results
        terms = [t.lower() for t in item.get("terms", [])]
        host = (item.get("host") or "").lower()
        agency = item.get("agency")

        term_hit = any(any(t in _doc_text(d) for t in terms) for d in res)
        host_hit = (
            any(host in (d.get("source_url") or "").lower() for d in res) if host else True
        )
        agency_hit = (
            any(d.get("agency") == agency for d in res[:3]) if agency else True
        )
        citeable = sum(1 for d in res if (d.get("source_url") or "").startswith("http"))
        relevant = term_hit and (host_hit or agency_hit)

        rows.append(
            {
                "q": item["q"],
                "agency": agency,
                "relevant": relevant,
                "term_hit": term_hit,
                "host_hit": host_hit,
                "agency_hit": agency_hit,
                "citeable": citeable,
                "found": len(res),
            }
        )
    return rows


def relevance_hit_rate(rows: List[Dict[str, Any]]) -> float:
    return (sum(1 for r in rows if r["relevant"]) / len(rows)) if rows else 0.0


def score_citation_integrity(gold: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Requires ANTHROPIC_API_KEY. Verifies cited URLs are a subset of provided sources."""
    from src.chat_api.answer import synthesize

    checked, clean, with_citation = 0, 0, 0
    for item in gold:
        res = synthesize(item["q"], item.get("agency"))
        source_urls = {s["url"] for s in res["sources"]}
        cited = res["citations"]
        checked += 1
        if cited:
            with_citation += 1
        if all(c["url"] in source_urls for c in cited):
            clean += 1
    return {
        "checked": checked,
        "citation_integrity_rate": (clean / checked) if checked else 0.0,
        "answers_with_citation_rate": (with_citation / checked) if checked else 0.0,
    }


def main() -> int:
    gold = load_gold()
    retriever = get_retriever()
    rows = score_retrieval(retriever, gold)

    print("=" * 78)
    print("RETRIEVAL RELEVANCE")
    print("=" * 78)
    for r in rows:
        mark = "✓" if r["relevant"] else "✗"
        print(f" {mark} [{r['agency']:<16}] {r['q']}")
        if not r["relevant"]:
            print(f"     term_hit={r['term_hit']} host_hit={r['host_hit']} "
                  f"agency_hit={r['agency_hit']} citeable={r['citeable']}/{r['found']}")

    hit_rate = relevance_hit_rate(rows)
    print("-" * 78)
    print(f"Relevance hit-rate: {hit_rate:.0%}  (bar {RELEVANCE_BAR:.0%})  "
          f"-> {'MET' if hit_rate >= RELEVANCE_BAR else 'NOT MET'}")

    try:
        provider = get_provider()
        has_key = bool(getattr(provider, "api_key", ""))
    except Exception:
        provider, has_key = None, False

    if has_key:
        print("\n" + "=" * 78)
        print(f"CITATION INTEGRITY (live answers via {provider.name}:{provider.model})")
        print("=" * 78)
        ci = score_citation_integrity(gold)
        print(f"  citation integrity: {ci['citation_integrity_rate']:.0%}  "
              f"(cited links all come from provided sources)")
        print(f"  answers with >=1 citation: {ci['answers_with_citation_rate']:.0%}")
        gate = hit_rate >= RELEVANCE_BAR and ci["citation_integrity_rate"] == 1.0
    else:
        print("\n(No provider API key set — skipping live answer/citation grading; "
              "retrieval-only gate.)")
        gate = hit_rate >= RELEVANCE_BAR

    print("\n" + "=" * 78)
    print(f"GO / NO-GO: {'GO' if gate else 'NO-GO'}")
    print("=" * 78)
    return 0 if gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
