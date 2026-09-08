# Fleet mechanics

Provider-neutral mechanics for running a mixed fleet under one coordinator. Doctrine is in
`../SKILL.md`; model names and budgets are in `routing.md`; brief text is in `templates.md`.

## The tracker is the message bus, not agent messaging

The issue tracker carries every hop, so any worker — resumable or not — can be picked up, killed, or
replaced without losing the thread:

| Hop | Where it lives |
|---|---|
| Brief | an issue comment titled `Dispatch brief (<adapter>)` — the literal `Dispatch brief (codex)` for Codex workers, which `codex-ticket.sh` matches with `startswith` |
| Report | the PR itself (body carries the evidence tails) |
| Verdict | `gh pr review <PR> --comment`, titled `Staff review — verdict: …` |
| Fix round | the review comment + the PR number, handed back to the builder role |
| Verification | the disposition + the original review, handed back to the reviewer role |
| Run log | `logs/tickets/<N>-<slug>.md`, committed with the PR |

The run log, the PR body and the review thread carry ALL context a dispatch needs. Write briefs so
that is true — a brief that depends on what an agent "already knows" cannot survive a fleet death.

## Worker adapters: resumable vs stateless

The ruling (2026-09-06 consolidation, reconciling the helm skill's "same builder agent" rule with the
mixed-fleet "workers are stateless" rule — both were true of their own adapter):

- **Resumable workers (Claude subagents).** They hold a transcript. A fix round goes back to the SAME
  agent by message ("Staff review on PR #P: REQUEST CHANGES …"); a killed agent resumes with
  "continue where you left off" and its worktree is intact. Never swap agents mid-argument.
- **Stateless workers (`codex exec` and anything else invoked per-run).** There is no transcript. A
  fix round is a FRESH invocation carrying the PR number and the review comment; a verification is a
  fresh invocation in the reviewer role. This is not a downgrade — it is why the tracker must carry
  everything, and it is how Claude fix rounds effectively worked anyway.
- **Both honour the same doctrine:** the same ROLE continues the argument, and the verification pass
  re-runs the reviewer's own probes. "Same role" is satisfied by resuming an agent or by re-invoking
  one with the full thread; it is never satisfied by a different reviewer starting fresh.
- **The standing heartbeat is non-optional for both** (Nick, 2026-08-22). Poll the tracker
  (`gh pr list`, review comments) on a ~20–30 min wakeup during any heavy phase. A stateless worker
  cannot send a completion notification at all, and a dead Claude fleet cannot either — where
  notifications do arrive they are a latency win on top of the heartbeat, never the safety net.
- **A worker's silence is not a failure.** Final reports often fail to reach the coordinator; an idle
  agent with no message means read the ticket/PR, not "it failed". Queued messages drain late —
  timestamps beat content when reconciling. Deliverable-producing agents write incrementally (append
  per section) so a session death leaves partial work on disk.

## Contract discovery — one contract, both fleets

Every repo carries `AGENTS.md` as a **git symlink to `CLAUDE.md`** (`ln -s CLAUDE.md AGENTS.md`,
committed as a symlink — verify with `git show HEAD:AGENTS.md` printing `CLAUDE.md`). Codex
auto-loads `AGENTS.md`, Claude loads `CLAUDE.md`, and neither fleet reads a duplicated, driftable
copy. That contract carries the "Worker conventions" and "Reviewer conventions" checklists below,
instantiated with this repo's paths and gate command.

## The checklists

These are the canonical generic forms. **Each repo's `CLAUDE.md` carries its own instantiated copy**
— not a pointer — because a stateless worker loads exactly one file (the repo contract) and never
reads this skill. The flow is one-way: this file is the source, the factory skeleton
(`~/code/web/_factory/skeleton/CLAUDE.md`) is the template, a repo's copy is the instance. Changes
land here first.

**Worker conventions**
1. **Claim first** — a comment on the ticket naming your branch and worktree, before any other work.
2. **Worktree from the ticket**, cut from fresh `origin/main`, at the path this repo's workflow rules
   fix. Never build from a stale base; never check out inside another agent's worktree; never in the
   orchestrator's checkout.
3. **Merge `origin/main` into your branch before the final gate run** — the gate must reflect the
   tree you are opening a PR against, with the baseline count the brief stated.
4. **The full gate green BEFORE the PR.** Do not hand back red. Paste the tail in the PR body.
5. **Run log `logs/tickets/<N>-<slug>.md`**, committed with the PR: decisions and what you rejected,
   gotchas, what the docs got wrong (flag it, never silently deviate), gate evidence, what the next
   ticket needs to know about your seams.
6. **Conventional commits, explicit staged paths.** Never `git add -A`, never `git add .`.
7. **PR titled `[#N] <title>` with `Closes #N`**, evidence tails (command output, not prose), and
   every shared-file touch declared at the top of the body.
8. **Mutation-test your own guards and say so in the run log** — break the thing a new test claims to
   guard and confirm the assertion goes red before reporting the suite green.
9. **Never merge, never touch `main`.** Disposition replies go on the PR, not in agent messages.

**Reviewer conventions**
1. **Detached, throwaway review worktree** — never inside the builder's worktree. Name the exact head
   SHA you reviewed; a head that moves mid-review is retargeted, never assumed.
2. **Run the gate and run the app.** "Reviewed the diff" is not "reviewed by running it". For UI,
   run it and screenshot it, then LOOK at the screenshots.
3. **Mutation-test the tests.** Break the guarded behaviour; a suite that stays green with the
   feature deleted is itself a BLOCKING finding.
4. **Probe adversarially** — the scenarios worth constructing for THIS ticket, not a generic pass.
5. **Cite the spec and the repo contract by section/rule number**, never from memory.
6. **File the verdict via `gh pr review <PR> --comment`.** Title it
   `Staff review — verdict: <APPROVE|REQUEST CHANGES>`, findings graded BLOCKING / SHOULD / NIT.
   A re-review is titled `Re-review — verdict: …` and names the SHA. Post the verdict, THEN reply.
7. **Do not edit files, do not merge.** Clean up the review worktree when done.

## Adapter spawn

- **Inline** — run the worker in the coordinator's own session when it is short and you want the
  result immediately. It blocks; use it for one dispatch, not a fan-out.
- **Under herdr** (`HERDR_ENV=1`), for anything long or parallel:
  `herdr agent start <name> --cwd <worktree> --no-focus -- <worker command>`. Watch with
  `herdr agent wait <name> --status idle` and `herdr agent read <name>`. Never
  `herdr worktree create` for a headless dispatch — herdr worktrees are for interactive panes; use a
  plain `git worktree add <path> -b <branch> origin/main`.
- **Wrap the dispatch in a repo script.** `scripts/codex-ticket.sh <N> build|review|fix|verify [PR]`
  resolves worktree and branch from the ticket, creates the worktree if missing, pulls the brief or
  review from the tracker, composes the role prompt, picks the model from role + label
  (`routing.md`), and runs the worker. `--spawn` runs it under herdr instead of inline; `--dry-run`
  resolves everything without creating a worktree or spending anything.
  `scripts/codex-ask.sh <brief> [model] [effort]` runs a read-only thought-partner or gate pass over
  a detached `origin/main` worktree.

## Proven `codex exec` flags (per machine, not per repo)

- **Write mode:** `--approve-for-me -c sandbox_workspace_write.network_access=true`. Never pass
  `-s`/`--sandbox` alongside `--approve-for-me` — the CLI rejects the pair, and `--approve-for-me`
  already implies the workspace-write sandbox. Network access is required: `gh` push and `npm` need it.
- **Read-only runs** (reviews, gates, thought-partner): `--sandbox read-only` with `-o <file>` for
  the answer.
- **Non-TTY stdin gotcha:** `codex exec` in a non-TTY MUST get `< /dev/null` (or a wrapper that
  closes stdin), or it blocks forever on "Reading additional input from stdin".
- **Per-exec model/effort only:** `-c model=… -c model_reasoning_effort=…`. Never edit the user's
  `~/.codex/config.toml`.
- Prove the sandbox/network flags once per machine (a trial that reads a file, runs `git status`, and
  makes a networked `gh` call) and pin them in the script. The sandbox is machine-level CLI
  behaviour, so a per-repo re-proof is wasted.

## No extra orchestration layer

The tracker + worktrees + PR-only merges already ARE the protocol. Another coordination layer
(omniagent, pi, or similar) adds a failure surface and no capability.

## Dispatcher contract learned on marlo (2026-09-09)

Evidence: `~/code/iosdev/_wiki/decisions/2026-09-09-helm-learnings-marlo-build1.md` §2, §5, §6.
These are the behaviours of `scripts/codex-ticket.sh` as it ended the run; a new repo's dispatcher
should reproduce them and a coordinator should assume them.

- **`## Wave` line in the ticket BODY**, never a comment: `` `w6` · branch `x` · worktree `~/code/<factory>/<app>-wt-<slug>` ``.
  The dispatcher resolves worktree and branch from it and creates the worktree with a plain
  `git worktree add <path> -b <branch> origin/main` when absent. Worktrees never under `/tmp`.
- **`build` hard-resets an existing worktree to `origin/<branch>`; `fix` reuses it without reset.**
  Commit and push any WIP a dead session left before re-dispatching `build` — and diff that WIP
  against the branch's tests first (it was once a mutation harness).
- **`fix` requires a formal review on the PR and reads the LATEST non-empty review body.** A
  coordinator ruling posted with `gh pr review --comment` replaces that text: every coordinator note
  embeds the original review verbatim. With no review at all, merge main by hand and dispatch
  `review`, not `fix`.
- **`review` refuses a stale `<app>-wt-review-<PR>` worktree; `verify` refuses without the reviewer's
  `CODEX_MODEL` and `CODEX_EFFORT` replayed** from the review dispatch. Both fail quietly enough to
  warrant a `--dry-run` first.
- **`complexity:<high|medium|low>` is required and singular**; the script refuses zero or two labels.
  A `high` review or verify refuses to run on the builder's tier.
- **Gate evidence is SHA-bound.** `GATE GREEN` names the SHA it ran on; commits above it are legal
  only if they touch nothing outside `logs/tickets/` or are a clean merge of `origin/main`.
- **Gate once per PR** (reviewer convention 2, Nick 2026-09-07): first review checks the SHA-bound
  block and runs only the touched suites plus ≤2 mutation probes and the changed screens' e2e flows;
  the verify-before-merge round runs the one full gate the reviewer owns; docs-only or merge-only
  re-reviews run a SHA check only; one prebooted review simulator per PR, deleted on the merge-round
  APPROVE. A review that skipped a gate says so and names the builder's block it relied on.
- **Verdicts never wait for a CI that does not exist**; the gate script is the CI (say so in the
  review template).
- **Spawned panes are pinned to the helm's own herdr workspace** (`HERDR_*` env), and only sessions
  with `-C <this repo>` count toward the cap — other factories share the machine.

## Fleet-ops checklist learned on marlo (2026-09-09)

- **On resume, first:** kill any monitor from the previous session, re-arm the heartbeat and the
  monitor, THEN read state.
- **Heartbeat cadence:** 30 min in heavy fleet phases, 60 min idle, ~25 min while an external state
  (a beta review, a deploy) is actively moving.
- **Heartbeat duties, every beat:** clear stale gate slots (`kill -0` the owner pid); delete orphaned
  gate simulators whose pid is dead; `scripts/sweep.sh --quiet`; `df`; `gh pr list --state open`;
  check each long-running process is alive (`pgrep`), not just its log; hold new dispatches while
  load > 150.
- **Monitor patterns (whole-line):** `^tokens used` (the only session-end marker),
  `^ERROR: You've hit your usage limit`, `^ERROR: Selected model is at capacity`,
  `No space left on device`, `^thread '.*' panicked at`, the repo's Codex process count, free disk
  under a floor, open-PR head changes. Substring matches on "usage limit" produce false positives
  from any log that reads a file containing those words.
- **Long runs:** `nohup … & disown` (Bash background tasks cap at 10 min) + a `tail -f | grep`
  monitor + a `pgrep` liveness loop; a monitor alone missed a `SHIP-*-EXIT` line once.
- **Sweep is orchestrator-only** and decides liveness from the tracker and process table: a running
  worker, an open PR, a ticket in a live brief, a live gate sim pid, the human's demo sim, or a
  modification in the last 6 h keeps a thing; everything else (merged worktrees + branches, review
  worktrees of closed PRs, dead sims, stuck `Deleting-*` sims, per-ticket tmp, scratch derived data,
  worker rollouts older than two days) is reclaimed. The gate fails fast under 8 GB free.
- **Kill one pid per call, and `ps -o command` it first** — a running gate was killed on an `lsof`
  match once.
- **Handoff = a running log** refreshed at every milestone, ~30 timestamped sections, ending in a
  resume checklist per open PR (head SHA, blocker, dirty/unpushed worktrees). Both fleet deaths on
  marlo were resumed from this file; the wakeup chain never fired through either outage.
- **Clearing the coordinator kills its Claude subagents but not its Codex fleet** — plan resumes
  around that asymmetry.
