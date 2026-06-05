# Deployment — Railway (single service)

The whole app runs as **one FastAPI service** (`src/web_app.py`) on **one origin** — no CORS,
one deploy. Railway is the recommended host because it runs a **persistent process with RAM**
(the ~103 MB knowledge graph stays in memory), which serverless platforms like Vercel can't do.

```
GET  /            static front-end (web/: Overview / Knowledge graph / MCP server tabs)
POST /chat        grounded, cited answer (Perplexity or Claude per CHAT_PROVIDER)
GET  /health      health check
GET  /api/mcp/tools, POST /api/mcp/call   MCP browser-demo bridge (powers the MCP tab)
/mcp/             real MCP streamable-HTTP endpoint for AI clients (e.g. Claude Desktop)
```

## Run locally (identical to prod)

```bash
./scripts/run_stack.sh            # → http://localhost:8000/
```

## Deploy on Railway

1. **Install + log in** (login is interactive — a browser pairing flow):
   ```bash
   brew install railway        # or: npm i -g @railway/cli
   railway login
   ```
2. **Create the project from this repo and deploy:**
   ```bash
   railway init -n mt-agency-knowledge
   railway up
   ```
   (or, in the Railway dashboard: New Project → Deploy from GitHub repo → `butifugo/mt_agency_knowledge_graph`)
3. **Set environment variables** (Railway dashboard → Variables, or `railway variables --set K=V`):
   - `CHAT_PROVIDER=perplexity`
   - `PERPLEXITY_API_KEY=…`  (your key; never commit it)
   - `GRAPH_URL=https://github.com/butifugo/mt_agency_knowledge_graph/releases/download/graph-v1/montana_knowledge.pkl`
     — the built graph (~108 MB), published as a public release asset (repo is public, so **no token needed**).
   - `GRAPH_URL_TOKEN` — not needed while the release asset is public; set it only if you later make
     the repo private (then use the asset's API URL + a GitHub token with `contents:read`).
   - `PORT` is provided by Railway automatically.
4. **Pick ≥ 1 GB RAM** for the service (graph + Python). Railway gives HTTPS automatically.

Build config: `railway.json` (Nixpacks start command + `/health` healthcheck), `.python-version`
pins Python 3.12, `Procfile` mirrors the start command.

## The graph (`montana_knowledge.pkl`, ~103 MB)

It's git-ignored (too big for the repo), so the host fetches it at boot via `GRAPH_URL`
(`src/chat_api/retrieval.py::_ensure_graph_file`). Provide it one of:
- **GitHub Release asset** — `gh release create graph-v1 src/network/exports/montana_knowledge.pkl`;
  for a private repo, set `GRAPH_URL` to the asset's API URL and `GRAPH_URL_TOKEN` to a GitHub token.
- **Object storage** (Cloudflare R2 / S3) — upload once, use the public/presigned URL.
- Don't ship the multi-GB `knowledge/` crawl; only the built pickle is needed at runtime.

## Point Claude Desktop at the hosted MCP

Once live, update the `-live` connector in `claude_desktop_config.json`:
```json
"montana-agency-knowledge-live": {
  "command": "npx",
  "args": ["-y", "mcp-remote", "https://YOUR-APP.up.railway.app/mcp/"]
}
```

## Secrets

`.env` is git-ignored — never commit keys. Set them in Railway's Variables.
```
