# Web widget + sample page (MVP Workstream 3)

A self-contained, drop-in chat widget (`widget.js`) and a sample agency page (`index.html`)
that demonstrates it. The widget calls the chat API (`POST /chat`) and renders a grounded
answer with clickable source citations.

## Run the local demo

From the repo root, with the venv active:

```bash
# 1. start the chat API (needs ANTHROPIC_API_KEY in .env to produce real answers)
.venv/bin/uvicorn src.chat_api.app:app --port 8001

# 2. in another shell, serve this folder
python -m http.server 8000 --directory web

# 3. open the sample page and click the chat button (bottom-right)
open http://localhost:8000/
```

The widget reads the API URL from the script tag: `<script src="widget.js" data-api="http://localhost:8001">`.
Without an API key the widget shows a friendly "service isn't set up yet" message instead of an answer.

## Embed elsewhere

Paste this just before `</body>` on any agency page, replacing the placeholder host in
**both** spots with your hosted answer service:

```html
<script src="https://YOUR-CHAT-API.mt.gov/widget.js"
        data-api="https://YOUR-CHAT-API.mt.gov"></script>
```

`data-api` is where the widget POSTs questions; it must point at the live `/chat` API, not
`localhost`. The demo page (`index.html`) shows this same snippet with a one-click Copy button.

No build step, no dependencies. Single-turn for MVP (each question is independent).
