---
name: proofing-room
description: Use when someone wants to review, proof, comment on, mark up, or collect feedback on an HTML page, static site, landing page, slide deck, or generated report — and feed that feedback back to an agent. Drops a self-contained wrapper onto any HTML so reviewers pin comments and edit copy in place, then export an anchored JSON an agent can action. No backend, no build step. Triggers include "add review/proofing mode", "let me comment on this page", "collect feedback on this HTML", "make this markup-able", or "turn review notes into a JSON for an agent".
---

# Proofing Room

## Overview

Proofing Room is a single drop-in script (`proofing-room.js`) that turns **any**
HTML page into a review surface. A human reviewer can pin comments to elements
and edit copy in place; then one button exports an **anchored JSON** describing
every comment and edit, which an agent reads to action the changes. No backend,
no framework, no build step — it's vanilla JS that stores state in
`localStorage`.

**Core loop:** agent builds HTML → human reviews in proofing mode → exports JSON
→ agent applies the feedback. This skill handles both ends: **wiring the wrapper
in**, and **acting on the JSON that comes back**.

Works on both **scrolling pages** (landing pages, reports, long HTML) and
**slide decks** where only one slide renders at a time (display/visibility/
transform/opacity toggling). On a deck, each pin tracks its own slide and is
hidden while that slide is off-screen, and `Extract JSON` maps every slide's
prose — not just the one on screen. (Jumping from the tray to a comment on
another slide auto-navigates reveal.js decks; for other custom deck frameworks,
navigate to the slide yourself, then the pin appears.)

## When to use

- "Add a way for me / a client to comment on this page or site."
- "Let me proof / review / mark up this HTML (landing page, report, deck)."
- "Collect feedback on this generated page and turn it into something you can act on."
- You produced an HTML artifact and want a tight review loop with a human.
- You were handed a `proofing-*.json` file and need to apply the feedback.

## How activation works

The wrapper is **dormant by default**. It only shows the review UI when the URL
carries the `proof` flag, so ordinary visitors never see it:

```
mypage.html?proof              → proofing mode ON
mypage.html                    → normal page (wrapper does nothing)
https://site.com/about?proof   → proofing mode ON
```

`#proof` at the end of the URL also works as a fallback (handy for `file://`
URLs where some browsers drop the query string). `?proof=1` still works too —
the flag just needs to be present.

This means you add **one** unconditional `<script>` tag and the script gates
itself. No conditional loader / no framework shim is required.

## Wiring it in

Pick the case that matches the target. In all cases, copy `proofing-room.js`
(it sits next to this SKILL.md) to where the page can load it.

### A standalone HTML file

1. Copy `proofing-room.js` next to the `.html` file.
2. Add this once, just before `</body>`:
   ```html
   <script src="proofing-room.js"></script>
   ```
3. Tell the user: open the file and add `?proof` to the URL (or use `#proof` if
   opening via `file://`).

### A static site / multi-page site

1. Copy `proofing-room.js` into the served root (e.g. `public/`, `static/`,
   `assets/`).
2. Add `<script src="/proofing-room.js"></script>` to the shared template /
   layout / `<head>` include so every page gets it.
3. Reviewers append `?proof` to any route. Comments are stored per-path, so each
   page keeps its own review set.

### A Next.js / React app

1. Copy `proofing-room.js` into `public/`.
2. Add the tag once in the root layout. Because the script self-gates on
   `?proof`, you do **not** need a conditional client component — just include it:
   ```tsx
   // app/layout.tsx — inside <body>
   <script src="/proofing-room.js" defer />
   ```
   (If a Content-Security-Policy blocks external scripts, host it from the same
   origin as above rather than inlining.)
3. Reviewers visit any route with `?proof`.

> Keep the wrapper a **separate file**, not inlined, so updates are a one-file
> swap and the page's own source stays clean.

## What the reviewer can do (explain this to the user)

- **+ Comment** → click any element to pin a numbered comment to it.
- **✎ Edit text** → click prose to rewrite it in place; the original is kept.
- **Reviewer** field → stamps each comment/edit with a name.
- **Extract JSON** → downloads `proofing-<page>-<date>.json` (the handoff file).
- **Collapse** (click the header) → shrinks to a floating toolbar that keeps the
  Comment / Edit / Extract buttons but hides the comment list, so it covers less
  of the page.
- **Drag** the header → move the panel anywhere; position is remembered.
- A thick plum **border + "Proofing mode" badge** signal the page is in review.
- Everything persists in `localStorage` per page path, so a reload is safe.

## The JSON contract

`Extract JSON` downloads an object shaped like this:

```jsonc
{
  "tool": "proofing-room",
  "version": "4",
  "url": "https://site.com/about?proof",
  "path": "/about",
  "title": "About",
  "extractedAt": "2026-06-15T10:30:00.000Z",
  "reviewers": ["Nick", "Lucas"],
  "comments": [
    {
      "id": "c1",
      "author": "Nick",
      "text": "Tighten this to one line — too wordy.",
      "createdAt": "…",
      "anchorText": "Body copy",      // visible text of the element
      "section": "Things you can review", // nearest heading above it
      "selector": "main > section:nth-of-type(2) > … > h3:nth-of-type(1)",
      "tag": "h3"
    }
  ],
  "edits": [
    {
      "id": "e1",
      "author": "Lucas",
      "original": "old copy",
      "text": "new copy",            // the reviewer's rewrite
      "createdAt": "…",
      "section": "…", "selector": "…", "tag": "p"
    }
  ],
  "document": [
    // flattened prose map of the page, each block with any comments attached:
    { "tag": "h3", "text": "Body copy", "selector": "…",
      "comments": [ { "author": "Nick", "text": "Tighten this…" } ],
      "edited": false }
  ]
}
```

## Acting on extracted JSON (the agent side)

When you're given a `proofing-*.json`:

1. **Locate each target** by `selector` first (precise), falling back to
   `anchorText` + `tag` if the selector no longer matches (the DOM may have
   changed since extraction). `section` helps you orient.
2. **Apply `edits`** literally — replace the element's text `original` → `text`.
   Treat these as approved copy changes unless the user says otherwise.
3. **Action `comments`** as instructions/requests against their anchored element.
   They're feedback, not literal replacements — interpret and implement, then
   report what you changed per comment `id`.
4. **Attribute** changes to `reviewers` where relevant, and confirm anything
   ambiguous or destructive with the user before applying.
5. The `document` array is a convenience map of all prose blocks with their
   comments already attached — use it to review the page holistically.

## Files in this skill

- `proofing-room.js` — the drop-in wrapper (the artifact you copy in).
- `example.html` — a demo page that loads the wrapper; open it with `?proof` to
  see the tool, or use it to verify a change.
- `README.md` — human-facing setup notes.
