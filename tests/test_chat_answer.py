"""Slice 2 — answer-synthesis logic (no Claude call required).

Covers source formatting from real retrieval, prompt grounding, and citation parsing.
The live Claude call is verified manually via curl once ANTHROPIC_API_KEY is set.
"""
from src.chat_api.answer import build_messages, extract_cited, format_sources


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
