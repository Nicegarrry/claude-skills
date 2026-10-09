---
status: v0.8
parent: ../SKILL.md
---

# change-application — reference

**Purpose:** how `helpers/apply_changes_docx.py` (v0.8) turns change blocks into native Word revisions. Use the stock helper as is: no run-local wrappers. If a block needs something the helper cannot do, change the block or list it as a helper gap.

## Revision markup

- Insertions: `<w:ins w:id w:author w:date>` around new runs. Deletions: `<w:del>` around the original runs, `w:t` renamed to `w:delText` (`instrText` to `delInstrText`).
- Paragraph marks: `<w:pPr><w:rPr><w:ins|w:del …/></w:rPr></w:pPr>`. Style changes: `<w:pPrChange>`. Table rows: `<w:trPr><w:ins>`.
- Existing reviewer revisions are never edited or removed; the helper only adds revisions. Deleting reviewer-inserted text nests the author `<w:del>` inside the reviewer `<w:ins>` (Word's own form).
- Inserted runs never inherit a reviewer's `w:rPrChange`, `w:ins`, `w:del`, `w:moveFrom` or `w:moveTo` from a cloned rPr.
- Post-pass: an author `<w:ins>` nested inside another author's `<w:ins>` (a replace inside reviewer-inserted text) is hoisted out, splitting the reviewer's insertion around it. The log line reads `post-pass: hoisted N …`.

## Locators and ordering

- `target_locator`: w14:paraId (hex) or 0-based paragraph index over `body.iter('w:p')` (includes table cells), or `para-N`.
- Paragraph edits run bottom-up by paragraph; several blocks on one paragraph run in file order. Then `reply_comment`, then `remove_comment`.
- Text matching is on the paragraph's current visible text (reviewer insertions and earlier author insertions count, deletions do not). Exact match first, then a whitespace-relaxed match. Not found → skipped with a note.

## Change types

| change_type | Required | Optional | Effect |
|---|---|---|---|
| `insert` | `after_text` | `italic: yes` | Appends at the true paragraph end, after any trailing reviewer `<w:ins>`, hyperlink or comment marker. Adds one space first unless the text already ends in whitespace or `after_text` starts with `. , ; : ! ? ) ] }` or a closing quote. |
| `delete` | `before_text` | | Wraps each matched run in `<w:del>` in place (see below). Never leaves a double space: a trailing space in `before_text` is honoured, and a single adjacent space is also deleted when the match sits between spaces, at the paragraph start, or at the paragraph end. If the paragraph ends up empty, its paragraph mark is deleted too (kept if the mark already has a revision, non-text content remains, or it is the last paragraph of its cell/body). |
| `replace` | `before_text`, `after_text` | | In-place delete, then `<w:ins>` immediately after the last deleted run. The new run copies the first deleted run's rPr minus revision marks and `w:highlight`. If the deletion ends a hyperlink (or smartTag/fldSimple/customXml), the insertion goes after the container so new text is not linked to the old target; inside a reviewer insertion it is placed exactly and then hoisted. |
| `insert_paragraph` | `after_text` | `position`, `sequence`, `clone_ppr_from`, `clone_ppr`, `style_name`, `clone_rpr_from`, `italic_text`, `italic` | New tracked paragraph before or after the target (below). |
| `delete_footnote_ref` | `footnote_id` | | Wraps the run holding `<w:footnoteReference w:id=N>` in an author `<w:del>`. Searches the target paragraph, then the whole body. Skipped if the reference is already deleted or missing. `footnotes.xml` is not touched. |
| `comment-only` | | | No document edit; logged and counted as skipped. |
| `footnote`, `insert_image`, `insert_table`, `apply_style`, `add_comment`, `reply_comment`, `remove_comment` | see SKILL.md | | Unchanged from v0.7. |

### In-place deletion

Each deleted run stays where it was and is wrapped in `<w:del>`; adjacent sibling runs share one `<w:del>`. Comment range markers, comment reference runs, bookmarks, `proofErr` and hyperlink boundaries keep their positions, so a placeholder such as `[x]` that carries a reviewer comment can be replaced without moving the comment anchor. Runs are split only strictly inside their text: a cut at a run boundary never creates an empty run. Non-text runs inside the span (footnote references, comment references) are left alone; use `delete_footnote_ref` for footnote marks. Expect more `<w:del>` elements than matched spans when markers sit between runs; the visible result is the same.

### insert_paragraph

```
feedback_id: S03
change_type: insert_paragraph
target_locator: 690B1204
position: before            # after (default) | before
sequence: 1                 # optional; orders several inserts on one target and position
clone_ppr_from: 690B1204    # optional paraId; default the target
style_name: Normal          # optional
after_text: ACCIONA 2020, 'ACCIONA to build …', news release, 26 March, accessed 3 October 2026, https://….
italic_text: ACCIONA to build …   # optional substring to italicise ("none" = no italics)
```

- The paragraph mark is tracked as inserted by the author and the text sits in `<w:ins>`. Each new paragraph gets a fresh unique `w14:paraId`.
- pPr is cloned from `clone_ppr_from` (or the target) minus `pPrChange`, `sectPr` and the paragraph-mark rPr. `clone_ppr: no` starts from an empty pPr.
- `style_name`: if it resolves to a different style from the cloned pPr, the pPr is reset to just that style (no inherited numbering or indents). Same style, or not found: the cloned pPr is kept (not found is noted in the log).
- `clone_rpr_from: target | <paraId>` copies the first run's formatting (minus revisions) onto the new text. `italic: yes` italicises the whole paragraph.
- Chaining: several inserts on the same target and position land in `sequence` order, ties and missing values in file order. "after" inserts stack below the target; "before" inserts stack above it, top to bottom.

### Aliases (accepted, normalised before applying)

| Written as | Treated as |
|---|---|
| `change_type: insert` + `new_paragraph: after` (or `before`) | `insert_paragraph`, `position` from `new_paragraph` |
| `change_type: comment-only` + `new_paragraph_after: <paraId> …` + `new_paragraph_text` | `insert_paragraph` after that paraId (first token), text from `new_paragraph_text` |
| `slot_order` | `sequence` |
| `style` | `style_name` |
| `paragraph_style: same as <paraId>` | `clone_ppr_from: <paraId>` (any other value is a `style_name`) |

New blocks should use `insert_paragraph` directly.

## Not supported (write the block differently)

- Run-specific formatting rules (for example italicising every "Source:" line). Use `italic_text` / `italic` on the block.
- Mid-paragraph insertion without deleting anything: use a `replace` that includes the neighbouring word.
- Moves (`w:moveFrom`/`w:moveTo`): use a delete plus an insert.

## Comments

Reviewer comments are never edited or removed. Replies thread under the reviewer's comment (`reply_comment`); feedback with no comment to reply to gets a new `add_comment`. `remove_comment` only removes comments by allowlisted authors (`FA_REMOVE_COMMENT_AUTHORS`).
