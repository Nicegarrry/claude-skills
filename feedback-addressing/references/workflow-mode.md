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
  units: [{ key: "d1", label: "Doc 1", doc: "/abs/d1.docx", dir: "/abs/runs/d1", notes: "doc-specific rules" }]
}})
```

Defaults: no comment is ever removed. Reviewer tracked changes are preserved and never anchored across. Edits are targeted, never wholesale rewrites.

Write the transcript's rules into a short `rules_file` first. Agents treat it as binding, and it is cheaper to read than a raw transcript.
