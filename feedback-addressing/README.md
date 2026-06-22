# feedback-addressing

A [Claude Code](https://claude.com/claude-code) skill for working through reviewer
feedback on a **Word (`.docx`)** document, end to end.

Hand it a document plus feedback (inline comments, a free-text dot-point dump, or
both) and it will:

1. **Extract** every comment and dot-point into a normalised list (including
   Word reply-chains via `commentsExtended.xml`).
2. **Tier** each item P1 / P2 / P3 and **plan** a concrete change, reading the
   full surrounding paragraph — not just the anchored span.
3. **Research** cited-evidence asks (optional, web-enabled) before escalating.
4. **Apply** the edits as **native Word track-changes** (`<w:ins>` / `<w:del>`,
   footnotes, images, tables, paragraph styles), with a single writer and a
   verification gate so nothing lands unchecked.
5. Produce an **internal audit table** and a **reviewer-facing email reply** you
   can paste into your mail client.

It **drafts only** — it never sends anything, and it never removes a reviewer's
comment (only comments by authors you explicitly allowlist, i.e. your own).

## What's in here

```
feedback-addressing/
  SKILL.md                     # what Claude reads — full workflow, rubric, output formats
  references/                  # extraction, change-application, and orchestration notes
  helpers/                     # Python tools + smoke tests
    extract_feedback.py        # doc → normalised feedback JSON
    apply_changes_docx.py      # change list → tracked-changes .docx
    render_tables.py           # internal table → reviewer email / table
    visual_qa.py               # rendered PDF + per-page PNGs (LibreOffice)
    _smoke_test_*.py           # 10 smoke tests, all passing
  local/                       # YOUR private overlay (gitignored, not published)
```

## Requirements

- Python 3.10+
- `pip install lxml python-docx`
- Optional: LibreOffice (`soffice` on `PATH`) for the visual-QA pass

## Install

Symlink (recommended — keeps it in sync with this repo):

```bash
ln -s "$PWD/feedback-addressing" ~/.claude/skills/feedback-addressing
```

…or copy it:

```bash
cp -R feedback-addressing ~/.claude/skills/
```

Claude Code auto-discovers the skill and loads it when your request matches the
`description` in `SKILL.md` (e.g. "address this feedback on the attached .docx").

Run the smoke tests to confirm the helpers work in your environment:

```bash
cd feedback-addressing/helpers
for t in _smoke_test_*.py; do python3 "$t" && echo "PASS $t"; done
```

## Personalising it (optional)

The skill works generically out of the box. To give it your own voice, vetted
sources, reference folders, and the ability to remove your own comments, fill in
the **`local/`** overlay — it's gitignored, so nothing personal is ever
published. See [`local/README.md`](local/README.md) for the four files / env vars
it understands.

## License

[MIT](../LICENSE) © Nick Pinidiya
