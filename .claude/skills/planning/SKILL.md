---
name: planning
description: Decompose a goal into scoped, delegable slices for the 3-tier agent team and write briefs subagents can act on with no prior context. Use when breaking down multi-step work, sequencing toward the MCP server, or handing work to Tier-2/Tier-3 agents.
---

# Planning & delegation

This project's work is delivered by a **3-tier agent team** (see `CLAUDE.md` → "Working with the agent team"). Subagents start with **no chat history**, so a plan is only useful if each delegated slice is a self-contained brief. Theoden (product-manager, Tier 1) is the entry point and owns this skill.

## The delivery loop (one slice)

```
Theoden (scope) → Legolas (locate) → Aragorn (plan) → Gandalf (build, +Elrond on failures)
   → Samwise (tests) + Faramir (review)  → Gimli (build graph, smoke a tool call)
   → Círdan (answer-quality verdict)      → Eomer (go/no-go)  → Bilbo (lesson, if any)
```

## How to decompose

1. **Outcome** — state the measurable change (e.g. "an MCP tool answers an agriculture question with a valid, cited `RAGResult`").
2. **Smallest valuable slices** — each slice ships something verifiable on its own. Prefer "one tool, end-to-end" over "all tools, half-wired."
3. **Sequence** — order by dependency; foundational gaps first (e.g. `git init`, a `tests/` harness, then the first FastMCP tool).
4. **Assign an owner per slice** by tier/role. Keep make and check with different agents.
5. **Define acceptance + verify** before any building.

## Brief template (copy per delegated slice)

```
## Brief: <slice name>   — owner: <agent>   tier: <n>
Goal: <one sentence outcome>
Context: <the 2-3 facts the agent needs; this project's relevant rule(s)>
Files (exact paths):
  - <path> — <what to do>
Constraints: graph is source of truth · schema.py is the contract · keep retrieval in src/network ·
             never hand-edit generated paths (knowledge/**, data/graphs/**, src/network/exports/**, html/agency-data/**) ·
             crawl only .mt.gov, honor config.yaml rate limits
Acceptance criteria:
  - <testable outcome>
Verify: <command/check, e.g. python src/network/3_build_network.py --quick + a retrieve() call returning RAGResult>
```

## Rules

- Theoden decomposes and briefs; he does not implement.
- Every brief names exact files — never "find the right file" without pointing at where to look (delegate that to Legolas first).
- The answer-quality verdict is always Círdan's, never the builder's (make/check separation).
- Tie each slice's "done" to the project's real gates: tests green, `RAGResult` contract intact, graph rebuilt, gold-set bar met.
