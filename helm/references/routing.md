# Routing and usage budget

**Current ruling: 2026-09-06 (Nick) — "Codex tiered usage".** This file is the ONLY place model
names, effort levels and usage budgets are doctrine. `SKILL.md` and every factory/repo doc route on
the provider-neutral `complexity:<high|medium|low>` label and link here.

**Supersedes**
- 2026-09-05 "Codex use" routing (`~/code/iosdev/_wiki/decisions/2026-09-05-codex-use-routing.md`) —
  sol built `low` and `medium`, sol reviewed both, mechanical went to sol. Replaced: the cheap tier
  was unused and the weekly pool drained in ~8 hours.
- 2026-09-05 mixed-fleet adoption
  (`~/code/iosdev/_wiki/decisions/2026-09-05-mixed-fleet-codex-workers.md`) — "`high` stays Opus
  builder + Opus staff review; `medium`/`low` route to Codex". Replaced by the table below; that
  decision's *mechanics* (tracker as bus, stateless workers, `AGENTS.md` symlink, `codex-ticket.sh`)
  remain in force and live in `fleet-mechanics.md`.
- 2026-08-21 factory orchestration playbook, "Opus workers, one ticket per agent"
  (`~/code/iosdev/_wiki/decisions/2026-08-21-factory-orchestration-playbook.md`) — single-provider
  Opus fleet. Its non-routing sections (waves, merge train, ship pipeline, disk janitor) still hold.

This table is the seed for `helm.toml` in the helm CLI (spec: `~/code/other/helm-cli/docs/spec.md`).

## Fleet composition

The coordinator stays Claude; workers are provider-mixed and routed by the ticket's complexity
label. Goal: Codex carries the volume, Claude carries judgement, and two providers reviewing each
other gives real adversarial pressure (on marlo, a Codex review of PR #61 found six blockers the
Opus-built branch's own gate had called green).

Models verified live on this machine via `codex exec` (2026-09-05): `gpt-5.6-sol` (workhorse),
`gpt-6-astra` (frontier; efforts up to `max`/`ultra`), `gpt-5.6-terra`/`-luna`. Claude: Fable
(coordinator), Opus (selective second reviewer), Sonnet (rare, mechanical).

## Routing table (2026-09-06)

| Role | Default | Notes |
|---|---|---|
| Coordinator | Fable (Claude) | charts, dispatches, merges, rules; never a worker |
| Builder `complexity:low` | Codex `gpt-5.6-terra`, effort high | one ticket, worktree, PR-only |
| Builder `complexity:medium` | Codex `gpt-5.6-sol`, effort high | one ticket, worktree, PR-only |
| Builder `complexity:high` | Codex `gpt-6-astra`, effort xhigh | **Fable reviews** (coordinator or a fork) — astra never reviews its own build |
| Staff review `low` | Codex `gpt-5.6-terra`, effort xhigh | fresh session, detached review worktree |
| Staff review `medium` | Codex `gpt-5.6-sol`, effort xhigh | fresh session, detached review worktree |
| Staff review `high` | Fable (Claude) | only Fable and astra review `high` |
| Fix round | same tier as the build | a `high` fix returns to astra only for a design-level blocker; otherwise sol |
| Selective Opus adversarial review | Opus (Claude) | on `medium`: any privacy/security/data-loss seam, a sol APPROVE with zero blockers on a large diff, or coordinator judgement — named in the dispatch |
| Verify pass | same provider/model as the reviewer | re-runs its own probes |
| Wave-close / milestone gate | `gpt-6-astra` xhigh, read-only | written brief → written report; the coordinator TESTS the conclusions before folding any in |
| Thought partner / blind A/B | `gpt-6-astra` xhigh, read-only | coordinator commits its own position in writing first, then reads, then records deltas + ruling |
| Mechanical | Codex `gpt-5.6-terra`, effort medium | issue creation, bulk edits, config |

## Budget rules (2026-09-06)

The weekly Codex allowance is ONE pool across models. The 2026-09-05 marlo run used only astra + sol
at 5–8 concurrent sessions, mostly `xhigh`, and drained the week in ~8 hours (limit 21:40 AEST,
reset Sep 12 18:34); the volume then fell to the Claude fleet, which hit the Claude 5-hour limit at
03:41 the same night. Two fleet deaths in one night, both avoidable.

1. **terra is the default** for anything `low` or mechanical; sol is reserved for `medium`; astra for
   `high` builds and at most ONE read-only gate or A/B per wave close.
2. **`high` effort for builds, `xhigh` only for reviews.** `max`/`ultra` never without the user.
3. **Re-tier UP only after the lower tier has failed the ticket**, with a comment saying why. Never
   start higher "to be safe".
4. **Plan the week:** target ≲15% of the pool per day, ≤4 concurrent Codex sessions, ≤2 concurrent
   gates. The machine's slot lock is the real ceiling (load >900 with six simulators on 09-05).
5. **A usage-limit message is a fleet death.** Parse the reset time, record it in the wiki/handoff,
   chain wakeups — and do NOT replay the same burst on the Claude fleet.

## Cross-provider review rules

1. A PR is never built and reviewed by the same *session*. sol may review a sol build in a fresh
   session (Nick's ask). Cross-model review is **mandatory on `high`** (astra builds → Fable reviews)
   and **selective on `medium`** (Opus).
2. Only Fable and astra review `high`.
3. Opus is a selective second reviewer, not the default — say why in the dispatch.
4. A/B outcomes are written down: `_wiki/decisions/` for map-level, the ticket for ticket-level.
5. Fan-out cap 4 concurrent worker sessions (collision surface and machine load, not tokens);
   stagger during heavy phases.
6. `scripts/codex-ticket.sh` picks the model from role + label; `CODEX_MODEL` / `CODEX_EFFORT`
   override per dispatch. `scripts/codex-ask.sh <brief> [model] [effort]` runs a read-only
   thought-partner/gate pass over a detached `origin/main` worktree.

## When there is no Codex allowance

Fall back to a single-provider Claude fleet on the same complexity tiers (this is the pre-2026-09-05
routing, kept here so the model names survive): coordinator Fable; `high` worked by the coordinator
or by an Opus builder with a Fable review; `medium` Opus builder + Opus staff review; `low` and
mechanical Sonnet. Reviews stay one tier at or above the builder. The Claude 5-hour window is then
the binding constraint, so budget rules 4 and 5 apply unchanged to the Claude fleet.
