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
    ".mtchat-bot{align-self:flex-start;background:#fff;border:1px solid #e2e5ea;border-bottom-left-radius:3px}" +
    ".mtchat-bot a{color:#1d4e89}" +
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
  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function addUser(text) {
    var d = document.createElement("div");
    d.className = "mtchat-msg mtchat-user";
    d.textContent = text;
    logEl.appendChild(d);
    logEl.scrollTop = logEl.scrollHeight;
  }

  // Render an answer, turning [n] markers into links to source n, plus a source list.
  function addBot(answer, sources) {
    var d = document.createElement("div");
    d.className = "mtchat-msg mtchat-bot";

    var html = escapeHtml(answer);
    if (sources && sources.length) {
      html = html.replace(/\[(\d+)\]/g, function (m, n) {
        var src = sources[parseInt(n, 10) - 1];
        if (src && src.url) {
          return '<a href="' + escapeHtml(src.url) + '" target="_blank" rel="noopener">[' + n + "]</a>";
        }
        return m;
      });
    }
    var block = "<div>" + html + "</div>";

    if (sources && sources.length) {
      var items = sources
        .map(function (s) {
          var label = escapeHtml(s.title) + (s.agency ? " (" + escapeHtml(s.agency) + ")" : "");
          return s.url
            ? '<li><a href="' + escapeHtml(s.url) + '" target="_blank" rel="noopener">' + label + "</a></li>"
            : "<li>" + label + "</li>";
        })
        .join("");
      block += '<div class="mtchat-srcs"><b>Sources</b><ol>' + items + "</ol></div>";
    }
    d.innerHTML = block;
    logEl.appendChild(d);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function addLoading() {
    var d = document.createElement("div");
    d.className = "mtchat-msg mtchat-bot";
    d.innerHTML = '<span class="mtchat-dots" aria-label="Thinking"></span>';
    logEl.appendChild(d);
    logEl.scrollTop = logEl.scrollHeight;
    return d;
  }

  // ---- ask -----------------------------------------------------------------
  formEl.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = inputEl.value.trim();
    if (!q) return;
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
          addBot(r.body.answer, r.body.sources || []);
        } else if (r.status === 503) {
          addBot("The answer service isn't set up yet (the site administrator needs to add an API key).", null);
        } else {
          var detail = r.body && r.body.detail ? " (" + r.body.detail + ")" : "";
          addBot("Sorry, I couldn't get an answer" + detail + ".", null);
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
  });
})();
