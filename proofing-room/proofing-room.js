/* ============================================================================
 * proofing-room.js — drop-in comment + extract wrapper for ANY html page.
 *
 * Usage: add  <script src="proofing-room.js"></script>  to any page, once.
 * The script stays DORMANT until proofing mode is switched on, so ordinary
 * visitors never see it. Switch it on by adding ?proof to the URL:
 *
 *     mypage.html?proof          → proofing ON
 *     mypage.html                → normal page
 *     https://site.com/about?proof   → proofing ON
 *
 * (#proof at the end of the URL also works, as a fallback for file:// URLs
 *  where some browsers drop the query string. ?proof=1 still works too.)
 *
 * In proofing mode, reviewers pin comments anywhere, edit copy in place, then
 * "Extract JSON" downloads an anchored review file an agent can process. No
 * backend. Comments/edits persist in localStorage per page path so a reload
 * doesn't lose them. Works on scrolling pages AND slide decks where only one
 * slide renders at a time (display:none / visibility / transform / opacity):
 * pins track their slide and hide while their slide is off-screen.
 *
 * Downloaded JSON:
 * { tool, version, url, title, path, extractedAt, reviewers[],
 *   comments[ {id,author,text,createdAt,anchorText,section,selector,tag} ],
 *   edits[ {id,author,original,text,createdAt,section,selector,tag} ],
 *   document[ {tag,text,selector,comments[{author,text}],edited?,original?} ] }
 *
 * v4 (2026-06-15): slide-deck support — a MutationObserver repositions pins on
 * slide changes (not just scroll/resize), pins for off-screen/hidden slides are
 * hidden instead of piling in the corner, and Extract maps every slide's prose
 * (not only the visible one). jumpTo navigates known deck frameworks too.
 * v3 (2026-06-15): self-gating on ?proof (no React shim needed), collapse to a
 * floating toolbar that keeps the Comment/Edit/Extract buttons while hiding the
 * list, and drag the header to move the panel anywhere (position persists).
 * v2 (2026-06-12): right-docked panel, expandable comments tray, sapphire+plum
 * styling, thick plum page border signalling proofing mode.
 * ========================================================================== */
(function () {
  "use strict";
  if (window.__proofingRoom) return;

  /* ---- gate: do nothing unless proofing mode is requested ----------------- */
  try {
    var sp = new URLSearchParams(location.search);
    if (!sp.has("proof") && location.hash !== "#proof") return;
  } catch (e) {
    if (location.search.indexOf("proof") < 0 && location.hash !== "#proof") return;
  }

  var KEY = "proofing-room:" + location.pathname;
  var POS_KEY = "proofing-room:pos";
  var COLLAPSE_KEY = "proofing-room:collapsed";
  var state = {
    reviewer: localStorage.getItem("proofing-room:reviewer") || "",
    commenting: false,
    editing: false,
    open: localStorage.getItem(COLLAPSE_KEY) !== "1",
    comments: [],
    edits: [],
    seq: 0,
  };
  try {
    var saved = JSON.parse(localStorage.getItem(KEY) || "{}");
    if (Array.isArray(saved.comments)) state.comments = saved.comments;
    if (Array.isArray(saved.edits)) state.edits = saved.edits;
    if (typeof saved.seq === "number") state.seq = saved.seq;
  } catch (e) {}

  function persist() {
    localStorage.setItem(
      KEY,
      JSON.stringify({ comments: state.comments, edits: state.edits, seq: state.seq })
    );
  }

  /* ---- element helpers ---------------------------------------------------- */
  function isUi(el) {
    return !!(el.closest && el.closest("#pr-root, #pr-pins, #pr-pop, #pr-border, #pr-badge"));
  }
  /* Is el actually on-screen right now? Decks hide inactive slides via
     display:none / visibility / opacity:0 / off-screen transforms; an anchor on
     such a slide must NOT get a pin (it would land in the corner or over the
     wrong slide). getClientRects() is empty for display:none; checkVisibility()
     (where supported) also catches visibility/opacity/content-visibility. */
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
    if (cs.display === "none" || cs.visibility === "hidden" || cs.visibility === "collapse" || cs.opacity === "0")
      return false;
    var r = el.getBoundingClientRect();
    return r.width > 0 || r.height > 0;
  }
  function selectorFor(el) {
    if (!el || el === document.body) return "body";
    var parts = [];
    while (el && el.nodeType === 1 && el !== document.body && parts.length < 8) {
      var tag = el.tagName.toLowerCase();
      if (el.id) {
        parts.unshift(tag + "#" + CSS.escape(el.id));
        break;
      }
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
      while (sib) {
        if (/^H[1-6]$/.test(sib.tagName || "")) return snippet(sib, 80);
        sib = sib.previousElementSibling;
      }
      cur = cur.parentElement;
    }
    var h = document.querySelector("h1");
    return h ? snippet(h, 80) : document.title;
  }

  /* ---- styles (SapphireOS sapphire + ClimatePulse plum) ------------------- */
  var SAPPHIRE = "#306FA8", SAPPHIRE_DEEP = "#1E4C80";
  var PLUM = "#3D1F3D", PLUM_MID = "#6B4A6B", PLUM_TINT = "#F5EEF5";
  var css =
    "#pr-root,#pr-pop,#pr-badge{font-family:ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif}" +
    /* thick proofing-mode page border + badge (stay put regardless of panel) */
    "#pr-border{position:fixed;inset:0;border:7px solid " + PLUM + ";pointer-events:none;z-index:2147481000}" +
    "#pr-badge{position:fixed;top:0;left:50%;transform:translateX(-50%);z-index:2147481500;" +
    "background:" + PLUM + ";color:#fff;font-size:10px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;" +
    "padding:5px 16px;border-radius:0 0 9px 9px;box-shadow:0 2px 10px rgba(61,31,61,.4)}" +
    "#pr-badge .d{display:inline-block;width:6px;height:6px;border-radius:50%;background:#e7b6e7;margin-right:7px;vertical-align:middle}" +
    /* right-docked panel */
    "#pr-root{position:fixed;right:14px;top:84px;z-index:2147483000;width:326px;max-height:calc(100vh - 104px);" +
    "display:flex;flex-direction:column;background:#fff;color:" + PLUM + ";border:1px solid #e6dbe6;" +
    "border-radius:14px;box-shadow:0 18px 50px rgba(61,31,61,.28);overflow:hidden}" +
    "#pr-root.pr-dragging{user-select:none;box-shadow:0 24px 64px rgba(61,31,61,.4)}" +
    "#pr-root *{box-sizing:border-box}" +
    "#pr-hd{display:flex;align-items:center;gap:9px;padding:12px 14px;background:" + PLUM + ";color:#fff;cursor:grab;" +
    "font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;font-weight:800;user-select:none}" +
    "#pr-root.pr-dragging #pr-hd{cursor:grabbing}" +
    "#pr-hd .grip{letter-spacing:1px;opacity:.55;margin-right:-3px}" +
    "#pr-hd .d{width:8px;height:8px;border-radius:50%;background:#e7b6e7}" +
    "#pr-hd .cnt{margin-left:auto;background:rgba(255,255,255,.18);border-radius:99px;padding:2px 9px;font-size:11px;letter-spacing:0}" +
    "#pr-hd .chev{transition:transform .18s ease;opacity:.85}#pr-root.collapsed #pr-hd .chev{transform:rotate(-90deg)}" +
    "#pr-controls{padding:13px 14px;display:flex;flex-direction:column;gap:10px;border-bottom:1px solid #efe6ef}" +
    "#pr-root.collapsed #pr-controls{border-bottom:none;padding-bottom:13px}" +
    "#pr-controls label{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:" + PLUM_MID + ";display:block;margin-bottom:4px}" +
    "#pr-name{width:100%;border:1px solid #ddcedd;color:" + PLUM + ";border-radius:8px;padding:8px 10px;font-size:13px}" +
    "#pr-name:focus{outline:none;border-color:" + SAPPHIRE + ";box-shadow:0 0 0 3px rgba(48,111,168,.18)}" +
    "#pr-btns{display:flex;gap:8px}.pr-b{flex:1;border:none;border-radius:8px;padding:9px 10px;font-size:12.5px;font-weight:700;cursor:pointer}" +
    ".pr-b.add{background:" + SAPPHIRE + ";color:#fff}.pr-b.add:hover{background:" + SAPPHIRE_DEEP + "}" +
    ".pr-b.add.active{background:" + PLUM + "}" +
    ".pr-b.ex{background:" + PLUM + ";color:#fff}.pr-b.ex:hover{background:" + PLUM_MID + "}" +
    ".pr-b.gh{background:" + PLUM_TINT + ";color:" + PLUM_MID + "}.pr-b.gh:hover{background:#ecdfec}" +
    ".pr-b.edit{background:#EEF4FA;color:" + SAPPHIRE_DEEP + "}.pr-b.edit:hover{background:#dbe8f3}.pr-b.edit.active{background:" + SAPPHIRE + ";color:#fff}" +
    '[contenteditable="true"].pr-editing-el{outline:2px solid ' + SAPPHIRE + "!important;outline-offset:2px;background:rgba(48,111,168,.06)!important}" +
    ".pr-edited{outline:1.5px dashed " + PLUM_MID + "!important;outline-offset:2px}" +
    ".pr-row.edit{border-left-color:" + SAPPHIRE + "}.pr-row.edit .pn{background:" + SAPPHIRE + "}.pr-row .was{margin-top:5px;font-size:11px;color:" + PLUM_MID + ";text-decoration:line-through}" +
    "#pr-list{overflow-y:auto;padding:8px;display:flex;flex-direction:column;gap:8px;background:#fbf7fb}" +
    /* collapsed → floating toolbar: keep Comment/Edit/Extract, hide the rest */
    "#pr-root.collapsed #pr-list,#pr-root.collapsed #pr-name-wrap,#pr-root.collapsed #pr-clear{display:none}" +
    "#pr-empty{padding:18px 10px;text-align:center;font-size:12px;color:" + PLUM_MID + "}" +
    ".pr-row{background:#fff;border:1px solid #efe6ef;border-left:3px solid " + PLUM + ";border-radius:9px;padding:10px 11px;cursor:pointer;transition:box-shadow .15s ease}" +
    ".pr-row:hover{box-shadow:0 4px 14px rgba(61,31,61,.12)}" +
    ".pr-row .top{display:flex;align-items:center;gap:8px;margin-bottom:5px}" +
    ".pr-row .pn{width:20px;height:20px;border-radius:50%;background:" + PLUM + ";color:#fff;font-size:11px;font-weight:800;display:flex;align-items:center;justify-content:center;flex:none}" +
    ".pr-row .who{font-size:11px;font-weight:700;color:" + PLUM + "}" +
    ".pr-row .del{margin-left:auto;color:#b08bb0;font-size:15px;line-height:1;background:none;border:none;cursor:pointer;padding:0 2px}" +
    ".pr-row .del:hover{color:#9a2e26}" +
    ".pr-row .txt{font-size:12.5px;line-height:1.45;color:#2a1a2a}" +
    ".pr-row .anchor{margin-top:6px;font-size:10px;color:" + PLUM_MID + ";letter-spacing:.02em;line-height:1.4}" +
    ".pr-row .anchor b{color:" + SAPPHIRE_DEEP + ";font-weight:700}" +
    "body.pr-commenting *{cursor:crosshair!important}" +
    ".pr-hl{outline:2px dashed " + SAPPHIRE + "!important;outline-offset:1px!important}" +
    ".pr-flash{animation:prflash 1.4s ease}@keyframes prflash{0%,100%{box-shadow:0 0 0 0 rgba(61,31,61,0)}30%{box-shadow:0 0 0 4px rgba(61,31,61,.45)}}" +
    "#pr-pins{position:absolute;top:0;left:0;width:0;height:0;z-index:2147482000}" +
    ".pr-pin{position:absolute;width:24px;height:24px;border-radius:50%;background:" + PLUM + ";color:#fff;font-size:11px;font-weight:800;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 9px rgba(61,31,61,.45);cursor:pointer;transform:translate(-50%,-50%);border:2px solid #fff}" +
    ".pr-pin:hover{background:" + PLUM_MID + "}" +
    "#pr-pop{position:absolute;z-index:2147483600;width:248px;background:#fff;color:" + PLUM + ";border-radius:11px;box-shadow:0 14px 40px rgba(61,31,61,.3);border:1px solid #e6dbe6;padding:13px}" +
    "#pr-pop textarea{width:100%;height:74px;border:1px solid #ddcedd;border-radius:8px;padding:8px;font:inherit;font-size:13px;resize:vertical;color:" + PLUM + "}" +
    "#pr-pop textarea:focus{outline:none;border-color:" + SAPPHIRE + "}" +
    "#pr-pop .meta{font-size:10.5px;color:" + PLUM_MID + ";margin:0 0 8px;line-height:1.4}" +
    "#pr-pop .meta b{color:" + SAPPHIRE_DEEP + "}" +
    "#pr-pop .row{display:flex;gap:8px;margin-top:9px}" +
    "#pr-pop button{flex:1;border:none;border-radius:8px;padding:8px;font-size:12.5px;font-weight:700;cursor:pointer}" +
    "#pr-pop .save{background:" + SAPPHIRE + ";color:#fff}#pr-pop .del{background:#f4e3ec;color:#9a2e26}#pr-pop .cancel{background:" + PLUM_TINT + ";color:" + PLUM_MID + "}";

  var styleEl = document.createElement("style");
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  /* ---- chrome: border, badge, panel, pins --------------------------------- */
  var border = document.createElement("div");
  border.id = "pr-border";
  document.body.appendChild(border);
  var badge = document.createElement("div");
  badge.id = "pr-badge";
  badge.innerHTML = '<span class="d"></span>Proofing mode';
  document.body.appendChild(badge);

  var root = document.createElement("div");
  root.id = "pr-root";
  if (!state.open) root.classList.add("collapsed");
  root.innerHTML =
    '<div id="pr-hd"><span class="grip">⠿</span><span class="d"></span>Proofing room<span class="cnt" id="pr-cnt">0</span>' +
    '<span class="chev">▾</span></div>' +
    '<div id="pr-controls">' +
    '<div id="pr-name-wrap"><label>Reviewer</label><input id="pr-name" placeholder="Your name" autocomplete="off" /></div>' +
    '<div id="pr-btns"><button class="pr-b add" id="pr-add">+ Comment</button>' +
    '<button class="pr-b edit" id="pr-edit">✎ Edit text</button></div>' +
    '<button class="pr-b ex" id="pr-ex">Extract JSON</button>' +
    '<button class="pr-b gh" id="pr-clear">Clear all</button>' +
    "</div>" +
    '<div id="pr-list"></div>';
  document.body.appendChild(root);

  var pins = document.createElement("div");
  pins.id = "pr-pins";
  document.body.appendChild(pins);

  var nameInput = root.querySelector("#pr-name");
  nameInput.value = state.reviewer;
  nameInput.addEventListener("input", function () {
    state.reviewer = nameInput.value.trim();
    localStorage.setItem("proofing-room:reviewer", state.reviewer);
  });

  /* ---- collapse + drag the header ----------------------------------------- */
  function setCollapsed(collapsed) {
    state.open = !collapsed;
    root.classList.toggle("collapsed", collapsed);
    localStorage.setItem(COLLAPSE_KEY, collapsed ? "1" : "");
  }
  function clampPos() {
    if (root.style.left === "" || root.style.left === "auto") return;
    var w = root.offsetWidth, left = parseFloat(root.style.left), top = parseFloat(root.style.top);
    left = Math.min(Math.max(6, left), Math.max(6, window.innerWidth - w - 6));
    top = Math.min(Math.max(6, top), Math.max(6, window.innerHeight - 44));
    root.style.left = left + "px";
    root.style.top = top + "px";
  }
  function applyPos(left, top) {
    root.style.right = "auto";
    root.style.left = left + "px";
    root.style.top = top + "px";
    clampPos();
  }
  try {
    var pos = JSON.parse(localStorage.getItem(POS_KEY) || "null");
    if (pos && typeof pos.left === "number") applyPos(pos.left, pos.top);
  } catch (e) {}

  var hd = root.querySelector("#pr-hd");
  var drag = { active: false, moved: false, sx: 0, sy: 0, ox: 0, oy: 0 };
  hd.addEventListener("mousedown", function (e) {
    if (e.button !== 0) return;
    drag.active = true;
    drag.moved = false;
    drag.sx = e.clientX;
    drag.sy = e.clientY;
    var r = root.getBoundingClientRect();
    drag.ox = r.left;
    drag.oy = r.top;
    e.preventDefault();
  });
  document.addEventListener("mousemove", function (e) {
    if (!drag.active) return;
    var dx = e.clientX - drag.sx, dy = e.clientY - drag.sy;
    if (!drag.moved && Math.abs(dx) + Math.abs(dy) < 4) return; // threshold: click vs drag
    drag.moved = true;
    root.classList.add("pr-dragging");
    applyPos(drag.ox + dx, drag.oy + dy);
  });
  document.addEventListener("mouseup", function () {
    if (!drag.active) return;
    drag.active = false;
    if (drag.moved) {
      root.classList.remove("pr-dragging");
      localStorage.setItem(POS_KEY, JSON.stringify({ left: parseFloat(root.style.left), top: parseFloat(root.style.top) }));
    } else {
      setCollapsed(state.open); // no movement → treat as a click, toggle collapse
    }
  });

  var addBtn = root.querySelector("#pr-add");
  var editBtn = root.querySelector("#pr-edit");
  addBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    setCommenting(!state.commenting);
  });
  editBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    setEditing(!state.editing);
  });
  root.querySelector("#pr-ex").addEventListener("click", function (e) {
    e.stopPropagation();
    extract();
  });
  root.querySelector("#pr-clear").addEventListener("click", function (e) {
    e.stopPropagation();
    if (!state.comments.length && !state.edits.length) return;
    if (confirm("Clear all comments and edits on this page?")) {
      state.comments = [];
      state.edits.forEach(function (ed) {
        var el = locate(ed);
        if (el) { el.textContent = ed.original; el.classList.remove("pr-edited"); el.removeAttribute("data-pr-orig"); }
      });
      state.edits = [];
      persist();
      render();
    }
  });

  function setCommenting(on) {
    if (on && state.editing) setEditing(false);
    state.commenting = on;
    document.body.classList.toggle("pr-commenting", on);
    addBtn.classList.toggle("active", on);
    addBtn.textContent = on ? "Click an element… (Esc)" : "+ Comment";
  }
  function setEditing(on) {
    if (on && state.commenting) setCommenting(false);
    state.editing = on;
    document.body.classList.toggle("pr-editing", on);
    editBtn.classList.toggle("active", on);
    editBtn.textContent = on ? "Editing… (Esc)" : "✎ Edit text";
  }

  /* ---- inline text editing ------------------------------------------------ */
  function isEditable(el) {
    if (!el || isUi(el)) return false;
    var t = el.tagName;
    if (/^(P|H[1-6]|LI|BLOCKQUOTE|FIGCAPTION|SPAN|A|BUTTON|TD|TH|DT|DD|EM|STRONG|CITE|SMALL|LABEL)$/.test(t))
      return (el.innerText || "").trim().length > 0;
    if (t === "DIV" && el.children.length === 0 && (el.innerText || "").trim()) return true;
    return false;
  }
  function upsertEdit(el, orig, now) {
    var s = selectorFor(el);
    var ex = state.edits.filter(function (x) { return x.selector === s; })[0];
    if (ex) {
      ex.text = now;
      ex.author = state.reviewer || ex.author || "anon";
    } else {
      state.seq++;
      state.edits.push({
        id: "e" + state.seq, kind: "edit", author: state.reviewer || "anon",
        original: orig, text: now, createdAt: new Date().toISOString(),
        section: nearestSection(el), selector: s, tag: el.tagName.toLowerCase(),
      });
    }
    persist();
    render();
  }
  function removeEditBySelector(s) {
    var n = state.edits.length;
    state.edits = state.edits.filter(function (x) { return x.selector !== s; });
    if (state.edits.length !== n) { persist(); render(); }
  }
  function removeEdit(id) {
    var e = state.edits.filter(function (x) { return x.id === id; })[0];
    if (e) {
      var el = locate(e);
      if (el) { el.textContent = e.original; el.classList.remove("pr-edited"); el.removeAttribute("data-pr-orig"); }
    }
    state.edits = state.edits.filter(function (x) { return x.id !== id; });
    persist();
    render();
  }
  function applyEdits() {
    state.edits.forEach(function (e) {
      var el = locate(e);
      if (!el) return;
      if (el.getAttribute("data-pr-orig") === null) el.setAttribute("data-pr-orig", e.original);
      if ((el.innerText || "").trim() !== e.text) el.textContent = e.text;
      el.classList.add("pr-edited");
    });
  }
  document.addEventListener("click", function (e) {
    if (!state.editing || isUi(e.target) || !isEditable(e.target)) return;
    e.preventDefault();
    e.stopPropagation();
    var el = e.target;
    if (el.getAttribute("data-pr-orig") === null)
      el.setAttribute("data-pr-orig", (el.innerText || "").trim());
    el.setAttribute("contenteditable", "true");
    el.classList.add("pr-editing-el");
    el.focus();
  }, true);
  document.addEventListener("blur", function (e) {
    var el = e.target;
    if (!el || !el.getAttribute || el.getAttribute("contenteditable") !== "true") return;
    if (el.getAttribute("data-pr-orig") === null) return;
    el.removeAttribute("contenteditable");
    el.classList.remove("pr-editing-el");
    var orig = el.getAttribute("data-pr-orig");
    var now = (el.innerText || "").trim();
    if (now !== orig) { upsertEdit(el, orig, now); el.classList.add("pr-edited"); }
    else { removeEditBySelector(selectorFor(el)); el.classList.remove("pr-edited"); el.removeAttribute("data-pr-orig"); }
  }, true);

  /* ---- comment capture ---------------------------------------------------- */
  var hoverEl = null;
  document.addEventListener(
    "mouseover",
    function (e) {
      if (!state.commenting || isUi(e.target)) return;
      if (hoverEl) hoverEl.classList.remove("pr-hl");
      hoverEl = e.target;
      hoverEl.classList.add("pr-hl");
    },
    true
  );
  document.addEventListener(
    "click",
    function (e) {
      if (!state.commenting || isUi(e.target)) return;
      e.preventDefault();
      e.stopPropagation();
      if (hoverEl) hoverEl.classList.remove("pr-hl");
      openPopover(e.target, e.clientX, e.clientY, null);
      setCommenting(false);
    },
    true
  );
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      if (state.commenting) setCommenting(false);
      if (state.editing) {
        var ce = document.querySelector('[contenteditable="true"].pr-editing-el');
        if (ce) ce.blur();
        else setEditing(false);
      }
      closePopover();
    }
  });

  /* ---- popover (create / edit) ------------------------------------------- */
  var pop = null;
  function closePopover() {
    if (pop) {
      pop.remove();
      pop = null;
    }
  }
  function openPopover(el, x, y, existing) {
    closePopover();
    pop = document.createElement("div");
    pop.id = "pr-pop";
    var meta = existing
      ? "On: <b>" + esc(existing.anchorText || existing.tag) + "</b>"
      : "On &lt;" + el.tagName.toLowerCase() + "&gt;: <b>" + esc(snippet(el, 70)) + "</b>";
    pop.innerHTML =
      '<div class="meta">' + meta + "</div>" +
      '<textarea placeholder="Your comment…"></textarea>' +
      '<div class="row"><button class="save">Save</button>' +
      (existing ? '<button class="del">Delete</button>' : "") +
      '<button class="cancel">Cancel</button></div>';
    document.body.appendChild(pop);
    var px = Math.min(Math.max(8, x + 8), window.innerWidth - 264);
    var py = Math.min(Math.max(8, y + 8), window.innerHeight - 180);
    pop.style.left = px + window.scrollX + "px";
    pop.style.top = py + window.scrollY + "px";
    var ta = pop.querySelector("textarea");
    ta.value = existing ? existing.text : "";
    ta.focus();
    pop.querySelector(".save").addEventListener("click", function () {
      var text = ta.value.trim();
      if (!text) return closePopover();
      if (existing) {
        existing.text = text;
        existing.author = state.reviewer || existing.author || "anon";
      } else {
        state.seq++;
        state.comments.push({
          id: "c" + state.seq,
          author: state.reviewer || "anon",
          text: text,
          createdAt: new Date().toISOString(),
          anchorText: snippet(el, 140),
          section: nearestSection(el),
          selector: selectorFor(el),
          tag: el.tagName.toLowerCase(),
        });
      }
      persist();
      render();
      closePopover();
    });
    if (existing)
      pop.querySelector(".del").addEventListener("click", function () {
        removeComment(existing.id);
        closePopover();
      });
    pop.querySelector(".cancel").addEventListener("click", closePopover);
  }

  function removeComment(id) {
    state.comments = state.comments.filter(function (c) {
      return c.id !== id;
    });
    persist();
    render();
  }

  /* ---- locate / jump ------------------------------------------------------ */
  function locate(c) {
    try {
      var el = document.querySelector(c.selector);
      if (el) return el;
    } catch (e) {}
    var nodes = document.getElementsByTagName(c.tag || "*");
    for (var i = 0; i < nodes.length; i++) {
      if (snippet(nodes[i], 140) === c.anchorText) return nodes[i];
    }
    return null;
  }
  function tryRevealSlide(el) {
    // reveal.js: drive the deck to the slide containing el (clean public API,
    // keeps the deck's own index/counter in sync). Other custom decks vary too
    // much to navigate generically — scrollIntoView still helps lazy-mount ones.
    try {
      if (window.Reveal && typeof Reveal.getIndices === "function" && typeof Reveal.slide === "function") {
        var sec = el.closest(".slides section, section");
        if (sec) { var idx = Reveal.getIndices(sec); if (idx) { Reveal.slide(idx.h, idx.v, idx.f); return true; } }
      }
    } catch (e) {}
    return false;
  }
  function jumpTo(c) {
    var el = locate(c);
    if (!el) return;
    if (!isVisible(el)) tryRevealSlide(el); // off-screen deck slide: drive the framework if we recognise it
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    var flash = function () {
      el.classList.add("pr-flash");
      setTimeout(function () { el.classList.remove("pr-flash"); }, 1500);
    };
    if (isVisible(el)) flash();
    else setTimeout(flash, 260); // allow a slide transition to land, then flash
  }

  /* ---- render pins + list ------------------------------------------------- */
  function render() {
    root.querySelector("#pr-cnt").textContent = state.comments.length + state.edits.length;
    // pins
    pins.innerHTML = "";
    state.comments.forEach(function (c, i) {
      var el = locate(c);
      if (!el || !isVisible(el)) return; // anchor on a hidden/off-screen slide → no pin
      var r = el.getBoundingClientRect();
      var pin = document.createElement("div");
      pin.className = "pr-pin";
      pin.textContent = i + 1;
      pin.title = (c.author || "anon") + ": " + c.text;
      pin.style.left = r.right + window.scrollX - 4 + "px";
      pin.style.top = r.top + window.scrollY + 11 + "px";
      pin.addEventListener("click", function (ev) {
        ev.stopPropagation();
        openPopover(el, r.right - 248, r.top, c);
      });
      pins.appendChild(pin);
    });
    // tray list (comments + edits)
    var list = root.querySelector("#pr-list");
    list.innerHTML = "";
    if (!state.comments.length && !state.edits.length) {
      list.innerHTML =
        '<div id="pr-empty">Nothing yet. <b>+ Comment</b> to pin a note, or <b>✎ Edit text</b> to change copy in place.</div>';
      return;
    }
    state.comments.forEach(function (c, i) {
      var row = document.createElement("div");
      row.className = "pr-row";
      row.innerHTML =
        '<div class="top"><span class="pn">' + (i + 1) + "</span>" +
        '<span class="who">' + esc(c.author || "anon") + "</span>" +
        '<button class="del" title="Delete">&times;</button></div>' +
        '<div class="txt">' + esc(c.text) + "</div>" +
        '<div class="anchor"><b>' + esc(c.section || "") + "</b> · " + esc((c.tag || "") + " · " + (c.anchorText || "")) + "</div>";
      row.addEventListener("click", function () { jumpTo(c); });
      row.querySelector(".del").addEventListener("click", function (ev) {
        ev.stopPropagation();
        removeComment(c.id);
      });
      list.appendChild(row);
    });
    state.edits.forEach(function (e) {
      var row = document.createElement("div");
      row.className = "pr-row edit";
      row.innerHTML =
        '<div class="top"><span class="pn">✎</span>' +
        '<span class="who">' + esc(e.author || "anon") + " · edit</span>" +
        '<button class="del" title="Revert edit">&times;</button></div>' +
        '<div class="txt">' + esc(e.text) + "</div>" +
        '<div class="was">' + esc(e.original) + "</div>" +
        '<div class="anchor"><b>' + esc(e.section || "") + "</b> · " + esc(e.tag || "") + "</div>";
      row.addEventListener("click", function () { jumpTo(e); });
      row.querySelector(".del").addEventListener("click", function (ev) {
        ev.stopPropagation();
        removeEdit(e.id);
      });
      list.appendChild(row);
    });
  }

  var rafPending = false;
  function scheduleReposition() {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(function () {
      rafPending = false;
      if (mo) mo.disconnect(); // render() mutates our UI — don't observe our own writes
      clampPos();
      render();
      observe();
    });
  }
  window.addEventListener("scroll", scheduleReposition, true); // capture: catches inner-scroll containers too
  window.addEventListener("resize", scheduleReposition);

  /* Slide decks change the active slide with no scroll/resize event — they
     toggle class/style/hidden or swap nodes. Watch the document for those and
     reposition, so pins follow the deck. Coalesced to one pass per frame via
     scheduleReposition; the observer is disconnected during render() so our own
     pin/list writes don't retrigger it. */
  var mo = typeof MutationObserver === "function" ? new MutationObserver(function (muts) {
    for (var i = 0; i < muts.length; i++) {
      if (!isUi(muts[i].target)) { scheduleReposition(); return; }
    }
  }) : null;
  function observe() {
    if (!mo) return;
    mo.observe(document.body, {
      attributes: true, attributeFilter: ["class", "style", "hidden", "aria-hidden"],
      subtree: true, childList: true,
    });
  }
  observe();

  /* ---- extract / download ------------------------------------------------- */
  function buildDocument() {
    var STD = /^(H[1-6]|P|LI|BLOCKQUOTE|FIGCAPTION|BUTTON|A)$/;
    var LEAF = /^(DIV|SPAN|TD|TH|DT|DD)$/;
    var PROSE = "p,li,h1,h2,h3,h4,h5,h6,blockquote,figcaption,button,a";
    var out = [];
    Array.prototype.forEach.call(document.body.querySelectorAll("*"), function (n) {
      if (isUi(n)) return;
      var tag = n.tagName;
      var take = STD.test(tag) || (LEAF.test(tag) && n.children.length === 0 && !n.closest(PROSE));
      if (!take) return;
      var text = snippet(n, 400);
      if (!text) { // hidden slide: innerText is "" under display:none → use raw text so every slide is mapped
        text = (n.textContent || "").replace(/\s+/g, " ").trim();
        if (text.length > 400) text = text.slice(0, 399) + "…";
      }
      if (!text) return;
      var s = selectorFor(n);
      var cs = state.comments
        .filter(function (c) {
          return c.selector === s;
        })
        .map(function (c) {
          return { author: c.author, text: c.text };
        });
      var item = { tag: n.tagName.toLowerCase(), text: text, selector: s, comments: cs };
      var ed = state.edits.filter(function (x) { return x.selector === s; })[0];
      if (ed) {
        item.edited = true;
        item.original = ed.original;
        item.editedBy = ed.author;
      }
      out.push(item);
    });
    return out;
  }
  function extract() {
    var reviewers = [];
    function noteR(a) { if (a && reviewers.indexOf(a) < 0) reviewers.push(a); }
    state.comments.forEach(function (c) { noteR(c.author); });
    state.edits.forEach(function (e) { noteR(e.author); });
    noteR(state.reviewer);
    var data = {
      tool: "proofing-room",
      version: "4",
      url: location.href,
      path: location.pathname,
      title: document.title,
      extractedAt: new Date().toISOString(),
      reviewers: reviewers,
      comments: state.comments,
      edits: state.edits,
      document: buildDocument(),
    };
    var blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    var a = document.createElement("a");
    var slug = location.pathname.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "") || "home";
    a.href = URL.createObjectURL(blob);
    a.download = "proofing-" + slug + "-" + new Date().toISOString().slice(0, 10) + ".json";
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  function esc(s) {
    return (s || "").replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  }

  applyEdits();
  render();
  window.__proofingRoom = { extract: extract, render: render, state: state };
})();
