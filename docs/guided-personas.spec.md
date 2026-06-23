# Guided Personas — Specification

> Owners: **Theoden** (scope + acceptance gates, Tier 1) · **Galadriel** (experience & answer-shape, MCP tool naming, Tier 2).
> Status: **blocked on data (NO-GO for v1 ship)** — build + contract certified (AC-1, AC-2, AC-5, AC-6 PASS; 52 tests green), but **AC-4 NO-GO** and **AC-3 unsatisfiable**: the 16 CPP source nodes are *title stubs only* (13–21 words, ~90–160 chars each; 1/16 mentions any planning/funding term). Answers aren't grounded in the cited pages. P0 was a false-green — it checked title-coverage, not retrievable body content. **Root cause: a crawl/extraction gap (likely JS-rendered CPP pages), not the persona code.** Build date: 2026-06-18 · Verification opened: 2026-06-22 · AC-4 run + corpus gap found: 2026-06-23.
> Principle: a persona is **configuration, not code** — one declarative file = one guided expert, usable from both the web widget and an MCP client, over the unchanged shared retrieval core.

## Objective

Add a **guided-expert** layer on top of the existing answer engine. Where today's assistant reactively answers one question at a time (`src/chat_api/answer.py` `SYSTEM_INSTRUCTIONS`), a **persona** is a goal-driven expert that holds a **stateful, multi-turn conversation**, narrows retrieval to a section of the knowledge graph, and drives the user toward a concrete deliverable.

The first persona — **Community Planning Guide** — helps a *local planner/economic developer* build a planning document, or a *prospecting company* evaluate a Montana community, grounded in the Department of Commerce **Community Planning Platform** (CPP) pages.

This is the "should-have" *multi-turn conversation memory* deferred in [`docs/mvp-requirements.md`](mvp-requirements.md), now promoted to a spec, plus a reusable persona framework around it.

## Confirmed decisions

| # | Decision | Choice |
|---|----------|--------|
| D1 | A persona is | a declarative **config file** (`personas/*.yaml`) loaded by name. Adding a persona never touches retrieval or graph code. |
| D2 | Conversation is | **stateful** and multi-turn. The agent tracks where it is in a guided flow and what it has learned. |
| D3 | Where state lives | **client-held transcript + a server-computed `state` object the client echoes back.** No server-side session store for v1. The server stays functionally stateless. |
| D4 | How state advances | the model **emits a `<<STATE>>` block** alongside its answer (mirrors the existing `<<FOLLOWUPS>>` pattern); the server merges it into the authoritative state and returns it. |
| D5 | Retrieval core | scoping needs a **candidate-level filter**, so `GraphRAGRetriever.retrieve()` gained one additive, backward-compatible `node_filter` param (`schema.py` untouched). Post-retrieval filtering was tried first and rejected — a 16-page section never survived top-k truncation. Everything else stays in `src/chat_api/`. |
| D6 | First persona shape | **one persona, two branches** (`build_plan` / `evaluate_community`) — same CPP content, branch chosen at the `orient` stage. |
| D7 | Both surfaces | the web widget owns its conversation loop and threads `state`; the **MCP host client owns its own loop**, so statefulness on MCP rides on the client's context (the tool stays near-stateless, optionally accepting/returning `state`). |

## Architecture

```
 web page (CPP-styled)              ┌──────────────────────────────────────────┐
 ┌───────────────────┐             │  src/network/  — SHARED CORE (UNCHANGED)   │
 │ chat widget        │            │  GraphRAGRetriever.retrieve() → RAGResult  │
 │ holds: history,    │            └───────▲───────────────────────▲────────────┘
 │ state, artifact    │                    │ import                 │ import
 └─────────┬──────────┘                    │                        │
           │ POST /chat                     │                        │
           │ {persona, question,            │                        │
           │  history[], state}      ┌──────┴───────────────┐ ┌──────┴───────────┐
           ▼                          │ src/chat_api         │ │ src/mcp_server   │
 ┌──────────────────────┐            │  answer.synthesize() │ │  persona tool(s) │──▶ AI client
 │ persona layer (NEW)   │◀──────────│  + persona layer     │ │  (host owns loop)│   (Claude Desktop)
 │ personas.py (load)    │            └──────────┬───────────┘ └──────────────────┘
 │ conversation.py(state)│                       │ scope + voice + state → prompt
 └──────────────────────┘                        ▼ providers.py → LLM (synthesis only)
```

New code is confined to `src/chat_api/` (+ a `personas/` config dir + widget). Retrieval logic stays in `src/network/`; the LLM is still called in exactly one place.

---

## Part 1 — The persona config framework

### 1.1 Schema (`personas/*.yaml`)

| Field | Type | Req | Meaning |
|-------|------|-----|---------|
| `id` | string (kebab) | ✓ | Stable identifier; selected by `persona` in the request / MCP tool. |
| `name` | string | ✓ | Human label shown in UI and MCP tool title. |
| `audience` | string | ✓ | Who it serves; informs the model's framing. |
| `scope` | object | ✓ | How retrieval is narrowed. See 1.2. |
| `voice` | string (multi-line) | ✓ | The system-prompt body. **Replaces** `SYSTEM_INSTRUCTIONS` for this persona. Must preserve the grounding + citation + `<<FOLLOWUPS>>` contract. |
| `goals` | string[] | ✓ | Ordered objectives the agent drives toward (rendered into the prompt). |
| `flow` | object | ✓ | The stage machine. See Part 2. |
| `slots` | object[] | ✓ | Facts the agent collects (`id`, `type`/`enum`, `branch?`, `prompt`). |
| `artifacts` | map | ✓ | Named output templates keyed by branch; each is an ordered field list. |
| `opening` | string | ✓ | First message the widget shows before any user input. |
| `starters` | string[] | – | Suggested first prompts the widget renders as buttons. |
| `mcp` | object | – | `tool_name`, `tool_description` for the MCP surface (3.3). |

### 1.2 `scope` — retrieval narrowing

```yaml
scope:
  agency: commerce                          # existing post-retrieval agency filter
  url_contains: "Community-Planning-Platform"  # NEW: section-level filter on source_url
  topics: [growth policy, zoning, CIP, CEDS]   # optional query-expansion hints
```

`scope` becomes a `node_filter` predicate (`build_node_filter()` in `retrieval.py`) passed into `GraphRAGRetriever.retrieve(..., node_filter=)`. The retriever applies it to ranked candidates **before** top-k truncation and guarantees every passing node is a candidate — so a small section (the CPP is ~16 pages in an 11.7k-node graph) is fully reachable even when its pages don't all match the query keywords. **Measured:** post-retrieval filtering returned 0 CPP pages for "growth policy"; candidate-level scoping returns 6/6. If a scoped query yields nothing, both surfaces fall back to an unscoped answer rather than going silent.

### 1.3 Loading (`src/chat_api/personas.py`, NEW)

- `get_persona(id) -> Persona` — `lru_cache`d registry that reads `personas/*.yaml`, validates required fields, and returns a typed object.
- `list_personas() -> [{id, name, audience}]` — for a future picker.
- Unknown `id` raises a clear error (HTTP 400 at the boundary). `persona=None` ⇒ today's generic assistant, unchanged.

---

## Part 2 — Stateful conversation design (the core)

### 2.1 State model

A small JSON object, computed by the server and echoed by the client each turn:

```jsonc
{
  "persona": "community-planning-guide",
  "stage":   "scope",                 // current stage id
  "branch":  "build_plan",            // null until orient resolves
  "slots": {                           // accumulated facts
    "community": "Red Lodge",
    "plan_type": "growth_policy"
  },
  "artifact": {                        // the deliverable, built up progressively
    "purpose": "...", "required_data": [...], "sections": [...],
    "template": null, "funding": [], "next_office": null,
    "action_items": [                  // the work plan's checkable to-do list (2.6)
      {"task": "Pull your Community Profile data", "owner": "Commerce CDD",
       "when": "before drafting", "cite": "[1]"}
    ]
  },
  "turn": 3
}
```

The **server is authoritative** on merging: it never trusts a client-sent `state` blindly for stage legality — it re-validates that the emitted transition is legal (2.4) before returning the new state.

### 2.2 Transport (D3) — why client-held + echo

- The widget keeps `history` (the transcript) and the last `state`, and sends both on each `POST /chat`.
- The server merges the model's `<<STATE>>` delta into the received `state`, validates, and returns the new `state` + answer.
- **No session store, no DB, no expiry** — the demo stays as simple to host as today. State survives a page reload only if the client persists it (optional `localStorage`).

### 2.3 State-emission protocol (D4)

The persona `voice` instructs the model to append, after the `<<FOLLOWUPS>>` block, a state delta:

```
<<STATE>>
{"stage":"scaffold","slots":{"plan_type":"growth_policy"},
 "artifact":{"sections":["Land use","Housing","Transportation"]}}
<</STATE>>
```

`src/chat_api/conversation.py` (NEW) extracts and parses it exactly like `split_followups` does today ([answer.py:106](../src/chat_api/answer.py#L106)) — tolerant of a missing close marker, malformed JSON falls back to "no change." The delta is **merged** (slots/artifact fields union; `stage` replaces) into prior state. The block is stripped from the visible answer.

### 2.4 The stage machine — Community Planning Guide

| Stage | Goal | Enter when | Exit when |
|-------|------|-----------|-----------|
| `orient` | Identify the branch | start | `branch` set (`build_plan` \| `evaluate_community`) |
| `scope` | Capture community + plan/need | branch set | `community` AND (`plan_type` \| `business_need`) |
| `ground` | Surface matching profile data + the right guidance/template | scope filled | relevant CPP sources presented; user confirms direction |
| `scaffold` | Assemble the artifact | ground confirmed | artifact core fields populated |
| `fund_act` | Map to program + office/form | artifact drafted | ≥1 funding program + a contact surfaced |
| `complete` | Recap deliverable + next steps | fund_act done | — |

Rules: stages advance **at most one step per turn** and only when the exit condition's slots are present; the server clamps illegal jumps back to the highest legal stage. The model may stay in a stage across turns while filling slots. Backward movement is allowed if the user changes the community/plan type.

### 2.5 Slots & artifacts (this persona)

```yaml
slots:
  - {id: branch,        enum: [build_plan, evaluate_community]}
  - {id: community,     type: string}
  - {id: plan_type,     branch: build_plan,
     enum: [growth_policy, capital_improvement_plan, ceds,
            zoning_ordinance, subdivision_regs, annexation]}
  - {id: business_need, branch: evaluate_community, type: string}
  - {id: planning_stage, type: string, optional: true}

artifacts:
  build_plan:        [purpose, required_data, sections, template, funding, next_office, action_items, sources]
  evaluate_community:[community, profile_highlights, infrastructure_notes, incentives, contacts, action_items, sources]
```

`funding` is drawn only from programs named in CPP sources (CDBG, Montana Main Street, Ready Communities, SLIPA) — never invented; same grounding rule as the base assistant.

### 2.6 The work plan — `action_items` (every persona)

The deliverable is a **work plan**, not just a narrative scaffold: alongside the prose fields, every
persona's artifact carries an ordered `action_items` list — the concrete next steps the interview
drives the user toward. Each item is an object:

```jsonc
{"task": "Adopt the growth policy by resolution",  // short imperative step
 "owner": "planning board",                         // an office/board NAMED in sources, or "you"
 "when":  "before drafting",                        // rough sequence/timing; omitted, never a guessed date
 "cite":  "[2]"}                                     // the [n] source it's grounded in, when one applies
```

Rules (enforced by the shared conversation paradigm in `answer.py`, not per-persona code):
- The model **re-emits the full list** in each `<<STATE>>` artifact delta; `merge_state` **replaces**
  it wholesale (an empty list is ignored, so a quiet turn never wipes it). It is built from the
  grounding stage onward and is the user's real to-do list by `complete`.
- `owner` and `cite` follow the same grounding rule as the rest of the answer — no invented office,
  contact, or deadline.
- The web widget renders `action_items` as an **interactive checklist** (check off / uncheck in the
  plan panel; copy/download export reflects checked state as `- [x]` / `- [ ]` markdown tasks). No
  server persistence — checked state is session-only, consistent with D3.

---

## Part 3 — Surfaces

### 3.1 Chat API contract changes (`src/chat_api/app.py`)

`ChatRequest` (additive, back-compatible):

```python
class ChatRequest(BaseModel):
    question: str                       # latest user message (unchanged)
    persona: Optional[str] = None       # NEW — null = generic assistant
    agency:  Optional[str] = None       # unchanged; persona.scope.agency wins if set
    history: List[Turn]    = []         # NEW — [{role, content}] prior turns
    state:   Optional[dict] = None      # NEW — last state echoed back
```

`ChatResponse` gains: `persona`, `stage`, `state`, and `artifact` (present once being built). Existing `answer / citations / sources / followups / strategy / provider / model` are unchanged.

### 3.2 Synthesis (`src/chat_api/answer.py`)

`synthesize(question, agency=None, persona=None, history=None, state=None)`:

1. Resolve persona → `voice`, `scope`, `flow`, current `stage`.
2. Retrieve, then apply `scope` filters (agency + `url_contains`).
3. Build the system prompt = `voice` + serialized **current state** + **stage-specific guidance** (the active stage's goal + what slot to fill next) + the grounding/citation/`<<FOLLOWUPS>>`/`<<STATE>>` protocol.
4. `build_messages` now returns `(system_text, messages[])` where `messages` = `history` + the new user turn (with the Sources block). **Multi-turn requires passing prior turns as real messages, not flattened text.**
5. Call provider, then extract follow-ups (existing), extract + merge `<<STATE>>` (new), strip invalid citations (existing).
6. Return answer + new `state` + `stage` + `artifact`.

`persona=None` skips steps 1/3-scope/5-state and behaves exactly as today (regression guard, AC-5).

### 3.3 Provider impact (`src/chat_api/providers.py`)

`complete(system_text, user_text)` → `complete(system_text, messages)` (a list of `{role, content}`). Both Perplexity (OpenAI-compatible) and Anthropic accept a messages array natively, so this is a signature change, not new infrastructure. The single-string callers (unit tests, generic assistant) pass a one-element list.

### 3.4 Web widget (`web/widget.js`, `web/index.html`)

- Read `data-persona`; on load show the persona's `opening` and `starters` buttons.
- Maintain `history` and `state`; send both each turn; store the returned `state`.
- Render the `artifact` as a live, growing panel (the "plan scaffold" the user watches assemble) — this is the visible payoff of statefulness.
- A dedicated `planning.html` styled to sit on / link from the CPP page is the intended embed.

### 3.5 MCP surface (`src/mcp_server/server.py`)

- Register one tool per persona, e.g. `community_planning_guide`, whose **description is the persona's pitch** so the host model knows when to use it (Galadriel owns the wording — see the `mcp-server` skill).
- The tool does **scoped retrieval + guidance only — it never calls an LLM** (project contract: MCP tools don't synthesize). It returns the persona-scoped passages (via the shared `build_node_filter` + `retrieve(node_filter=)`) plus a `guidance` block (goals + stages + how-to-use). The **host client is the conversation loop** and writes the guided, cited answer from those passages.
- Statefulness on MCP is therefore **free**: the host client (Claude Desktop) holds the conversation; the tool is stateless.

---

## Part 4 — Contract & data impact

- **No `schema.py` change.** Personas read existing `RAGResult` / `source_url`. The graph is untouched; nothing to rebuild.
- New Pydantic/dataclass models (`Persona`, `Turn`, conversation `State`) live in `src/chat_api/` only.
- Faramir reviews the new models + confirms the LLM is still called in exactly one place and retrieval isn't reimplemented.

## Part 5 — File-by-file change map

| File | Change |
|------|--------|
| `personas/community-planning-guide.yaml` | NEW — the first persona instance |
| `src/chat_api/personas.py` | NEW — load + validate + registry |
| `src/chat_api/conversation.py` | NEW — state model, merge, stage machine, `<<STATE>>` extraction |
| `src/network/rag_retriever.py` | `retrieve()` gained additive `node_filter` (candidate-level scoping) |
| `src/chat_api/retrieval.py` | NEW `build_node_filter(agency, url_contains)` — shared by both surfaces |
| `src/chat_api/answer.py` | persona-aware `synthesize`; history via `provider.complete(..., history)`; persona system-prompt assembly; state extract/merge; scoped retrieval + unscoped fallback |
| `src/chat_api/providers.py` | `complete()` / `build_payload()` take optional `history` (back-compatible) |
| `src/chat_api/app.py` | `ChatRequest`/`ChatResponse` fields + `GET /personas/{id}` |
| `web/widget.js`, `web/planning.html` | hold history+state, render starters + artifact panel |
| `src/mcp_server/server.py` | scoped persona tool (retrieval + guidance, no LLM) |
| `tests/test_personas.py`, `test_conversation.py`, `test_persona_answer.py` | persona load, state machine + `<<STATE>>` parse, scoped persona synthesis, generic regression |
| `docs/guided-personas.spec.md` | this file |

## Part 6 — Acceptance gates

- **P0 (precondition):** ⚠️ **RETRACTED 2026-06-23** — the 2026-06-18 check confirmed 16 CPP docs *exist* matching `agency=commerce` + `url_contains=Community-Planning-Platform` across all six plan types, Community Profiles, and Planning Resources **by title**, but did NOT verify retrievable body content. Re-measured 2026-06-23: each CPP node carries only 13–21 words / ~90–160 chars (page title + nav, no guidance text); only 1 of 16 mentions any of grant/CDBG/funding/zoning/Main Street/Ready Communities/SLIPA. **The persona does not have solid ground.** P0 must be re-defined to assert *content depth* (e.g. ≥N words of body text per CPP node, key programs present) and re-passed after a CPP re-crawl/re-extract + graph rebuild. Lesson: a precondition that counts documents but not their content is a false-green.
- **AC-1 (flow):** a scripted 5-turn conversation advances `orient → scope → ground → scaffold → fund_act` correctly; no illegal stage jumps; `state` round-trips through request/response.
- **AC-2 (scope):** every cited source for this persona resolves to a `Community-Planning-Platform` URL; out-of-scope agencies don't leak in.
- **AC-3 (artifact):** by `complete`, the `build_plan` artifact has populated `sections`, ≥1 grounded `funding` program, a `next_office`, and an `action_items` work plan (≥2 ordered steps), each traceable to a citation where one applies.
- **AC-4 (quality, independent):** **Círdan** scores a planning gold-question set for answer relevance + citation accuracy and gives go/no-go (make/check separation — the implementer does not certify their own answer quality).
- **AC-5 (no regression):** `persona=None` produces byte-comparable behavior to today's assistant; existing pure-function unit tests still pass.
- **AC-6 (contract):** **Faramir** confirms `schema.py` untouched, the `node_filter` addition to `retrieve()` is additive + backward-compatible (default `None` = prior behavior), retrieval logic stays in `src/network/` (not reimplemented in a surface), and the LLM is called in exactly one place (`providers.py`) — the MCP persona tool does **not** synthesize.

## Part 7 — Open decisions & out of scope

- **Open:** auto-routing (a meta-layer that picks the persona from the user's first message) — deferred; v1 selects persona explicitly via `data-persona` / tool choice.
- **Open:** persisting `state` across reloads (`localStorage`) — nice-to-have, not required for AC.
- **Known:** `get_persona` is `lru_cache`d for the process — editing a persona YAML requires a server restart to take effect (acceptable for v1; revisit if hot-reload is wanted).
- **Out of scope (v1):** server-side session store, streaming responses, auth, multi-language, embedding on a live `.mt.gov` page.
- **Deferred to v2 (runtime persona team):** the build has produced four additional personas (`funding-grants-advisor`, `growth-policy-advisor`, `infrastructure-cip-advisor`, `site-selection-advisor`) plus a `<<HANDOFF>>` routing protocol (`_conversation_paradigm`, `_resolve_handoff` in `src/chat_api/`). This multi-persona advisory team is **runtime-grounded** (all four scope to the same 16-node CPP corpus) and **contract-safe** (pure config; Faramir-certified, no `src/network/` or LLM-site change), but is **undocumented here, untested, and not wired into the MCP surface** (only `community-planning-guide` registers; handoff is chat-API-only). It is **out of v1 scope** and rides dormant in-tree until a v2 spec defines its own gates (handoff correctness, per-persona scope isolation, team-routing quality). v1 ships the single Community Planning Guide.

### Note — build-time agents vs. runtime persona-agents (do not conflate)

Two distinct "agent" populations exist in this repo and must stay cleanly separated:

- **Build-time team** (`.claude/agents/` — Theoden, Legolas, Faramir, Samwise, Círdan, …): Claude Code development subagents. **No production footprint** — never imported by `src/`, never shipped, never invoked by the running app. Verified: no `src/` reference to any team member.
- **Runtime persona-agents** (`personas/*.yaml`, served by `src/chat_api/` + `src/mcp_server/`): the guided experts a citizen actually interacts with. The `<<HANDOFF>>` / `<<STATE>>` protocols belong here. **This is the product.**

When this spec or a brief says "the team," confirm which population is meant. The acceptance gates in Part 6 govern the **runtime** layer only.

---

### Suggested build sequence (for Theoden to slice)

1. Verify P0 (Treebeard). 2. `personas.py` + the YAML (load + validate). 3. `conversation.py` state machine + `<<STATE>>` parse (unit-tested first — Samwise). 4. `synthesize`/providers/`app.py` wiring. 5. Widget history+state+artifact panel. 6. MCP persona tool. 7. Círdan quality gate.
