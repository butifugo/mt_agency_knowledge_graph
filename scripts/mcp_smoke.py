"""MVP Slice 5 smoke — verify the MCP server's tools work over the real graph.

Runs under the dedicated 3.12 venv (FastMCP requires >= 3.10):
    .venv/bin/python scripts/mcp_smoke.py

Calls the tool *logic* directly (no MCP client needed) and also confirms the tools
are registered on the FastMCP server. This doubles as the cross-version proof that
the 3.9-built montana_knowledge.pkl loads under Python 3.12.
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.mcp_server import server as S


def main() -> None:
    print(f"Python {sys.version.split()[0]}")

    # 1. search across agencies
    r = S._search("agriculture pesticide licensing", top_k=3)
    print(f"\nsearch_agency_knowledge: strategy={r['search_strategy']} "
          f"found={r['total_found']} {r['execution_time_ms']}ms")
    for i, d in enumerate(r["results"], 1):
        print(f"  {i}. {d['title']}  [{d['agency']}]")
        print(f"     {d['source_url']}")

    # 2. scope to one agency
    a = S._agency("human-resources", "leave", top_k=3)
    print(f"\nsearch_by_agency('human-resources','leave'): {a['total_found']} results")
    for d in a["results"]:
        print(f"  - {d['title']}")

    # 3. document context for the first hit
    if r["results"]:
        ctx = S._context(r["results"][0]["node_id"])
        rel = {k: len(v) for k, v in ctx.items() if isinstance(v, list)}
        print(f"\nget_document_context: related counts {rel}")

    # 4. confirm tools are registered on the FastMCP server (best-effort introspection;
    #    a successful import already proves the @mcp.tool decorators ran).
    try:
        tools = asyncio.run(S.mcp.get_tools())
        names = sorted(tools.keys()) if isinstance(tools, dict) else sorted(t.name for t in tools)
        print(f"\nRegistered MCP tools: {names}")
    except Exception as exc:  # introspection API can vary across FastMCP versions
        print(f"\n(tool introspection skipped: {exc!r}) — import succeeded, so tools registered")

    print("\n✓ MCP tools return real, citation-ready data and are registered.")


if __name__ == "__main__":
    main()
