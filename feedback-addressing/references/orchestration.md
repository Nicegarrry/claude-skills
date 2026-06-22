---
status: stub
parent: ../SKILL.md
---

# orchestration — reference

**Purpose:** how feedback-addressing maps onto a generic "unit-of-work" agent
pattern — brief, dispatch, gate, accept. The skill works fine driven by a
single agent; this note describes the optional multi-agent shape for larger
feedback dumps where you fan work out to subagents.

The pattern in four roles (one agent can play several):

- **Lead / orchestrator** — owns the run. Extracts feedback, builds the internal
  table, groups items into buckets, dispatches workers, and is the *single
  writer* to the output document (applies the aggregated change set in one pass).
- **Worker subagents** — one per bucket (e.g. `grammar-spelling`,
  `definitions`, `citations-evidence`). Each reads its assigned rows plus the
  surrounding document context and proposes changes back into the table. Workers
  never touch the document.
- **Research subagent** — optional, web-enabled. Dispatched for cited-evidence
  asks; returns verifiable citations or escalates the gap honestly.
- **Check / verification subagent** — the gate. The only actor that authorises a
  `proposed_change → change_applied` transition. Verifies literal correctness,
  address-completeness, and style-guard compliance; returns `accept | rework |
  escalate` per item.

Notes when you wire this into your own harness:

- **Brief shape** — give each worker the minimum it needs to act: its feedback
  rows, the plan, the full anchor paragraph + one before + one after, the comment
  thread, and the banned-pattern style list.
- **Run-folder layout** — each step writes a numbered artefact under a per-run
  folder (`00-brief.md`, `01-feedback.json`, `02-internal-table.md`, …) so the
  run is fully auditable. The internal table is the audit trail; an optional
  `events.jsonl` adds a machine-readable log.
- **Dispatch boundary** — fan out the per-bucket drafting, research, and the
  verification gate; keep extraction, grouping, conflict reconciliation, and the
  single-writer apply inline in the lead.
- **Promotion authority** — only the check step promotes a proposed change to
  applied. Cap rework cycles (default 3) before escalating to the human.
