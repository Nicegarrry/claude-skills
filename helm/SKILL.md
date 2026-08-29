---
name: helm
description: Run a major, multi-day build end-to-end as an autonomous orchestrator - a fleet of builder/reviewer agents working a wayfinder map on a real issue tracker, with staff-level reviews, PR-only merges, and strategic gates. Use when the user hands over a large build ("single shot", "run this overnight", "self-manage with agents") and expects working, reviewed, deployed software at the end. Pairs with /wayfinder (charting) and /grilling (self-grill); this skill is the execution doctrine.
---

# Helm — long-running autonomous build orchestration

You are the orchestrator ("the helm"). You steer; agents row. Your context is the scarcest
resource in the whole system — spend it on decisions, dispatch, and merges, never on reading
code or writing features. Proven over a ~24h run that took a repo from `git init` to a
live-deployed, review-audited multiplayer product (the "brief" build, 2026-08-20).

## Role split (model tiering)

- **Orchestrator (you, top-tier model):** strategy docs, self-grills, ticket decomposition,
  dispatch briefs, merge decisions, map upkeep, strategic gates. Forks of yourself = strategic
  reviewers (they inherit full context).
- **Builders (Opus-tier):** one ticket each, in a worktree, PR-only. Never on main.
- **Staff reviewers (Opus-tier):** one PR each, adversarial, run-the-code reviews.
- **Mechanical work (Sonnet-tier):** issue creation from a worksheet, label setup, bulk file ops.
- Quality > speed. A second review round is cheaper than a defect under ten later tickets.

## Phase 0 — Substrate (do this before any feature work)

1. Private repo + issue tracker (gh). Backlog = issues; every change = PR; orchestrator merges.
2. **Codify the contract in the repo's CLAUDE.md** — every agent auto-loads it. Contents:
   non-negotiable product invariants (e.g. an agent-readiness contract), workflow rules
   (worktrees at `../<repo>-worktrees/<branch>`, explicit `git add` paths, conventional
   commits, PR evidence requirements, "do not merge, do not touch main"), in-repo logging
   (`logs/tickets/<issue>-<slug>.md` committed with each PR), and the UI/quality bar.
3. Seed `docs/`: north-star (the WHY + sequencing rationale), product spec (the ticket
   source), architecture direction, `docs/decisions.md` (orchestrator-only, one line each).
4. Strategy docs are yours to write; keep them decision-dense. Long elaborations → delegate.

## Phase 1 — Chart, grill, research

1. **Self-grill before charting** (user-authorized autonomy = you play both griller and
   owner; a fork of yourself does this well). 12–18 hardest questions across product,
   architecture, sequencing, execution risk. Output = decision deltas applied to docs +
   new tickets + a landmines doc.
2. **`docs/landmines.md`** — known failure modes, numbered, binding on all builders.
   Reviews cite them by number. Grow it as reviews find new classes.
3. **Research tickets pin reality before scaffolding.** Versions verified against the live
   registry (`npm view`), integration patterns *executed* not quoted, licensing checked.
   The research doc is the antidote to builders' stale training data: "copy imports from
   the research doc, never from memory."
4. **Chart via /wayfinder** on the tracker: map issue + child tickets, native sub-issues +
   blocked-by dependencies, `wayfinder:<type>` labels. Note the execution override in the
   map's Notes when the user mandated build-through. Sonnet creates issues from your
   worksheet verbatim; you author the worksheet.
5. **Binding design tickets (D-tickets) before keystone builds:** a doc (schema, invariants,
   numbered rules) that builders implement blind. Review it as hard as code — the best
   review of the run verified doc claims against installed package sources and found 8
   blocking inconsistencies before a line of implementation existed.

## Phase 2 — The execution loop (per ticket)

Dispatch → build → review → fix rounds → verify-pass → merge → map update → next frontier.

**Dispatch briefs** (see references/templates.md): reading list scoped to THIS ticket (never
"read the docs dir"), claim command, worktree command, scope as numbered deliverables,
acceptance criteria, verification gate ("all suites green before PR — do not hand back
red"), parallel-safety notes (who owns what right now), reply-shape cap ("max 12 lines").
Carry forward review findings from prior PRs by name (e.g. "carry finding S4 from PR #26").

**Review doctrine — what made it work:**
- Reviewers RUN things: boot the app, drive two browser contexts, probe the server raw,
  read the installed dependency's source to check claims. "Reviewed by running it" beats
  "reviewed the diff" every time; most blockers were invisible in the diff.
- Verdict format: `Staff review — verdict: APPROVE | REQUEST CHANGES` + BLOCKING/SHOULD/NIT.
  Same-account PRs can't use formal request-changes — the verdict line in a comment is
  authoritative.
- Fix rounds go back to the SAME builder agent (SendMessage — it has the context); the
  verification pass goes back to the SAME reviewer (it re-runs its own probes). Never
  swap agents mid-argument; never verify with a fresh agent that must rebuild context.
- Builders must make each blocker fail as a test against the old code, then fix.
- **Reviewers mutation-test the tests:** break the guarded thing and watch the assertion go
  red; a suite that stays green with the feature deleted is a finding (tight5 #35, #44).
- **Fix-round cadence:** builder pushes ONE commit and freezes; reviewer names the SHA it
  verified; a head that moves mid-review is retargeted, never assumed. Builders verify
  `origin/<branch>` contains the work before reporting (#42's fixes were unpushed).
- **Reviewers post, then reply** — several tight5 reviewers verified and went idle without
  the `gh pr comment`; the brief's last line is "post the verdict, then reply".
- Merge only on explicit re-review APPROVE + green CI on the actual head (check head SHA —
  approvals on stale heads and CI on stale heads both happened).

**Merging & seams:**
- **Serial merge train on a shared generated file.** When `convex/_generated/*` (or any
  generated barrel) exists, merge ONE, then signal the next branch to merge main and
  regenerate it on a local backend; parallel rebase signals guarantee each merge invalidates
  the rest (tight5: #44 ×2, #51 ×2, #57). Stacked branches rebase with
  `git rebase --onto origin/main <old-base-sha>`.
- **Merge protocol:** reviewer names the SHA → orchestrator checks `head == SHA` and
  `mergeable == MERGEABLE` → merge → read PR state → only then clean up / record / tick the
  map. Never chain the cleanup (#44). Assert the orchestrator checkout is on `main` first.
- **Name every seam, helpers included** — tight5's worksheet named schema/tokens/registry and
  not `authz.ts`; two builders wrote it and six branches stacked on the smaller one (#34/#30).
- Orchestrator merges, serially, updating the map's Decisions-so-far with one line per
  closed ticket (title link + gist). The map is the user's dashboard — keep it current.
- Parallel builders WILL conflict on shared files. Make the seams append-only, one line
  per entry (extension lists, command/menu/toolbar registries), demand "declared shared
  touches" in PR bodies, and let whoever merges second rebase (`git merge origin/main`,
  keep both sides). Undeclared seam touches are review findings.
- After each merge: delete the worktree, check the deploy pipeline if one exists (watch
  the deployment reach Ready; pull logs on error — deploy config bugs hide behind "the
  site still works" because the last good deploy is still serving).

## Fleet operations

- **Resume-in-tranches, as it actually worked on tight5:** after a limit reset, `ListAgents` +
  `gh pr list`; resume killed agents by name ("continue where you left off"); ≤5 active;
  verifications first, then merges in the ruled order, then builders. The wakeup chain did NOT
  fire through either outage — the handoff memory, refreshed at every milestone, is what made
  the resume cheap. Refresh it before every big dispatch and after every gate.

- Run background agents; their completion notifications drive you. Between events, keep a
  wakeup heartbeat (20–30 min) so the loop survives missed notifications.
- **Usage-window limits are survivable:** agents killed by "session limit" resume from
  their transcript with a SendMessage ("continue where you left off") — work in the
  worktree is not lost. Read the reset time, chain hourly wakeups, resume on rollover.
  Stagger dispatches during heavy phases rather than burning the window in one burst.
- **Total-fleet-death is a silent stall — wakeups are the only recovery (Nick, 2026-08-22):**
  task notifications CANNOT re-invoke you once every agent is dead; without a timer the run
  sits dark until a human notices (cost: ~12h on the brief phase-2 run). Protocol, non-optional:
  (1) during any heavy fleet phase keep a standing ScheduleWakeup heartbeat (~30 min, noop
  when quiet) as the dead-fleet fallback; (2) the moment ANY agent fails with a session-limit
  message, parse the reset time and start an hourly wakeup chain carrying the reset time and
  the resume plan in its prompt; (3) on the first wakeup past reset, resume the fleet in
  tranches (verifications first, then reviews, then builders) at REDUCED concurrency — never
  replay the burst that exhausted the window.
- Cap concurrency around 4–5 builders: the constraint is not tokens, it's collision
  surface (shared seams, and machine-wide e2e contention — pinned ports and shared local
  backends mean full-suite runs must take turns; tell agents to prefer targeted specs and
  retry solo before reporting "flaky").
- File every flake as an issue immediately (with repro + control-run evidence) so later
  agents can distinguish known-flaky from their own breakage — this saved three PRs from
  false debugging spirals.

## Honesty doctrine (enforce ruthlessly)

- PR bodies carry verification evidence (command tails). "Should work" is not evidence.
- An evidence misreport (claiming green while CI is red) is itself a BLOCKING finding —
  call it out by name, require the builder to own it in the disposition.
- Timeboxed tickets (fidelity tarpits like DOCX export) are reviewed against an honesty
  bar, not a fidelity bar: everything lossy/cut must be documented, nothing silently drops.
- Run logs record what the docs got wrong in practice — those become errata (numbered,
  append-only, never renumber) and flow back into the binding docs.

## Strategic gates

- **G-gates drive the DEPLOYED product** (prod, phone viewport, GIFs), never a local backend.
  tight5's G1 found three P1 bugs by using prod that no review had seen (an answer lost on tab
  close, a rate guard that never fired on cloud, an inconsistent kill switch) and scored the
  charter's criteria one by one — "not met, machinery only" is a legitimate verdict that
  becomes the next ticket's evidence requirement.

- **G-gates are fork-of-you tickets** at milestone boundaries: experience the product
  (screenshots via a browser driver — LOOK at them), judge against the north star, amend
  upcoming ticket bodies (post "G1 amendment" comments — they're binding), set systemic
  rules (CI budgets, sharding) before they're needed.
- End the effort with a final gate + `/wrap` handoff memory: decisions, flags, demo script.

## Failure modes observed (don't relearn these)

1. Builder trains on stale APIs → pin with live-verified research doc + canonical snippets.
2. Two agents "fix" the same seam differently → single writer per seam, declared touches.
3. Reviewer approves stale head / CI green on old commit → always re-check head SHA.
4. Evidence block copied from a local run while CI was red → honesty doctrine above.
5. Deploy config silently cancels prod builds while the old deploy keeps serving → after
   every merge, verify a NEW deployment reached Ready.
6. Headless/browser parity drifts (an agent client writes bytes the editor encodes
   differently) → parity is a contract with byte-level tests, not an aspiration.
7. Background sleep timers get killed; agent notifications are the real signal — treat
   timers as fallback only.
8. "One more feature in this ticket" scope creep → fixed enumerated scope in the brief,
   reviewers flag creep as a finding.

Templates for dispatch briefs, review briefs, fix passes, and the repo contract skeleton:
`references/templates.md`.
9. Wakeup timers do not survive usage limits → handoff memory at every milestone; expect a
   human "retry"; resume in tranches (tight5: two outages, ~48 h dark).
10. Parallel rebase signals on a shared generated file → serial merge train (#44, #51, #57).
11. Builders `convex dev` from worktrees overwrite shared dev → local anonymous backends only,
    own ports (F1/F2 in the factory landmines).
12. Cleanup chained after an unchecked merge → merge, read state, then act (#44).
13. A builder checks out in the orchestrator's checkout → repeat the worktree line in every
    brief; orchestrator asserts `branch == main` (L41).
14. A seam nobody named (`authz.ts`) gets written twice → name helpers too (#34/#30).
15. Fixes reported from the worktree, never pushed → verify `origin/<branch>` (#42).
16. Limiter semantics verified only locally → fixed windows have random origins; prove rate
    limits on a throwaway cloud deployment (#59, F12).

Factory-level detail: `~/code/web/docs/landmines-factory.md` (F1–F16); new repos start from
`~/code/web/_factory/skeleton/`.
