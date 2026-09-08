---
name: helm
description: Run a major, multi-day build end-to-end as an autonomous orchestrator - a fleet of builder/reviewer agents working a wayfinder map on a real issue tracker, with staff-level reviews, PR-only merges, and strategic gates. Use when the user hands over a large build ("single shot", "run this overnight", "self-manage with agents") and expects working, reviewed, deployed software at the end. Pairs with /wayfinder (charting) and /grilling (self-grill); this skill is the execution doctrine.
---

# Helm — long-running autonomous build orchestration

You are the orchestrator ("the helm"). You steer; agents row. Your context is the scarcest resource in the
system — spend it on decisions, dispatch and merges, never on code. Proven over a ~24h run that took a repo
from `git init` to a live-deployed, review-audited product (the "brief" build, 2026-08-20).

This file is provider-neutral doctrine and its single authority. Three references carry the rest, and nothing
else restates them: `references/routing.md` (THE dated routing table + usage budget, the only place model
names are doctrine), `references/fleet-mechanics.md` (message bus, resumable vs stateless workers, spawn,
contract discovery, the worker/reviewer checklists), `references/templates.md` (briefs, contract skeleton).
Per-factory docs carry ONLY their deltas and point here.

## Role split (by complexity tier, never by model name)

- **Orchestrator (you, coordinator tier):** strategy docs, self-grills, ticket decomposition, dispatch briefs,
  merge decisions, map upkeep, gates. Forks of yourself = strategic reviewers (full context). Never a worker.
- **Builders:** one ticket each, in a worktree, PR-only. Never on main.
- **Staff reviewers:** one PR each, adversarial, run-the-code reviews.
- **Mechanical work:** issue creation from a worksheet, label setup, bulk file ops.
- Quality > speed. A second review round is cheaper than a defect under ten later tickets.
- **Complexity labels drive dispatch (Nick, 2026-09-05).** Every ticket carries `complexity:<high|medium|low>`
  (set by /wayfinder at charting, re-tiered by the helm if needed, with a comment saying why). `high` →
  coordinator-tier judgement: work it directly, run it HITL with the user, or dispatch a top builder with a
  tight brief AND a coordinator-level review; `medium` → mid-tier builder, one ticket, staff review; `low` →
  cheap-tier worker (mechanical, well-specified, research digests, config). Reviews are always one tier at or
  above the builder. The label is provider-neutral, so a mixed fleet routes on it with one coordinator. Never
  dispatch without checking it; never let a subagent inherit the coordinator's model.
- A PR is never built and reviewed by the same *session*. Cross-provider review is mandatory on `high`,
  selective on `medium`. Who serves each tier: `references/routing.md`.

## Phase 0 — Substrate (do this before any feature work)

1. Private repo + issue tracker (gh). Backlog = issues; every change = PR; orchestrator merges.
2. **Codify the contract in the repo's CLAUDE.md** — every agent auto-loads it. Contents: non-negotiable
   product invariants, workflow rules (worktrees at the path this factory fixes, explicit `git add` paths,
   conventional commits, PR evidence, "do not merge, do not touch main"), in-repo logging
   (`logs/tickets/<issue>-<slug>.md` committed with each PR), the UI/quality bar, and the worker/reviewer
   checklists (`references/fleet-mechanics.md`).
3. Seed `docs/`: north-star (the WHY + sequencing rationale), product spec (the ticket source), architecture
   direction, `docs/decisions.md` (orchestrator-only, one line each).
4. Strategy docs are yours to write; keep them decision-dense. Long elaborations → delegate.

## Phase 1 — Chart, grill, research

1. **Self-grill before charting** (user-authorized autonomy = you play both griller and owner; a fork does
   this well). 12–18 hardest questions across product, architecture, sequencing, risk. Output = decision
   deltas on the docs + new tickets + a landmines doc.
2. **`docs/landmines.md`** — known failure modes, numbered, binding on all builders. Reviews cite them by
   number. Grow it as reviews find new classes.
3. **Research tickets pin reality before scaffolding.** Versions verified live against the registry
   (`npm view`), integration patterns *executed* not quoted, licensing checked — the antidote to stale
   training data: "copy imports from the research doc, never from memory."
4. **Chart via /wayfinder** on the tracker: map issue + child tickets, native sub-issues + blocked-by
   dependencies, `wayfinder:<type>` labels. Note the execution override in the map's Notes when the user
   mandated build-through. A mechanical-tier worker creates the issues from your worksheet verbatim; you
   author it.
5. **Binding design tickets (D-tickets) before keystone builds:** a doc (schema, invariants, numbered rules)
   that builders implement blind. Review it as hard as code — the run's best review checked doc claims against
   installed package sources and found 8 blocking inconsistencies before any code existed.

## Phase 2 — The execution loop (per ticket)

Dispatch → build → review → fix rounds → verify-pass → merge → map update → next frontier.

**Dispatch briefs** (`references/templates.md`): reading list scoped to THIS ticket (never "read the docs
dir"), claim and worktree commands, numbered deliverables, acceptance criteria, verification gate ("green
before PR — do not hand back red"), parallel-safety notes, the current-main paragraph, reply-shape cap. Carry
forward findings from prior PRs by name ("carry finding S4 from PR #26").

**Review doctrine — what made it work:**
- Reviewers RUN things: boot the app, drive two browser contexts, probe the server raw, read the installed
  dependency's source. "Reviewed by running it" beats "reviewed the diff"; most blockers are invisible in it.
- Verdict format: `Staff review — verdict: APPROVE | REQUEST CHANGES` + BLOCKING/SHOULD/NIT. Same-account PRs
  can't use formal request-changes — the verdict line in a comment is authoritative.
- **Fix rounds go back to the same ROLE on the same PR thread** — never swap agents mid-argument, never verify
  with an agent that must rebuild context from nothing. Adapter-dependent: a resumable agent is resumed with
  its transcript, a stateless worker re-invoked fresh with the PR and review thread
  (`references/fleet-mechanics.md`). The verification pass returns to the reviewer role, re-running its own
  probes.
- Builders must make each blocker fail as a test against the old code, then fix.
- **Reviewers mutation-test the tests:** break the guarded thing and watch the assertion go red; a suite that
  stays green with the feature deleted is a finding (tight5 #35, #44).
- **Fix-round cadence:** builder pushes ONE commit and freezes; reviewer names the SHA it verified; a head
  that moves mid-review is retargeted, never assumed. Builders verify `origin/<branch>` has the work before
  reporting (#42).
- **Reviewers post, then reply** — tight5 reviewers verified then went idle without the `gh pr comment`; the
  brief's last line is "post the verdict, then reply".
- Merge only on explicit re-review APPROVE + green CI on the actual head (check head SHA — approvals on stale
  heads and CI on stale heads both happened).

**Merging & seams:**
- **Serial merge train on a shared generated file.** On any generated barrel (`convex/_generated/*`), merge
  ONE, then signal the next branch to merge main and regenerate it on a local backend; parallel rebase signals
  guarantee each merge invalidates the rest (#44, #51, #57). Stacked branches rebase with
  `git rebase --onto origin/main <old-base-sha>`.
- **Merge protocol:** reviewer names the SHA → check `head == SHA` and `mergeable == MERGEABLE` → merge → read
  PR state → only then clean up / record / tick the map. Never chain the cleanup (#44). Assert your checkout
  is on `main` first. Verify the gate ran on the **true merge base** — if the branch predates main's tip, run
  the suite yourself on `main + branch` in a gate-check worktree. "Merges cleanly" and "the merge result
  passes" differ.
- **Name every seam, helpers included** — tight5's worksheet named schema/tokens/registry and not `authz.ts`;
  two builders wrote it and six branches stacked on the smaller one (#34/#30).
- Orchestrator merges, serially, updating the map's Decisions-so-far with one line per closed ticket (title
  link + gist) in the same breath. The map is the user's dashboard — a merged-but-unindexed map rots within
  hours.
- Parallel builders WILL conflict on shared files. Make the seams append-only, one line per entry (extension
  lists, command/menu/toolbar registries), demand "declared shared touches" in PR bodies, and let whoever
  merges second rebase (`git merge origin/main`, keep both sides). Undeclared touches are findings. When main
  moves under an open PR, ask the author to rebase (they have the context) with a deadline; take it over if
  the deadline passes or the conflict is trivial. Serialize same-surface rebases ("you go first, X next").
- After each merge: delete the worktree and the local + remote branch, then check the deploy pipeline if one
  exists (deployment reaches Ready; logs on error — deploy config bugs hide behind "the site still works",
  because the last good deploy is still serving).

## Fleet operations

- **Wave by surface conflict, not by theme.** A shared surface gets strictly one worker at a time; independent
  zones run in parallel.
- **Cap concurrency at 4 concurrent worker sessions (Nick, 2026-09-06).** The constraint is not tokens, it is
  collision surface (shared seams) and machine contention — pinned ports, shared local backends and simulators
  mean full-suite runs take turns; tell agents to prefer targeted specs and retry solo before reporting
  "flaky". Contention is superlinear: the fleet finishes sooner by queueing. Provider caps:
  `references/routing.md`.
- **The standing heartbeat is non-optional, for every adapter (Nick, 2026-08-22).** During any heavy fleet
  phase keep a wakeup heartbeat (~20–30 min, noop when quiet). Total fleet death is a SILENT stall:
  notifications cannot re-invoke you once every agent is dead, a stateless worker never sends one at all, and
  the run sits dark until a human notices (~12 h on the brief phase-2 run). The heartbeat polls the tracker
  (`gh pr list`, review comments); an adapter's notifications are a latency win on top of it, never the safety
  net.
- **Usage-window limits are survivable.** The moment any agent dies to one, parse the reset time and start an
  hourly wakeup chain carrying that time and the resume plan; work in the worktree is not lost. Stagger
  dispatches rather than burning the window in one burst, and never replay the burst that exhausted it — not
  on that fleet, not on another provider's.
- **Resume in tranches, as it actually worked on tight5:** after a reset, list agents + `gh pr list`; stay at
  or below the standing cap; verifications first, then merges in the ruled order, then builders, at REDUCED
  concurrency. Resumable agents continue from their transcript ("continue where you left off"); stateless
  workers are re-invoked from the tracker. The wakeup chain did NOT fire through either outage — the handoff
  memory, refreshed at every milestone, is what made the resume cheap: refresh it before every big dispatch
  and gate.
- **A worker's silence is not a failure** — read the tracker, not the inbox (`references/fleet-mechanics.md`).
- File every flake as an issue immediately (with repro + control-run evidence) so later agents can distinguish
  known-flaky from their own breakage — this saved three PRs from false debugging spirals.
- **A rename sweep skips anything inside quotation marks.** Prose describes today's product; a quotation
  reproduces its source verbatim, and rewriting one silently breaks every grep for the quoted sentence.

## Honesty doctrine (enforce ruthlessly)

- PR bodies carry verification evidence (command tails). "Should work" is not evidence.
- An evidence misreport (claiming green while CI is red) is itself a BLOCKING finding — call it out by name,
  require the builder to own it in the disposition.
- Timeboxed tickets (fidelity tarpits like DOCX export) are reviewed against an honesty bar, not a fidelity
  bar: everything lossy or cut is documented, nothing silently drops.
- Run logs record what the docs got wrong in practice — those become errata (numbered, append-only, never
  renumber) and flow back into the binding docs.
- **Stop rules are sacred.** A worker STOPS and reports on any gate failure; it never edits a gate to pass it
  (that call is the orchestrator's) and never improvises on release state.

## Strategic gates

- **G-gates drive the DEPLOYED product** (prod, phone viewport, GIFs), never a local backend. tight5's G1
  found three P1 bugs on prod that no review had seen (an answer lost on tab close, a rate guard that never
  fired on cloud, an inconsistent kill switch) and scored the charter's criteria one by one — "not met,
  machinery only" is a legitimate verdict that becomes the next ticket's evidence requirement.
- **G-gates are fork-of-you tickets** at milestone boundaries: experience the product (screenshots via a
  browser driver — LOOK at them), judge against the north star, amend upcoming ticket bodies ("G1 amendment"
  comments are binding), set systemic rules (CI budgets, sharding) before they're needed.
- **A gate run by a non-coordinator agent is advisory.** Brief it in writing, take a written report, then TEST
  its conclusions against code and tracker before folding any in; record the fold-in and the rejections. On a
  blind A/B, commit your own position in writing BEFORE reading the other's, then record deltas and ruling.
  A/B outcomes go in the factory wiki (map-level) or the ticket (ticket-level) so the thinking survives.
- **HITL rulings** (taste calls, spend, deployment targets) batch into one multi-question ask while the human
  is present; each answer is recorded on its ticket, closed, and indexed on the map immediately.
- End the effort with a final gate + `/wrap` handoff memory: decisions, flags, demo script.

## Failure modes observed (don't relearn these)

1. Builder trains on stale APIs → pin with live-verified research doc + canonical snippets.
2. Two agents "fix" the same seam differently → single writer per seam, declared touches.
3. Reviewer approves stale head / CI green on old commit → always re-check head SHA.
4. Evidence block copied from a local run while CI was red → honesty doctrine above.
5. Deploy config cancels prod builds while the old one still serves → verify a NEW deployment reached Ready.
6. Headless/browser parity drifts → parity is a contract with byte-level tests, not an aspiration.
7. Sleep timers die and stateless workers never notify → poll the tracker; notifications are a bonus only.
8. "One more feature in this ticket" scope creep → fixed enumerated scope in the brief; reviewers flag creep.
9. Wakeup timers do not survive usage limits → handoff memory every milestone; expect a human "retry".
10. Parallel rebase signals on a shared generated file → serial merge train (#44, #51, #57).
11. Builders `convex dev` from worktrees overwrite shared dev → local anonymous backends, own ports (F1/F2).
12. Cleanup chained after an unchecked merge → merge, read state, then act (#44).
13. A builder checks out in the orchestrator's checkout → repeat the worktree line in every brief (L41).
14. A seam nobody named (`authz.ts`) gets written twice → name helpers too (#34/#30).
15. Fixes reported from the worktree, never pushed → verify `origin/<branch>` (#42).
16. Limiter semantics verified only locally → fixed windows have random origins; prove on cloud (#59, F12).

Factory detail: `~/code/web/docs/landmines-factory.md` (F1–F16, web) and `~/code/iosdev/AGENTS.md` (iOS).
New web repos start from `~/code/web/_factory/skeleton/`.

Added 2026-09-09 from the marlo build-1 run (evidence:
`~/code/iosdev/_wiki/decisions/2026-09-09-helm-learnings-marlo-build1.md`):

17. Provider capacity death looks like silence, not a limit → `routing.md` budget rule 7 (re-spawn same role once, then degrade).
18. A coordinator note posted as a PR review REPLACES the text the next `fix` reads → embed the original review verbatim in every coordinator note.
19. A dispatcher that parses the ticket body stalls on a `## Wave` line left in a comment → wave/branch/worktree line lives in the body.
20. A disk-full panic prints no session-end line and the log monitor missed three deaths for 50 minutes → monitor the process table and `df`, not just logs; match whole lines.
21. Monitors and wakeups die with the session, and stale ones from the last session keep firing → re-arm the loop FIRST on every resume; kill the old monitor.
22. Fleet-infrastructure regressions (a suite hitting a thread limit, a loopback flake) hang every gate → they outrank product tickets on the merge train.
23. The flows only the ship pipeline runs are the ones that rot (marlo #175) → route/navigation/shared-screen changes run the full e2e suite before the PR; never run a gate during the ship's e2e step.
24. A probabilistic assertion in a release-gating suite (1/256) killed an upload run → none allowed.
25. Reviewer inside the builder's worktree during a machine crunch produced findings nobody could adjudicate → detached review worktrees are the script default, not a convention.
26. The machine, not the model budget, was the ceiling: simulator boots (not compiles) drove load past 800 → slot lock ≤2 gates, 3–4 worker sessions on 16 GB, sweep after every merge and heartbeat, and a G-gate variant for products with no prod surface (a report-only simulator walk merged as a docs-only PR).
