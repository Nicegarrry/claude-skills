---
status: stub-pending-v0.2
parent: ../SKILL.md
---

# feedback-extraction — reference

**Purpose:** how `helpers/extract_feedback.py` pulls reviewer feedback out of `.docx` files and normalises a free-text dotpoint dump into the same shape.

Full version (v0.2) will cover:

- Word `comments.xml` schema — `w:comment` elements, `w:commentRangeStart` / `w:commentRangeEnd` anchors, author + date attribution
- Anchor resolution — mapping a comment to the paragraph it points at
- Dotpoint normalisation — splitting an email or chat-message blob into discrete items (heuristics: bullets, numbered lists, blank-line separation)
- Edge cases — replies-to-comments threading, resolved comments, comments anchored to deleted text, embedded objects
- Output JSON schema — exact field list and example
