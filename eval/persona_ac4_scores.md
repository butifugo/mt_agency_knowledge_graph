# AC-4 — Community Planning Guide answer-quality scores (Círdan)

Date: 2026-06-23 · Provider: anthropic / claude-haiku-4-5 · Persona: community-planning-guide (v1, single persona)
Harness: `eval/persona_eval.py` · Gold set: `eval/persona_gold_questions.yaml`

Rubric (per question, scored on the conversation as a whole):
- Relevance 0-2 — answers the planning question and drives toward the deliverable.
- Citation accuracy 0-2 — cited URLs are real CPP URLs AND actually support the claims.
- Grounded PASS/FAIL — substantive claims traceable to retrieved passages (no fabrication).
- Guided PASS/FAIL — asks the missing slot / advances the stage vs. dumping a generic answer.

Threshold applied for GO: mean relevance ≥ 1.5/2, mean citation accuracy ≥ 1.5/2,
groundedness PASS rate ≥ 80%, no question with a fabricated funding program.

| id | branch | Relevance | Citation acc. | Grounded | Guided | Note |
|----|--------|-----------|---------------|----------|--------|------|
| growth_policy_redlodge | build_plan | 2 | 0 | FAIL | PASS | Good guided flow; section list is from model knowledge, cited [1] does not contain it |
| cip_question | build_plan | 1 | 1 | FAIL | PASS | Asked slot, didn't yet answer CIP contents; citation real but stub |
| ceds_question | build_plan | 1 | 1 | FAIL | PASS | Asked scratch-vs-update; no grounded CEDS content available |
| zoning_subdivision | build_plan | 2 | 0 | FAIL | PASS | Strong zoning/subdivision answer — entirely from model, sources are title stubs |
| funding_growth_policy | build_plan | 1 | 2 | PASS | PASS | Correctly refused to invent programs; handed to v2 persona instead of grounding |
| evaluate_facility | evaluate_community | 1 | 2 | PASS | PARTIAL | Immediately handed off to v2 site-selection-advisor; never answered in-persona |
| evaluate_buildings | evaluate_community | 2 | 1 | FAIL | PASS | Named Buildings DB [1]; "search by location/type" detail not in source stub |
| profile_data_lookup | evaluate_community | 1 | 1 | FAIL | PASS | Asked branch then community; never reached actual profile data (none in corpus) |

Aggregate:
- Mean relevance: 1.375 / 2  (below 1.5 bar)
- Mean citation accuracy: 1.0 / 2  (below 1.5 bar)
- Groundedness PASS rate: 2/8 = 25%  (far below 80% bar)
- Fabricated funding program: NONE (0/8) — §2.5 rule held

ROOT CAUSE (single, dominant): the 16 scoped CPP source pages contain ~90-132 chars of text
each — the page TITLE only, no body. Verified: zero occurrences of "grant","fund","CDBG",
"Main Street","Ready Communities","SLIPA" in any scoped passage; section/data claims in the
answers appear in NONE of the cited source texts. Substance comes from the model's training
knowledge, decorated with [n] citations to pages that don't substantiate the claim.

VERDICT: NO-GO on AC-4. Citations are in-scope and never fabricated (AC-2 clean, §2.5 clean),
but they do not support the claims — the answers are not grounded in retrieved content. The
fund_act stage and AC-3's "≥1 grounded funding program" are unsatisfiable from this corpus.
