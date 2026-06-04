# mt_agency_knowledge_graph

Montana State Government **Knowledge Network**. Crawls 37+ state-agency websites (HTML, PDF,
DOCX), builds per-agency **knowledge graphs** with semantic relationships, derives **navigation
graphs**, and renders interactive D3 visualizations and a unified dashboard. The graph engine
in `src/network/` also exposes a **graph-enhanced RAG retriever** — the core we are evolving
into an **MCP server** so AI agents can query agency knowledge directly, embeddable on every
agency website.

## Pipeline mental model

```
agency websites (agencies.md)
        │  crawl + extract           src/phase1_crawl  (HTML/PDF/DOCX extractors)
        ▼
knowledge/{agency}/*.md  (markdown + frontmatter; generated, gitignored)
        │  build graph              src/phase2_knowledge  +  src/network/3_build_network.py
        ▼
data/graphs/knowledge/*.pkl  ·  src/network/exports/montana_knowledge.pkl  (KnowledgeGraph, gitignored)
        │  navigation hierarchy     src/phase3_navigation
        ▼
data/graphs/navigation/*.json
        │  visualize                src/phase4/5/6_viz_*
        ▼
html/interactive-dashboard.html  +  html/agency-data/{agency}.json  (generated, gitignored)
```

One agency → many markdown docs → one `KnowledgeGraph` (nodes = documents, edges = relationships,
chunks = RAG units). The graph is the **single source of truth**: visualizations, navigation, and
the RAG retriever all read from it — they never recompute relationships independently.

## The graph engine (`src/network/`) — the mission-critical core

This is where the MCP evolution lives. Treat it as the durable API; the phase CLIs are drivers around it.

| File | Role |
|------|------|
| `schema.py` | Data model: `KnowledgeGraph`, `NodeMetadata`, `EdgeMetadata`, `ContentChunk`, `RAGResult`, `NodeType`, `EdgeType`. **The contract.** |
| `graph_builder.py` | Markdown → nodes/edges/chunks |
| `semantic_layer.py` | TF-IDF / similarity edges, topic relationships |
| `rag_retriever.py` | `GraphRAGRetriever` — `retrieve()`, `search_by_agency()`, `get_document_context()`. **These are the natural MCP tool surfaces.** |
| `analyzer.py` | Network analytics (PageRank, centrality, communities) |
| `persistence.py` | `GraphPersistence(output_dir="src/network/exports")` — load/save `.pkl` (`montana_knowledge.pkl`) |
| `d3_visualizer.py` | Graph → D3 JSON |
| `3_build_network.py` | Build orchestrator (argparse; `--quick` skips expensive steps) |

The retrieval contract is `RAGResult` (`query`, `results[]`, `total_found`, `search_strategy`,
`execution_time_ms`, `expanded_nodes`). When the MCP server is built, its tools **wrap these
methods and return this shape** — never reimplement retrieval.

## Canonical layout

```
config.yaml                  paths, crawling, knowledge (rag chunk_size/overlap), viz settings
agencies.md                  agency → URL → folder registry (source of which agencies exist)
src/shared/                  config.py (Config + DEFAULT_CONFIG), schemas.py, utils.py
src/phase1_crawl/            cli.py, crawler.py, extractors/{html,pdf,docx}_extractor.py
src/phase2_knowledge/        cli.py, knowledge_builder.py, semantic_analyzer.py
src/phase3_navigation/       cli.py, navigation_builder.py, hierarchy_analyzer.py, mime_classifier.py
src/phase4_viz_knowledge/    cli.py, knowledge_viz.py
src/phase5_viz_navigation/   cli.py, html_navigation_viz.py, navigation_viz.py
src/phase6_viz_interactive/  cli.py, dashboard_viz.py, integrated_cli.py
src/network/                 the graph engine (table above)
src/extract/, src/viz/       LEGACY (crawler_1.py, 2_refresh.py, 4_agency_network_viz.py) — prefer phase modules
scripts/run_all.py           master orchestrator (--agencies / --all-agencies / --phases / --skip-crawl / --quick)
scripts/generate_agency_index.py
serve_dashboard.py           local HTTP server for the dashboard (port 8000)
data/graphs/                 generated graph exports (knowledge/*.pkl, navigation/*.json)
knowledge/{agency}/          crawled markdown (generated, gitignored)
html/                        dashboard + agency-data/*.json (generated, gitignored; some files are 100MB+)
```

## Commands (run from repo root; activate `.venv` first)

```bash
# Per-phase
python -m src.phase1_crawl.cli --agency agriculture        # crawl (--all, --dry-run, --update-only)
python -m src.phase2_knowledge.cli --build --agency agriculture
python -m src.phase3_navigation.cli --agency agriculture
python -m src.phase4_viz_knowledge.cli --agency agriculture
python -m src.phase6_viz_interactive.cli                   # unified dashboard (all agencies)

# Graph engine
python src/network/3_build_network.py --quick              # build KnowledgeGraph → exports/

# Full pipeline
python scripts/run_all.py --agencies agriculture,commerce --quick
python scripts/run_all.py --all-agencies --skip-crawl

# Serve dashboard
python serve_dashboard.py   # → http://localhost:8000/interactive-dashboard.html
```

## Rules to honor

- **The graph is the source of truth.** Visualizations, navigation, and RAG read from the
  `KnowledgeGraph`; if you change a relationship, change it in the builder/semantic layer, then
  rebuild — don't patch downstream JSON/pkl by hand.
- **`schema.py` is the contract.** Renaming a field on `NodeMetadata`/`RAGResult`/etc. ripples to
  `graph_builder`, `rag_retriever`, `d3_visualizer`, the dashboard JSON, and any future MCP tool.
  Change them together.
- **Never hand-edit generated/sensitive paths** (a hook blocks this): `knowledge/**`,
  `data/graphs/**`, `src/network/exports/**`, `html/agency-data/**`, `.env`. Regenerate via the
  pipeline instead.
- **Crawling is outward-facing.** Honor `config.yaml` `crawling.rate_limit_delay` and the user
  agent; prefer `--dry-run` / `--update-only` before a full re-crawl. Don't crawl non-`.mt.gov`
  hosts.
- **MCP framing:** the server (planned, not yet built) is **Python / FastMCP**, wrapping
  `GraphRAGRetriever`. Keep new retrieval logic in `src/network/` so it's reusable from both the
  CLIs and the future server. See the `mcp-server` skill.
- This project is **not yet a git repo**; there's no remote. Don't assume `git`/`origin`.

## Working with the agent team

The team is a set of named subagents in [`.claude/agents/`](.claude/agents/), tuned for this
project and assigned Claude model tiers (haiku = cheap/read-only, sonnet = workhorse, opus =
heavy reasoning). Quick guide:

| Need | Use | model |
|------|-----|-------|
| "Where is X?" / "how does Y work?" / "what changes for Z?" | **Legolas** (explorer, read-only) | haiku |
| Plan a change across the `schema.py` contract and its consumers | **Aragorn** (planner) | sonnet |
| Implement a feature/fix end-to-end (plan → build → test → verify) | **Gandalf** (implementer) | sonnet |
| A traceback or pipeline failure to isolate and fix | **Elrond** (debugger) | sonnet |
| Audit code for contract integrity, crawl safety, secrets | **Faramir** (code-reviewer) | sonnet |
| Write/run pytest coverage (retrieval, graph, MCP tools) | **Samwise** (test-writer) | sonnet |
| Judge answer relevance & citation accuracy of RAG/MCP output | **Círdan** (retrieval-evaluator) | opus |
| Build the graph, start the server, smoke-test a tool call → PASS/FAIL | **Gimli** (run-verifier) | haiku |
| Crawl health, data freshness, agency coverage, `.mt.gov` guardrails | **Treebeard** (crawl-steward, read-only) | haiku |
| Review the D3 visualizations / dashboard / presentations | **Arwen** (visualization-reviewer) | sonnet |
| Shape the question-answering experience & MCP tool naming | **Galadriel** (experience director) | sonnet |
| Roadmap, scope, acceptance gates for the MCP server | **Theoden** (product-manager) | opus |
| Release readiness / go-no-go for a versioned graph + server | **Eomer** (release-manager) | sonnet |
| Capture lessons after incidents | **Bilbo** (learning-steward) | haiku |

Shared voice: [`.claude/agents/agent-voice.md`](.claude/agents/agent-voice.md).

### 3-tier structure (each agent's `tier:` frontmatter)

The team is organized as a delegation flow, not a flat pool. Higher tier = rarer, costlier, more decisive.

- **Tier 1 — Strategy & Verdict (opus):** Theoden (scope + sequence + acceptance gates), Círdan (answer-quality verdict). *What should we do, and is the result good enough to ship?*
- **Tier 2 — Delivery & Assurance (sonnet):** *Build* — Aragorn, Gandalf, Elrond, Galadriel · *Assure* — Faramir, Samwise, Arwen, Eomer. *Make the change, and prove the code is sound.*
- **Tier 3 — Recon & Ops (haiku):** Legolas, Gimli, Treebeard, Bilbo. *Find it, run it, watch the data — fast and cheap.*

Delegation rules:

- **Theoden is the entry point** for any non-trivial request. He decomposes the goal into scoped slices and emits briefs (see the `planning` skill) rather than work being hand-delegated to 14 peers. Subagents carry no chat history — every brief must include goal, acceptance criteria, and exact file paths.
- **Make/check separation (non-negotiable):** the agent that builds a change never certifies its own answer quality. Code soundness is judged by the Tier-2 *Assure* group (Faramir/Samwise); answer relevance + citation accuracy is judged independently by **Círdan** (Tier 1). This is the trust guarantee for a citizen-facing answer engine.

Skills: `planning` (delegation/decomposition), `mcp-server` (build/extend the FastMCP server), `knowledge-query` (load and query the graph during development) — see `.claude/skills/`.
