/* ============================================================================
 * proofing-room.js — drop-in review layer for ANY html page.
 *
 * Add  <script src="proofing-room.js"></script>  once. Dormant until ?proof.
 *     page.html?proof         → review mode (desktop: floating toolbar, hover+click to comment)
 *     page.html?proof=mobile  → force the mobile "Hairline" UI (desktop preview)
 *     on a real phone         → mobile UI auto-detects (≤640px / coarse pointer)
 *
 * Reviewers annotate, then Extract JSON (download) or Send (Discord
 * webhook). No backend. Everything persists in localStorage per page path.
 *
 * v7.0 (2026-07-14) — desktop UI unification, replacing the old v6.4 two-rail
 *   design. Replaced the right controls rail + left docs rail + top wordmark
 *   with the SAME floating bottom toolbar mobile uses (pill / docked composer /
 *   notes drawer), scaled up ~1.3x for a 1280-1440 viewport. Desktop keeps its
 *   own interaction model on top of that shared chrome: hover-highlight + click
 *   to comment (armed via two new pill buttons, "+"/pencil, instead of
 *   long-press) and all existing keyboard shortcuts (C/E/J/K/[/]/⌘⏎/?/Esc).
 *   Reviewer name / theme (incl. OLED) / Extract JSON / Clear all — previously
 *   in the right rail — now live in the same notes drawer mobile already had
 *   (tap/click the pill's count). Docs navigation (previously the left rail)
 *   is now a ☰ button (fixed top-left, BOTH platforms) opening a slide-in
 *   drawer — same window.PROOFING_DOCS contract, same isSafeDocUrl() scheme
 *   guard, absent/empty list → no button at all (this is mobile's first docs
 *   nav). buildMobile() renamed buildToolbar() since both platforms call it;
 *   render() no longer branches on IS_MOBILE for pins/pill — only the
 *   comment/edit ENTRY interaction (arm-then-click vs long-press) still does.
 * v6.2 (2026-07-13) — tabs: pages opt in by tagging top-level containers with
 *   data-proof-tab="Label"; one horizontal bar, tap or swipe to switch, active tab
 *   persisted (proofing-room:tab:<path>). No [data-proof-tab] on the page → no tab
 *   bar, single-view behaviour unchanged. Notes drawer lists notes across all tabs
 *   and jumps cross-tab. Additive only — no change to selectorFor/locate, the
 *   webhook shape, or the data-proof-ask contract.
 * v6.1 (2026-07-13) — manual dark-mode toggle (auto/light/dark via data-pr-theme on
 *   <html>, persisted), notes drawer (tap the count → list of all notes, tap to jump),
 *   and edit/delete a comment from its card (pencil / trash).
 * v6 (2026-07-13) — "Hairline" mobile redesign + inline-response primitives:
 *   • long-press any element to annotate (no comment mode); one 44px floating
 *     pill (count · ‹n/N› stepper · send); anchored cards; 2px top hairline.
 *   • dark mode via prefers-color-scheme (live).
 *   • NEW annotation kinds beyond comment/edit: answer (yes/no + scale slider),
 *     reaction (up/down), approval (per section), done (checkbox), reminder
 *     (due date). Declared by the page via data-proof-ask / data-ask-type /
 *     data-proof-section; the layer renders native controls in place.
 *   • iOS: 16px inputs (no focus zoom), touch-action manipulation, long-press
 *     magnifier suppression, visualViewport keyboard tracking.
 *   Extract JSON v6: version "6", adds answers[]/reactions[]/approvals[]/done[]/
 *   reminders[] and KEEPS comments[]/edits[] exactly as v5 (backward compatible).
 *   Webhook contract unchanged (payload_json + files[0]). Desktop = v5.
 * v5 (2026-07-13): mobile bottom-sheet + webhook send (superseded by v6 mobile).
 * v4 (2026-06-15): slide-deck support (MutationObserver reposition, per-slide map).
 * ========================================================================== */
(function () {
  "use strict";
  if (window.__proofingRoom) return;

  /* ---- gate --------------------------------------------------------------- */
  try {
    var sp = new URLSearchParams(location.search);
    if (!sp.has("proof") && location.hash !== "#proof") return;
  } catch (e) {
    if (location.search.indexOf("proof") < 0 && location.hash !== "#proof") return;
  }

  /* ---- config ------------------------------------------------------------- */
  var WEBHOOK =
    (typeof window.PROOFING_WEBHOOK === "string" && window.PROOFING_WEBHOOK) ||
    (document.body && document.body.getAttribute("data-proofing-webhook")) ||
    null;
  var FORCE_MOBILE = /(?:^|[?&#])(?:proof=mobile|mobile)/.test(location.search + location.hash);
  var IS_MOBILE = FORCE_MOBILE || (function () {
    try { return matchMedia("(max-width:640px)").matches || matchMedia("(pointer:coarse)").matches; }
    catch (e) { return (window.innerWidth || 999) <= 640; }
  })();
  var CHIPS = (function () {
    if (Array.isArray(window.PROOFING_CHIPS)) return window.PROOFING_CHIPS;
    var a = document.body && document.body.getAttribute("data-proofing-chips");
    if (a) { try { return JSON.parse(a); } catch (e) {} }
    return ["Shorter", "Cut this", "Wrong", "More detail"];
  })();

  /* manual dark-mode override: '' = follow system, else 'light' | 'dark' | 'oled' */
  var THEME_KEY = "proofing-room:theme";
  function getTheme() { return localStorage.getItem(THEME_KEY) || ""; }
  function applyTheme(t) {
    if (t === "light" || t === "dark" || t === "oled") document.documentElement.setAttribute("data-pr-theme", t);
    else document.documentElement.removeAttribute("data-pr-theme");
  }
  function setTheme(t) { if (t) localStorage.setItem(THEME_KEY, t); else localStorage.removeItem(THEME_KEY); applyTheme(t); }
  applyTheme(getTheme());
  // send-button label — generic "Send" by default; a host page can brand it
  // (e.g. "Send to Team") via window.PROOFING_SEND_LABEL or data-proofing-send-label.
  var SEND_LABEL =
    (typeof window.PROOFING_SEND_LABEL === "string" && window.PROOFING_SEND_LABEL) ||
    (document.body && document.body.getAttribute("data-proofing-send-label")) ||
    "Send";

  /* ---- doc identity ------------------------------------------------------- */
  /* A host page can namespace its stored notes by declaring a doc-id, so a
     page served from a stable/reused URL (e.g. a recurring report published
     at the same address) gets a fresh sheet each edition instead of
     resurfacing yesterday's annotations. Declared via window.PROOFING_DOC_ID
     or <body data-proofing-doc>. Absent → pathname-only key (static-page
     behaviour, unchanged). */
  var DOC_ID =
    (typeof window.PROOFING_DOC_ID === "string" && window.PROOFING_DOC_ID) ||
    (document.body && document.body.getAttribute("data-proofing-doc")) ||
    "";

  /* ---- state (v5 comments/edits kept; v6 primitives in annos[]) ----------- */
  var KEY = "proofing-room:" + location.pathname + (DOC_ID ? "@" + DOC_ID : "");
  /* When a doc-id is declared, sweep prior editions' notes for this same path
     (yesterday's edition at the same URL) so stale annotations don't linger on
     the device. Only runs when DOC_ID is set → static-page usage is untouched. */
  if (DOC_ID) {
    try {
      var _pfx = "proofing-room:" + location.pathname + "@";
      for (var _i = localStorage.length - 1; _i >= 0; _i--) {
        var _k = localStorage.key(_i);
        if (_k && _k.indexOf(_pfx) === 0 && _k !== KEY) localStorage.removeItem(_k);
      }
    } catch (e) {}
  }
  var state = {
    reviewer: localStorage.getItem("proofing-room:reviewer") || "",
    comments: [], edits: [], annos: [], seq: 0, sent: false,
    commenting: false, editing: false,
  };
  try {
    var saved = JSON.parse(localStorage.getItem(KEY) || "{}");
    if (Array.isArray(saved.comments)) state.comments = saved.comments;
    if (Array.isArray(saved.edits)) state.edits = saved.edits;
    if (Array.isArray(saved.annos)) state.annos = saved.annos; // v6; absent in v5 blobs → []
    if (typeof saved.seq === "number") state.seq = saved.seq;
  } catch (e) {}
  function persist() {
    localStorage.setItem(KEY, JSON.stringify({
      comments: state.comments, edits: state.edits, annos: state.annos, seq: state.seq,
    }));
  }
  function nid(p) { state.seq++; return (p || "a") + state.seq; }

  /* ---- element helpers (v4/v5, unchanged) --------------------------------- */
  function isUi(el) {
    return !!(el.closest && el.closest(
      "#pr-pins,#pr-pop,#pr-hairline,#pr-pill,#pr-burger," +
      "#pr-menu,#pr-sheet,#pr-card,#pr-composer,#pr-scrim,#pr-lift,#pr-tabs,#pr-shortcuts,#pr-docs"));
  }
  function isVisible(el) {
    if (!el || !el.isConnected) return false;
    if (!el.getClientRects().length) return false;
    if (typeof el.checkVisibility === "function") {
      return el.checkVisibility({
        contentVisibilityAuto: true, opacityProperty: true, visibilityProperty: true,
        checkOpacity: true, checkVisibilityCSS: true,
      });
    }
    var cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden" || cs.opacity === "0") return false;
    var r = el.getBoundingClientRect();
    return r.width > 0 || r.height > 0;
  }
  function selectorFor(el) {
    if (!el || el === document.body) return "body";
    var parts = [];
    while (el && el.nodeType === 1 && el !== document.body && parts.length < 8) {
      var tag = el.tagName.toLowerCase();
      if (el.id) { parts.unshift(tag + "#" + CSS.escape(el.id)); break; }
      var i = 1, sib = el;
      while ((sib = sib.previousElementSibling)) if (sib.tagName === el.tagName) i++;
      parts.unshift(tag + ":nth-of-type(" + i + ")");
      el = el.parentElement;
    }
    return parts.join(" > ");
  }
  function snippet(el, max) {
    var t = (el.innerText || el.textContent || "").replace(/\s+/g, " ").trim();
    max = max || 140;
    return t.length > max ? t.slice(0, max - 1) + "…" : t;
  }
  function nearestSection(el) {
    var cur = el;
    while (cur && cur !== document.body) {
      var sib = cur;
      while (sib) { if (/^H[1-6]$/.test(sib.tagName || "")) return snippet(sib, 80); sib = sib.previousElementSibling; }
      cur = cur.parentElement;
    }
    var h = document.querySelector("h1");
    return h ? snippet(h, 80) : document.title;
  }
  function locate(c) {
    try { var el = document.querySelector(c.selector); if (el) return el; } catch (e) {}
    var nodes = document.getElementsByTagName(c.tag || "*");
    for (var i = 0; i < nodes.length; i++) if (snippet(nodes[i], 140) === c.anchorText) return nodes[i];
    return null;
  }
  function esc(s) {
    // v6.4 — also escapes quotes: the docs-drawer links interpolate esc() output
    // straight into href="…"/title="…" attributes, not just text nodes, so an
    // unescaped quote in a doc title/url could break out of the attribute.
    return (s || "").replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function anchorMeta(el) {
    return { selector: selectorFor(el), anchorText: snippet(el, 140), section: nearestSection(el), tag: el.tagName.toLowerCase() };
  }

  /* ---- styles ------------------------------------------------------------- */
  /* v7.0 — desktop no longer has its own chrome shell (rail/badge); it shares
   * cssMobile's toolbar/composer/drawer wholesale (see below) and only keeps
   * what's genuinely desktop-only: the click-to-comment popover, the
   * hover/edit-in-place affordances, and the keyboard-shortcuts overlay. All
   * still retokenised onto the same --pr-* Prism tokens as mobile. */
  var cssDesktop =
    "#pr-pop,#pr-shortcuts{font-family:'Hanken Grotesk',ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif}" +
    "body.pr-commenting *{cursor:crosshair!important}.pr-hl{outline:2px dashed var(--pr-accent)!important}" +
    "#pr-pop{position:absolute;z-index:2147483600;width:248px;background:var(--pr-card);color:var(--pr-ink);border-radius:11px;box-shadow:0 14px 40px rgba(8,24,38,.3);border:1px solid var(--pr-bd);padding:13px}" +
    "#pr-pop .pr-pop-head{font-size:10.5px;color:var(--pr-ink2);margin-bottom:8px;line-height:1.4}" +
    "#pr-pop textarea{width:100%;height:74px;border:1px solid var(--pr-bd);background:var(--pr-card);color:var(--pr-ink);border-radius:8px;padding:8px;font:inherit;font-size:13px}" +
    "#pr-pop .row{display:flex;gap:8px;margin-top:9px}#pr-pop button{flex:1;border:none;border-radius:8px;padding:8px;font-size:12.5px;font-weight:700;cursor:pointer}" +
    "#pr-pop .save{background:var(--pr-accent);color:#fff}#pr-pop .cancel{background:var(--pr-tint);color:var(--pr-ink2)}" +
    '[contenteditable="true"].pr-editing-el{outline:2px solid var(--pr-accent)!important;outline-offset:2px}.pr-edited{outline:1.5px dashed var(--pr-ink2)!important}' +
    /* v6.3 — reaction/reminder affordances added to the same comment popover */
    "#pr-pop .pr-pop-actions{display:flex;gap:6px;margin-bottom:8px}" +
    "#pr-pop .pr-pop-actions button{flex:1;border:1px solid var(--pr-bd);background:var(--pr-tint);color:var(--pr-ink);border-radius:8px;padding:7px 4px;font-size:12px;cursor:pointer}" +
    "#pr-pop .pr-pop-actions button.rmd{flex:1.6}" +
    "#pr-pop .pr-pop-actions button.rx.on{background:var(--pr-accent);color:#fff;border-color:var(--pr-accent)}" +
    "#pr-pop .pr-pop-remind{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}" +
    "#pr-pop .pr-pop-remind[hidden]{display:none}" +
    "#pr-pop .pr-pop-remind button{border:1px solid var(--pr-bd);background:var(--pr-card);color:var(--pr-ink);border-radius:99px;padding:6px 10px;font-size:11.5px;cursor:pointer}" +
    /* v6.3 — keyboard-shortcut hint, now rendered inside the shared notes
     * drawer (desktop only — see openDrawer) instead of a permanent rail. */
    ".pr-kbd-hint{font-size:10px;line-height:1.6;color:var(--pr-ink2)}" +
    ".pr-kbd-hint kbd{font:inherit;font-size:9.5px;font-weight:700;color:var(--pr-ink);background:var(--pr-tint);border:1px solid var(--pr-bd);border-radius:4px;padding:1px 4px}" +
    /* v6.3 — shortcuts cheat-sheet overlay (desktop only) */
    "#pr-shortcuts{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:2147483647;width:320px;max-width:90vw;background:var(--pr-card);border:1px solid var(--pr-bd);border-radius:14px;box-shadow:0 22px 60px rgba(8,24,38,.32);color:var(--pr-ink);font-size:13px;overflow:hidden}" +
    "#pr-shortcuts .hd{display:flex;align-items:center;padding:12px 14px;font-weight:800;font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;border-bottom:1px solid var(--pr-line);background:var(--pr-tint)}" +
    "#pr-shortcuts .hd .x{margin-left:auto;background:none;border:none;color:var(--pr-ink2);font-size:18px;cursor:pointer;line-height:1;padding:0}" +
    "#pr-shortcuts .body{padding:6px 0;max-height:60vh;overflow-y:auto}" +
    "#pr-shortcuts .pr-kb-row{display:flex;align-items:center;gap:10px;padding:8px 14px;border-bottom:.5px solid var(--pr-line)}" +
    "#pr-shortcuts .pr-kb-row:last-child{border-bottom:none}" +
    "#pr-shortcuts .pr-kb-key{flex:none;min-width:88px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:var(--pr-ink);background:var(--pr-tint);border:1px solid var(--pr-bd);border-radius:6px;padding:3px 7px;text-align:center}" +
    "#pr-shortcuts .pr-kb-desc{color:var(--pr-ink2)}";

  /* v6 mobile "Hairline" — monochrome, tokenised, light+dark */
  var cssMobile =
    ":root{--pr-ink:#141A21;--pr-ink2:#6B7785;--pr-surface:rgba(255,255,255,.72);--pr-card:#fff;--pr-line:rgba(20,26,33,.10);--pr-bd:rgba(20,26,33,.18);--pr-tint:rgba(20,26,33,.05);--pr-scrim:rgba(8,24,38,.3);--pr-accent:#306FA8;--pr-signal:#B0552E}" +
    "@media (prefers-color-scheme:dark){:root{--pr-ink:#E8EEF2;--pr-ink2:#8B97A4;--pr-surface:rgba(8,24,38,.42);--pr-card:#12293C;--pr-line:rgba(232,238,242,.12);--pr-bd:rgba(232,238,242,.22);--pr-tint:rgba(232,238,242,.08);--pr-scrim:rgba(8,24,38,.55);--pr-accent:#4F9EDB;--pr-signal:#C8794F}}" +
    /* explicit theme override (manual toggle) — beats the media query by specificity */
    ":root[data-pr-theme=light]{--pr-ink:#141A21;--pr-ink2:#6B7785;--pr-surface:rgba(255,255,255,.72);--pr-card:#fff;--pr-line:rgba(20,26,33,.10);--pr-bd:rgba(20,26,33,.18);--pr-tint:rgba(20,26,33,.05);--pr-scrim:rgba(8,24,38,.3);--pr-accent:#306FA8;--pr-signal:#B0552E}" +
    ":root[data-pr-theme=dark]{--pr-ink:#E8EEF2;--pr-ink2:#8B97A4;--pr-surface:rgba(8,24,38,.42);--pr-card:#12293C;--pr-line:rgba(232,238,242,.12);--pr-bd:rgba(232,238,242,.22);--pr-tint:rgba(232,238,242,.08);--pr-scrim:rgba(8,24,38,.55);--pr-accent:#4F9EDB;--pr-signal:#C8794F}" +
    /* v6.8 — OLED: true-black surface, slightly-grey (not pure white) ink; manual-only, no prefers-color-scheme match */
    ":root[data-pr-theme=oled]{--pr-ink:#C9CED4;--pr-ink2:#6B7079;--pr-surface:rgba(0,0,0,.55);--pr-card:#0C0D10;--pr-line:rgba(255,255,255,.09);--pr-bd:rgba(255,255,255,.18);--pr-tint:rgba(255,255,255,.06);--pr-scrim:rgba(0,0,0,.7);--pr-accent:#4F9EDB;--pr-signal:#C8794F}" +
    ".pr-seg4{display:flex;gap:4px;margin:2px 0 4px}.pr-seg4 button{flex:1;border:1px solid var(--pr-bd);background:var(--pr-card);color:var(--pr-ink);border-radius:9px;padding:9px 2px;font:inherit;font-size:12.5px;font-weight:600;white-space:nowrap;cursor:pointer;min-height:40px}.pr-seg4 button.on{background:var(--pr-accent);color:#fff}" +
    "#pr-menu .drawer-list{max-height:44vh;overflow-y:auto;border-top:.5px solid var(--pr-line)}" +
    "#pr-menu .dr{display:flex;align-items:flex-start;gap:9px;width:auto;padding:12px 16px;border-bottom:.5px solid var(--pr-line);font-size:14px;font-weight:500;text-align:left}" +
    "#pr-menu .dr .k{font-size:11px;color:var(--pr-ink2);flex:none;min-width:60px;padding-top:2px}#pr-menu .dr .t{flex:1;line-height:1.35}" +
    "#pr-card .ed,#pr-card .rm{background:none;border:none;color:var(--pr-ink2);cursor:pointer;font-size:15px;padding:0 2px}#pr-card .ed:hover,#pr-card .rm:hover{color:var(--pr-ink)}" +
    "html.pr-on{touch-action:manipulation}" +
    "body.pr-m{font-family:'Hanken Grotesk',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,system-ui,sans-serif}" +
    "body.pr-m *{-webkit-touch-callout:none;-webkit-user-select:none;user-select:none}" +
    "body.pr-m #pr-composer input,body.pr-m [contenteditable='true']{-webkit-user-select:text;user-select:text}" +
    "#pr-hairline{position:fixed;top:0;left:0;right:0;height:2px;background:var(--pr-ink);z-index:2147483646;pointer-events:none}" +
    "#pr-mfont{font-family:'Hanken Grotesk',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,system-ui,sans-serif}" +
    "#pr-pill{position:fixed;left:50%;transform:translateX(-50%);bottom:max(22px,calc(env(safe-area-inset-bottom) + 8px));z-index:2147483600;display:flex;align-items:center;height:44px;padding:0 6px;gap:2px;background:var(--pr-surface);-webkit-backdrop-filter:blur(14px) saturate(160%);backdrop-filter:blur(14px) saturate(160%);border:1px solid var(--pr-bd);border-radius:99px;box-shadow:0 8px 28px rgba(8,24,38,.14);color:var(--pr-ink);font:inherit}" +
    "#pr-pill.hide{display:none}#pr-pill.dim{opacity:.45}" +
    "#pr-pill .seg{display:flex;align-items:center;justify-content:center;min-width:40px;height:44px;background:none;border:none;color:var(--pr-ink);font-size:15px;font-weight:600;cursor:pointer}" +
    "#pr-pill .cnt{gap:6px;padding:0 10px}#pr-pill .div{width:1px;height:20px;background:var(--pr-line)}" +
    "#pr-pill .nn{min-width:42px;font-variant-numeric:tabular-nums;font-size:13px;color:var(--pr-ink2)}" +
    "#pr-pill .snd{position:relative}#pr-pill .snd .dot{position:absolute;top:9px;right:7px;width:6px;height:6px;border-radius:50%;background:var(--pr-signal)}" +
    "#pr-pill svg{width:19px;height:19px;stroke:var(--pr-ink);fill:none;stroke-width:1.8}" +
    "#pr-pill .snd svg{stroke:var(--pr-signal)}" +
    /* v7.0 — desktop-only comment/edit mode toggles (arm-then-click, since
     * there's no long-press on a mouse); mirrors the old rail's + Comment/
     * ✎ Edit buttons but lives in the pill so mobile and desktop share one
     * toolbar. */
    "#pr-pill .seg.mode.on{background:var(--pr-accent);border-radius:50%}#pr-pill .seg.mode.on svg{stroke:#fff}" +
    "#pr-scrim{position:fixed;inset:0;z-index:2147483500;background:var(--pr-scrim);-webkit-backdrop-filter:blur(2px);backdrop-filter:blur(2px)}" +
    "#pr-lift{position:fixed;z-index:2147483520;pointer-events:none;border-radius:8px;box-shadow:0 18px 50px rgba(23,15,23,.35);transform:scale(1.02);transform-origin:center;background:var(--pr-card);overflow:hidden}" +
    "#pr-menu{position:fixed;z-index:2147483540;width:250px;background:var(--pr-surface);-webkit-backdrop-filter:blur(24px) saturate(180%);backdrop-filter:blur(24px) saturate(180%);border:1px solid var(--pr-bd);border-radius:16px;overflow:hidden;box-shadow:inset 0 1px 0 rgba(255,255,255,.65),0 8px 28px rgba(8,24,38,.14);color:var(--pr-ink)}" +
    "#pr-menu button{display:flex;align-items:center;width:100%;gap:10px;padding:13px 16px;background:none;border:none;border-bottom:.5px solid var(--pr-line);color:var(--pr-ink);font:inherit;font-size:15.5px;font-weight:550;text-align:left;cursor:pointer}" +
    "#pr-menu button:last-child{border-bottom:none}#pr-menu button .ic{margin-left:auto;font-size:15px;color:var(--pr-ink2)}" +
    "#pr-menu .sub{display:flex;gap:6px;padding:10px 12px;flex-wrap:wrap}#pr-menu .sub button{width:auto;border:1px solid var(--pr-bd);border-radius:99px;padding:10px 13px;font-size:13.5px;flex:none}" +
    "#pr-composer{position:fixed;left:0;right:0;bottom:0;z-index:2147483600;background:var(--pr-card);border-top:1px solid var(--pr-line);border-radius:16px 16px 0 0;box-shadow:0 -12px 30px rgba(20,26,33,.11);padding:12px 14px calc(12px + env(safe-area-inset-bottom));color:var(--pr-ink)}" +
    "#pr-composer .chips{display:flex;gap:8px;overflow-x:auto;padding-bottom:10px}#pr-composer .chips button{flex:none;border:1px solid var(--pr-bd);background:var(--pr-tint);color:var(--pr-ink);border-radius:99px;padding:9px 14px;font:inherit;font-size:13.5px;font-weight:600;cursor:pointer}" +
    "#pr-composer .q{font-size:11px;color:var(--pr-ink2);margin:0 0 7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
    "#pr-composer .r2{display:flex;align-items:center;gap:10px}" +
    "#pr-composer input{flex:1;font-size:16px;padding:11px 12px;border:1px solid var(--pr-bd);border-radius:12px;background:var(--pr-card);color:var(--pr-ink);font-family:inherit}" +
    "#pr-composer .go{flex:none;width:38px;height:38px;border-radius:50%;border:none;background:var(--pr-ink);cursor:pointer;display:flex;align-items:center;justify-content:center}" +
    "#pr-composer .go svg{width:17px;height:17px;stroke:var(--pr-card);fill:none;stroke-width:1.9}" +
    ".pr-dot{position:absolute;width:9px;height:9px;border-radius:50%;background:var(--pr-ink);box-shadow:0 0 0 2px var(--pr-card);z-index:2147482000;cursor:pointer;transform:translate(-50%,-50%)}" +
    ".pr-dot.on{outline:2px solid var(--pr-ink);outline-offset:2px}" +
    "#pr-card{position:absolute;z-index:2147483400;width:min(300px,86vw);background:var(--pr-card);border:1px solid var(--pr-bd);border-radius:12px;box-shadow:0 12px 30px rgba(20,26,33,.11);padding:12px 13px;color:var(--pr-ink);font-size:13.5px;line-height:1.45}" +
    "#pr-card .top{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--pr-ink2);margin-bottom:6px}" +
    "#pr-card .top .n{width:18px;height:18px;border-radius:50%;background:var(--pr-ink);color:var(--pr-card);font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center}" +
    "#pr-card .x{margin-left:auto;background:none;border:none;color:var(--pr-ink2);font-size:16px;cursor:pointer}" +
    "#pr-card .was{margin-top:4px;font-size:11px;color:var(--pr-ink2);text-decoration:line-through}" +
    ".pr-anchor-live{box-shadow:inset 0 0 0 1.5px rgba(128,128,128,.6);background:var(--pr-tint)}" +
    ".pr-ask{margin-top:9px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}" +
    ".pr-ask .pr-ask-btn{border:1px solid var(--pr-bd);background:var(--pr-card);color:var(--pr-ink);border-radius:99px;padding:9px 16px;font:inherit;font-size:14px;font-weight:600;min-height:40px;cursor:pointer}" +
    ".pr-ask .pr-ask-btn.on{background:var(--pr-accent);color:#fff;border-color:var(--pr-accent)}" +
    ".pr-ask .pr-ask-btn:not(.on){opacity:.72}" +
    ".pr-check{display:inline-flex;align-items:center;gap:10px;cursor:pointer;font:inherit;margin-top:2px}" +
    ".pr-check .box{width:22px;height:22px;border-radius:6px;border:2px solid var(--pr-ink);display:inline-flex;align-items:center;justify-content:center;flex:none}" +
    ".pr-check.on .box{background:var(--pr-ink)}.pr-check.on .box svg{stroke:var(--pr-card)}.pr-check .box svg{width:13px;height:13px;stroke:transparent;fill:none;stroke-width:2.4}" +
    ".pr-check.on .lbl{text-decoration:line-through;color:var(--pr-ink2)}" +
    ".pr-done-cap{font-size:11px;color:var(--pr-ink2);margin-top:3px}" +
    ".pr-scale{width:100%;margin-top:12px}.pr-scale .val{display:flex;align-items:baseline;justify-content:space-between;font-size:12px;color:var(--pr-ink2);margin-bottom:4px}.pr-scale .val b{color:var(--pr-ink);font-size:22px;font-variant-numeric:tabular-nums}" +
    ".pr-scale input[type=range]{width:100%;height:30px;-webkit-appearance:none;appearance:none;background:transparent;cursor:pointer}" +
    ".pr-scale input[type=range]::-webkit-slider-runnable-track{height:6px;border-radius:99px;background:var(--pr-line)}" +
    ".pr-scale input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:26px;height:26px;border-radius:50%;background:var(--pr-ink);margin-top:-10px;box-shadow:0 2px 8px rgba(0,0,0,.28)}" +
    ".pr-scale input[type=range]::-moz-range-track{height:6px;border-radius:99px;background:var(--pr-line)}.pr-scale input[type=range]::-moz-range-thumb{width:26px;height:26px;border:none;border-radius:50%;background:var(--pr-ink)}" +
    ".pr-approve{width:22px;height:22px;border-radius:50%;border:2px solid var(--pr-ink);background:none;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;vertical-align:middle;margin-left:8px}" +
    ".pr-approve.on{background:var(--pr-ink)}.pr-approve svg{width:12px;height:12px;stroke:transparent;stroke-width:2.6;fill:none}.pr-approve.on svg{stroke:var(--pr-card)}";

  /* v6.2 tabs — reuses the same tokens as cssMobile (defined at :root, available in
   * both desktop and mobile modes since both style blocks are always injected).
   * v7.0 — base position dropped to top:2px (was 26px, to clear the old desktop
   * wordmark): both platforms now show just the 2px hairline up top. */
  var cssTabs =
    "#pr-tabs{position:fixed;top:2px;left:0;right:0;z-index:2147483610;display:flex;overflow-x:auto;-webkit-overflow-scrolling:touch;background:var(--pr-surface);-webkit-backdrop-filter:blur(14px) saturate(160%);backdrop-filter:blur(14px) saturate(160%);border-bottom:1px solid var(--pr-bd);scrollbar-width:none}" +
    "#pr-tabs::-webkit-scrollbar{display:none}" +
    ".pr-tab{flex:none;border:none;background:none;color:var(--pr-ink2);font-family:'Hanken Grotesk',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,system-ui,sans-serif;font-size:13.5px;font-weight:600;padding:11px 16px;cursor:pointer;white-space:nowrap;border-bottom:2px solid transparent}" +
    ".pr-tab.on{color:var(--pr-accent);border-bottom-color:var(--pr-accent);font-weight:700}";

  /* v7.0 — ☰ docs button + slide-in drawer. Reachable on BOTH platforms (a
   * new capability for mobile, which never had docs nav before). Only ever
   * built when window.PROOFING_DOCS is a non-empty, scheme-safe list — see
   * buildHamburger() below. Reuses the #pr-scrim/closeOverlays() plumbing the
   * notes drawer and long-press menu already share, so only one overlay is
   * ever open at a time. */
  var cssDocs =
    "#pr-burger{position:fixed;top:max(14px,env(safe-area-inset-top));left:14px;z-index:2147483620;width:40px;height:40px;border-radius:50%;border:1px solid var(--pr-bd);background:var(--pr-surface);-webkit-backdrop-filter:blur(14px) saturate(160%);backdrop-filter:blur(14px) saturate(160%);box-shadow:0 8px 24px rgba(8,24,38,.14);color:var(--pr-ink);display:flex;align-items:center;justify-content:center;cursor:pointer}" +
    "#pr-burger svg{width:18px;height:18px;stroke:var(--pr-ink);fill:none;stroke-width:2}" +
    "#pr-docs{position:fixed;top:0;left:0;bottom:0;z-index:2147483540;width:min(300px,84vw);background:var(--pr-surface);-webkit-backdrop-filter:blur(24px) saturate(180%);backdrop-filter:blur(24px) saturate(180%);border-right:1px solid var(--pr-bd);box-shadow:8px 0 28px rgba(8,24,38,.14);color:var(--pr-ink);display:flex;flex-direction:column;overflow:hidden;transform:translateX(-100%);transition:transform .18s ease}" +
    "#pr-docs.open{transform:translateX(0)}" +
    "#pr-docs .pr-docs-hd{display:flex;align-items:center;padding:16px 16px 10px;padding-top:max(16px,env(safe-area-inset-top));font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--pr-ink2);font-weight:700}" +
    "#pr-docs .pr-docs-hd .x{margin-left:auto;background:none;border:none;color:var(--pr-ink2);font-size:20px;cursor:pointer;line-height:1;padding:0}" +
    "#pr-docs .pr-docs-list{flex:1;overflow-y:auto;padding:2px 10px 16px;display:flex;flex-direction:column;gap:2px}" +
    ".pr-doc-link{display:block;padding:10px 10px;border-radius:9px;font-size:13.5px;line-height:1.35;color:var(--pr-ink);text-decoration:none}" +
    ".pr-doc-link:hover{background:var(--pr-tint)}.pr-doc-link.on{background:var(--pr-accent);color:#fff}" +
    ".pr-doc-link .src{display:block;font-size:10.5px;color:var(--pr-ink2);margin-top:2px}.pr-doc-link.on .src{color:rgba(255,255,255,.8)}";

  /* v7.0 — desktop scale-up: the SAME pill/composer/drawer as mobile, ~1.3x
   * for pointer-sized targets on a 1280-1440 viewport. Two extra pill segs
   * (comment/edit mode toggles, desktop-only — no long-press to fall back on)
   * are sized alongside. Higher specificity than cssMobile's base rules
   * (body.pr-d adds a class) so these always win regardless of declaration
   * order. */
  var cssDesktopScale =
    "body.pr-d #pr-burger{width:46px;height:46px;top:18px;left:18px}body.pr-d #pr-burger svg{width:20px;height:20px}" +
    /* mobile: push page content below the fixed ☰ so it doesn't sit over the top-left header. desktop content is centred, no clash. */
    "body.pr-m.pr-nav{padding-top:62px!important}" +
    "body.pr-d #pr-docs{width:min(340px,88vw)}" +
    "body.pr-d #pr-docs .pr-docs-hd{font-size:12px;padding:20px 18px 12px}" +
    "body.pr-d .pr-doc-link{font-size:14.5px;padding:12px 12px}" +
    "body.pr-d #pr-pill{height:56px;padding:0 8px;gap:3px;bottom:32px}" +
    "body.pr-d #pr-pill .seg{min-width:50px;height:56px;font-size:17px}" +
    "body.pr-d #pr-pill .seg.mode{font-size:19px}" +
    "body.pr-d #pr-pill .seg.busy{opacity:.5}" +
    "body.pr-d #pr-pill .cnt{padding:0 14px;gap:8px}" +
    "body.pr-d #pr-pill .nn{min-width:54px;font-size:16px}" +
    "body.pr-d #pr-pill .div{height:26px}" +
    "body.pr-d #pr-pill svg{width:23px;height:23px}" +
    "body.pr-d #pr-composer{left:50%;right:auto;transform:translateX(-50%);width:min(640px,90vw);border-radius:20px 20px 0 0;padding:18px 20px calc(18px + env(safe-area-inset-bottom))}" +
    "body.pr-d #pr-composer .chips{padding-bottom:12px;gap:10px}" +
    "body.pr-d #pr-composer .chips button{font-size:14.5px;padding:10px 16px}" +
    "body.pr-d #pr-composer .q{font-size:12.5px}" +
    "body.pr-d #pr-composer input{font-size:16.5px;padding:13px 15px;border-radius:14px}" +
    "body.pr-d #pr-composer .go{width:44px;height:44px}body.pr-d #pr-composer .go svg{width:19px;height:19px}" +
    "body.pr-d #pr-menu{width:min(380px,92vw)}" +
    "body.pr-d #pr-menu button{font-size:16px;padding:14px 18px}" +
    "body.pr-d #pr-menu .dr{font-size:15px}";

  var st = document.createElement("style");
  st.textContent = cssDesktop + cssMobile + cssTabs + cssDocs + cssDesktopScale;
  document.head.appendChild(st);

  var ICON_CHAT = '<svg viewBox="0 0 24 24"><path d="M21 12a8 8 0 0 1-11.6 7.1L3 21l1.9-6.4A8 8 0 1 1 21 12z"/></svg>';
  var ICON_SEND = '<svg viewBox="0 0 24 24"><path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4 20-7z"/></svg>';
  var ICON_CHECK = '<svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>';
  // v7.0 — desktop pill mode toggles + the docs hamburger
  var ICON_COMMENT = '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>';
  var ICON_EDIT = '<svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>';
  var ICON_BURGER = '<svg viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18"/></svg>';

  /* ======================================================================== */
  /*  SHARED: reviewer, edit-in-place, annotations, extract/send              */
  /* ======================================================================== */
  function reviewer() { return state.reviewer || "anon"; }
  function noteReviewer(v) { state.reviewer = (v || "").trim(); localStorage.setItem("proofing-room:reviewer", state.reviewer); }

  function upsertEdit(el, orig, now) {
    var s = selectorFor(el), ex = state.edits.filter(function (x) { return x.selector === s; })[0];
    if (ex) { ex.text = now; ex.author = reviewer(); }
    else state.edits.push(Object.assign({ id: nid("e"), kind: "edit", author: reviewer(), original: orig, text: now, createdAt: new Date().toISOString() }, anchorMeta(el)));
    state.sent = false; persist(); render();
  }
  function removeEditBySelector(s) { var n = state.edits.length; state.edits = state.edits.filter(function (x) { return x.selector !== s; }); if (state.edits.length !== n) { persist(); render(); } }
  function applyEdits() {
    state.edits.forEach(function (e) { var el = locate(e); if (!el) return; if (el.getAttribute("data-pr-orig") === null) el.setAttribute("data-pr-orig", e.original); if ((el.innerText || "").trim() !== e.text) el.textContent = e.text; el.classList.add("pr-edited"); });
  }
  document.addEventListener("blur", function (e) {
    var el = e.target;
    if (!el || !el.getAttribute || el.getAttribute("contenteditable") !== "true") return;
    if (el.getAttribute("data-pr-orig") === null) return;
    el.removeAttribute("contenteditable"); el.classList.remove("pr-editing-el");
    var orig = el.getAttribute("data-pr-orig"), now = (el.innerText || "").trim();
    if (now !== orig) { upsertEdit(el, orig, now); el.classList.add("pr-edited"); }
    else { removeEditBySelector(selectorFor(el)); el.classList.remove("pr-edited"); el.removeAttribute("data-pr-orig"); }
  }, true);
  function isEditable(el) {
    if (!el || isUi(el)) return false;
    var t = el.tagName;
    if (/^(P|H[1-6]|LI|BLOCKQUOTE|FIGCAPTION|SPAN|A|TD|TH|DT|DD|EM|STRONG|CITE|SMALL|LABEL)$/.test(t)) return (el.innerText || "").trim().length > 0;
    if (t === "DIV" && el.children.length === 0 && (el.innerText || "").trim()) return true;
    return false;
  }
  function startEdit(el) {
    if (el.getAttribute("data-pr-orig") === null) el.setAttribute("data-pr-orig", (el.innerText || "").trim());
    el.setAttribute("contenteditable", "true"); el.classList.add("pr-editing-el"); el.focus();
  }

  function addComment(el, text) { if (!text) return; state.comments.push(Object.assign({ id: nid("c"), kind: "comment", author: reviewer(), text: text, createdAt: new Date().toISOString() }, anchorMeta(el))); state.sent = false; persist(); render(); }
  function annoFor(kind, el, askId) {
    var s = selectorFor(el);
    return state.annos.filter(function (a) { return a.kind === kind && (askId ? a.askId === askId : a.selector === s); })[0];
  }
  // render, but keep the reviewer's scroll position — iOS scroll-anchoring can
  // jump the page (e.g. to the bottom) when the DOM rebuilds after ticking a
  // done/answer control; capture scrollY and restore it after the re-render.
  function renderKeepScroll() {
    var sy = window.scrollY || window.pageYOffset || 0;
    render();
    requestAnimationFrame(function () { if (Math.abs((window.scrollY || 0) - sy) > 3) window.scrollTo(0, sy); });
  }
  // Bring an anchored element into view for annotating. Bias it toward the
  // UPPER portion of the *visible* viewport (not the full-height centre) so it
  // stays above where the composer + soft keyboard dock — block:center / a
  // full-innerHeight centre reads as "scrolled too far down" once the keyboard
  // rises and the reviewer has to scroll back up (observed on iOS, 2026-07-14).
  function scrollAnchorIntoView(el) {
    if (!el) return;
    var vv = window.visualViewport;
    var vh = (vv && vv.height) || window.innerHeight || 600;
    var top = el.getBoundingClientRect().top + (window.scrollY || window.pageYOffset || 0);
    var y = top - Math.max(88, vh * 0.28);
    window.scrollTo({ top: Math.max(0, y), behavior: "smooth" });
  }
  function setAnno(kind, el, extra, askId) {
    var keySel = selectorFor(el);
    var i = state.annos.findIndex(function (a) { return a.kind === kind && (askId ? a.askId === askId : a.selector === keySel); });
    var base = Object.assign({ id: (i >= 0 ? state.annos[i].id : nid("n")), kind: kind, author: reviewer(), createdAt: new Date().toISOString() }, anchorMeta(el));
    if (askId) base.askId = askId;
    var rec = Object.assign(base, extra);
    if (i >= 0) state.annos[i] = rec; else state.annos.push(rec);
    state.sent = false; persist(); renderKeepScroll();
    return rec;
  }
  function removeAnno(id) { state.annos = state.annos.filter(function (a) { return a.id !== id; }); persist(); renderKeepScroll(); }
  function removeById(id) {
    state.comments = state.comments.filter(function (c) { return c.id !== id; });
    state.annos = state.annos.filter(function (a) { return a.id !== id; });
    persist(); renderKeepScroll();
  }

  function buildDocument() {
    var STD = /^(H[1-6]|P|LI|BLOCKQUOTE|FIGCAPTION|BUTTON|A)$/, LEAF = /^(DIV|SPAN|TD|TH|DT|DD)$/, PROSE = "p,li,h1,h2,h3,h4,h5,h6,blockquote,figcaption,button,a";
    var out = [];
    Array.prototype.forEach.call(document.body.querySelectorAll("*"), function (n) {
      if (isUi(n)) return;
      var tag = n.tagName, take = STD.test(tag) || (LEAF.test(tag) && n.children.length === 0 && !n.closest(PROSE));
      if (!take) return;
      var text = snippet(n, 400);
      if (!text) { text = (n.textContent || "").replace(/\s+/g, " ").trim(); if (text.length > 400) text = text.slice(0, 399) + "…"; }
      if (!text) return;
      var s = selectorFor(n);
      var cs = state.comments.filter(function (c) { return c.selector === s; }).map(function (c) { return { author: c.author, text: c.text }; });
      var item = { tag: n.tagName.toLowerCase(), text: text, selector: s, comments: cs };
      var ed = state.edits.filter(function (x) { return x.selector === s; })[0];
      if (ed) { item.edited = true; item.original = ed.original; item.editedBy = ed.author; }
      var na = state.annos.filter(function (a) { return a.selector === s; });
      if (na.length) item.annotations = na.map(function (a) { return { kind: a.kind, value: a.value, at: a.at, askId: a.askId }; });
      out.push(item);
    });
    return out;
  }
  function byKind(k) { return state.annos.filter(function (a) { return a.kind === k; }); }
  function buildPayload() {
    var reviewers = [];
    function noteR(a) { if (a && reviewers.indexOf(a) < 0) reviewers.push(a); }
    state.comments.concat(state.edits, state.annos).forEach(function (x) { noteR(x.author); });
    noteR(state.reviewer);
    return {
      tool: "proofing-room", version: "6", url: location.href, path: location.pathname, title: document.title,
      extractedAt: new Date().toISOString(), reviewers: reviewers,
      comments: state.comments, edits: state.edits,
      answers: byKind("answer"), reactions: byKind("reaction"), approvals: byKind("approval"),
      done: byKind("done"), reminders: byKind("reminder"),
      document: buildDocument(),
    };
  }
  function extract() {
    var data = buildPayload();
    var blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    var a = document.createElement("a");
    var slug = location.pathname.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "") || "home";
    a.href = URL.createObjectURL(blob); a.download = "proofing-" + slug + "-" + new Date().toISOString().slice(0, 10) + ".json";
    document.body.appendChild(a); a.click(); a.remove();
  }
  function sendSummary() {
    var parts = [];
    function p(n, w) { if (n) parts.push(n + " " + w + (n > 1 ? "s" : "")); }
    p(state.comments.length, "comment"); p(state.edits.length, "edit");
    p(byKind("answer").length, "answer"); p(byKind("approval").length, "approval");
    p(byKind("done").length, "done"); p(byKind("reaction").length, "reaction"); p(byKind("reminder").length, "reminder");
    return "📝 " + reviewer() + " — " + (parts.join(" · ") || "no notes") + " on \"" + (document.title || location.pathname) + "\"";
  }
  function sendToWebhook(btn) {
    if (!WEBHOOK) { extract(); return; }
    var data = buildPayload();
    var slug = location.pathname.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "") || "home";
    var fd = new FormData();
    fd.append("payload_json", JSON.stringify({ content: sendSummary().slice(0, 1900) }));
    fd.append("files[0]", new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }), "proofing-" + slug + "-" + new Date().toISOString().slice(0, 10) + ".json");
    if (btn) btn.classList.add("busy");
    return fetch(WEBHOOK, { method: "POST", body: fd }).then(function (r) {
      if (btn) btn.classList.remove("busy");
      if (!r.ok) throw new Error("HTTP " + r.status);
      state.sent = true; render(); toast("Sent ✓");
    }).catch(function (e) { if (btn) btn.classList.remove("busy"); console.log("proofing send error", e); toast("Send failed — downloading"); extract(); });
  }
  function totalCount() { return state.comments.length + state.edits.length + state.annos.length; }

  var toastEl = null;
  function toast(msg) {
    if (toastEl) toastEl.remove();
    toastEl = document.createElement("div"); toastEl.id = "pr-mfont"; toastEl.textContent = msg;
    toastEl.style.cssText = "position:fixed;left:50%;bottom:80px;transform:translateX(-50%);z-index:2147483647;background:var(--pr-ink,#241c22);color:var(--pr-card,#fff);padding:10px 16px;border-radius:99px;font:600 13px -apple-system,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.3)";
    document.body.appendChild(toastEl);
    setTimeout(function () { if (toastEl) { toastEl.remove(); toastEl = null; } }, 2200);
  }

  /* ---- tabs (v6.2): declare panels via data-proof-tab="Label" ------------- */
  /* One page, several briefs. If the page has NO [data-proof-tab] elements this
   * whole feature is a no-op — single-view pages behave exactly as before. */
  var TAB_KEY = "proofing-room:tab:" + location.pathname;
  var tabPanels = []; // [{ label, el }], in document order
  var activeTab = null;
  var tabsBar = null;
  function findOwnerTab(el) {
    if (!tabPanels.length || !el) return null;
    for (var i = 0; i < tabPanels.length; i++) {
      if (tabPanels[i].el === el || (tabPanels[i].el.contains && tabPanels[i].el.contains(el))) return tabPanels[i];
    }
    return null;
  }
  function reserveSpaceForTabs() {
    if (!tabsBar) return;
    var need = Math.ceil(tabsBar.getBoundingClientRect().bottom);
    if (need <= 0) return;
    var cur = parseFloat(getComputedStyle(document.body).paddingTop) || 0;
    if (cur < need) document.body.style.paddingTop = need + "px"; // additive only; never shrinks existing padding
  }
  function setActiveTab(label, isInitial) {
    if (!tabPanels.length) return;
    var found = tabPanels.filter(function (t) { return t.label === label; })[0] || tabPanels[0];
    activeTab = found.label;
    tabPanels.forEach(function (t) { t.el.style.display = (t === found) ? "" : "none"; });
    if (tabsBar) {
      Array.prototype.forEach.call(tabsBar.querySelectorAll(".pr-tab"), function (b) {
        b.classList.toggle("on", b.getAttribute("data-pr-tab-label") === activeTab);
      });
    }
    localStorage.setItem(TAB_KEY, activeTab);
    if (!isInitial) { closeCard(); closeOverlays(); closeComposer(); }
    render(); // pins/cards recompute; hidden panels' anchors auto-drop via isVisible()
  }
  function buildTabsBar() {
    tabsBar = document.createElement("div"); tabsBar.id = "pr-tabs";
    tabPanels.forEach(function (t) {
      var b = document.createElement("button"); b.type = "button"; b.className = "pr-tab";
      b.setAttribute("data-pr-tab-label", t.label); b.textContent = t.label;
      b.addEventListener("click", function (ev) { ev.stopPropagation(); if (activeTab !== t.label) setActiveTab(t.label); });
      tabsBar.appendChild(b);
    });
    document.body.appendChild(tabsBar);
    installTabSwipe();
  }
  function installTabSwipe() {
    var sx = 0, sy = 0, tracking = false;
    var SKIP = "a,button,input,textarea,select,label,[contenteditable='true'],.pr-ask,.pr-check,.pr-scale,.pr-approve";
    document.addEventListener("pointerdown", function (e) {
      tracking = false;
      if (!tabPanels.length || e.pointerType === "mouse" || isUi(e.target)) return;
      if (e.target.closest && e.target.closest(SKIP)) return;
      sx = e.clientX; sy = e.clientY; tracking = true;
    }, true);
    document.addEventListener("pointerup", function (e) {
      if (!tracking) return; tracking = false;
      var dx = e.clientX - sx, dy = e.clientY - sy;
      if (Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) * 1.5) return; // too short, or more vertical than horizontal (scroll)
      var idx = -1;
      for (var i = 0; i < tabPanels.length; i++) if (tabPanels[i].label === activeTab) { idx = i; break; }
      if (idx < 0) return;
      var next = idx + (dx < 0 ? 1 : -1); // swipe left → next tab, swipe right → previous tab
      if (next < 0 || next >= tabPanels.length) return;
      setActiveTab(tabPanels[next].label);
    }, true);
    document.addEventListener("pointercancel", function () { tracking = false; }, true);
  }
  function initTabs() {
    var els = document.querySelectorAll("[data-proof-tab]");
    if (!els.length) return; // no declared tabs — do not regress single-view pages
    Array.prototype.forEach.call(els, function (el) { tabPanels.push({ label: el.getAttribute("data-proof-tab"), el: el }); });
    buildTabsBar();
    reserveSpaceForTabs();
    var saved = localStorage.getItem(TAB_KEY);
    var initial = tabPanels[0].label;
    if (saved && tabPanels.some(function (t) { return t.label === saved; })) initial = saved;
    setActiveTab(initial, true);
  }

  /* ---- declared asks: render native controls in place --------------------- */
  function renderAsks() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-proof-ask]"), function (host) {
      if (host.querySelector(".pr-ask,.pr-check,.pr-scale")) return; // already rendered
      var askId = host.getAttribute("data-proof-ask"), type = host.getAttribute("data-ask-type") || "yesno";
      if (type === "yesno") {
        var opts = (host.getAttribute("data-ask-options") || "Yes,No").split(",").map(function (s) { return s.trim(); });
        var wrap = document.createElement("div"); wrap.className = "pr-ask";
        opts.forEach(function (opt) {
          var b = document.createElement("button"); b.className = "pr-ask-btn"; b.type = "button"; b.textContent = opt;
          b.addEventListener("click", function (ev) { ev.stopPropagation(); setAnno("answer", host, { askType: "yesno", value: opt }, askId); });
          wrap.appendChild(b);
        });
        host.appendChild(wrap);
      } else if (type === "done") {
        var chk = document.createElement("label"); chk.className = "pr-check";
        chk.innerHTML = '<span class="box">' + ICON_CHECK + '</span><span class="lbl"></span>';
        var lbl = chk.querySelector(".lbl"); lbl.textContent = host.textContent.trim(); host.textContent = "";
        chk.addEventListener("click", function (ev) { ev.stopPropagation(); var cur = annoFor("done", host, askId); if (cur && cur.value) removeAnno(cur.id); else setAnno("done", host, { value: true }, askId); });
        host.appendChild(chk);
        var cap = document.createElement("div"); cap.className = "pr-done-cap"; cap.style.display = "none"; cap.textContent = "Marked done · syncs with the review"; host.appendChild(cap);
      } else if (type === "scale") {
        var min = +(host.getAttribute("data-ask-min") || 1), max = +(host.getAttribute("data-ask-max") || 5), step = +(host.getAttribute("data-ask-step") || 1);
        var box = document.createElement("div"); box.className = "pr-scale";
        var cur2 = annoFor("answer", host, askId), v0 = cur2 ? cur2.value : Math.round((min + max) / 2);
        box.innerHTML = '<div class="val"><span>' + min + '</span><b>' + v0 + '</b><span>' + max + '</span></div><input type="range" min="' + min + '" max="' + max + '" step="' + step + '" value="' + v0 + '">';
        var rng = box.querySelector("input"), out = box.querySelector("b");
        rng.addEventListener("input", function () { out.textContent = rng.value; });
        rng.addEventListener("change", function () { setAnno("answer", host, { askType: "scale", value: +rng.value }, askId); });
        rng.addEventListener("click", function (e) { e.stopPropagation(); });
        rng.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
        host.appendChild(box);
      }
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-proof-section]"), function (sec) {
      var head = sec.querySelector("h1,h2,h3,h4,h5,h6") || sec;
      if (head.querySelector(".pr-approve")) return;
      var b = document.createElement("button"); b.className = "pr-approve"; b.type = "button"; b.title = "Approve section"; b.innerHTML = ICON_CHECK;
      b.addEventListener("click", function (ev) { ev.stopPropagation(); var cur = annoFor("approval", sec); if (cur && cur.value) removeAnno(cur.id); else setAnno("approval", sec, { value: true, section: sec.getAttribute("data-proof-section") || nearestSection(sec) }); });
      head.appendChild(b);
    });
  }
  function paintAsks() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-proof-ask]"), function (host) {
      var askId = host.getAttribute("data-proof-ask"), type = host.getAttribute("data-ask-type") || "yesno";
      if (type === "yesno") {
        var a = annoFor("answer", host, askId);
        Array.prototype.forEach.call(host.querySelectorAll(".pr-ask-btn"), function (b) { b.classList.toggle("on", !!a && b.textContent === a.value); });
      } else if (type === "done") {
        var d = annoFor("done", host, askId), chk = host.querySelector(".pr-check"), cap = host.querySelector(".pr-done-cap");
        if (chk) chk.classList.toggle("on", !!(d && d.value));
        if (cap) cap.style.display = d && d.value ? "block" : "none";
      }
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-proof-section]"), function (sec) {
      var a = annoFor("approval", sec), b = sec.querySelector(".pr-approve");
      if (b) b.classList.toggle("on", !!(a && a.value));
    });
  }

  /* ---- render (pins + counts, both modes) --------------------------------- */
  var pinsLayer = document.createElement("div"); pinsLayer.id = "pr-pins";
  pinsLayer.style.cssText = "position:absolute;top:0;left:0;width:0;height:0;z-index:2147482000";
  var order = [];
  function allAnchored() { return state.comments.concat(state.edits, state.annos); }
  // v7.0 — pins + the pill are now built for BOTH platforms (desktop lost its
  // rail list, so the dot is the only on-page marker for an existing note; the
  // stepper/count live in the shared pill). Only the ADD/EDIT entry gesture
  // still branches on IS_MOBILE (long-press vs arm-then-click).
  function render() {
    renderAsks(); paintAsks();
    pinsLayer.innerHTML = ""; order = [];
    allAnchored().forEach(function (a) {
      var el = locate(a); if (!el || !isVisible(el)) return;
      a._top = el.getBoundingClientRect().top + window.scrollY; order.push(a);
      var r = el.getBoundingClientRect();
      var d = document.createElement("div"); d.className = "pr-dot" + (activeId === a.id ? " on" : "");
      d.style.left = r.right + window.scrollX - 6 + "px"; d.style.top = r.top + window.scrollY + 10 + "px";
      d.addEventListener("click", function (ev) { ev.stopPropagation(); openCard(a); });
      pinsLayer.appendChild(d);
    });
    order.sort(function (a, b) { return a._top - b._top; });
    updatePill();
  }

  /* ======================================================================== */
  /*  DESKTOP: click-to-comment + edit-in-place (v7.0 — the chrome itself is  */
  /*  now shared with mobile, built by buildToolbar() below; what's left here */
  /*  is genuinely desktop-only: hover-highlight, the click-driven popover,   */
  /*  and the comment/edit ARM buttons that now live in the pill instead of a */
  /*  removed rail — mouse press-hold has no long-press to fall back on.)     */
  /* ======================================================================== */
  var addBtn, editBtn, hoverEl = null;

  /* ---- docs list (v7.0): opt-in via window.PROOFING_DOCS =
   * [{title,url,source}], surfaced through the ☰ hamburger drawer (built in
   * buildHamburger, shared by both platforms) — replaces the old left rail.
   * Absent/empty → no hamburger at all. Links preserve the current proof mode
   * so hopping between docs stays in review mode. */
  function proofSuffixFor(url) {
    var mode = FORCE_MOBILE ? "proof=mobile" : "proof";
    var hi = url.indexOf("#"), hash = hi >= 0 ? url.slice(hi) : "", base = hi >= 0 ? url.slice(0, hi) : url;
    return base + (base.indexOf("?") >= 0 ? "&" : "?") + mode + hash;
  }

  // Defence-in-depth: PROOFING_DOCS urls are supplied by the host page, but
  // never render an <a href> for a script-executing scheme — a doc whose
  // url is javascript:/vbscript:/data: is dropped from the drawer entirely
  // (not rendered as "#").
  function isSafeDocUrl(url) {
    var v = String(url || "").replace(/[\u0000-\u0020]+/g, "").toLowerCase();
    return v.indexOf("javascript:") !== 0 && v.indexOf("vbscript:") !== 0 && v.indexOf("data:") !== 0;
  }
  function docMatchesHere(d) {
    try { return new URL(d.url, location.href).pathname === location.pathname; }
    catch (e) { return d.url === location.pathname || d.url === location.href; }
  }
  function setCommenting(on) {
    if (on && state.editing) setEditing(false);
    state.commenting = on;
    document.body.classList.toggle("pr-commenting", on);
    if (addBtn) { addBtn.classList.toggle("on", on); addBtn.title = on ? "Click an element… (Esc to cancel)" : "Comment mode (C)"; }
  }
  function setEditing(on) {
    if (on && state.commenting) setCommenting(false);
    state.editing = on;
    if (editBtn) { editBtn.classList.toggle("on", on); editBtn.title = on ? "Editing… click a text element" : "Edit mode (E)"; }
  }
  document.addEventListener("mouseover", function (e) { if (IS_MOBILE || !state.commenting || isUi(e.target)) return; if (hoverEl) hoverEl.classList.remove("pr-hl"); hoverEl = e.target; e.target.classList.add("pr-hl"); }, true);
  document.addEventListener("click", function (e) {
    if (state.editing && !isUi(e.target) && isEditable(e.target)) { e.preventDefault(); e.stopPropagation(); startEdit(e.target); return; }
    if (IS_MOBILE || !state.commenting || isUi(e.target)) return;
    e.preventDefault(); e.stopPropagation();
    if (hoverEl) hoverEl.classList.remove("pr-hl");
    openDesktopPop(e.target, e.clientX, e.clientY); setCommenting(false);
  }, true);
  var dpop = null;
  /* v6.3 — reaction (👍/👎) + reminder now reachable from the same popover a
   * comment is added from (desktop's only anchored-interaction surface), so
   * they run through the SAME setAnno("reaction",…)/commitRemind data path
   * as the mobile long-press menu. No new UI surface, no data-model change. */
  function paintDesktopPopRx(el) {
    if (!dpop) return;
    var a = annoFor("reaction", el);
    Array.prototype.forEach.call(dpop.querySelectorAll(".rx"), function (b) {
      b.classList.toggle("on", !!a && a.value === b.getAttribute("data-rx"));
    });
  }
  function openDesktopPop(el, x, y) {
    if (dpop) dpop.remove();
    dpop = document.createElement("div"); dpop.id = "pr-pop";
    dpop.innerHTML =
      '<div class="pr-pop-head">On &lt;' + el.tagName.toLowerCase() + '&gt;: <b>' + esc(snippet(el, 60)) + '</b></div>' +
      '<div class="pr-pop-actions">' +
      '<button type="button" class="rx" data-rx="up" title="Looks right">👍</button>' +
      '<button type="button" class="rx" data-rx="down" title="Off the mark">👎</button>' +
      '<button type="button" class="rmd" title="Set a reminder">⏰ Remind</button>' +
      '</div>' +
      '<div class="pr-pop-remind" hidden><button type="button" data-t="1">Tomorrow 09:00</button><button type="button" data-t="mon">Mon 09:00</button><button type="button" data-t="pick">Pick…</button></div>' +
      '<textarea placeholder="Your comment…"></textarea><div class="row"><button class="save">Save</button><button class="cancel">Cancel</button></div>';
    document.body.appendChild(dpop);
    dpop.style.left = Math.min(x + 8, window.innerWidth - 264) + window.scrollX + "px";
    dpop.style.top = Math.min(y + 8, window.innerHeight - 180) + window.scrollY + "px";
    var ta = dpop.querySelector("textarea"); ta.focus();
    paintDesktopPopRx(el);
    dpop.querySelector(".save").addEventListener("click", function () { addComment(el, ta.value.trim()); dpop.remove(); dpop = null; });
    dpop.querySelector(".cancel").addEventListener("click", function () { dpop.remove(); dpop = null; });
    Array.prototype.forEach.call(dpop.querySelectorAll(".rx"), function (b) {
      b.addEventListener("click", function (ev) {
        ev.stopPropagation();
        setAnno("reaction", el, { value: b.getAttribute("data-rx") });
        paintDesktopPopRx(el);
        toast(b.getAttribute("data-rx") === "up" ? "Marked looks right" : "Marked off the mark");
      });
    });
    var rmdBtn = dpop.querySelector(".rmd"), rmdSub = dpop.querySelector(".pr-pop-remind");
    rmdBtn.addEventListener("click", function (ev) { ev.stopPropagation(); rmdSub.hidden = !rmdSub.hidden; });
    rmdSub.addEventListener("click", function (ev) {
      var b = ev.target.closest("button[data-t]"); if (!b) return;
      ev.stopPropagation();
      var t = b.getAttribute("data-t");
      if (t === "1") { commitRemind(el, at9(1)); if (dpop) { dpop.remove(); dpop = null; } }
      else if (t === "mon") { commitRemind(el, nextMon9()); if (dpop) { dpop.remove(); dpop = null; } }
      else { pickDate(el); } // native picker; commitRemind fires on change (shared with mobile)
    });
  }
  // v7.0 — the desktop notes LIST (renderDesktopList) is gone with the rail;
  // openCard()/openDrawer() below (shared with mobile) already show every
  // note, including its cross-tab owner (shortKind()), so nothing is lost.
  function kindLabel(a) {
    return a.kind === "edit" ? "edit" : a.kind === "answer" ? "answer: " + a.value : a.kind === "reaction" ? (a.value === "up" ? "👍 looks right" : "👎 off the mark") : a.kind === "approval" ? "approved ✓" : a.kind === "done" ? "done ✓" : a.kind === "reminder" ? "remind " + String(a.at || "").slice(0, 16).replace("T", " ") : "comment";
  }

  /* ======================================================================== */
  /*  DESKTOP KEYBOARD SHORTCUTS (v6.3) — replaces mobile's long-press/swipe.  */
  /*  Entirely gated on !IS_MOBILE; never touches the mobile long-press path. */
  /* ======================================================================== */
  var kbHoverEl = null, shortcutsEl = null;
  if (!IS_MOBILE) {
    document.addEventListener("mouseover", function (e) { if (isUi(e.target)) return; kbHoverEl = e.target; }, true);
  }
  function openDesktopPopAt(el) {
    var r = el.getBoundingClientRect();
    openDesktopPop(el, r.left, r.top);
  }
  function stepTab(dir) {
    if (!tabPanels.length) return;
    var idx = -1;
    for (var i = 0; i < tabPanels.length; i++) if (tabPanels[i].label === activeTab) { idx = i; break; }
    if (idx < 0) return;
    var next = idx + dir;
    if (next < 0 || next >= tabPanels.length) return;
    setActiveTab(tabPanels[next].label);
  }
  var SHORTCUT_ROWS = [
    ["C", "Comment on the hovered element"],
    ["E", "Edit the hovered element"],
    ["J or ↓", "Next annotation"],
    ["K or ↑", "Previous annotation"],
    ["[ / ]", "Previous / next tab"],
    ["⌘/Ctrl + ⏎", SEND_LABEL],
    ["Esc", "Close popovers / this overlay"],
    ["?", "Toggle this help"]
  ];
  function toggleShortcutsOverlay() {
    if (shortcutsEl) { hideShortcutsOverlay(); return; }
    shortcutsEl = document.createElement("div"); shortcutsEl.id = "pr-shortcuts";
    var rows = SHORTCUT_ROWS.map(function (r) {
      return '<div class="pr-kb-row"><span class="pr-kb-key">' + esc(r[0]) + '</span><span class="pr-kb-desc">' + esc(r[1]) + '</span></div>';
    }).join("");
    shortcutsEl.innerHTML = '<div class="hd">Keyboard shortcuts<button type="button" class="x" title="Close">&times;</button></div><div class="body">' + rows + '</div>';
    document.body.appendChild(shortcutsEl);
    shortcutsEl.querySelector(".x").addEventListener("click", hideShortcutsOverlay);
  }
  function hideShortcutsOverlay() { if (shortcutsEl) { shortcutsEl.remove(); shortcutsEl = null; } }
  function closeAllDesktopOverlays() {
    if (dpop) { dpop.remove(); dpop = null; }
    closeCard();
    hideShortcutsOverlay();
    closeOverlays(); // v7.0 — also dismisses the notes/docs drawer if open (shared with mobile)
  }
  document.addEventListener("keydown", function (e) {
    if (IS_MOBILE) return;
    var t = e.target, tag = t && t.tagName;
    if (e.key === "Escape") {
      if (dpop || cardEl || shortcutsEl || menuEl) { e.preventDefault(); closeAllDesktopOverlays(); }
      return;
    }
    var typing = !!(t && (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || t.isContentEditable));
    if (typing) return;
    if (e.metaKey || e.ctrlKey) {
      if (e.key === "Enter") { e.preventDefault(); var sb = document.getElementById("pr-send"); if (sb) sendToWebhook(sb); }
      return;
    }
    if (e.altKey) return;
    if (e.key === "?") { e.preventDefault(); toggleShortcutsOverlay(); return; }
    if (e.key === "c" || e.key === "C") { if (kbHoverEl) { e.preventDefault(); openDesktopPopAt(kbHoverEl); if (state.commenting) setCommenting(false); } return; }
    if (e.key === "e" || e.key === "E") { if (kbHoverEl && isEditable(kbHoverEl)) { e.preventDefault(); startEdit(kbHoverEl); } return; }
    if (e.key === "j" || e.key === "ArrowDown") { e.preventDefault(); step(1); return; }
    if (e.key === "k" || e.key === "ArrowUp") { e.preventDefault(); step(-1); return; }
    if (e.key === "[") { e.preventDefault(); stepTab(-1); return; }
    if (e.key === "]") { e.preventDefault(); stepTab(1); return; }
  }, true);

  /* ======================================================================== */
  /*  TOOLBAR — pill / composer / drawer, shared by BOTH platforms (v7.0).    */
  /*  Was "MOBILE UI v6 — Hairline"; desktop now reuses it wholesale (scaled   */
  /*  up via body.pr-d, see cssDesktopScale) instead of its own rail. The     */
  /*  only branch left is the comment/edit ENTRY gesture: mobile long-presses */
  /*  (installLongPress), desktop arms a mode via two extra pill buttons then */
  /*  clicks (setCommenting/setEditing, defined in the DESKTOP section above).*/
  /* ======================================================================== */
  var pill, stepIdx = -1, activeId = null, cardEl = null, scrim = null, menuEl = null, liftEl = null, composer = null;
  function buildToolbar() {
    if (IS_MOBILE) document.documentElement.classList.add("pr-on");
    document.body.classList.add(IS_MOBILE ? "pr-m" : "pr-d");
    var hair = document.createElement("div"); hair.id = "pr-hairline"; document.body.appendChild(hair);
    pill = document.createElement("div"); pill.id = "pr-pill";
    pill.innerHTML =
      (!IS_MOBILE ?
        '<button type="button" class="seg mode" id="pr-mode-add" title="Comment mode (C)">' + ICON_COMMENT + '</button>' +
        '<button type="button" class="seg mode" id="pr-mode-edit" title="Edit mode (E)">' + ICON_EDIT + '</button>' +
        '<span class="div"></span>' : '') +
      '<button class="seg cnt" id="pr-count">' + ICON_CHAT + '<span id="pr-cn">0</span></button>' +
      '<span class="div"></span><button class="seg" id="pr-prev">‹</button><span class="seg nn" id="pr-nn">0/0</span><button class="seg" id="pr-next">›</button>' +
      '<span class="div"></span><button class="seg snd" id="pr-send" title="' + SEND_LABEL + '">' + ICON_SEND + '</button>';
    document.body.appendChild(pill);
    document.getElementById("pr-prev").addEventListener("click", function () { step(-1); });
    document.getElementById("pr-next").addEventListener("click", function () { step(1); });
    document.getElementById("pr-count").addEventListener("click", function () { openDrawer(); });
    var sendSeg = document.getElementById("pr-send");
    if (!WEBHOOK) sendSeg.style.display = "none";
    sendSeg.addEventListener("click", function () { sendToWebhook(sendSeg); });
    if (IS_MOBILE) {
      installLongPress();
    } else {
      addBtn = document.getElementById("pr-mode-add"); editBtn = document.getElementById("pr-mode-edit");
      addBtn.addEventListener("click", function () { setCommenting(!state.commenting); });
      editBtn.addEventListener("click", function () { setEditing(!state.editing); });
    }
    buildHamburger();
  }

  /* ---- ☰ docs button (v7.0): both platforms, opt-in via window.PROOFING_DOCS.
   * Shares the notes drawer's scrim/closeOverlays() plumbing below, so at
   * most one overlay is ever open. Absent/empty list → no button at all. */
  var DOCS = (Array.isArray(window.PROOFING_DOCS) ? window.PROOFING_DOCS : []).filter(function (d) { return d && d.url && isSafeDocUrl(d.url); });
  var burgerEl = null;
  function buildHamburger() {
    if (!DOCS.length) return; // no declared docs — no hamburger, either platform
    burgerEl = document.createElement("button"); burgerEl.type = "button"; burgerEl.id = "pr-burger"; burgerEl.title = "Docs"; burgerEl.innerHTML = ICON_BURGER;
    burgerEl.addEventListener("click", function (ev) { ev.stopPropagation(); if (menuEl && menuEl.id === "pr-docs") closeOverlays(); else openDocsDrawer(); });
    document.body.appendChild(burgerEl);
    document.body.classList.add("pr-nav"); // clear page content below the fixed ☰ (mobile)
  }
  function openDocsDrawer() {
    closeCard(); closeOverlays(); hideBurgerForOverlay();
    scrim = document.createElement("div"); scrim.id = "pr-scrim"; scrim.addEventListener("click", closeOverlays); document.body.appendChild(scrim);
    menuEl = document.createElement("div"); menuEl.id = "pr-docs";
    var links = DOCS.map(function (d) {
      var on = docMatchesHere(d);
      return '<a class="pr-doc-link' + (on ? " on" : "") + '" href="' + esc(proofSuffixFor(d.url)) + '">' + esc(d.title || d.url) + (d.source ? '<span class="src">' + esc(d.source) + '</span>' : "") + '</a>';
    }).join("");
    menuEl.innerHTML = '<div class="pr-docs-hd">Docs<button type="button" class="x" title="Close">&times;</button></div><div class="pr-docs-list">' + links + '</div>';
    document.body.appendChild(menuEl);
    menuEl.querySelector(".x").addEventListener("click", closeOverlays);
    requestAnimationFrame(function () { if (menuEl) menuEl.classList.add("open"); });
  }
  function updatePill() {
    if (!pill) return;
    document.getElementById("pr-cn").textContent = totalCount();
    document.getElementById("pr-nn").textContent = order.length ? (Math.max(0, stepIdx) + 1) + "/" + order.length : "0/0";
    var snd = document.getElementById("pr-send");
    if (snd) { var d = snd.querySelector(".dot"); var unsent = totalCount() > 0 && !state.sent; if (unsent && !d) { var dd = document.createElement("span"); dd.className = "dot"; snd.appendChild(dd); } else if (!unsent && d) d.remove(); }
  }
  function step(dir) {
    if (!order.length) return;
    stepIdx = (stepIdx + dir + order.length) % order.length;
    var a = order[stepIdx], el = locate(a);
    scrollAnchorIntoView(el);
    setTimeout(function () { openCard(a); }, 260);
  }

  function installLongPress() {
    var t = null, sx = 0, sy = 0, tgt = null;
    document.addEventListener("pointerdown", function (e) {
      if (!IS_MOBILE || isUi(e.target)) return;
      if (e.target.closest("a,button,input,textarea,select,label,[contenteditable='true'],.pr-ask,.pr-check,.pr-scale,.pr-approve")) return;
      sx = e.clientX; sy = e.clientY; tgt = e.target;
      t = setTimeout(function () { t = null; fire(); }, 450);
    }, true);
    function cancel() { if (t) { clearTimeout(t); t = null; } }
    document.addEventListener("pointermove", function (e) { if (t && Math.abs(e.clientX - sx) + Math.abs(e.clientY - sy) > 8) cancel(); }, true);
    document.addEventListener("pointerup", cancel, true);
    document.addEventListener("pointercancel", cancel, true);
    function fire() { try { navigator.vibrate && navigator.vibrate(10); } catch (e) {} swallowNextClick(); openMenu(tgt); }
  }
  var swallow = false;
  function swallowNextClick() { swallow = true; setTimeout(function () { swallow = false; }, 700); }
  // Eat the stray click a long-press produces, but NEVER a tap on our own UI
  // (menu/composer/card/pill), or the menu tap that follows would be swallowed.
  document.addEventListener("click", function (e) {
    if (!swallow) return;
    if (e.target.closest && e.target.closest("#pr-menu,#pr-composer,#pr-card,#pr-pill,#pr-sheet,#pr-docs,#pr-burger")) { swallow = false; return; }
    swallow = false; e.preventDefault(); e.stopPropagation();
  }, true);
  function pressToOpen(el, fn) { var t = null; el.addEventListener("pointerdown", function () { t = setTimeout(fn, 450); }); ["pointerup", "pointercancel", "pointermove"].forEach(function (ev) { el.addEventListener(ev, function () { if (t) { clearTimeout(t); t = null; } }); }); }

  // v7.0 — the ☰ button shares its corner with any open drawer's own header
  // (the docs drawer especially), so hide it while an overlay is up — each
  // open*() below calls hideBurgerForOverlay(); closeOverlays() brings it back.
  function closeOverlays() { [scrim, menuEl, liftEl].forEach(function (n) { if (n) n.remove(); }); scrim = menuEl = liftEl = null; if (pill) pill.classList.remove("dim"); if (burgerEl) burgerEl.style.display = ""; }
  function hideBurgerForOverlay() { if (burgerEl) burgerEl.style.display = "none"; }
  function openMenu(el) {
    closeCard(); closeOverlays(); hideBurgerForOverlay();
    scrim = document.createElement("div"); scrim.id = "pr-scrim"; scrim.addEventListener("click", closeOverlays); document.body.appendChild(scrim);
    var r = el.getBoundingClientRect();
    liftEl = document.createElement("div"); liftEl.id = "pr-lift";
    liftEl.style.left = r.left + "px"; liftEl.style.top = r.top + "px"; liftEl.style.width = r.width + "px"; liftEl.style.minHeight = r.height + "px";
    liftEl.innerHTML = "<div style='padding:6px 8px;font:15px/1.35 -apple-system,sans-serif;color:var(--pr-ink)'>" + esc(snippet(el, 120)) + "</div>";
    document.body.appendChild(liftEl);
    if (pill) pill.classList.add("dim");
    menuEl = document.createElement("div"); menuEl.id = "pr-menu";
    menuEl.innerHTML =
      '<button data-a="comment">Comment<span class="ic">✏️</span></button>' +
      '<button data-a="up">Looks right<span class="ic">✓</span></button>' +
      '<button data-a="down">Off the mark<span class="ic">✕</span></button>' +
      (isEditable(el) ? '<button data-a="edit">Edit text<span class="ic">✎</span></button>' : "") +
      '<button data-a="remind">Remind me<span class="ic">◷</span></button>';
    document.body.appendChild(menuEl);
    var mw = 250, mx = Math.min(Math.max(8, r.right - mw), window.innerWidth - mw - 8);
    var my = Math.min(r.bottom + 8, window.innerHeight - 270); if (my < 8) my = 8;
    menuEl.style.left = mx + "px"; menuEl.style.top = my + "px";
    menuEl.addEventListener("click", function (ev) {
      var b = ev.target.closest("button[data-a]"); if (!b) return;
      var a = b.getAttribute("data-a");
      if (a === "comment") { closeOverlays(); openComposer(el); }
      else if (a === "up") { setAnno("reaction", el, { value: "up" }); closeOverlays(); toast("Marked looks right"); }
      else if (a === "down") { setAnno("reaction", el, { value: "down" }); closeOverlays(); toast("Marked off the mark"); }
      else if (a === "edit") { closeOverlays(); startEdit(el); }
      else if (a === "remind") { openRemind(el); }
    });
  }
  function openRemind(el) {
    if (!menuEl) return;
    menuEl.innerHTML = '<div class="sub"><button data-t="1">Tomorrow 09:00</button><button data-t="mon">Mon 09:00</button><button data-t="pick">Pick…</button></div>';
    menuEl.addEventListener("click", function (ev) {
      var b = ev.target.closest("button[data-t]"); if (!b) return;
      var t = b.getAttribute("data-t");
      if (t === "1") commitRemind(el, at9(1));
      else if (t === "mon") commitRemind(el, nextMon9());
      else pickDate(el);
    });
  }
  function at9(days) { var d = new Date(); d.setDate(d.getDate() + days); d.setHours(9, 0, 0, 0); return d.toISOString(); }
  function nextMon9() { var d = new Date(); var add = ((8 - d.getDay()) % 7) || 7; d.setDate(d.getDate() + add); d.setHours(9, 0, 0, 0); return d.toISOString(); }
  function pickDate(el) {
    var inp = document.createElement("input"); inp.type = "datetime-local"; inp.style.cssText = "position:fixed;left:-9999px";
    document.body.appendChild(inp);
    inp.addEventListener("change", function () { if (inp.value) commitRemind(el, new Date(inp.value).toISOString()); inp.remove(); });
    inp.focus(); inp.click();
  }
  function commitRemind(el, iso) { setAnno("reminder", el, { at: iso, value: iso }); closeOverlays(); toast("Reminder set"); }

  function openComposer(el, existing) {
    closeComposer();
    if (pill) pill.classList.add("hide");
    el.classList.add("pr-anchor-live");
    composer = document.createElement("div"); composer.id = "pr-composer";
    var chips = existing ? "" : CHIPS.map(function (c) { return '<button type="button">' + esc(c) + '</button>'; }).join("");
    composer.innerHTML = (chips ? '<div class="chips">' + chips + '</div>' : "") + '<div class="q">↳ ' + esc(snippet(el, 70)) + '</div><div class="r2"><input placeholder="' + (existing ? "Edit note…" : "Add a note…") + '" enterkeyhint="done"/><button class="go" title="Save note">' + ICON_CHECK + '</button></div>';
    document.body.appendChild(composer);
    var inp = composer.querySelector("input");
    if (existing) inp.value = existing.text || "";
    // redraw after the composer is gone + keyboard retracts, so the new pin
    // always lands (fixes "pin sometimes missing right after posting")
    function done() { closeComposer(); el.classList.remove("pr-anchor-live"); setTimeout(render, 60); }
    function save(text) {
      if (!text) { done(); return; }
      if (existing) { existing.text = text; existing.author = reviewer(); state.sent = false; persist(); render(); }
      else addComment(el, text);
      done();
    }
    composer.querySelectorAll(".chips button").forEach(function (b) { b.addEventListener("click", function () { save(b.textContent); }); });
    composer.querySelector(".go").addEventListener("click", function () { save(inp.value.trim()); });
    inp.addEventListener("keydown", function (e) { if (e.key === "Enter") { save(inp.value.trim()); } });
    positionComposer();
    setTimeout(function () { inp.focus(); }, 30);
  }
  function positionComposer() { if (!composer) return; var vv = window.visualViewport; var kb = vv ? Math.max(0, window.innerHeight - (vv.height + vv.offsetTop)) : 0; composer.style.bottom = kb + "px"; }
  function closeComposer() { if (composer) { composer.remove(); composer = null; } if (pill) pill.classList.remove("hide"); }
  if (window.visualViewport) { visualViewport.addEventListener("resize", positionComposer); visualViewport.addEventListener("scroll", positionComposer); }

  function closeCard() { if (cardEl) { cardEl.remove(); cardEl = null; } activeId = null; }
  function openCard(a) {
    closeCard(); activeId = a.id; render();
    var el = locate(a); if (!el) return;
    var r = el.getBoundingClientRect();
    cardEl = document.createElement("div"); cardEl.id = "pr-card";
    cardEl.innerHTML = '<div class="top"><span class="n">' + (order.indexOf(a) + 1) + '</span>' + esc(a.author || "anon") + ' · ' + esc(kindLabel(a)) +
      '<span style="margin-left:auto;display:flex;gap:4px;align-items:center">' +
      (a.kind === "comment" ? '<button class="ed" title="Edit">✎</button>' : "") +
      '<button class="rm" title="Remove">🗑</button><button class="x" title="Close">×</button></span></div>' +
      (a.text ? '<div>' + esc(a.text) + '</div>' : "") + (a.original ? '<div class="was">' + esc(a.original) + '</div>' : "");
    document.body.appendChild(cardEl);
    var cw = cardEl.offsetWidth || 300;
    cardEl.style.left = Math.min(Math.max(8, r.left + window.scrollX), window.innerWidth - cw - 8) + "px";
    cardEl.style.top = r.bottom + window.scrollY + 8 + "px";
    cardEl.querySelector(".x").addEventListener("click", closeCard);
    cardEl.querySelector(".rm").addEventListener("click", function () { closeCard(); removeById(a.id); });
    var ed = cardEl.querySelector(".ed"); if (ed) ed.addEventListener("click", function () { closeCard(); openComposer(el, a); });
  }
  function shortKind(a) {
    var k = a.kind === "comment" ? "note" : a.kind === "answer" ? "answer" : a.kind === "reaction" ? (a.value === "up" ? "👍" : "👎") : a.kind === "approval" ? "approve" : a.kind === "done" ? "done" : a.kind === "reminder" ? "remind" : a.kind;
    if (tabPanels.length) { // flag notes that live on a tab other than the one showing
      var el = locate(a), owner = el && findOwnerTab(el);
      if (owner && owner.label !== activeTab) k += " · " + owner.label;
    }
    return k;
  }
  function openDrawer() {
    closeOverlays(); hideBurgerForOverlay();
    scrim = document.createElement("div"); scrim.id = "pr-scrim"; scrim.addEventListener("click", closeOverlays); document.body.appendChild(scrim);
    menuEl = document.createElement("div"); menuEl.id = "pr-menu";
    menuEl.style.cssText = "left:50%;transform:translateX(-50%);bottom:80px;top:auto;width:min(340px,94vw);max-height:80vh;display:flex;flex-direction:column";
    var cur = getTheme();
    // drawer lists every note across every tab (not just the currently-visible
    // `order`, which only holds the active tab's items) so a tap can jump cross-tab.
    var rows = allAnchored().map(function (a) {
      return '<button class="dr" data-jump="' + a.id + '"><span class="k">' + esc(shortKind(a)) + '</span><span class="t">' + esc(a.text || a.anchorText || "") + '</span></button>';
    }).join("") || '<div style="padding:16px;color:var(--pr-ink2);font-size:13px">' + (IS_MOBILE ? "No notes yet — long-press any line." : "No notes yet — comment or edit any element.") + '</div>';
    // v7.0 — the shortcuts hint that used to sit permanently in the right rail
    // now lives here, desktop-only (mobile has no keyboard to hint at).
    var kbdHint = !IS_MOBILE ? '<div style="padding:2px 14px 10px" class="pr-kbd-hint">Shortcuts: <kbd>C</kbd> comment · <kbd>E</kbd> edit · <kbd>J/K</kbd> step · <kbd>[/]</kbd> tabs · <kbd>&#8984;&crarr;</kbd> send · <kbd>?</kbd> help</div>' : '';
    menuEl.innerHTML =
      '<div style="padding:12px 14px 4px"><input id="pr-name" placeholder="Your name" value="' + esc(state.reviewer) + '" style="width:100%;font-size:16px;padding:11px;border:1px solid var(--pr-bd);border-radius:10px;background:var(--pr-card);color:var(--pr-ink)"></div>' +
      '<div style="padding:6px 14px 2px"><div class="pr-seg4"><button data-th="">Auto</button><button data-th="light">Light</button><button data-th="dark">Dark</button><button data-th="oled">OLED</button></div></div>' +
      kbdHint +
      '<div class="drawer-list">' + rows + '</div>' +
      '<button data-a="ex">Extract JSON<span class="ic">⤓</span></button>' +
      '<button data-a="clear">Clear notes<span class="ic">🗑</span></button>';
    document.body.appendChild(menuEl);
    menuEl.querySelectorAll("[data-th]").forEach(function (b) { b.classList.toggle("on", b.getAttribute("data-th") === cur); });
    var nm = menuEl.querySelector("#pr-name"); nm.addEventListener("input", function () { noteReviewer(nm.value); });
    menuEl.addEventListener("click", function (ev) {
      var th = ev.target.closest("[data-th]");
      if (th) { setTheme(th.getAttribute("data-th")); menuEl.querySelectorAll("[data-th]").forEach(function (b) { b.classList.toggle("on", b === th); }); return; }
      var jr = ev.target.closest("[data-jump]");
      if (jr) {
        var a = allAnchored().filter(function (x) { return x.id === jr.getAttribute("data-jump"); })[0];
        closeOverlays();
        if (a) {
          var el = locate(a);
          var owner = el && findOwnerTab(el);
          if (owner && owner.label !== activeTab) { setActiveTab(owner.label); el = locate(a); } // switch tab before jumping
          scrollAnchorIntoView(el);
          setTimeout(function () { openCard(a); }, 260);
        }
        return;
      }
      var b = ev.target.closest("button[data-a]"); if (!b) return;
      var a2 = b.getAttribute("data-a");
      if (a2 === "ex") { extract(); closeOverlays(); }
      else if (a2 === "clear") { if (confirm("Clear all notes on this page?")) { state.edits.forEach(function (ed) { var el = locate(ed); if (el) { el.textContent = ed.original; el.classList.remove("pr-edited"); } }); state.comments = []; state.edits = []; state.annos = []; state.sent = false; persist(); render(); } closeOverlays(); }
    });
  }

  /* ---- reposition on scroll/resize/mutation ------------------------------- */
  var raf = false;
  function reflow() { if (raf) return; raf = true; requestAnimationFrame(function () { raf = false; if (mo) mo.disconnect(); render(); observe(); }); }
  window.addEventListener("scroll", reflow, true);
  window.addEventListener("resize", reflow);
  var mo = typeof MutationObserver === "function" ? new MutationObserver(function (m) { for (var i = 0; i < m.length; i++) if (!isUi(m[i].target)) { reflow(); return; } }) : null;
  function observe() { if (mo) mo.observe(document.body, { attributes: true, attributeFilter: ["class", "style", "hidden", "aria-hidden"], subtree: true, childList: true }); }

  /* ---- boot --------------------------------------------------------------- */
  document.body.appendChild(pinsLayer);
  buildToolbar();
  initTabs();
  applyEdits();
  render();
  observe();
  window.__proofingRoom = { extract: extract, send: sendToWebhook, render: render, state: state };
})();
