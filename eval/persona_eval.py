"""AC-4 persona answer-quality harness (Círdan's gate) for community-planning-guide.

Runs each gold question's 1-2 turn conversation through the REAL persona answer path
(src.chat_api.answer.synthesize, live provider), carrying state forward between turns,
and dumps the material needed to score relevance / citation-accuracy / groundedness /
guided-behavior.

    .venv/bin/python -m eval.persona_eval            # human-readable
    .venv/bin/python -m eval.persona_eval --json     # machine-readable transcript

Citation universe is computed from the graph itself (the 16 CPP-scoped docs), so the
'is this a real in-scope URL' check is grounded, not hand-listed.
"""
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.chat_api.answer import synthesize  # noqa: E402
from src.chat_api.retrieval import build_node_filter, get_retriever  # noqa: E402

GOLD = ROOT / "eval" / "persona_gold_questions.yaml"
PERSONA = "community-planning-guide"


def scoped_urls():
    """The legitimate citation universe: every CPP-scoped source_url in the graph."""
    r = get_retriever()
    nf = build_node_filter("commerce", "Community-Planning-Platform")
    urls = set()
    for nid, meta in r.graph.nodes.items():
        try:
            ok = nf(nid, meta)
        except TypeError:
            ok = nf(meta)
        if ok:
            u = getattr(meta, "source_url", None)
            if u:
                urls.add(u)
    return urls


def run():
    gold = yaml.safe_load(open(GOLD))["questions"]
    legit = scoped_urls()
    out = []
    for item in gold:
        state = None
        turns_log = []
        for msg in item["turns"]:
            res = synthesize(msg, persona=PERSONA, history=_history(turns_log), state=state)
            state = res.get("state")
            turns_log.append({"user": msg, "assistant": res["answer"]})
            cited = [c.get("url") for c in res.get("citations", [])]
            srcs = [s.get("url") for s in res.get("sources", [])]
            turns_log[-1].update(
                stage=res.get("stage"),
                branch=(state or {}).get("branch"),
                slots=(state or {}).get("slots"),
                artifact=res.get("artifact"),
                followups=res.get("followups"),
                citations=cited,
                sources=srcs,
                handoff=res.get("handoff"),
                cited_out_of_scope=[u for u in cited if u and u not in legit],
                sources_out_of_scope=[u for u in srcs if u and u not in legit],
            )
        out.append({"id": item["id"], "branch": item["branch"],
                    "expect_url": item.get("expect_url"),
                    "expect_terms": item.get("expect_terms", []),
                    "turns": turns_log})
    return out, legit


def _history(turns_log):
    h = []
    for t in turns_log:
        h.append({"role": "user", "content": t["user"]})
        h.append({"role": "assistant", "content": t["assistant"]})
    return h or None


if __name__ == "__main__":
    data, legit = run()
    if "--json" in sys.argv:
        print(json.dumps({"legit_urls": sorted(legit), "results": data}, indent=2))
    else:
        for q in data:
            print("=" * 90)
            print(f"[{q['id']}]  branch_expected={q['branch']}  expect_url~={q['expect_url']}")
            print("=" * 90)
            for i, t in enumerate(q["turns"], 1):
                print(f"\n--- turn {i} | stage={t['stage']} branch={t['branch']} slots={t['slots']}")
                print(f"USER: {t['user']}")
                print(f"ASSISTANT:\n{t['assistant']}")
                print(f"  citations: {t['citations']}")
                if t["cited_out_of_scope"]:
                    print(f"  !! CITED OUT OF SCOPE: {t['cited_out_of_scope']}")
                print(f"  followups: {t['followups']}")
                if t["artifact"]:
                    print(f"  artifact: {t['artifact']}")
                if t["handoff"]:
                    print(f"  handoff: {t['handoff']}")
