# MVP Requirements — Montana Agency Answer Engine

> Author: **Theoden** (product-manager, Tier 1). Status: draft for build. Date: 2026-06-04.
> Principle: **go fast to a working MVP, on real data.** Decisions below were confirmed with the product owner.

## Objective

A citizen can ask a question on a sample web page and get a **Claude-written answer, with citations**, drawn from real Montana state-agency public content — and the same knowledge is reachable by AI clients through an **MCP server**. Both surfaces sit on **one shared retrieval core** (`GraphRAGRetriever` over the existing knowledge graph).

## Confirmed decisions (the foundation — do not relitigate for MVP)

| # | Decision | Choice |
|---|----------|--------|
| D1 | MVP content | **Use the existing built graph as-is** — `src/network/exports/montana_knowledge.pkl` (~390 MB, 10 agencies, ~10,300 docs). **No crawl for MVP.** |
| D2 | Answer generation | **Claude synthesizes** a natural-language answer **with inline citations**. |
| D3 | Architecture | **Shared core**: the graph RAG feeds **both** a FastMCP server (AI clients) **and** a thin FastAPI `/chat` endpoint (the widget). |
| D4 | Hosting | **Local demo** (localhost). Sample page = a simple static HTML page with the chat widget docked in a corner. |

## Architecture (MVP)

```
                       ┌─────────────────────────────────────────┐
 sample page (static)  │  src/network/  — THE SHARED CORE         │
 ┌───────────────┐     │  GraphRAGRetriever over montana_*.pkl    │
 │ chat widget   │     │  retrieve / search_by_agency /           │
 │ (corner)      │     │  get_document_context → RAGResult        │
 └──────┬────────┘     └───────▲─────────────────────▲────────────┘
        │ HTTP (JSON)          │ import (in-process)  │ import (in-process)
        ▼                      │                      │
 ┌───────────────┐   ┌─────────┴──────────┐   ┌───────┴──────────┐
 │ FastAPI /chat │──▶│ retrieve passages  │   │ FastMCP server   │──▶ AI clients
 │ + Claude      │   │ (RAGResult)        │   │ (stdio)          │    (Claude, etc.)
 │ synthesis     │◀──┤                    │   │ tools → RAGResult│
 └───────────────┘   └────────────────────┘   └──────────────────┘
        │ calls Anthropic API (synthesize answer + cite sources)
        ▼  ANTHROPIC_API_KEY
```

Retrieval logic lives **only** in `src/network/`. The chat API and the MCP server are thin drivers that both call it — neither reimplements retrieval. Proposed new code locations: `src/mcp_server/` (FastMCP) and `src/chat_api/` (FastAPI); the widget + sample page under `web/` (or `html/widget/`).

## Scope

- **Must-have (MVP):** load the existing graph; retrieve real passages; Claude answer with citations; FastAPI `/chat`; embeddable JS widget on a local sample page; FastMCP server exposing the three retrieval tools; a small answer-quality eval gate.
- **Should-have (fast-follow):** multi-turn conversation memory; streaming responses; agency selector in the widget; HTTP transport for MCP; deployment.
- **Not now:** re-crawl / freshness automation; auth; analytics; production embedding on a live `.mt.gov` page; multi-language.

---

## Workstream 1 — Context for the MCP server (the knowledge core)

**Purpose:** make the existing real data queryable, fast, without a crawl.

**Functional requirements**
- W1.1 Load `src/network/exports/montana_knowledge.pkl` via `GraphPersistence` and construct a `GraphRAGRetriever` **once** at process start (shared by both surfaces).
- W1.2 Confirm the loaded graph covers the 10 agencies and that `retrieve()` returns a valid `RAGResult` with non-empty, **source-bearing** results.
- W1.3 Define (but do not run for MVP) the refresh path: `phase1_crawl` → `3_build_network.py` → new `.pkl`. Document it so freshness is a known, deferred step.
- W1.4 Each retrieved result must expose enough source metadata (document title + URL) to render a citation. If today's `RAGResult.results[]` lacks a clean URL, that is the one allowed core change — add it in `src/network/`, ripple per the `schema.py` contract, and rebuild.

**Acceptance:** a Python call loads the graph and returns cited passages for a known question in < 2 s after warm load.
**Owners:** Treebeard (data/coverage check) · Gimli (load + smoke) · Gandalf (only if W1.4 schema change is needed) · Faramir (contract review if schema touched).

## Workstream 2 — MCP server + web chat API (shared core)

**Purpose:** two thin interfaces over the same retriever; the widget's brain.

### 2a. Web chat API (FastAPI) — the widget's backend
- W2.1 `POST /chat` → request `{ "question": str, "agency": str|null }`; response `{ "answer": str, "citations": [{ "title", "url", "snippet" }], "agency": str|null }`.
- W2.2 Pipeline: retrieve (scope to `agency` if given via `search_by_agency`, else `retrieve`) → build a grounded prompt from the top-K passages → call **Claude** → return the answer + the citations actually used.
- W2.3 **Grounding rule:** the system prompt instructs Claude to answer **only** from the supplied passages, cite sources, and say it doesn't know when the passages don't cover it. No outside knowledge, no invented links.
- W2.4 Claude model: default **Haiku 4.5** (`claude-haiku-4-5`) for cost/speed; config toggle to Sonnet. Use the Anthropic SDK with **prompt caching** on the static system instructions.
- W2.5 `GET /health` returns ok once the graph is loaded. CORS allows the local sample-page origin.
- W2.6 Secrets: `ANTHROPIC_API_KEY` from env/`.env` (already a hook-protected path) — never logged, never returned.

### 2b. MCP server (FastMCP) — for AI clients
- W2.7 Expose three tools wrapping the retriever, each returning the **`RAGResult`** shape unchanged:
  `search_agency_knowledge` (→ `retrieve`), `search_by_agency` (→ `search_by_agency`), `get_document_context` (→ `get_document_context`).
- W2.8 Clear tool **names + descriptions** (the calling model reads these) — owned with Galadriel; align with the answer/citation format used by the chat API.
- W2.9 Transport **stdio** for MVP. Read-only: no crawling or graph mutation from the server.
- W2.10 Add `fastmcp` (and `anthropic`, `fastapi`, `uvicorn`) to `requirements.txt`.

**Acceptance:**
- `/chat` returns a grounded, cited answer for real questions across ≥ 3 agencies; an unanswerable question returns an honest "not found."
- The MCP server starts (stdio), and each tool returns a valid `RAGResult` from a test client.
**Owners:** Aragorn (plan) · Gandalf (build, via `mcp-server` skill) · Galadriel (tool naming + answer/citation format) · Faramir (contract + secret hygiene) · Samwise (pytest) · Elrond (failures).

## Workstream 3 — Widget + sample page

**Purpose:** a visible, real demo — a chatbot in the corner of a page.

**Functional requirements**
- W3.1 A self-contained JS widget (vanilla, no framework) injected by a single `<script>`: a floating button (bottom-right) that opens a chat panel.
- W3.2 Panel: question input, send, scrolling answer area; renders the answer text and a **clickable citations list** (title → source URL); loading + error states.
- W3.3 Calls the local `/chat` API; single-turn for MVP (multi-turn is should-have).
- W3.4 A simple static **sample page** (plausible "agency page" layout) that loads the widget in the corner — the demo surface.
- W3.5 Accessible and legible: keyboard-reachable, focus states, sufficient contrast, sane on a smaller viewport.

**Acceptance:** open the sample page locally, ask a question, get a cited answer in the corner panel; clicking a citation opens the real source page.
**Owners:** Gandalf (build) · Galadriel (experience) · Arwen (widget UI/legibility review).

---

## Cross-cutting requirements

- **Trust / citations are the product.** Every answer either cites real sources from the retrieved passages or honestly declines. A confident answer with a wrong/missing citation is a **defect**, not a warning (Círdan gates this).
- **Make/check separation.** The agent that builds the chat pipeline does not certify its own answer quality — **Círdan** judges relevance + citation accuracy independently.
- **Guardrails inherited from the project:** graph is the source of truth; `schema.py` is the contract; keep retrieval in `src/network/`; never hand-edit generated paths; `.mt.gov`-only (no crawl in MVP anyway).

## Prioritized slices (fast path to MVP)

1. **Core load + retrieval smoke** — load `.pkl`, prove `retrieve()` returns cited passages; bootstrap `tests/`. *(Gimli + Samwise; Gandalf if W1.4)*
2. **`/chat` end-to-end (vertical slice)** — FastAPI + Claude synthesis + citations for one agency, tested with curl. *(Gandalf; Galadriel; Faramir)*
3. **Widget + sample page** — corner chatbot calling `/chat`, citations clickable. *(Gandalf; Arwen)*
4. **All-agency + agency scope** — extend `/chat` to all 10 agencies and optional agency filter. *(Gandalf)*
5. **MCP server** — FastMCP wrapping the same three retriever methods, stdio, tested. *(Gandalf via `mcp-server` skill; Faramir)*
6. **Answer-quality gate** — Círdan's gold set (~5 Qs × 3 agencies) scored for relevance + citation; Eomer go/no-go. *(Círdan; Eomer; Bilbo for lessons)*

Slices 2–3 give a demoable product first; 5 (MCP) follows the same core. This honors "widget visible fast" while still delivering the MCP server.

## MVP Acceptance Criteria (Go/No-Go)

- [ ] Loads the existing real graph; no crawl required.
- [ ] `/chat` returns grounded, **cited** answers across ≥ 3 agencies; honest "not found" path works.
- [ ] Sample page shows the corner widget; a question returns a cited answer; citations link to real `.mt.gov` pages.
- [ ] MCP server starts (stdio) and all three tools return valid `RAGResult`s.
- [ ] pytest green for retrieval + `/chat` + MCP tools.
- [ ] Círdan's gold-set bar met (relevance + citation accuracy).
- [ ] No secrets leaked; `RAGResult` contract intact.

## Risks & decisions

- **Big graph, local load (~390 MB pkl):** first load is slow/memory-heavy. *Mitigation:* load once at startup, keep warm; if painful, build a smaller MVP subset. *(Treebeard/Gimli flag.)*
- **Retrieval is keyword + graph, not embeddings** (README's own note): some answers may be thin. *Mitigation:* Círdan's eval tells us where; embeddings are a post-MVP slice behind the same contract.
- **Citation URLs may not be clean in current `RAGResult`:** the one sanctioned core change (W1.4); rebuild after.
- **Not yet a git repo:** before building, `git init` so slices are revertible. *(Recommended pre-step.)*
- **`.env` is hook-protected:** the API key must be set by the user; the build reads it, never writes it.

## Assumptions (state-and-proceed; correct me if wrong)

- Single-turn Q&A for MVP; conversation memory and streaming are fast-follow.
- Claude Haiku 4.5 default for synthesis (Sonnet via config).
- New code in `src/mcp_server/` and `src/chat_api/`; widget + sample page in `web/`.
- Top-K passages for grounding ≈ 5–8 (tunable).
