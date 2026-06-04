"""Slice 6 — the answer-quality gate as an automatable check (Eomer's go/no-go).

Asserts retrieval relevance over the gold question set meets the bar. Live answer/
citation grading needs a key, so it runs in eval/evaluate.py, not here.
"""
from eval.evaluate import RELEVANCE_BAR, load_gold, relevance_hit_rate, score_retrieval


def test_retrieval_relevance_meets_bar(retriever):
    gold = load_gold()
    rows = score_retrieval(retriever, gold)
    rate = relevance_hit_rate(rows)
    assert rate >= RELEVANCE_BAR, (
        f"retrieval relevance {rate:.0%} is below the gate bar {RELEVANCE_BAR:.0%}; "
        "investigate retrieval quality before release"
    )
