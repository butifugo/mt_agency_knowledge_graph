#!/bin/bash
# Launch the full demo stack with the durable, networked MCP service. Ctrl-C stops all.
#
#   MCP HTTP service  :8003   (deployable MCP server; clients connect at /mcp)
#   chat API          :8001   (widget backend; Perplexity synthesis)
#   MCP demo bridge   :8002   (HTTP -> MCP client -> the :8003 service)
#   web page          :8000   (overview / knowledge graph / MCP server tabs)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python

export MCP_SERVER_URL="http://127.0.0.1:8003/mcp"

echo "→ MCP HTTP service  :8003"
$PY -m src.mcp_server.server --http --host 127.0.0.1 --port 8003 & P_MCP=$!
echo "→ chat API          :8001"
$PY -m uvicorn src.chat_api.app:app --host 127.0.0.1 --port 8001 & P_CHAT=$!
echo "→ MCP demo bridge   :8002  (-> $MCP_SERVER_URL)"
$PY -m uvicorn src.mcp_demo.app:app --host 127.0.0.1 --port 8002 & P_BRIDGE=$!
echo "→ web page          :8000"
$PY -m http.server 8000 --bind 127.0.0.1 --directory web & P_WEB=$!

trap 'echo; echo "stopping..."; kill $P_MCP $P_CHAT $P_BRIDGE $P_WEB 2>/dev/null' INT TERM EXIT
echo
echo "Open http://localhost:8000/   (Ctrl-C to stop everything)"
wait
