/*
 * Montana Agency Answer widget — a self-contained, drop-in chatbot.
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

  var DISCLAIMER =
    "AI-generated from public Montana agency pages. Verify important details on the source site.";

  // ---- styles (prefixed to avoid clashing with the host page) -------------
  var css =
    "" +
    ".mtchat-launch{position:fixed;right:20px;bottom:20px;width:56px;height:56px;border-radius:50%;" +
    "background:#1d4e89;color:#fff;border:none;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.3);" +
    "font-size:24px;line-height:56px;z-index:2147483000}" +
    ".mtchat-launch:focus-visible{outline:3px solid #ffc629;outline-offset:2px}" +
    ".mtchat-panel{position:fixed;right:20px;bottom:88px;width:360px;max-width:calc(100vw - 32px);" +
    "height:520px;max-height:calc(100vh - 120px);background:#fff;border-radius:12px;display:none;" +
    "flex-direction:column;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,.35);z-index:2147483000;" +
    "font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1a1a1a}" +
    ".mtchat-panel.mtchat-open{display:flex}" +
    ".mtchat-head{background:#1d4e89;color:#fff;padding:12px 14px;display:flex;align-items:center;justify-content:space-between}" +
    ".mtchat-head h2{margin:0;font-size:15px;font-weight:600}" +
    ".mtchat-head p{margin:2px 0 0;font-size:11px;opacity:.85}" +
    ".mtchat-close{background:none;border:none;color:#fff;font-size:20px;cursor:pointer;line-height:1;padding:4px;border-radius:6px}" +
    ".mtchat-close:focus-visible{outline:2px solid #ffc629}" +
    ".mtchat-log{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:12px;background:#f5f6f8}" +
    ".mtchat-msg{max-width:88%;padding:9px 12px;border-radius:12px;font-size:14px;line-height:1.45;white-space:pre-wrap}" +
    ".mtchat-user{align-self:flex-end;background:#1d4e89;color:#fff;border-bottom-right-radius:3px}" +
    ".mtchat-bot{align-self:flex-start;background:#fff;border:1px solid #e2e5ea;border-bottom-left-radius:3px;white-space:normal}" +
    ".mtchat-bot a{color:#1d4e89}" +
    ".mtchat-bot p{margin:0 0 8px}.mtchat-bot p:last-child{margin-bottom:0}" +
    ".mtchat-bot ul,.mtchat-bot ol{margin:6px 0;padding-left:20px}.mtchat-bot li{margin:2px 0}" +
    ".mtchat-bot code{background:#eef1f4;border-radius:4px;padding:1px 4px;font-size:12px;" +
    "font-family:ui-monospace,Menlo,Consolas,monospace}" +
    ".mtchat-bot .mtchat-h{font-weight:600;margin:8px 0 4px}.mtchat-bot .mtchat-h:first-child{margin-top:0}" +
    ".mtchat-fups{margin-top:10px;display:flex;flex-direction:column;gap:6px}" +
    ".mtchat-fups b{font-size:12px;color:#555;font-weight:600}" +
    ".mtchat-fup{text-align:left;background:#eef2f8;border:1px solid #d5deec;color:#1d4e89;" +
    "border-radius:8px;padding:7px 10px;font-size:13px;cursor:pointer;line-height:1.35}" +
    ".mtchat-fup:hover{background:#e2e9f5}" +
    ".mtchat-fup:focus-visible{outline:2px solid #1d4e89;outline-offset:1px}" +
    ".mtchat-srcs{margin-top:8px;font-size:12px;border-top:1px solid #e2e5ea;padding-top:6px}" +
    ".mtchat-srcs b{display:block;margin-bottom:4px;color:#555;font-weight:600}" +
    ".mtchat-srcs ol{margin:0;padding-left:18px}" +
    ".mtchat-srcs li{margin-bottom:3px}" +
    ".mtchat-disc{font-size:11px;color:#777;padding:6px 14px;background:#f5f6f8;border-top:1px solid #e2e5ea}" +
    ".mtchat-form{display:flex;gap:6px;padding:10px;border-top:1px solid #e2e5ea;background:#fff}" +
    ".mtchat-input{flex:1;border:1px solid #c7ccd4;border-radius:8px;padding:9px 10px;font-size:14px;min-height:24px}" +
    ".mtchat-input:focus-visible{outline:2px solid #1d4e89;border-color:#1d4e89}" +
    ".mtchat-send{background:#1d4e89;color:#fff;border:none;border-radius:8px;padding:0 14px;cursor:pointer;font-size:14px;min-width:48px}" +
    ".mtchat-send:disabled{opacity:.5;cursor:default}" +
    ".mtchat-dots{display:inline-block}" +
    ".mtchat-dots:after{content:'…';animation:mtchat-blink 1.2s infinite}" +
    "@keyframes mtchat-blink{0%,100%{opacity:.3}50%{opacity:1}}";

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  // ---- markup --------------------------------------------------------------
  var launch = document.createElement("button");
  launch.className = "mtchat-launch";
  launch.setAttribute("aria-label", "Open the Montana help chat");
  launch.innerHTML = "&#128172;"; // speech balloon

  var panel = document.createElement("div");
  panel.className = "mtchat-panel";
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "Montana agency help chat");
  panel.innerHTML =
    '<div class="mtchat-head">' +
    "<div><h2>Ask Montana</h2><p>Answers from state agency websites</p></div>" +
    '<button class="mtchat-close" aria-label="Close chat">&times;</button>' +
    "</div>" +
    '<div class="mtchat-log" id="mtchat-log" aria-live="polite"></div>' +
    '<div class="mtchat-disc">' + escapeHtml(DISCLAIMER) + "</div>" +
    '<form class="mtchat-form" id="mtchat-form">' +
    '<input class="mtchat-input" id="mtchat-input" type="text" autocomplete="off" ' +
    'placeholder="Ask a question…" aria-label="Your question" />' +
    '<button class="mtchat-send" id="mtchat-send" type="submit">Send</button>' +
    "</form>";

  document.body.appendChild(launch);
  document.body.appendChild(panel);

  var logEl = panel.querySelector("#mtchat-log");
  var formEl = panel.querySelector("#mtchat-form");
  var inputEl = panel.querySelector("#mtchat-input");
  var sendEl = panel.querySelector("#mtchat-send");
  var closeEl = panel.querySelector(".mtchat-close");

  // ---- open / close --------------------------------------------------------
  function open() {
    panel.classList.add("mtchat-open");
    if (!logEl.childElementCount) {
      addBot("Hi! Ask me a question about Montana state agencies and I'll answer from their public websites.", null);
    }
    inputEl.focus();
  }
  function close() {
    panel.classList.remove("mtchat-open");
    launch.focus();
  }
  launch.addEventListener("click", function () {
    panel.classList.contains("mtchat-open") ? close() : open();
  });
  closeEl.addEventListener("click", close);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && panel.classList.contains("mtchat-open")) close();
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
  function addBot(answer, sources, followups) {
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
    d.innerHTML = block;

    // Follow-up chips: buttons that re-ask on click. Appended as real nodes
    // (after innerHTML) so their click handlers survive.
    if (followups && followups.length) {
      var wrap = document.createElement("div");
      wrap.className = "mtchat-fups";
      var lbl = document.createElement("b");
      lbl.textContent = "You might also ask";
      wrap.appendChild(lbl);
      followups.forEach(function (q) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "mtchat-fup";
        b.textContent = q;
        b.addEventListener("click", function () { ask(q); });
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

    fetch(API_BASE.replace(/\/$/, "") + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    })
      .then(function (res) {
        return res.json().then(function (body) {
          return { ok: res.ok, status: res.status, body: body };
        });
      })
      .then(function (r) {
        loading.remove();
        if (r.ok) {
          addBot(r.body.answer, r.body.sources || [], r.body.followups || []);
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
})();
