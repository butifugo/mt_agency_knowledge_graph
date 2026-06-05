# Deployment

## The architecture reality (read this first)

This project has two parts with very different hosting needs:

- **Front-end (`web/`)** — static HTML/JS: the demo page, the chat widget, the D3
  knowledge-graph view, and the small `coverage.json` / `graph.json` data files.
  **This is Vercel-friendly.**
- **Backend** — the FastAPI chat API (`src/chat_api`), the MCP service (`src/mcp_server`),
  and the **knowledge graph** (`src/network/exports/montana_knowledge.pkl`, ~103 MB, loaded
  into memory). This needs a **persistent server with RAM**. It is **NOT a fit for Vercel
  serverless functions**: a 103 MB graph can't be reloaded per cold-start invocation, the
  `.pkl` isn't in the repo (gitignored), and building it needs the multi-GB `knowledge/` crawl.

So Vercel hosts the **front-end**; the **backend lives elsewhere**.

| Piece | Recommended host |
|------|------------------|
| `web/` static front-end | **Vercel** |
| chat API + MCP service + graph | **Render / Railway / Fly.io / a small VM** (a persistent process) |

## Front-end on Vercel

1. Import the GitHub repo in Vercel.
2. Framework preset: **Other**. Root stays repo root; `vercel.json` serves the **`web/`** directory
   (`outputDirectory: web`, no build).
3. **Point the widget at the hosted backend.** In `web/index.html`:
   - the widget tag `data-api="…"` → your backend's chat API URL
   - the MCP tab's `MCP_API` constant → your backend's MCP-bridge URL
   (For local dev these default to `http://localhost:8001` / `:8002`.)

Without a hosted backend, the **Overview** and **Knowledge graph** tabs still work (static),
but **Chat** and **MCP server** tabs need the backend reachable.

## Backend on a persistent host

1. Deploy the repo; `pip install -r requirements.txt` (Python 3.12).
2. Provide the graph one of three ways:
   - commit `montana_knowledge.pkl` via **Git LFS**, or
   - rebuild on the host (`scripts/build_graph_fast.py`, needs `knowledge/`), or
   - store it in object storage and download at boot.
3. Run the processes (set env: `CHAT_PROVIDER`, `PERPLEXITY_API_KEY`, etc.):
   - chat API: `uvicorn src.chat_api.app:app --host 0.0.0.0 --port $PORT`
   - MCP service: `python -m src.mcp_server.server --http --host 0.0.0.0 --port 8003`
   - (optional) MCP bridge: `MCP_SERVER_URL=… uvicorn src.mcp_demo.app:app …`
4. Set CORS to your Vercel domain (currently permissive for the local demo).

## Secrets

Never commit `.env` (it's git-ignored). Set `PERPLEXITY_API_KEY` / `ANTHROPIC_API_KEY` and
`CHAT_PROVIDER` in each host's environment settings.

## Local: run the whole stack

```bash
./scripts/run_stack.sh   # web :8000, chat :8001, MCP bridge :8002, MCP HTTP :8003
```
