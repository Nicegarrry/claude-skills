---
status: stub-pending-v0.2
parent: ../SKILL.md
---

# change-application — reference

**Purpose:** rules for applying tracked edits as native Word revisions.

Full version (v0.2) will cover:

- Word native revisions — `<w:ins>` and `<w:del>` element shape, required author/date attributes, paragraph-property revisions (`<w:pPrChange>`), revision-id (`w:rsid`) handling
- Optional visible fallback (when native revisions misbehave) — strikethrough run-property + coloured-bold insertion. Colour spec: `#FF6A00` is the working default; override with your own brand/design tokens if you have them
- Locator format — `paragraph_id` for docx (zero-indexed paragraph in body order)
- Insert / delete / replace semantics — replace = delete-then-insert at same anchor, both showing in the tracked output
- Comment-only changes — when the proposed change is "leave a note for the reviewer" rather than edit text, write a Word comment instead of a text edit
- Idempotency — how the helper guards against double-application if run twice on the same input
