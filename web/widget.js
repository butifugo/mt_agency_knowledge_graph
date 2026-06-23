/*
 * MAGPIE chat widget — Montana Agency Public Information Engine.
 * A self-contained, drop-in chatbot for an unofficial example MCP server.
 *
 * Embed on any page with a single tag:
 *   <script src="widget.js" data-api="http://localhost:8001"></script>
 *
 * It injects its own styles + markup, asks the /chat API, and renders a grounded
 * answer with clickable source citations. No dependencies, single-turn (MVP).
 */
(function () {
  "use strict";

  var script = document.currentScript;
  var API_BASE =
    (script && script.getAttribute("data-api")) ||
    window.MT_CHAT_API ||
    "http://localhost:8001";

  // Optional guided-persona mode. With data-persona set, the widget runs a stateful,
  // multi-turn conversation: it holds the transcript + the server-computed state and
  // echoes both back each turn (no server session store). Absent → single-turn assistant.
  var PERSONA =
    (script && script.getAttribute("data-persona")) || window.MT_CHAT_PERSONA || null;

  // Optional inline/docked mode. With data-mount="#selector", the widget renders its panel
  // INTO that element (the page's advisor surface) instead of as a fixed corner bubble: no
  // launch button, always visible, fills its container. Absent → unchanged corner widget.
  var MOUNT_SEL = (script && script.getAttribute("data-mount")) || null;
  var mountEl = MOUNT_SEL ? document.querySelector(MOUNT_SEL) : null;
  var INLINE = !!mountEl;

  var convState = null; // last `state` object returned by the API
  var history = []; // [{role:"user"|"assistant", content}] prior turns
  var personaMeta = null; // {name, opening, starters} fetched once
  var greeted = false;
  var transcript = []; // [{q, answer, sources, followups, artifact, handoff}] — for persist + replay

  // Session persistence (docked workspace only): survives a reload for the browser session,
  // clears on tab close. One active conversation per mount → one stable key.
  var STORE_KEY = "magpie:session:" + (MOUNT_SEL || "corner");

  var DISCLAIMER =
    "MAGPIE is an unofficial example tool. AI-generated from public Montana agency pages — " +
    "verify important details on the source .mt.gov site.";

  // ---- styles (prefixed to avoid clashing with the host page) -------------
  // MAGPIE design system: warm-white canvas, teal primary + coral warmth, SF type,
  // soft shadows, generous radii. Values are hardcoded (not CSS vars) so the widget
  // looks right on any host page, not just ones that define MAGPIE tokens.
  var css =
    "" +
    ".mtchat-launch{position:fixed;right:20px;bottom:20px;width:58px;height:58px;border-radius:50%;" +
    "background:linear-gradient(135deg,#ff6b5e,#ff8f5e);color:#fff;border:none;cursor:pointer;" +
    "box-shadow:0 8px 22px rgba(255,107,94,.4);font-size:25px;line-height:58px;z-index:2147483000;" +
    "transition:transform .15s ease,box-shadow .2s ease}" +
    ".mtchat-launch:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(255,107,94,.5)}" +
    ".mtchat-launch:focus-visible{outline:3px solid #0ea5a5;outline-offset:2px}" +
    ".mtchat-panel{position:fixed;right:20px;bottom:90px;width:384px;max-width:calc(100vw - 32px);" +
    "height:560px;max-height:calc(100vh - 120px);background:#fefcfa;border-radius:20px;display:none;" +
    "flex-direction:column;overflow:hidden;box-shadow:0 4px 12px rgba(26,26,46,.06),0 24px 56px rgba(26,26,46,.18);" +
    "z-index:2147483000;-webkit-font-smoothing:antialiased;" +
    "font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a1a2e}" +
    ".mtchat-panel.mtchat-open{display:flex}" +
    ".mtchat-head{background:#fff;color:#1a1a2e;padding:14px 16px;display:flex;align-items:center;" +
    "justify-content:space-between;border-bottom:1px solid #ece8e3}" +
    ".mtchat-head h2{margin:0;font-size:15px;font-weight:700;letter-spacing:-.01em;display:flex;align-items:center;gap:8px}" +
    ".mtchat-head h2:before{content:'';width:9px;height:9px;border-radius:50%;flex:none;" +
    "background:linear-gradient(135deg,#0ea5a5,#ff6b5e)}" +
    ".mtchat-head p{margin:2px 0 0;font-size:11px;color:#8a8a9a}" +
    ".mtchat-close{background:none;border:none;color:#8a8a9a;font-size:22px;cursor:pointer;line-height:1;padding:4px;border-radius:8px;transition:color .15s,background .15s}" +
    ".mtchat-close:hover{color:#1a1a2e;background:#f3efe9}" +
    ".mtchat-close:focus-visible{outline:2px solid #0ea5a5}" +
    ".mtchat-log{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px;background:#fefcfa}" +
    ".mtchat-msg{max-width:88%;padding:10px 14px;border-radius:16px;font-size:14.5px;line-height:1.5;white-space:pre-wrap}" +
    ".mtchat-user{align-self:flex-end;background:linear-gradient(135deg,#0ea5a5,#0b8585);color:#fff;" +
    "border-bottom-right-radius:5px;box-shadow:0 4px 12px rgba(14,165,165,.28)}" +
    ".mtchat-bot{align-self:flex-start;background:#fff;border:1px solid #ece8e3;border-bottom-left-radius:5px;" +
    "white-space:normal;box-shadow:0 1px 2px rgba(26,26,46,.04)}" +
    ".mtchat-bot a{color:#0b8585;font-weight:500}" +
    ".mtchat-bot p{margin:0 0 8px}.mtchat-bot p:last-child{margin-bottom:0}" +
    ".mtchat-bot ul,.mtchat-bot ol{margin:6px 0;padding-left:20px}.mtchat-bot li{margin:3px 0}" +
    ".mtchat-bot code{background:#f3efe9;border-radius:6px;padding:1px 5px;font-size:12px;" +
    "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}" +
    ".mtchat-bot .mtchat-h{font-weight:700;margin:10px 0 4px;letter-spacing:-.01em}.mtchat-bot .mtchat-h:first-child{margin-top:0}" +
    ".mtchat-fups{margin-top:12px;display:flex;flex-direction:column;gap:7px}" +
    ".mtchat-fups b{font-size:11px;color:#8a8a9a;font-weight:600;text-transform:uppercase;letter-spacing:.05em}" +
    ".mtchat-fup{text-align:left;background:#e9faf8;border:1px solid #cdeeea;color:#0b8585;" +
    "border-radius:12px;padding:9px 13px;font-size:13px;cursor:pointer;line-height:1.4;font-weight:500;" +
    "transition:background .15s,border-color .15s,transform .05s}" +
    ".mtchat-fup:hover{background:#d7f4f0;border-color:#0ea5a5}" +
    ".mtchat-fup:active{transform:translateY(1px)}" +
    ".mtchat-fup:focus-visible{outline:2px solid #0ea5a5;outline-offset:1px}" +
    ".mtchat-srcs{margin-top:10px;font-size:12px;border-top:1px solid #ece8e3;padding-top:8px}" +
    ".mtchat-srcs b{display:block;margin-bottom:4px;color:#8a8a9a;font-weight:600;text-transform:uppercase;letter-spacing:.05em}" +
    ".mtchat-srcs ol{margin:0;padding-left:18px}" +
    ".mtchat-srcs li{margin-bottom:3px}" +
    ".mtchat-artifact{margin-top:12px;background:linear-gradient(135deg,#e9faf8,#fff);border:1px solid #cdeeea;" +
    "border-radius:14px;padding:12px 14px;font-size:13px}" +
    ".mtchat-artifact b{display:block;margin-bottom:6px;color:#0b8585;font-weight:700}" +
    ".mtchat-artifact ul{margin:0;padding-left:16px}.mtchat-artifact li{margin:3px 0;line-height:1.45}" +
    // Handoff: a prominent chip that switches to a recommended fellow advisor — coral, the
    // MAGPIE primary-action color, so it reads as the one strong CTA in the transcript.
    ".mtchat-handoff{margin-top:12px;display:flex;align-items:center;gap:8px;width:100%;text-align:left;" +
    "background:linear-gradient(135deg,#ff6b5e,#ff8f5e);color:#fff;border:none;border-radius:14px;padding:12px 14px;" +
    "font-size:13.5px;font-weight:600;cursor:pointer;line-height:1.35;box-shadow:0 8px 22px rgba(255,107,94,.28);" +
    "transition:transform .15s ease,box-shadow .2s ease}" +
    ".mtchat-handoff:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(255,107,94,.4)}" +
    ".mtchat-handoff:focus-visible{outline:2px solid #0ea5a5;outline-offset:2px}" +
    ".mtchat-handoff .mtchat-ho-ic{font-size:17px}" +
    ".mtchat-disc{font-size:11px;color:#8a8a9a;padding:7px 16px;background:#fefcfa;border-top:1px solid #ece8e3}" +
    ".mtchat-form{display:flex;gap:8px;padding:12px;border-top:1px solid #ece8e3;background:#fff}" +
    ".mtchat-input{flex:1;border:1px solid #e0dad2;border-radius:999px;padding:11px 16px;font-size:14px;min-height:24px;" +
    "background:#fefcfa;color:#1a1a2e;font-family:inherit}" +
    ".mtchat-input:focus{outline:none;border-color:#0ea5a5;box-shadow:0 0 0 3px rgba(14,165,165,.15)}" +
    ".mtchat-send{background:linear-gradient(135deg,#0ea5a5,#0b8585);color:#fff;border:none;border-radius:999px;" +
    "padding:0 18px;cursor:pointer;font-size:14px;font-weight:600;min-width:52px;box-shadow:0 4px 12px rgba(14,165,165,.28);" +
    "transition:transform .15s ease}" +
    ".mtchat-send:hover{transform:translateY(-1px)}" +
    ".mtchat-send:disabled{opacity:.5;cursor:default;transform:none}" +
    ".mtchat-dots{display:inline-block}" +
    ".mtchat-dots:after{content:'…';animation:mtchat-blink 1.2s infinite}" +
    "@keyframes mtchat-blink{0%,100%{opacity:.3}50%{opacity:1}}" +
    // Inline/docked mode: the panel fills its mount container instead of floating.
    ".mtchat-panel.mtchat-inline{position:static;right:auto;bottom:auto;width:100%;height:100%;" +
    "max-width:none;max-height:none;display:flex;border-radius:inherit;box-shadow:none;z-index:auto;background:#fff}" +
    ".mtchat-panel.mtchat-inline .mtchat-log{background:#fefcfa}" +
    ".mtchat-panel.mtchat-inline .mtchat-close{display:none}" +
    ".mtchat-empty{margin:auto;padding:24px;text-align:center;color:#8a8a9a;font-size:14px;max-width:280px}";

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  // ---- markup --------------------------------------------------------------
  var launch = document.createElement("button");
  launch.className = "mtchat-launch";
  launch.setAttribute("aria-label", "Open MAGPIE chat");
  launch.innerHTML = "&#128172;"; // speech balloon

  var panel = document.createElement("div");
  panel.className = "mtchat-panel";
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "MAGPIE — Montana agency help chat");
  panel.innerHTML =
    '<div class="mtchat-head">' +
    "<div><h2>Ask MAGPIE</h2><p>Public Montana agency websites · unofficial</p></div>" +
    '<button class="mtchat-close" aria-label="Close chat">&times;</button>' +
    "</div>" +
    '<div class="mtchat-log" id="mtchat-log" aria-live="polite"></div>' +
    '<div class="mtchat-disc">' + escapeHtml(DISCLAIMER) + "</div>" +
    '<form class="mtchat-form" id="mtchat-form">' +
    '<input class="mtchat-input" id="mtchat-input" type="text" autocomplete="off" ' +
    'placeholder="Ask a question…" aria-label="Your question" />' +
    '<button class="mtchat-send" id="mtchat-send" type="submit">Send</button>' +
    "</form>";

  if (INLINE) {
    // Docked into the page's advisor surface: always-open panel, no floating launcher.
    panel.classList.add("mtchat-inline", "mtchat-open");
    mountEl.appendChild(panel);
  } else {
    document.body.appendChild(launch);
    document.body.appendChild(panel);
  }

  var logEl = panel.querySelector("#mtchat-log");
  var formEl = panel.querySelector("#mtchat-form");
  var inputEl = panel.querySelector("#mtchat-input");
  var sendEl = panel.querySelector("#mtchat-send");
  var closeEl = panel.querySelector(".mtchat-close");

  // ---- open / close --------------------------------------------------------
  function open() {
    panel.classList.add("mtchat-open");
    greet();
    inputEl.focus();
  }

  // Inline placeholder shown before any advisor is chosen (the mount starts empty).
  function showEmpty(msg) {
    logEl.innerHTML =
      '<div class="mtchat-empty">' + escapeHtml(msg || "Choose an advisor to begin.") + "</div>";
  }

  // Fetch the active persona's metadata once and reflect its name in the header.
  // Split out from greet() so the conversation-first entry can set the advisor's
  // name (and remember its starters) without showing the opening message.
  function fetchPersonaMeta(cb) {
    fetch(API_BASE.replace(/\/$/, "") + "/personas/" + encodeURIComponent(PERSONA))
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; })
      .then(function (meta) {
        personaMeta = meta;
        if (meta && meta.name) {
          var h = panel.querySelector(".mtchat-head h2");
          if (h) h.textContent = meta.name;
        }
        if (cb) cb(meta);
      });
  }

  // First-open greeting. Generic mode shows a fixed line; persona mode fetches the
  // persona's opening + starter chips and updates the header title.
  function greet() {
    if (greeted) return;
    greeted = true;
    if (!PERSONA) {
      addBot("Hi! Ask me a question about Montana state agencies and I'll answer from their public websites.", null);
      return;
    }
    fetchPersonaMeta(function (meta) {
      addBot((meta && meta.opening) || "Hi! How can I help you build your plan?", null);
      if (meta && meta.starters && meta.starters.length) renderChips(meta.starters, "Try one of these");
    });
  }

  // Clicking a suggested prompt (starter or follow-up) doesn't send it — it drops
  // the text into the input so the user can edit it first, then submit themselves.
  function fillInput(q) {
    if (!panel.classList.contains("mtchat-open")) open();
    inputEl.value = q || "";
    inputEl.focus();
    // Put the caret at the end so editing continues naturally.
    var n = inputEl.value.length;
    try { inputEl.setSelectionRange(n, n); } catch (e) {}
  }

  // Append clickable question chips to the most recent bot message.
  function renderChips(items, label) {
    var host = logEl.lastChild;
    if (!host) return;
    var wrap = document.createElement("div");
    wrap.className = "mtchat-fups";
    var lbl = document.createElement("b");
    lbl.textContent = label;
    wrap.appendChild(lbl);
    items.forEach(function (q) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "mtchat-fup";
      b.textContent = q;
      b.addEventListener("click", function () { fillInput(q); });
      wrap.appendChild(b);
    });
    host.appendChild(wrap);
  }

  function prettyKey(k) {
    return String(k).replace(/_/g, " ").replace(/^\w/, function (c) { return c.toUpperCase(); });
  }

  // The guided deliverable, rendered as a labeled list of the fields filled so far.
  function renderArtifact(artifact) {
    if (!artifact) return "";
    var keys = Object.keys(artifact).filter(function (k) {
      var v = artifact[k];
      return v != null && v !== "" && !(Array.isArray(v) && !v.length);
    });
    if (!keys.length) return "";
    var rows = keys.map(function (k) {
      var v = artifact[k];
      if (Array.isArray(v)) v = v.join(", ");
      return "<li><strong>" + escapeHtml(prettyKey(k)) + ":</strong> " + escapeHtml(String(v)) + "</li>";
    }).join("");
    return '<div class="mtchat-artifact"><b>Your plan so far</b><ul>' + rows + "</ul></div>";
  }

  // A handoff suggestion → a one-tap chip that brings in the recommended advisor.
  // Appended as a real node (with a click handler) to the most recent bot message.
  function renderHandoff(handoff) {
    if (!handoff || !handoff.to) return;
    var host = logEl.lastChild;
    if (!host) return;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "mtchat-handoff";
    b.innerHTML =
      '<span class="mtchat-ho-ic" aria-hidden="true">&#129309;</span>' + // handshake
      "<span>" + escapeHtml(handoff.label || ("Bring in the " + (handoff.name || "advisor"))) + "</span>";
    b.addEventListener("click", function () { window.MAGPIE.startPersona(handoff.to); });
    host.appendChild(b);
  }
  function close() {
    if (INLINE) return; // docked panel stays put — there's nothing to collapse into
    panel.classList.remove("mtchat-open");
    launch.focus();
  }
  launch.addEventListener("click", function () {
    panel.classList.contains("mtchat-open") ? close() : open();
  });
  closeEl.addEventListener("click", close);
  document.addEventListener("keydown", function (e) {
    if (!INLINE && e.key === "Escape" && panel.classList.contains("mtchat-open")) close();
  });

  // ---- rendering -----------------------------------------------------------
  // Normalize an error body's `detail` to a short human string. FastAPI sends a
  // plain string for HTTPException, but a list of {msg,...} objects for request
  // validation (422) — concatenating that list naively renders "[object Object]".
  function detailText(body) {
    var d = body && body.detail;
    if (!d) return "";
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d
        .map(function (e) {
          return e && typeof e === "object" ? e.msg || "" : String(e);
        })
        .filter(Boolean)
        .join("; ");
    }
    if (typeof d === "object") return d.msg || "";
    return String(d);
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  // Escaping entities is NOT scheme validation: a "javascript:"/"data:" URL has
  // no HTML-special chars and would survive escapeHtml into a live href. Only
  // http(s) URLs become real links; anything else degrades to "#".
  function safeHref(url) {
    return /^https?:\/\//i.test(url || "") ? escapeHtml(url) : "#";
  }

  // Inline Markdown on already-escaped text: links, code, bold, italic.
  // Only http(s) links are linkified, so a javascript: URI can't slip through.
  function renderInline(t) {
    return t
      .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/__([^_]+)__/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
      .replace(/(^|[^_\w])_([^_\n]+)_/g, "$1<em>$2</em>");
  }

  // Minimal, XSS-safe Markdown → HTML. Escapes first, then handles headings,
  // bullet/numbered lists, and paragraphs (blank line separates them). The
  // model is asked to reply in simple Markdown; this keeps it readable without
  // pulling in a dependency.
  function renderMarkdown(src) {
    var lines = escapeHtml(src).split(/\r?\n/);
    var out = [];
    var list = null; // "ul" | "ol" | null
    var para = [];
    function closeList() { if (list) { out.push("</" + list + ">"); list = null; } }
    function flushPara() {
      if (para.length) { out.push("<p>" + para.join("<br>") + "</p>"); para = []; }
    }
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].replace(/\s+$/, "");
      var h = /^(#{1,6})\s+(.*)$/.exec(line);
      var ul = /^\s*[-*]\s+(.*)$/.exec(line);
      var ol = /^\s*\d+\.\s+(.*)$/.exec(line);
      if (h) {
        flushPara(); closeList();
        out.push('<div class="mtchat-h">' + renderInline(h[2]) + "</div>");
      } else if (ul) {
        flushPara();
        if (list !== "ul") { closeList(); out.push("<ul>"); list = "ul"; }
        out.push("<li>" + renderInline(ul[1]) + "</li>");
      } else if (ol) {
        flushPara();
        if (list !== "ol") { closeList(); out.push("<ol>"); list = "ol"; }
        out.push("<li>" + renderInline(ol[1]) + "</li>");
      } else if (line === "") {
        flushPara(); closeList();
      } else {
        closeList();
        para.push(renderInline(line));
      }
    }
    flushPara(); closeList();
    return out.join("");
  }

  // The top of the most recent exchange — the user's question. We anchor the
  // view here so a long answer can be read from its top rather than its end.
  var threadTop = null;

  // Scroll the log so el's top sits near the top of the visible panel.
  // The browser clamps scrollTop, so a short answer simply scrolls as far up
  // as it can; a long answer reaches the top.
  function anchorTop(el) {
    if (!el) return;
    logEl.scrollTop += el.getBoundingClientRect().top - logEl.getBoundingClientRect().top - 8;
  }

  function addUser(text) {
    var d = document.createElement("div");
    d.className = "mtchat-msg mtchat-user";
    d.textContent = text;
    logEl.appendChild(d);
    threadTop = d;
    anchorTop(d);
  }

  // Render an answer: Markdown → HTML, [n] markers → links to source n, a source
  // list, and clickable follow-up question chips.
  function addBot(answer, sources, followups, artifact) {
    var d = document.createElement("div");
    d.className = "mtchat-msg mtchat-bot";

    var html = renderMarkdown(answer);
    if (sources && sources.length) {
      html = html.replace(/\[(\d+)\]/g, function (m, n) {
        var src = sources[parseInt(n, 10) - 1];
        if (!src) return ""; // out-of-range marker (e.g. [7] with 6 sources) → drop it
        return src.url
          ? '<a href="' + safeHref(src.url) + '" target="_blank" rel="noopener">[' + n + "]</a>"
          : "[" + n + "]"; // valid source, no link
      });
    }
    var block = html;

    if (sources && sources.length) {
      var items = sources
        .map(function (s) {
          var label = escapeHtml(s.title) + (s.agency ? " (" + escapeHtml(s.agency) + ")" : "");
          return s.url
            ? '<li><a href="' + safeHref(s.url) + '" target="_blank" rel="noopener">' + label + "</a></li>"
            : "<li>" + label + "</li>";
        })
        .join("");
      block += '<div class="mtchat-srcs"><b>Sources</b><ol>' + items + "</ol></div>";
    }
    block += renderArtifact(artifact);
    d.innerHTML = block;

    // Follow-up chips: buttons that re-ask on click. Appended as real nodes
    // (after innerHTML) so their click handlers survive.
    if (followups && followups.length) {
      var wrap = document.createElement("div");
      wrap.className = "mtchat-fups";
      var lbl = document.createElement("b");
      lbl.textContent = "You could say";
      wrap.appendChild(lbl);
      followups.forEach(function (q) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "mtchat-fup";
        b.textContent = q;
        b.addEventListener("click", function () { fillInput(q); });
        wrap.appendChild(b);
      });
      d.appendChild(wrap);
    }

    logEl.appendChild(d);
    // Anchor to the top of this exchange (the question) so the reader starts
    // at the beginning of the answer. Falls back to this message — e.g. the
    // opening greeting, which has no preceding question.
    anchorTop(threadTop || d);
  }

  function addLoading() {
    var d = document.createElement("div");
    d.className = "mtchat-msg mtchat-bot";
    d.innerHTML = '<span class="mtchat-dots" aria-label="Thinking"></span>';
    logEl.appendChild(d);
    return d;
  }

  // ---- ask -----------------------------------------------------------------
  // Send a question to the API and render the reply. Reused by the input form
  // and the follow-up chips.
  function ask(question) {
    var q = (question || "").trim();
    if (!q) return;
    if (!panel.classList.contains("mtchat-open")) open();
    addUser(q);
    inputEl.value = "";
    sendEl.disabled = true;
    var loading = addLoading();

    var payload = { question: q };
    if (PERSONA) {
      payload.persona = PERSONA;
      payload.history = history.slice(-12); // bound context sent each turn
      payload.state = convState;
    }

    fetch(API_BASE.replace(/\/$/, "") + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (res) {
        return res.json().then(function (body) {
          return { ok: res.ok, status: res.status, body: body };
        });
      })
      .then(function (r) {
        loading.remove();
        if (r.ok) {
          var artifact = r.body.state && r.body.state.artifact;
          addBot(r.body.answer, r.body.sources || [], r.body.followups || [], artifact);
          if (PERSONA) {
            convState = r.body.state || convState;
            history.push({ role: "user", content: q });
            history.push({ role: "assistant", content: r.body.answer });
            renderHandoff(r.body.handoff);
          }
          // Record the turn so the session can be saved + replayed, and let the host page
          // (the plan workspace) react to the new accumulated state.
          transcript.push({
            q: q,
            answer: r.body.answer,
            sources: r.body.sources || [],
            followups: r.body.followups || [],
            artifact: artifact || null,
            handoff: r.body.handoff || null,
          });
          saveSession();
          emitState();
        } else if (r.status === 503) {
          addBot("The answer service isn't set up yet (the site administrator needs to add an API key).", null);
        } else {
          var detail = detailText(r.body);
          addBot("Sorry, I couldn't get an answer" + (detail ? " (" + detail + ")" : "") + ".", null);
        }
      })
      .catch(function () {
        loading.remove();
        addBot("I couldn't reach the answer service. Please make sure it's running and try again.", null);
      })
      .then(function () {
        sendEl.disabled = false;
        inputEl.focus();
      });
  }

  formEl.addEventListener("submit", function (e) {
    e.preventDefault();
    ask(inputEl.value);
  });

  // ---- public hook --------------------------------------------------------
  // Lets a host page (e.g. the demo's "Samples" tab) launch a guided persona in
  // this same widget at runtime, or return to the generic assistant. Resets the
  // transcript + conversation state so each launch starts clean.
  function resetConversation() {
    logEl.innerHTML = "";
    convState = null;
    history = [];
    personaMeta = null;
    greeted = false;
    transcript = [];
    clearSession();
    var h = panel.querySelector(".mtchat-head h2");
    if (h && !PERSONA) h.textContent = "Ask MAGPIE";
  }

  // ---- session persistence + the plan-state hook --------------------------
  // Announce the accumulated conversation state so a host page (the plan workspace)
  // can render/refresh the living plan document. The page owns all plan UI.
  function emitState() {
    document.dispatchEvent(
      new CustomEvent("magpie:state", { detail: { persona: PERSONA, state: convState } })
    );
  }

  function saveSession() {
    if (!INLINE || !transcript.length) return; // only the docked workspace persists
    try {
      sessionStorage.setItem(
        STORE_KEY,
        JSON.stringify({ persona: PERSONA, state: convState, transcript: transcript })
      );
    } catch (e) { /* storage full/blocked — non-fatal */ }
  }

  function clearSession() {
    try { sessionStorage.removeItem(STORE_KEY); } catch (e) {}
  }

  // Rehydrate a saved conversation on boot: replay the transcript into bubbles, restore
  // state + history, and tell the page to go live with the plan populated. Returns true
  // if a session was restored.
  function restoreSession() {
    var raw;
    try { raw = sessionStorage.getItem(STORE_KEY); } catch (e) { return false; }
    if (!raw) return false;
    var data;
    try { data = JSON.parse(raw); } catch (e) { return false; }
    if (!data || !data.transcript || !data.transcript.length) return false;

    PERSONA = data.persona || null;
    convState = data.state || null;
    transcript = data.transcript;
    history = [];
    greeted = true;
    panel.classList.add("mtchat-open");
    if (PERSONA) fetchPersonaMeta(null); // restore the advisor's name in the header (async)

    logEl.innerHTML = "";
    transcript.forEach(function (t) {
      addUser(t.q);
      addBot(t.answer, t.sources || [], t.followups || [], t.artifact);
      history.push({ role: "user", content: t.q });
      history.push({ role: "assistant", content: t.answer });
      if (PERSONA && t.handoff) renderHandoff(t.handoff);
    });

    // Defer the announcement: a host page whose listener script runs AFTER this widget
    // script must be wired up before we fire, or it misses the restore on first paint.
    // The transcript bubbles above are restored synchronously, so the chat shows at once.
    setTimeout(function () {
      document.dispatchEvent(new CustomEvent("magpie:persona", { detail: { id: PERSONA } }));
      emitState();
    }, 0);
    return true;
  }
  window.MAGPIE = {
    // Launch a guided persona. With an optional initialQuestion, the widget skips the
    // persona's opening message and goes straight to answering that question — the
    // entry point for a conversation-first host page where the user types up front.
    startPersona: function (id, initialQuestion) {
      PERSONA = id || null;
      resetConversation();
      var q = (initialQuestion || "").trim();
      if (q && PERSONA) {
        greeted = true; // suppress the opening; the answer to q stands first
        panel.classList.add("mtchat-open");
        fetchPersonaMeta(null); // still surface the advisor's name in the header
        document.dispatchEvent(new CustomEvent("magpie:persona", { detail: { id: PERSONA } }));
        ask(q);
        return;
      }
      open();
      // Let the host page sync UI (e.g. highlight the active advisor card), including
      // when the switch came from a handoff chip rather than a card click.
      document.dispatchEvent(new CustomEvent("magpie:persona", { detail: { id: PERSONA } }));
    },
    ask: function (q) { ask(q); },
    resume: function () { return restoreSession(); },
    reset: function () {
      PERSONA = null;
      resetConversation();
      open();
    },
  };

  // Inline mode boots visible. First try to resume a saved session (survives reload);
  // otherwise, if a persona is preset (data-persona), greet it now; else wait for the
  // page to call MAGPIE.startPersona(id) from an advisor card.
  if (INLINE) {
    if (!restoreSession()) {
      if (PERSONA) open();
      else showEmpty();
    }
  }
})();
