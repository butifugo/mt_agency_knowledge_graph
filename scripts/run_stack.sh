#!/bin/bash
# Run the whole app locally as ONE service — identical to the Railway deployment.
#   /            static front-end (Overview / Knowledge graph / MCP server tabs)
#   /chat        grounded, cited answers
#   /api/mcp/*   MCP browser-demo bridge
#   /mcp/        real MCP endpoint for AI clients
set -euo pipefail
cd "$(dirname "$0")/.."
exec .venv/bin/python -m uvicorn src.web_app:app --host 127.0.0.1 --port "${PORT:-8000}"
