# Workflow mode (multi-agent, for complex rounds)

Use when a round is too big or too cross-cutting for one agent: several related documents, a reviewer call transcript, reference-heavy fixes, or comments whose fix must be consistent across documents. Script: `workflows/deep-feedback.js` (Claude Code Workflow tool; the user must opt in to multi-agent orchestration).

## Shape

1. **Understand**: one deep reader per document extracts feedback, reads the whole document, every thread, and the transcript or rules file, and writes the brief, internal table and an intent file (the spirit of each comment). It also records the baseline count of existing tracked revisions.
2. **Consistency** (barrier): one agent compares all the documents and writes X-rows for fixes that must be applied the same way everywhere.
3. **Plan**: buckets per document. `spellcheck-grammar-style` is always included, plus any `mandatory_buckets` (e.g. `references-integrity`, `tables-figures`), which audit the whole document. Research questions go to rule K.
4. **Research**: one researcher per question (web, downloaded sources, optional Codex cross-check), then an adversarial checker with one retry. Unverified claims are marked so writers escalate.
5. **Write**: one writer per bucket produces targeted change blocks plus exactly one `reply_comment` per comment (author `Claude` by default).
6. **Check**: the step 8 gate, with up to 2 rework rounds back to the owning bucket.
7. **Review**: spirit, voice and accuracy lenses in parallel, then one fixer.
8. **Apply**: a single writer per document applies the changes with the owner as tracked-change author. It verifies every comment got a reply, that pre-existing revisions survive, and that the file opens. It also writes the final table and summary.

Documents run as a pipeline after Consistency, so one document can be in Apply while another is still in Research.

## Setting up a round

Do this before launching. It is what made a three-document course-unit round (October 2026) work.

1. **Round folder** next to the documents, e.g. `working-docs/feedback-round-YYYY-MM/`, with `in/` for the reviewer's commented .docx files, `runs/` for outputs and a short `README.md` naming the workflow and where outputs land.
2. **Rules file.** If there was a reviewer call, save the transcript and distil it into `reviewer-call-rules.md`: numbered rules for all documents (tracking, tables and figures, references, claims needing sources, activities, forbidden features), then a short section per document. Mark anything the reviewer reserved for the owner ("do not rewrite X; reply with options"). Agents treat this file as binding.
3. **`run-config.json`** holding the args below, with per-document `notes` that repeat the document-specific rules in one or two lines. Keep the document in its original folder (with a copy in `in/` if wanted); point `dir` at `runs/<key>/`.
4. **Gate on the reviewer.** Do not launch a document the reviewer is still editing.
5. **Owner names.** Put every display name the owner uses in Word into `owner_names` (they often differ by machine).

Keep recurring presets for a client or publisher (forbidden features, mandatory buckets, style guide, reference folders) in `local/presets.md`, not in this repo.

## After the run

- The owner reviews the tracked output and returns an edited version, often with comments addressed to Claude.
- Run `helpers/owner_pass_diff.py` on the pair (rule P) and fold repeated patterns into the skill or `local/reviewer-voice.md`.
- A follow-up run on the owner's version, launched with `followup: true`, actions the "Claude ..." comments (rule O). Only set it for a file the owner edited and handed back: Word author names are self-declared, so a comment's author is not proof it came from the owner.

## Lessons from the October 2026 round

- **Fix the helper, not the run.** Each document's apply agent wrote its own wrapper for the same helper gaps (tracked new paragraphs, deletes that keep comment anchors, nested insertions). Those are now in the helper (v0.8). The apply agent must report any new gap, never patch around it.
- **Replies were too long.** 52 of 53 replies on one document were over 30 words (median 79); the owner deleted half unread. Rule N.
- **Too many suggestions.** The owner's follow-up comments mostly said "make the change you suggested" or "update to the latest edition, with the new figure". Rule M.
- **Consistency pass earned its place.** It caught citation-style conflicts and one worked example used in contradicting ways across documents.

## Run

Pass args as a JSON object (not a string):

```
Workflow({ scriptPath: "<skill>/workflows/deep-feedback.js", args: {
  run_id: "2026-10-03T1000", author: "Owner Name", reply_author: "Claude",
  context: "What the documents are and who reads them.",
  transcript: "/abs/transcript.md", rules_file: "/abs/rules.md",
  style_guide: "/abs/style.md", ai_tells: "/abs/log.md",
  reference_folders: ["/abs/downloads"], forbid: ["footnote"],
  mandatory_buckets: ["references-integrity", "tables-figures"],
  owner_names: ["Owner Name", "Owner Display Name"],
  units: [{ key: "d1", label: "Doc 1", doc: "/abs/d1.docx", dir: "/abs/runs/d1", notes: "doc-specific rules" }]
}})
```

Defaults: no comment is ever removed. Reviewer tracked changes are preserved and never anchored across. Edits are targeted, never wholesale rewrites.

Write the transcript's rules into a short `rules_file` first. Agents treat it as binding, and it is cheaper to read than a raw transcript.
