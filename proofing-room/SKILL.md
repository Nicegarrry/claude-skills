---
name: proofing-room
description: Use when someone wants to review, proof, comment on, mark up, or collect feedback on an HTML page, static site, landing page, slide deck, or generated report — on desktop OR mobile — and feed that feedback back to an agent. Drops a self-contained wrapper onto any HTML so reviewers comment, edit copy in place, answer inline yes/no or scale questions, tick off to-dos, approve sections, react, and set reminders — then export (or optionally send) an anchored JSON an agent can action. No backend, no build step. Triggers include "add review/proofing mode", "let me comment on this page", "collect feedback on this HTML", "make this markup-able for a client/reviewer", or "turn review notes into a JSON for an agent".
---

# Proofing Room

## Overview

Proofing Room is a single drop-in script (`proofing-room.js`) that turns **any**
HTML page into a review surface — on desktop and on mobile. A reviewer can pin
comments, edit copy in place, answer inline questions the page declares
(yes/no, a slider, a checkbox), react to anything, approve a whole section,
and set a reminder — then export an **anchored JSON** describing everything,
which an agent reads to action the feedback. No backend, no framework, no
build step — it's vanilla JS that stores state in `localStorage`.

**Core loop:** agent builds HTML → human reviews in proofing mode (phone or
desktop) → exports (or sends) JSON → agent applies the feedback. This skill
handles both ends: **wiring the wrapper in**, and **acting on the JSON that
comes back**.

Works on scrolling pages (landing pages, reports, long HTML), slide decks
(only one slide visible at a time — pins track their own slide), and
multi-tab pages (the page can declare more than one "brief" and the layer
builds a tab bar automatically — see [Tabs](#tabs) below).

## When to use

- "Add a way for me / a client to comment on this page or site."
- "Let me proof / review / mark up this HTML (landing page, report, deck) —
  from my phone."
- "Collect feedback on this generated page and turn it into something you can act on."
- You produced an HTML artifact and want a tight review loop with a human.
- You want the reviewer to answer specific questions in place (yes/no, a
  rating, a checkbox), not just leave free-text comments.
- You were handed a `proofing-*.json` file and need to apply the feedback.

## How activation works

The wrapper is **dormant by default**. It only shows the review UI when the
URL carries the `proof` flag, so ordinary visitors never see it:

```
mypage.html?proof              → proofing mode ON (desktop layout)
mypage.html?proof=mobile       → proofing mode ON, forcing the mobile "Hairline"
                                  UI even on a desktop browser (handy for
                                  previewing what a phone reviewer will see)
mypage.html                    → normal page (wrapper does nothing)
```

On an actual phone (≤640px viewport, or a touch/coarse pointer), the mobile UI
is used automatically with plain `?proof` — you don't need `=mobile` there.

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

## What the reviewer can do

**Desktop** (`?proof`):
- **+ Comment** → click any element to pin a numbered comment to it.
- **✎ Edit** → click prose to rewrite it in place; the original is kept.
- From the same popover as a comment: react (👍/👎) and set a reminder.
- Keyboard shortcuts: `C` comment the hovered element, `E` edit it, `J`/`K` (or
  arrows) step through notes, `[`/`]` switch tabs, `⌘/Ctrl+Enter` send, `?` for
  a shortcuts overlay.
- **Reviewer** field stamps each note with a name. Light/dark/auto theme toggle.
- **Extract JSON** downloads the handoff file; **Send** (only shown if a
  return channel is configured — see below) posts it instead.

**Mobile** (real phone, or `?proof=mobile` to preview on desktop) — the
"Hairline" UI:
- **Long-press any element** → a menu: Comment · Looks right · Off the mark ·
  Edit text · Remind me. No separate "comment mode" to toggle.
- One floating pill: note count · `‹ n/N ›` stepper (cycles through every note)
  · send. **Tap the count** for a drawer listing every note (jump to any of
  them, across tabs); set your reviewer name and light/dark/auto theme there too.
- Anchored cards open in place under the element, with edit/delete on comments.
- Composer docks above the keyboard; quick-reply chips save a note in one tap.

Everything persists in `localStorage` per page path, so a reload never loses
notes.

## Declaring questions, checkboxes, and approvals

Beyond free-form comments (which work on any element, no markup needed), a
page can declare specific questions. proofing-room renders a native control in
place, and the answer is captured and anchored exactly like a comment.

| Attribute | On | Effect |
|---|---|---|
| `data-proof-ask="<id>" data-ask-type="yesno"` + `data-ask-options="A,B"` | any element | inline option buttons → an `answer` |
| `data-proof-ask="<id>" data-ask-type="scale"` + `data-ask-min/max/step` | any element | a visual slider → an `answer` (numeric) |
| `data-proof-ask="<id>" data-ask-type="done"` | element (its text becomes the label) | a checkbox → a `done` mark |
| `data-proof-section="Name"` | a section container | an approve circle in its heading → an `approval` |

`data-proof-ask` ids just need to be unique on the page — use whatever slug
makes sense for your content.

### Tabs

If a page needs to hold more than one brief in one review session, tag each
top-level container with `data-proof-tab="Label"`:

```html
<div data-proof-tab="Engineering"> … </div>
<div data-proof-tab="Marketing"> … </div>
```

proofing-room builds a tab bar automatically (tap or swipe to switch), tracks
which tab each note lives on, and lets the reviewer jump to a note on another
tab from the notes drawer/list. **A page with no `data-proof-tab` elements at
all behaves exactly like a single-view page** — tabs are entirely opt-in.

`example.html` in this folder demonstrates every one of the above: two tabs,
a `data-proof-section` approve, and one each of `yesno` / `scale` / `done`.

## Optional: wire a return channel

By default there's nothing to configure — reviewers use **Extract JSON**
(a plain download) and you hand that file to the agent yourself. These are
NOT wired up for you; you provide your own channel if you want it:

### (a) Send to a Discord webhook

Set `data-proofing-webhook` on `<body>` (or `window.PROOFING_WEBHOOK` before
the script loads) to **your own** Discord channel webhook URL:

```html
<body data-proofing-webhook="https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN">
```

With a webhook configured, a **Send** button appears (desktop panel, mobile
pill) that POSTs a short summary plus the full anchored review as a `.json`
file attachment straight to that channel. No webhook set → the button simply
doesn't render; Extract JSON keeps working regardless.

**That URL is a secret** — anyone who has it can post into your channel.
Keep the page private, and rotate the webhook if it ever leaks.

### (b) Host it on here.now (or any static host)

The page is a static file with one script tag — it works wherever you can
serve HTML. Publishing it via `here.now` (or your own host) is enough to hand
a reviewer a link with `?proof` on it; no server-side piece is required either
way.

## The JSON contract (what Extract / Send produces)

```jsonc
{
  "tool": "proofing-room",
  "version": "6",
  "url": "https://example.com/brief?proof",
  "path": "/brief",
  "title": "Weekly Team Brief",
  "extractedAt": "2026-07-13T10:30:00.000Z",
  "reviewers": ["Alex"],
  "comments": [
    { "id": "c1", "author": "Alex", "text": "Tighten this — too wordy.",
      "createdAt": "…", "anchorText": "…", "section": "Needs a decision",
      "selector": "…", "tag": "p" }
  ],
  "edits": [
    { "id": "e1", "author": "Alex", "original": "old copy", "text": "new copy",
      "createdAt": "…", "section": "…", "selector": "…", "tag": "p" }
  ],
  "answers":    [ { "kind": "answer",   "value": "Yes", "askId": "friday-deploys", "selector": "…" } ],
  "reactions":  [ { "kind": "reaction", "value": "up",  "selector": "…" } ],
  "approvals":  [ { "kind": "approval", "value": true,  "section": "Needs a decision", "selector": "…" } ],
  "done":       [ { "kind": "done",     "value": true,  "askId": "staging-refresh", "selector": "…" } ],
  "reminders":  [ { "kind": "reminder", "at": "2026-07-14T09:00:00.000Z", "selector": "…" } ],
  "document": [
    { "tag": "p", "text": "…", "selector": "…", "comments": [ { "author": "Alex", "text": "…" } ], "edited": false }
  ]
}
```

Each item is anchored by CSS `selector` + visible `anchorText` + nearest
`section` heading (+ `askId` for declared asks), so an agent can locate the
target even if the DOM has shifted slightly since the review.

## Acting on extracted JSON (the agent side)

When you're given a `proofing-*.json`:

1. **Locate each target** by `selector` first (precise), falling back to
   `anchorText` + `tag` if the selector no longer matches. `section` helps you
   orient.
2. **Apply `edits`** literally — replace the element's text `original` → `text`.
   Treat these as approved copy changes unless the user says otherwise.
3. **Action `comments`** as instructions/requests against their anchored
   element — interpret and implement, then report what you changed per
   comment `id`.
4. **Reconcile `answers` / `done` / `approvals`** into whatever they were
   actually asking about (a config value, a task tracker, a go/no-go).
   `reminders` are just a due date the reviewer wants surfaced later.
5. **Attribute** changes to `reviewers` where relevant, and confirm anything
   ambiguous or destructive before applying.
6. The `document` array is a convenience map of every prose block with its
   comments already attached — use it to review the page holistically.

## Files in this skill

- `proofing-room.js` — the drop-in wrapper (the artifact you copy in).
- `example.html` — a demo page with two tabs and one of every declared ask;
  open it with `?proof` (or `?proof=mobile`) to see the tool, or use it to
  verify a change.
- `README.md` — human-facing setup notes.
