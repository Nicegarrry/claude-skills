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
| `review_request` | Spawn a read-only reviewer on the PR head; it posts its verdict as a PR comment. |
| `pr_status` | Mergeability, checks and reviews from GitHub. |
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
5. **Gate** with `gate_run`. A red gate goes back to the worker via `worker_steer` with the
   failing check named.
6. **PR** with `pr_open` once the gate is green at the current head.
7. **Review** with `review_request` on a *different model family* from the builder (the tool
   refuses same-family by default — keep it that way). Treat BLOCKING findings as a steer
   back to the builder, then re-gate and re-review.
8. **Merge** with `pr_merge`, passing the head SHA you reviewed. Check `pr_status` first if
   anything is pending.

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
