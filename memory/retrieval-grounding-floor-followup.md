---
name: retrieval-grounding-floor-followup
description: Deferred fix — chat hallucinates on out-of-corpus questions; needs a retrieval relevance floor / real embeddings
metadata:
  type: project
---

Deferred follow-up (decided 2026-06-04): the chat answer engine fabricates on
out-of-corpus questions (Círdan caught "best pizza in Bozeman" and "dog camping"
inventing specifics and mis-citing). Root cause is retrieval-side, not the prompt:
the keyword + graph-BFS retriever returns `top_k` docs regardless of how weak the
match is, so the LLM is handed off-topic sources and back-fills.

The 2026-06-04 "more helpful" answer change (commit c414533) shipped with only a
prompt mitigation ("WHEN THE SOURCES DON'T FIT" guard in `SYSTEM_INSTRUCTIONS`,
`src/chat_api/answer.py`) — **unverified**. The durable fix is a retrieval
relevance floor (decline honestly when top scores are weak) and/or real
embeddings in the semantic layer.

**Why:** a confident answer mis-cited to an unrelated source is a trust failure on
a citizen-facing engine — the part you can't fix after launch.

**How to apply:** the durable change lives in `src/network/` (semantic_layer /
rag_retriever) behind the `RAGResult` contract — keep it there so both the chat API
and the MCP server benefit. Re-gate with Círdan on the out-of-corpus cases.
