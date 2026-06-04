"""Slice 2 — answer-synthesis logic (no Claude call required).

Covers source formatting from real retrieval, prompt grounding, and citation parsing.
The live Claude call is verified manually via curl once ANTHROPIC_API_KEY is set.
"""
from src.chat_api.answer import (
    build_messages,
    extract_cited,
    format_sources,
    split_followups,
    strip_invalid_citations,
)


def test_format_sources_from_real_retrieval(retriever):
    rag = retriever.retrieve("pesticide licensing", top_k=6, return_chunks=True)
    sources = format_sources(rag.results, max_sources=6)
    assert sources, "expected grounding sources for a common query"
    for s in sources:
        assert s["title"]
        assert "url" in s
        assert s["content"]  # grounding text present


def test_build_messages_grounds_and_lists_sources():
    sources = [
        {
            "title": "Pesticide Licensing",
            "agency": "agriculture",
            "url": "https://agr.mt.gov/x",
            "snippet": "...",
            "content": "A pesticide applicator license is required.",
        }
    ]
    system_text, user = build_messages("How do I get a pesticide license?", sources)
    assert isinstance(system_text, str) and "ONLY" in system_text
    assert "[1] Pesticide Licensing" in user
    assert "A pesticide applicator license is required." in user
    assert "How do I get a pesticide license?" in user


def test_extract_cited_parses_bracket_markers():
    sources = [
        {"title": f"Doc{i}", "agency": "a", "url": "u", "snippet": "s"} for i in range(1, 4)
    ]
    cited = extract_cited("According to [1] and [3], yes.", sources)
    assert {c["title"] for c in cited} == {"Doc1", "Doc3"}


def test_split_followups_extracts_block_and_cleans_answer():
    raw = (
        "Here is the answer with a citation [1].\n\n"
        "<<FOLLOWUPS>>\n"
        "- How do I renew my license?\n"
        "2. What are the fees?\n"
        "Where do I submit the form?\n"
        "<</FOLLOWUPS>>"
    )
    answer, followups = split_followups(raw)
    assert answer == "Here is the answer with a citation [1]."
    assert followups == [
        "How do I renew my license?",
        "What are the fees?",
        "Where do I submit the form?",
    ]


def test_split_followups_absent_returns_empty_list():
    answer, followups = split_followups("Just an answer, no follow-ups here.")
    assert answer == "Just an answer, no follow-ups here."
    assert followups == []


def test_strip_invalid_citations_drops_out_of_range_markers():
    # 3 sources: [1]-[3] are valid, [7] is not and must be removed cleanly.
    text = "See the form [1] and the fee schedule [7]. Also [3] applies."
    out = strip_invalid_citations(text, n_sources=3)
    assert "[7]" not in out
    assert "[1]" in out and "[3]" in out
    assert " ." not in out  # spacing tidied where the marker was dropped


def test_strip_invalid_citations_keeps_all_when_in_range():
    text = "Steps: register [1], pay [2], submit [3]."
    assert strip_invalid_citations(text, n_sources=3) == text


def test_split_followups_caps_at_three():
    raw = "A.\n<<FOLLOWUPS>>\nq1?\nq2?\nq3?\nq4?\n<</FOLLOWUPS>>"
    _, followups = split_followups(raw)
    assert followups == ["q1?", "q2?", "q3?"]
