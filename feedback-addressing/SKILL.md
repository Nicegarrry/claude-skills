---
name: feedback-addressing
description: Use when addressing reviewer feedback on a Word (.docx) document — a file plus inline comments and/or free-text dot-point notes — and you need the document back with native Word track-changes applied, an internal audit table, and a reviewer-facing email reply. Triggers include "address this feedback", "incorporate these comments", "respond to the reviewer", "work through these review notes", or a doc handed over with a feedback dump. Tiered P1/P2/P3 findings. Drafts only — never auto-sends.
version: "0.5"
license: MIT
---

# feedback-addressing

End-to-end loop for addressing reviewer feedback on a Word document — extract the feedback, plan, research the gaps, ask the right clarifying questions, apply tracked edits, and produce both an internal audit table and a reviewer-facing summary.

The skill works driven by a single agent. For larger feedback dumps it fans work out to subagents (one per category) with a single writer to the document and a verification gate before anything is applied — see [`references/orchestration.md`](references/orchestration.md). It ships Python helpers for the mechanical parts (comment extraction, native Word track-changes, reviewer-email rendering, visual QA).

## Local configuration (private overlay)

Nothing personal is committed in this skill. Anything you want it to use about *you* lives in a local, untracked `local/` overlay (gitignored) and/or environment variables:

- **`local/reviewer-voice.md`** — an optional house-style / your-own-voice file. Best-practice capture (rule F) appends to it; per-bucket drafting can read it to match your style.
- **`local/sources.md`** — your vetted "primary/secondary source" list for the research bucket (rule K). Off-list sources are still usable but get flagged `confidence=low`.
- **`local/reference-folders.txt`** — paths to your own knowledge/reference folders the research step searches first.
- **`FA_REMOVE_COMMENT_AUTHORS`** (env) — comma-separated list of comment authors whose comments may be removed (i.e. your own display name). Default is EMPTY: no comment is ever removed unless you opt in. Reviewer comments must never be listed.
- **`--signoff "Your Name"`** — passed to `render_tables.py` so the reviewer email is signed by you.

If the overlay is absent the skill still runs; it just behaves generically (no personal voice, no pre-vetted source list, no comment removal).

## When to use

Trigger this skill when:

- You are handed a `.docx` path plus reviewer feedback (inline comments, dot-points, or both) and asked to "address", "incorporate", "respond to", or "work through" the feedback
- A reviewer's comments are a separate dump (email body, chat message, doc) attached to a target file
- The output you want is a tracked-changes / annotated version plus an email reply you can paste into your mail client

Do **NOT** use this skill for:

- Authoring a new document from scratch — this is edit-mode only
- PDFs with reviewer markup (out of scope; surface as a known limit)
- Validating whether the reviewer's feedback is *correct* — all reviewer items are treated as legitimate input
- Rewriting an entire section because a reviewer said "redo this" — escalate to the document owner before mass rewrites

## Inputs

Required:

- **Document path** — absolute path to a `.docx` file
- **Feedback** — at least one of:
  - Inline comments embedded in the file (Word `Comments` track)
  - Free-text dot-point feedback (passed as a string, file path, or chat-message body)

Optional:

- **Reviewer name(s)** — for attribution in the internal table
- **Internal context links** — paths or URLs to prior versions, related documents, pages
- **Run folder** — where working artefacts land. Default `./feedback-runs/<run-id>/`.
- **`reviewer_table_format`** — `email-draft` (default — concise grouped email reply, see step 11), `markdown-table` (table only), or `docx-export` (write a `.docx` of the table; opt-in only).

If the input is malformed (file unreadable, no feedback supplied, both feedback channels empty): stop, flag to the user, do not invent feedback.

## Workflow

Each step produces a named artefact under the run folder (default `./feedback-runs/<run-id>/`). The run is one full address-the-feedback cycle on one document. 12 steps, with 9a Visual-QA inserted:

1. **Brief.** Produce `00-brief.md`. Frontmatter: doc path, reviewers, feedback channels present, run-id (`YYYY-MM-DDTHHMM`). Body: 1-paragraph summary of the doc's purpose, 1-paragraph summary of the feedback dump, success criteria, scope boundaries. This is the contract for the rest of the run.

2. **Extract feedback to a normalised JSON.** Run `helpers/extract_feedback.py <doc-path> [--dotpoints <path-or-stdin>]`. Returns a JSON list with one entry per feedback item: `{feedback_id, source_type: inline|dotpoint, source_locator, reviewer, raw_text, anchor_text, anchor_location, anchor_paragraph_id, anchor_paragraph_index, comment_wid, date, comment_thread}`. `feedback_id` is `F01`, `F02`, … in extraction order. Save to `01-feedback.json`.

   **Comment reply-chain reading (rule I).** The extractor parses `word/commentsExtended.xml` (Word's `w15:commentEx` elements with `w15:paraIdParent` pointers) and emits a `comment_thread` field per row: an ordered list `[{comment_id, author, text, role, date}, …]` capturing the parent comment plus replies in date order. Where a comment is itself a reply, the chain includes its parent. Worker briefs (step 5) MUST include `comment_thread` so subagents read the parent's ask, not just the literal reply text.

   **Shorthand-quality flagging (rule H).** When extracting, mark a row `clarifying_Q?=yes` whenever the comment is ≤30 chars, OR contains imperative verbs without an object (e.g. "fix this", "redo", "to do"), OR uses placeholder language ("…", "todo", "tbc"). Do NOT treat the literal string as the change ask — the planning step (step 4) will infer intent from anchored content + neighbours + `comment_thread`.

3. **Build the internal table — first pass.** From `01-feedback.json`, render `02-internal-table.md` with all 11 columns (see Output format below). Columns 1–4 (`feedback_id`, `source`, `feedback_summary`, `tier`) filled now; remaining columns left as `—` placeholders. Tier each item P1/P2/P3 per the rubric below.

4. **Plan to address each item.** For each row, fill the `plan_to_address` cell with one or two sentences naming the concrete change. Read the WHOLE paragraph the comment anchors in PLUS the immediately surrounding paragraphs (one before, one after) — see § Section-context rule below — AND the `comment_thread` field (rule I). Mark `knowledge_gap?` (yes/no — does someone need new evidence?) and `clarifying_Q?` (yes/no — is intent ambiguous enough that an answer changes the response?). Save as `02-internal-table.md` (overwrite). Also do address-completeness analysis: list each distinct ask in the comment so step 8's gate can verify all of them get a change-or-escalation.

   **Low-confidence draft mode for shorthand (rule J).** When a row was flagged `clarifying_Q?=yes` by step 2, the planning step ALWAYS attempts a draft using the full anchor context PLUS `comment_thread`. Only escalate when intent is genuinely undecipherable after reading: anchor + 1 before + 1 after + comment thread + any in-paragraph parenthetical that already gestures at the answer. If a sibling reviewer comment in the same thread states the intent (e.g. the parent comment explicitly says "I would put a footnote here to define X"), use THAT as the change spec — an owner reply of "to do" means "agree with the reviewer ask, action it". Mark such rows `confidence=low` so the reviewer email surfaces them as inferred-intent ("we drafted X based on inferred intent — please confirm").

5. **Group items into work buckets, then dispatch workers in parallel.** The lead/orchestrator (see [`references/orchestration.md`](references/orchestration.md)):
   - Groups items by category. Default buckets: `grammar-spelling`, `definitions`, `citations-evidence`, `structural-clarity`, `factual-correction`. Create new buckets if the dump warrants. **Always also create a mandatory `spellcheck-grammar-style` bucket — even if no reviewer comment asked for one** (rule C).
   - **Auto-research bucket (rule K).** Whenever ≥1 row matches the cited-evidence trigger heuristic (the comment names a data source or dataset AND uses a fetch verb like "pull", "fetch", "get", "find", "show me", "add data"), create a `citations-evidence-research` bucket and dispatch a single research subagent with web access — ONE pass, ≤30 min wall-clock budget, ≥2 verifiable citations or escalate. Source-quality rule: cite primary where reachable; cite the credible secondary verbatim when the primary is paywalled. Never invent figures. If the pass returns insufficient evidence, write the prose qualitatively and escalate the gap honestly. The `spellcheck-grammar-style` bucket subagent reads the whole document and surfaces (i) typos, (ii) grammar slips, (iii) AI-tells to avoid (em dashes, hedging, "incredibly", unnecessary intensifiers), (iv) style consistency (sentence-case headings, tense, voice), (v) references-section integrity (alphabetical order, complete coverage, format consistency). Each finding becomes a P3 row in `02-internal-table.md` with a proposed `replace`/`delete` change.
   - Flags `thematic=yes` for any item that is cross-cutting / requires multiple coordinated updates throughout the doc / is a high-level reviewer comment. Each `thematic=yes` item gets its OWN dedicated subagent with a full per-item brief.
   - Writes the bucket assignments to `02a-grouping.md` (rows: feedback_id, bucket, worker_id, thematic_yes/no). This is the dispatch contract.

   Each dispatched worker's brief: its assigned feedback rows, the plan column, and the reference folders to search first. **Always include the full anchor paragraph + ONE BEFORE + ONE AFTER** in the brief (rule A) — not just the anchor span. **Always include the style guard** (rule L) — the brief enumerates the banned patterns so workers don't introduce em dashes, AI-tell hedge fillers, or overclaims into `after_text` or `footnote_text`. Default reference-folder scope comes from `local/reference-folders.txt` if present. Workers have web access for citation/factual buckets. Research artefacts saved per worker at `03-research/<worker_id>.md`.

6. **Draft clarifying questions while research runs.** For all `clarifying_Q?=yes` items, draft a single message to the user listing the questions as numbered bullets, each tagged with the `feedback_id`. Stage it (do NOT send directly). Wait for the answers. Save them as `04-answers.md`. Steps 5 and 6 run concurrently; do not block step 5 on step 6.

7. **Each dispatched worker writes its proposed changes back into the table.** Workers do NOT touch the document. They append `proposed_change` blocks to `05-proposed-changes.md` for each row they own: `{feedback_id, worker_id, change_type, target_locator, …}`. Schema fields by `change_type`:
   - `insert | delete | replace | comment-only` — `before_text` / `after_text` per § change-block format below.
   - `footnote` — `target_locator`, `anchor_after_text` (optional), `footnote_text`.
   - `insert_image` — `target_locator`, `image_path`, `width_emu` (optional), `height_emu` (optional), `caption_text` (optional), `style_name` (optional).
   - `insert_table` — `target_locator`, `headers` (JSON list or `|`-sep), `rows` (JSON list-of-lists), `caption_text` (optional).
   - `apply_style` — `target_locator`, `style_name` (e.g. "Heading 1", "Quote").
   - `remove_comment` — `comment_id` (the Word `w:id`), `comment_author` (must be in the allowlist; default EMPTY, set via env `FA_REMOVE_COMMENT_AUTHORS`). The helper raises `RemoveCommentAuthorNotAllowed` if the author is not in the allowlist; the orchestration catches this and logs the change as `escalated`. **NEVER add `remove_comment` for a reviewer comment** — it destroys the review trail. Pair every owner-authored substantive change with a `remove_comment` row for the same comment_id (rule B). If the substantive change is escalated, suppress the paired `remove_comment` (preserve the comment to revisit).

   `target_locator` is `paragraph_id` (w14:paraId hex) or `paragraph_index` (0-based int). One block per row.

8. **Run the verification (check) gate on each proposed change.** Dispatch a check subagent (see [`references/orchestration.md`](references/orchestration.md)) with `05-proposed-changes.md` and the original brief. The check subagent returns `{accept, rework, escalate}` per item. The gate verifies BOTH literal correctness AND **address-completeness** (rule D): "For each item, identify the distinct asks in the comment. For each ask, confirm a corresponding change exists OR a documented escalation. If neither, return `rework`."

   **Inferred-intent gate.** For any row marked `confidence=low` (rule J shorthand-draft, or rule K off-list-secondary citation), the check ALSO verifies the change rationale explicitly captures the signal that fired — for rule J one of {sibling-reviewer-comment, in-paragraph parenthetical, neighbour paragraph, comment thread}; for rule K the unvetted-secondary source noted by name. Rows missing this captured signal return `rework`. Low-confidence is not a pass-through.

   **Style-guard gate (rule L).** The check also inspects every `after_text` and `footnote_text` against the rule L banned-pattern list (em dashes; "honestly" / "incredibly" / "frankly" / "fundamentally" / "ultimately" used as throat-clearing; overclaims like "comprehensive" / "robust" / "seamless" without a number; self-referential meta like "this analysis shows"). Any hit returns `rework`.

   Save as `06-check-results.md`. Items marked `rework` go back to the owning worker (re-runs step 7 for that row only). Cap at **3 rework cycles** per item — fourth failure → `escalate`. Items marked `escalate` are surfaced in the summary; no edit applied.

9. **Aggregate and apply all changes — single writer to the document.** Workers never touch the doc. The lead takes `05-proposed-changes.md` (full set of accepted proposed changes from step 8) plus the original `02-internal-table.md` and:
   - **Detects overlap conflicts.** Group proposed changes by `target_locator`. Reconcile incompatible edits — higher-tier wins (P1 > P2 > P3); loser → `escalated` with reason `overlap-conflict-with-<feedback_id>`. Log all reconciliations to `06b-overlap-reconciliation.md`.
   - **Sequences the edits** so insertions don't shift downstream locators (apply bottom-up by paragraph_id). The helper sorts paragraph-anchored changes descending; `remove_comment` rows run AFTER all paragraph-anchored edits.
   - **Applies the aggregated change set in one pass** via the helper below. The lead is the only writer to the output document. **For owner-authored comments**, after the substantive change applies cleanly, the paired `remove_comment` row runs (rule B). For reviewer comments, the comment STAYS (allowlist enforcement at helper level).

   Helper — `helpers/apply_changes_docx.py <doc-path> <06c-aggregated-changes.md> --out <out-path> --author "<your name or tool name>" --date <ISO>`. Native Word revisions (`<w:ins>` / `<w:del>` markup, `<w:pPrChange>` for style, `<w:trPr><w:ins>` for table rows). Output filename: `<original-stem>-tracked-<run-id>.docx`. The helper preserves any pre-existing `<w:ins>`/`<w:del>` markup (it only ADDS new revisions). Footnote/image/table/apply_style are first-class. The `remove_comment` change_type enforces an author allowlist at HELPER level. Save the output path to `07-output-doc-path.txt`.

   **9a. Visual-QA pass (rule G).** Run `helpers/visual_qa.py <out-doc> --out-dir 09-visual-qa/`. Wraps `soffice --headless --convert-to pdf` plus `pdftoppm` to produce `09-visual-qa/<stem>.pdf` + `<stem>-pageNN.png`. If `soffice` is not on PATH the helper returns `{"skipped": true, "reason": "soffice not found"}` with exit 0 — the run continues. Surface the visual-QA result in the run summary.

10. **Update the internal table — final pass.** For each row, fill `change_applied` (text), `change_location` (locator), and `status` (`applied` / `escalated` / `skipped-no-change-needed`). Save final `02-internal-table.md`.

11. **Produce the reviewer-facing email reply.** Default mode (`reviewer_table_format=email-draft`, rule E — concise grouped): run `helpers/render_tables.py 02-internal-table.md --format email-draft --doc-stem <stem> --reviewer-name <first-name> --signoff "<your name>" --out 08-reviewer-reply.md`. Shape:
    - Salutation: `Hi <first-name>,` — first-name only, no title.
    - Cover note: 2 sentences MAX. Default tone: informal peer ("Thanks for the comments — addressed below.").
    - Body: when 3+ items in a category, GROUP them ("All seven word-tightening edits applied as suggested."). Only itemise when an item needs explicit reviewer attention (escalated, deviated from suggested text, request a clarification).
    - Sign-off: your name (via `--signoff`).

    The `--format markdown-table` (table only) and `docx-export` modes are opt-in. Skipped/escalated items still appear with `what_changed` = "no change — see note" and `where` = "—".

    **Best-practice capture (rule F).** When a comment flags a section as "best practice" / "good example" / "use this style for later", capture the section text verbatim into your optional `local/reviewer-voice.md` (create it if absent). Append under a "Best-practice samples" section: doc, paragraph_id, verbatim text, the annotation.

12. **Deliver the summary.** A single message to the user:
    - 2–3 line summary (item count, P1/P2/P3 split, escalations count, comments-removed count)
    - Path to the tracked output doc
    - Path to the reviewer email reply (`08-reviewer-reply.md`)
    - List of any escalated items by `feedback_id` with the check reason
    - Path to the run folder for the full audit trail
    The user reviews, copies the email reply into their mail client, and sends it themselves. The skill never auto-sends.

## Section-context rule (rule A)

When a per-bucket worker drafts a proposed change, it MUST first read the WHOLE paragraph the comment is anchored in, plus the immediately surrounding paragraphs (one before, one after). The comment's anchor span is the prompt, not the boundary. Per-bucket briefs include the full enclosing paragraph + neighbours, not just the anchor span.

Worked example: a comment anchored on the word "standard" where the surrounding sentences use "traditional" — match to "traditional", don't invent a synonym. Reading only the anchored sentence misses this.

## Address-completeness check (rule D)

The check subagent (step 8 gate) verifies not only that the proposed change is correct, but also that it FULLY addresses the reviewer's intent. If the comment said "X is unclear AND Y is wrong", a change that only fixes X passes the literal-correctness test but fails completeness. The check's step-7 brief explicitly enumerates each distinct ask and confirms a change-or-escalation exists for each.

Worked example: "This comment was not fully addressed — the ask was [A and B]; you only addressed [A]."

## Mandatory spellcheck-grammar-style bucket (rule C)

Create a `spellcheck-grammar-style` bucket EVERY run. Mandatory output: a subsection in the run summary "Spellcheck/grammar pass found N items; M applied, K escalated."

## Best-practice capture (rule F)

Sections flagged "best practice" / "good example" / "use this style for later" → captured verbatim into the optional `local/reviewer-voice.md` under "Best-practice samples" (doc, paragraph_id, verbatim text, annotation).

## Visual-QA (rule G, step 9a)

`helpers/visual_qa.py` wraps `soffice --headless --convert-to pdf` + `pdftoppm` for per-page PNGs. Output goes to `09-visual-qa/<stem>.pdf` + `<stem>-pageNN.png`. If LibreOffice is not on PATH, returns `{"skipped": true, "reason": "soffice not found"}` and exits 0 — non-fatal.

## Shorthand-quality pass (rule H)

When a comment is terse, casual, or shorthand (e.g. "fix this", "to do", "need footnote"), comment-extraction does NOT treat the literal string as the change ask. Mark `clarifying_Q?=yes` whenever the comment is < 30 chars OR contains imperative verbs without an object OR uses placeholder language ("…", "todo", "tbc"). The planning step (step 4, rule J) reads anchored content + neighbours + comment thread (rule I) and drafts at low confidence rather than escalating.

## Comment reply-chain reading (rule I)

Word stores comment threads as a flat list in `comments.xml` plus a parent/child map in `commentsExtended.xml`. Each `w15:commentEx` element has a `w15:paraId` (linking to the comment's first-paragraph paraId in `comments.xml`) and an optional `w15:paraIdParent` (pointing at the parent comment's paraId). The extractor parses this map and emits a `comment_thread` field per row: the ordered sequence of `[parent, …replies-by-date]` entries, each with `{comment_id, author, text, role: parent|self|reply, date}`.

Worked example: an owner reply of "to do" (comment 127) that replies to a reviewer's "I would put a footnote here to define what we mean by 'rating'" (comment 126). Reading the thread recognises the "to do" as agreement with the reviewer ask, and drafts the footnote rather than escalating.

**Out of scope.** This reads `commentsExtended.xml` only. Word also stores `commentsIds.xml` (durable comment-id mapping) and author @-mentions inside a comment body. Those signals are not surfaced — documented as a known limit; impact is low for peer-review docs but matters for corporate review threads.

## Low-confidence draft mode for shorthand (rule J)

Shorthand → draft at low confidence using full context (rather than escalating). The planning step always attempts a draft when:

- The shorthand has a clear sibling reviewer comment in the same thread that states intent (then the reviewer comment IS the change spec).
- The anchor paragraph already contains a parenthetical that gestures at the answer (lift it into a definition / footnote).
- Anchor + 1 before + 1 after make the intent obvious by context.

Escalate only when none of these signals fire. Rows drafted under rule J are marked `confidence=low` in the internal table; the reviewer email flags them as inferred ("drafted X based on inferred intent — please confirm").

## Auto-research before escalate (rule K)

Cited-evidence asks (e.g. "pull the latest figures from <a named source>") trigger a research dispatch BEFORE escalating. Trigger heuristics:

- The comment names a data source or dataset.
- The comment names a data type (e.g. revenue, market share, a rate, a cost).
- The comment verb is "pull", "fetch", "get", "find", "show me", "add data", "show the numbers".

The bucket subagent gets web access, ONE pass, ≤30 min wall-clock, ≥2 verifiable citations as the bar. Source-quality: primary where reachable; a credible secondary when primary is paywalled — and ATTRIBUTE the secondary, not the inaccessible primary. Never invent figures. If the pass yields no concrete numbers, write qualitatively and surface the gap.

**Vetted-source rule.** Maintain your pre-vetted source list in `local/sources.md`. If the subagent cites a source NOT on that list, it MUST surface the unvetted source by name in the row's change rationale (e.g. "secondary cited: example.com — not on pre-vetted list") and auto-flag the row as `confidence=low`. The reviewer email then surfaces the row as inferred ("drafted X using <unvetted-source>; please confirm the source"). The check gate refuses these rows if the rationale doesn't name the unvetted source.

## Style guard for all generated prose (rule L)

Every piece of prose this skill writes into a deliverable — proposed-change `after_text`, `footnote_text`, qualitative gap notes, the reviewer email cover and grouped bullets — must avoid AI-style tells. Banned patterns:

- **Em dashes (—).** Use commas, parentheses, or full stops. (The workflow text in this SKILL.md uses em dashes; that's internal documentation, not deliverable prose. The ban applies to text that lands in the docx or reviewer email.)
- **Hedge / intensifier fillers.** No "honestly", "frankly", "to be clear", "incredibly", "absolutely", "fundamentally", "ultimately" used as throat-clearing. Cut, or replace with a concrete claim.
- **Overclaims.** No "comprehensive", "robust", "seamless", "powerful" without an accompanying number, range, or specific.
- **Self-referential meta.** No "this analysis shows", "as we have seen", "it is worth noting", "importantly".

Mechanics:

- Worker dispatch briefs (step 5) include this rule verbatim so workers don't introduce the patterns when drafting.
- The check gate (step 8) inspects every `after_text` and `footnote_text` against the banned-pattern list and returns `rework` on a hit.
- The reviewer-email render (step 11) post-processes the cover note and grouped bullets — any em dash or banned filler in the rendered output → `rework`.

## Output format

### Internal table (`02-internal-table.md`)

```markdown
# Internal feedback addressing audit — <doc-stem> — <run-id>

| feedback_id | source | feedback_summary | tier | plan_to_address | knowledge_gap? | research_dispatched? | clarifying_Q? | change_applied | change_location | status |
|---|---|---|---|---|---|---|---|---|---|---|
| F01 | inline-c12 (Reviewer A) | "Define the key term before first use." | P2 | Insert one-sentence definition at first use; cite source. | yes | dispatched 2026-05-09T11:48 → 03-research/F01.md | no | Inserted: "A … (Author, Year)" | p3 §2.1 | applied |
| F02 | dotpoint #3 | "Section 4 too dense." | P3 | Split paragraph 4 into 2 paragraphs at the "however" pivot. | no | — | no | Split paragraph at line 78. | p4 §4 | applied |
| F03 | inline-c14 (Reviewer A) | "Is this 2024 or 2025 data?" | P1 | Confirm source year with author; update citation. | no | — | yes | — | — | escalated |
```

### Reviewer email reply (`08-reviewer-reply.md`) — concise grouped default

```markdown
Hi Sam,

Thanks for the comments on <doc-stem> — addressed below. Tracked-changes attached for review.

- All seven word-tightening edits applied as suggested.
- Three definitions added inline as proposed; two terms also got a footnote.
- F09 (requested dataset): pulling current numbers; will follow up.
- F11 ("placement context"): added the intro sentence you suggested.

<your name>
```

### Summary message (literal template)

```
Feedback round on <doc-stem> done.

- <N> items: <P1> P1 / <P2> P2 / <P3> P3
- <K> applied / <E> escalated / <S> skipped
- <R> reviewer comments preserved / <C> owner comments removed
- Tracked doc: <abs path to 07 output>
- Reviewer email: <abs path to 08-reviewer-reply.md>
- Visual QA: <abs path to 09-visual-qa/> (or "skipped: soffice not found")
- Escalations: F03 (source year ambiguous), F07 (reviewer wants restructure — needs a call)
- Full audit trail: <run-folder>/

Review and send when ready.
```

### Change-block markdown format (input to `apply_changes_docx.py`)

Each block separated by a `---` line. Within each block, `key: value` lines. `target_locator` accepts `paragraph_id` (w14:paraId hex) or `paragraph_index` (0-based int).

```
feedback_id: F01
change_type: replace          # insert | delete | replace | comment-only | footnote | insert_image | insert_table | apply_style | remove_comment
target_locator: 6DF65335      # paraId hex OR int paragraph index — not required for remove_comment
before_text: incredibly       # required for delete/replace
after_text: especially        # required for insert/replace
rationale: shorter, less hyperbolic per reviewer
evidence_refs: F01
```

For `footnote`: `footnote_text` (required), `anchor_after_text` (optional, defaults to end-of-paragraph).
For `insert_image`: `image_path` (required), `width_emu`/`height_emu`/`caption_text`/`style_name` (optional).
For `insert_table`: `headers` and/or `rows` (one required; JSON list or pipe-separated), `caption_text` (optional).
For `apply_style`: `style_name` (required) — emits `<w:pPrChange>` so reviewers can see the prior pPr.
For `remove_comment`: `comment_id` (required), `comment_author` (required, must be in allowlist; default EMPTY, set via env `FA_REMOVE_COMMENT_AUTHORS`).

## Boundary

The skill explicitly does **NOT**:

- Auto-send the document or reviewer email to anyone — the user reviews and sends themselves
- Auto-accept reviewer comments without confirmation on `clarifying_Q?=yes` items
- Validate whether the reviewer's feedback is *substantively correct* — all feedback is treated as legitimate input
- Regenerate sections, charts, or text from scratch — only applies targeted insert/delete/replace/footnote/image/table/style edits
- Handle PDF reviewer markup — out of scope
- Edit Google Docs — local `.docx` files only
- Resolve cross-document feedback — escalates
- **Remove a reviewer comment.** Helper-level allowlist enforcement: only authors you explicitly allowlist (i.e. yourself) may be removed (default EMPTY). Attempts to remove a non-allowlisted author raise `RemoveCommentAuthorNotAllowed` and are logged as `escalated`. Belt + braces: even if a change row claims an allowed `comment_author`, the helper cross-checks the actual `w:author` attribute in `word/comments.xml` and refuses if they don't match.
- Validate that supplied images are licensed / safe — caller's responsibility
- Generate caption numbering — pass `caption_text` as a literal string ("Figure 1: …", "Table 3.2: …")
- Honour Word's "Track Changes formatting" toggle for `apply_style` — `<w:pPrChange>` always emitted regardless

## Quality bar

A run is "good" when:

- Every feedback item in the dump appears as a row in the internal table (recall = 1.0)
- Every applied change passes the check gate
- Every `clarifying_Q?=yes` item either has an answer or is marked `escalated` — never silently skipped
- The mandatory spellcheck-grammar-style bucket ran and the result is in the run summary
- Section-context was read for every per-bucket dispatch
- Every owner-authored comment that got an applied change has a paired `remove_comment` that succeeded
- Every reviewer comment is preserved (ranges intact in body + comments.xml)
- Every cited-evidence row triggered by rule K either lands ≥2 verifiable citations OR is escalated with the research log attached
- Every `confidence=low` row drafted under rule J or rule K has the inferred-intent signal explicitly captured in the change rationale
- No generated prose (`after_text`, `footnote_text`, reviewer-email cover and grouped bullets) contains em dashes or rule L banned fillers
- Visual-QA pass either ran cleanly or recorded a graceful skip
- The reviewer email is plain enough to paste into a mail client with no further editing

A run is "bad" when:

- Feedback items are silently dropped because they were ambiguous (should be `escalated`, not skipped)
- Track-changes markup is applied without a check pass
- A reviewer comment was removed (CRITICAL — destroys the review trail)
- The reviewer email mentions internal terminology (run-id, feedback_id, tier)
- A `knowledge_gap=yes` item gets a change applied without a research dispatch (no evidence trail)

## Severity rubric

- **P1** — substantive correction. Affects accuracy, factual claims, the sign of an argument, or a citation that's wrong. Fix before the doc goes back to the reviewer.
- **P2** — clarity / structure improvement. Reordering, adding a missing definition, splitting a dense paragraph, tightening a transition. Fix in this revision.
- **P3** — style / polish / typo. Spelling, formatting, single-word swaps, capitalisation. Fix when time permits; never block delivery on a P3.

If a feedback item could plausibly cause the reader to draw a wrong conclusion → **always P1**. Otherwise tier strictly.

- "Key term undefined on first use" → **P2** (clarity, not correctness)
- "Is this 2024 or 2025 data?" → **P1** (citation correctness)
- "Typo: 'incentivse' → 'incentivise'" → **P3**
- "This claim contradicts your earlier section" → **P1** (internal consistency = correctness)
- "Punchier opening sentence please" → **P3** (style)
- "Add a worked example here" → **P2** (clarity)

## Files in this skill

- `SKILL.md` — this file (workflow + output format + rubric)
- `references/feedback-extraction.md` — how to pull comments from `.docx`; XML schema notes
- `references/orchestration.md` — the optional multi-agent shape (brief, dispatch, gate, accept)
- `references/change-application.md` — how native Word track-changes markup is applied
- `helpers/extract_feedback.py` — `(doc-path, [dotpoints]) → 01-feedback.json`
- `helpers/apply_changes_docx.py` — `(doc-path, proposed-changes-md, --out) → tracked .docx`. Native Word revisions; footnote/image/table/apply_style/remove_comment first-class
- `helpers/render_tables.py` — `(internal-table-md, --reviewer-name, --signoff) → reviewer reply`
- `helpers/visual_qa.py` — `(doc-path, --out-dir) → PDF + per-page PNGs` via LibreOffice + pdftoppm
- `helpers/_smoke_test_*.py` — smoke tests for the docx helper (apply, footnotes, image, table, styles, indexing, hyperlink replace, remove_comment, comment threads, visual_qa) — all pass
- `local/` — your private, gitignored overlay (reviewer voice, vetted sources, reference folders). Not committed.

## Known limits

- Supports `.docx` only
- `.pdf` reviewer markup not handled
- Reference-folder scope is whatever you configure in `local/reference-folders.txt`
- Three rework cycles per item before escalation
- Caption auto-numbering not generated — pass literal strings (`"Figure 1: …"`)
- No diff against prior runs
- Cross-document feedback not detected — escalates by default
- Native Word `<w:ins>`/`<w:del>` author/date metadata may render dates oddly in some Word versions when the timezone differs from the system clock
- Auto-research budget is ONE pass per cited-evidence row (≤30 min wall-clock); deeper research escalates
- @-mentions inside Word comment bodies are not surfaced — the extractor reads `commentsExtended.xml` parent/child links only, not `commentsIds.xml`
- Style-guard banned-pattern list (rule L) is the explicit set above; novel AI-tell phrasings not on the list can slip through
