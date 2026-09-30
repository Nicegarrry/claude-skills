---
name: helm
description: Drive the Helm MCP server to dispatch coding work to cheap worker agents, each in its own git worktree, and get back gates, PRs, reviews and merges without spending your own context on the mechanics. Use when you are orchestrating a build that is bigger than one sitting — "run this overnight", "self-manage with agents", "fan this out to workers", "use helm" — and the helm MCP tools (worker_spawn, worker_wait, gate_run, pr_open, review_request, pr_merge) are available. Harness and setup live at github.com/Nicegarrry/helm3.
---

# Helm — orchestrating workers through the Helm MCP

You are the orchestrator. Workers write the code; you decide, dispatch, verify and merge.
Your context is the scarcest resource in the run — spend it on decisions, never on reading
diffs line by line or polling.

The harness itself (install, daemon, dashboard, configuration) is documented in the
[helm3 repo](https://github.com/Nicegarrry/helm3) — read `helm/README.md` there if the tools
are missing or misbehaving. This skill covers only how to *use* them well.

## Tool profiles (keep context small)

Helm's MCP exposes a small **core** set by default: `worker_spawn`, `worker_steer`, `worker_inspect`, `inbox_reply`, `wake_list`, `gate_run`, `pr_open`, `run_status`, plus two meta tools:

- `helm_help {}`: one-line index of every Helm tool; `helm_help {tool: "pr.merge"}`: that tool's full input schema.
- `helm_call {tool: "<dotted.name>", input: {...}}`: call any Helm tool with the same validation, guards and taps as a direct call.

Everything in the table below that isn't in core is reached with `helm_call` (e.g. `helm_call {tool: "merge.enqueue", input: {number: 12, project: "owner/repo"}}`). Don't ask for the `all` profile to get direct tools; that defeats the point. Responses are compact by default; pass `verbose: true` only when you need the detail.

## The tools

Every tool returns `{ ok: true, ... }` or `{ ok: false, reason }`; nothing throws. Read the
`reason` and act on it.

| Tool | Use it to |
|---|---|
| `worker_spawn` | Start a builder (or reviewer) on a new branch in a fresh worktree. `model` picks the lane: `provider/model` for a Pi session, or `codex/<model>[:<effort>]` for the Codex CLI. |
| `worker_wait` | Block until any of the given workers settles, or a timeout. **The only way to wait.** |
| `worker_inspect` | Result, head, spend, diff stat and recent events for one worker — after it settles. |
| `worker_list` | One line per worker. |
| `worker_steer` | Send a follow-up to an idle or interrupted worker in its own session (fix-ups, resumes). |
| `worker_stop` | Stop a running worker. |
| `gate_run` | Run the repo's checks at the worker's exact head. |
| `pr_open` | Push and open a PR — refused unless a gate passed at the current head. |
| `review_request` | Spawn a read-only reviewer on the PR head (needs an explicit `model`). For Claude reviews run outside Helm, use `review_record`. |
| `review_record` | Record a posted review comment (`APPROVE: ` / `REQUEST_CHANGES: ` last line) at the PR head; `pr_merge` requires an approving one. |
| `gate_baseline` | Record a validator's red acceptance test (gate-first). Builders spawned with `baselineId` must turn it green without editing it. |
| `claims_check` | Jev checks the builder's claims against its diff; blocks merge in block mode. |
| `worker_retry` | Steer the same session with the named violation and its evidence (gate, acceptance, claims, review, tests_edited, conflict); capped per kind. |
| `jev_check` | Jev presets for skills: `issue` (testable, too_big, complexity), `dedupe`, `verdict`, `raw`. |
| `envelope_get` / `tap_request` | Read the project's autonomy envelope; request a one-time human approval code for an out-of-envelope action. |
| `memory_write` / `memory_log` / `memory_list` | Project memory in Common Ground page shape (local mirror + outbox until CG sync is on). |
| `pr_status` | Mergeability, checks and reviews from GitHub. |
| `merge_enqueue` / `merge_queue` / `merge_dequeue` | Ordered merges: base merged in, re-gated, re-reviewed if the interdiff changed. |
| `envelope_check` / `tap_confirm` | Decide allow / tap / never for an external action; confirm Nick's one-time code. |
| `jev_label` / `scorecard_export` | Label Jev calls with real outcomes; export the sprint scorecard. |
| `deploy_run` / `deploy_status` / `deploy_rollback` | Deploys with smoke checks and rollback (Helm v4 C2a; only if present in your tool list). |
| `pr_merge` | Merge — only when open, not draft, mergeable, all checks green, head matches. |
| `run_status` | Spend against the cap, active workers. |

## The loop, per ticket

1. **Brief.** Write a self-contained objective: the ticket, the files and docs to read, the
   acceptance criteria, what *not* to touch. Pass long context as `contextPaths`, not inline.
   A worker knows nothing you did not give it.
2. **Spawn** with `worker_spawn` (`repo`, `objective`, `model`, `baseRef`, `acceptance`,
   an `idempotencyKey` so a retried call never double-spawns).
3. **Wait** with `worker_wait` and go quiet. On `timedOut: true`, call it again. Pass several
   ids to wake on whichever settles first. Never loop on `worker_inspect`.
4. **Judge the result** from `worker_inspect` — the worker's own summary and diff stat, not the
   full diff. Wrong or incomplete → `worker_steer` with a specific correction.
5. **Gate** with `gate_run`, then `claims_check`. A red gate or flagged claims go back via
   `worker_retry {workerId, kind}` (it names the violation and evidence; capped per kind).
6. **PR** with `pr_open` once the gate is green at the current head.
7. **Review** on a *different model family* from the builder: `review_request` (Helm spawns
   a reviewer), or your own reviewer subagent that posts one comment ending `APPROVE: ` /
   `REQUEST_CHANGES: `. Either way, `review_record` the comment at the PR head; merges need
   it. BLOCKING findings → `worker_retry {kind: 'review'}`, re-gate, re-review.
8. **Merge** with `merge_enqueue` (the queue merges base in, re-gates, and calls `pr_merge` at
   the reviewed head), or `pr_merge` directly with that head if the project has no queue.
   Check `pr_status` first if anything is pending.

Run independent tickets in parallel up to the worker cap; keep dependent ones in sequence.

## Rules that save runs

- **Wait, don't poll.** One `worker_wait` per state change. Polling burns your context for
  nothing.
- **Cheap builders, cross-family reviewers.** Route routine work to the cheapest lane that
  can do it; escalate the model only after a concrete failure. Never let a model review its
  own family's work.
- **The gate is the truth, not the worker.** A worker saying "tests pass" means nothing until
  `gate_run` agrees at that exact head.
- **`baseRef` must exist as a local branch** in the repo you point `worker_spawn` at. After
  creating or moving a branch on the remote, update the local ref before spawning from it.
- **Watch the budget.** Check `run_status` between waves. A `warning` field on a spawn or
  steer result means the soft cap is crossed — slow down and prefer the subscription lane.
- **Workers cannot push, call `gh`, or touch other worktrees.** That is by design; PRs,
  reviews and merges are yours, through the tools above.
- **An `unknown` or `interrupted` worker is resumable.** Steer it; don't respawn and lose its
  worktree.
- **Keep a trail.** Record ticket → worker id → PR in a file in the repo or your scratchpad,
  so a fresh session can pick the run up.

## When the tools are not there

If no `worker_*` tools are available, Helm isn't connected. Point the user at the
[helm3 repo](https://github.com/Nicegarrry/helm3) setup (add `helm serve --stdio` to the
project's `.mcp.json`) rather than improvising a fleet by hand.
