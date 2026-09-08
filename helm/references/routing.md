# Routing and usage budget

**Current ruling: 2026-09-07 (Nick) — "three-dimension routing, cross-family review, OpenCode Go
as the cheap lane".** This file is the ONLY place model names, tiers, effort levels and usage
budgets are doctrine. `SKILL.md` and every factory/repo doc route on the provider-neutral
`complexity:<high|medium|low>` label plus the seam class and link here.

Evidence base: `~/code/other/helm-cli/docs/routing-proposal-2026-09-07.md` and the two research
reports under `~/code/other/helm-cli/docs/research/` (221 classified tickets across marlo, brief,
tight5, coffeeclub, VG, admiral; live-verified provider facts). This table is the seed for
`helm.toml` in the helm CLI (spec: `~/code/other/helm-cli/docs/spec.md`, D2).

**Supersedes**
- 2026-09-06 "Codex tiered usage" (terra / sol / astra by label, reviews one tier at or above the
  builder). Replaced: the review rule is now cross-family wherever judgement is at stake, seam
  floors override the label, and OpenCode Go supplies T0/T1 below terra. Its budget rules survive
  below, extended with pools.
- 2026-09-05 "Codex use" routing (`~/code/iosdev/_wiki/decisions/2026-09-05-codex-use-routing.md`)
  and 2026-09-05 mixed-fleet adoption (`…/2026-09-05-mixed-fleet-codex-workers.md`). Their
  mechanics (tracker as bus, stateless workers, `AGENTS.md` symlink, `codex-ticket.sh`) remain in
  force and live in `fleet-mechanics.md`.
- 2026-08-21 factory orchestration playbook (single-provider Opus fleet). Its non-routing sections
  still hold.
- The 2026-09-07 marlo re-tier that moved `medium` fix rounds to terra (previously only a comment
  in `marlo/scripts/codex-ticket.sh`) is recorded here as the fix-round row.

## Amendments 2026-09-09 (marlo build 1 evidence)

Source: `~/code/iosdev/_wiki/decisions/2026-09-09-helm-learnings-marlo-build1.md` (rules 1–6) and its
evidence file. Applied to the tables below.

1. **`medium` builds → astra at effort `medium`.** Two trials (marlo #74: 573k tokens, zero fix rounds;
   #23, 83 files: 1.37M tokens, one fix round) against the sol-high baseline (#31: 5.5M tokens, seven
   rounds). Locked on marlo main `ad7fcbb` Sep 7. **Sol is avoided** ("inefficient middle ground",
   Nick Sep 8); it is the fallback only when astra is at capacity. Fix rounds for `medium` stay terra.
2. **Default under budget pressure (Nick, Sep 8): terra for builds, reviews and verifies; astra only
   for `high`/tricky; luna for `low`; no sol; cap 4 concurrent.** Every cap of the week was a human
   reading the dashboard percentage, never a computed figure — treat any pool number not from
   `codex exec --json` `rate_limits` or the dashboard as unverified.
3. **Capacity death is a distinct class from quota death** (budget rule 7 below).
4. **Cheap-tier dispatch rule, sharpened:** luna/T1 bounce on evidence hygiene (SHA-bound gate block,
   `[#N]` title, command tails), never on substance, and could not land a ship-path integration
   (#173). Cheap tier = one file or one script + a machine-decidable oracle, or don't.

## Principles (ruled 2026-09-07)

1. **Route on three dimensions.** The complexity label picks the builder tier. The seam class
   (privacy, security, data loss, screen-by-eye) sets a floor that overrides the label. Review is
   cross-family wherever judgement is at stake.
2. **Family is a property of the model, not of the CLI that serves it.** OpenCode Go carries an
   OpenAI model (GPT 5.6 Luna); a Luna review of a Codex build is same-family.
3. **The reviewer files; the coordinator rules.** Every finding is disposed as defect, convention,
   flake, or needs-ruling, and the disposition is recorded against the reviewer model. Cheap
   tiers fail on calibration, not capability (marlo #78: two of five rounds were arbitration).
4. **Whoever reviews must run the code.** Roughly three quarters of blocking findings in the
   corpus were invisible in the diff. The dispatch prompt mandates the gate, the mutation table
   and screenshots; run-the-code evidence then appears in 96–100% of verdicts at every tier.
5. **Cheap tiers exist to stay inside quota windows.** Quota, not capability, killed three fleets
   in one night on 2026-09-05/06.
6. **A new tier enters only through an A/B on the same ticket** against a T2 control, same
   cross-family reviewer, coordinator blind until disposition. One thrash is a no.
7. **Ticket size scales down with tier (Nick, 2026-09-07).** The cheap-tier successes in the
   corpus were all one file or one script with a machine-decidable oracle and no cross-seam
   reasoning (marlo #68, #80, #98, #77: zero rounds). The thrashes were strategy-sized tickets
   sent to one strong model to "solve and execute" (marlo #33: a million tokens, six rounds).
   The coordinator decomposes before dispatch; the CLI refuses what it can detect.

## Ticket sizing by tier

| Tier | Shape of one ticket | Oracle | Turn budget |
|---|---|---|---|
| T0 (mechanical, `low` with oracle) | one file or one script, one seam, no design choice left open | a named command that decides acceptance, mandatory | ~40–60 |
| T1 | as T0, plus a research digest or a review of a T0/T2 build | mandatory for builds; citation check for digests | ~60 |
| T2 (`low` on terra/Sonnet) | one bounded slice, one seam, spec-stated acceptance | mandatory | ~60 |
| T3 (`medium`) | one vertical slice across at most two seams; the brief names both | tests plus the gate | ~300 |
| T4 (`high`) | strategy plus execution allowed as one unit; design docs, keystones, seams | the gate plus a coordinator-level review | unbounded |

Rules: a `low` or mechanical brief without an `Oracle:` line is refused by `helm dispatch`
("split the ticket or name the oracle"); an attempt that passes its tier's turn budget is
flagged `over_budget` in the ledger and raised to the inbox, never auto-killed in v1; a ticket
that needs a strategy decided before it can be built is re-tiered `high` or split into a
D-ticket and build tickets at charter time. The old pattern of one massive issue to astra to
"work out the approach and then do it" stays legal only at T4.

## The ladder

| Tier | Models (family) | Pool |
|---|---|---|
| T0 bulk | **Qwen3.8 Flash** (qwen; default, Nick 2026-09-07: better on review evidence at $0.013 a ticket against MiMo's $0.008, a difference not worth optimising) and **MiMo-V2.5** (xiaomi; second model; the cross-family reviewer of a Qwen build): the only two Go models ENABLED (keep it simple, known publishers only). Both 3/3 on the planted-defect review probe, Qwen with run-the-code evidence. Muse Spark 1.3 Contributor (meta; cheapest and 3/3) is declared but **gated**: synthetic work only unless Nick names a repo | Go: $12 / 5 h, $30 / week, $60 / month, ONE pool for every Go model |
| T1 mid | **None enabled for now.** Noted from testing, declared and disabled in `[models]`, re-checked on the cadence below: Omen Alpha (best review evidence, but undisclosed publisher: **avoid**, Nick 2026-09-07), GPT 5.6 Luna (openai; Claude builds only), GLM-5.3-Flash (untested); reserve LongCat-2.0, Hy3, Qwen3.7 Plus, Hy4, MiMo-V2.5-Pro, Kimi K2.6, Qwen3.6 Plus; not routed Kimi K2.7 Code (10.9× MiMo, same result), MiniMax M3 (5×, under-severed), MiniMax M2.7 (missed a planted defect), GLM-5.1/5.2 (dominated), Grok 4.6 | same Go pool |
| T1 on the Pro pool | **Codex `gpt-5.6-luna`** (openai): 5 / 0.5 / 30 credits per 1M tokens against terra's 50 / 5 / 300 (rate card, verified 2026-09-07); measured 0.60 credits per ticket against terra's 7.05 on the vendored build task. Builds `low`; reviews Claude, Qwen and MiMo builds; never a Codex build. Takes the `low` build default after A/B 3 against terra | ChatGPT Pro weekly (rolling 7 days) |
| T2 workhorse | Codex `gpt-5.6-terra` (openai); Claude Sonnet (anthropic) | ChatGPT Pro weekly; Claude 5x |
| T3 strong | Codex `gpt-5.6-sol` (openai); Claude Opus (anthropic) | same |
| T4 frontier | Codex `gpt-6-astra` (openai); Claude Fable, coordinator only (anthropic) | same |

**China-hosted models are excluded (Nick, 2026-09-07).** Only `deepseek-v4-flash` and
`deepseek-v4-pro` sit behind the China-hosted opt-in (403 verified on this machine);
`deepseek-v4-flash-vision-exp` is not gated and is excluded on purpose as experimental. OpenCode
states all its models are US-hosted, so the Qwen, GLM, Kimi, MiMo, MiniMax, LongCat and Hy models
are NOT excluded by the ruling. `allow_china_hosted = false` in every repo. Allocation evidence:
`~/code/other/helm-cli/docs/research/go-model-allocation-2026-09-07.md` (16 live runs, $0.22). Observed cost per trivial turn (2026-09-07, each
turn carries ~15k tokens of OpenCode's system prompt; MiniMax M2.7's first reading of $0.00004
did not reproduce, the allocation probe measured $0.0011): GLM-5.3-Flash $0.0012, Muse Spark 1.3 Contributor $0.0016, MiMo-V2.5 $0.0020, Hy3 $0.0022, Omen Alpha $0.0032,
Qwen3.8 Flash $0.0033, GPT 5.6 Luna $0.0036, MiniMax M3 $0.0044, LongCat-2.0 $0.0048, Qwen3.7
Plus $0.0066, MiMo-V2.5-Pro $0.0071, Kimi K2.7 Code $0.0142, Kimi K2.6 $0.0143.

Go models under 1,000 per 5 h (GLM-5.3 220, Qwen3.8 Max 160, Grok 4.6 169, Kimi K3 110) are
frontier-priced and are not routed through Go except as a single wave-close second opinion. A Go
"request" is one model turn; a 150-turn build consumes 150. Allowances verified 2026-09-07 at
https://opencode.ai/docs/go/. Model ids are `opencode-go/<id>`, to be verified against
`opencode models`.

Status 2026-09-07: Go is subscribed and authenticated on this machine (`opencode` 1.18.29 via
`brew install anomalyco/tap/opencode`; credential in `~/.local/share/opencode/auth.json`, provider
id `opencode-go`; `opencode models opencode-go` lists all 27 ids above). Until the helm CLI's
`opencode` adapter lands (M1), T0/T1 work stays on terra; ad-hoc use is
`opencode run --model opencode-go/<id> --format json "<prompt>"`.

## Routing table (2026-09-07)

"Cross" = reviewer family differs from builder family. "Runnable" = detached worktree at the head
SHA, gate, mutation table, screenshots where there is a screen.

| Role | Default | Notes |
|---|---|---|
| Coordinator | Fable (Claude) | charts, dispatches, merges, rules; never a worker |
| Builder `low`, script oracle | T2 `gpt-5.6-terra`, effort high; T1 `gpt-5.6-luna` via Codex in pilot (A/B 3 against terra, medium effort); T0 `qwen3.8-flash` in pilot (A/B 1 against terra) | one ticket, worktree, PR-only; `Oracle:` line mandatory; a Luna build gets a cross review from qwen, mimo or Sonnet, never terra |
| Builder `low`, research digest | T2 terra; T0 `qwen3.8-flash` in pilot (`mimo-v2.5` where 1M context matters) | citation check is mandatory in review |
| Builder `medium` | T4 `gpt-6-astra`, effort **medium** (amended 2026-09-09; was T3 sol high) | one ticket, worktree, PR-only; sol high only as the fallback when astra is at capacity |
| Builder `high` | T4 `gpt-6-astra`, effort xhigh | coordinator-level review by whichever family is neither the builder's nor the scarce one this week (Fable, or sol/astra xhigh cross inside Codex when Anthropic usage is being protected); astra never reviews its own build |
| Mechanical (tracker ops, bulk edits, config) | T0 `qwen3.8-flash` in pilot (`mimo-v2.5` second); terra effort medium until then | script oracle, no review |
| **Floor: UI by eye** (any label) | T3 build with the simulator loop | T3 cross review, screenshots looked at; no cheap-tier success exists |
| **Floor: privacy / security / data-loss seam** (any label) | T4 build | T4 cross review; Opus second read when the build was Codex; the supervisor never dispatches these |
| Staff review `low` | T2, fresh session, runnable; cross preferred (Sonnet for a Codex build, terra for a Claude build); cheap cross candidate `qwen3.8-flash` (A/B 2 against a terra review); `mimo-v2.5` may review a qwen build (cross) | same-family fresh session allowed; a Go reviewer files findings only, never a verdict line |
| Staff review `medium` | T2 **cross** (Sonnet reviews Codex builds; terra reviews Claude builds); T3 cross when the slice crosses two or more seams | effort xhigh |
| Staff review `high` | Fable (coordinator or fork) | Opus second read on seams |
| Fix round | build tier, or one tier down within the same family (the 2026-09-07 re-tier: `medium` fix rounds → terra) | back to the build tier only on a design-level blocker; same builder role |
| Verify pass | same reviewer model, its own probes | never a fresh cold reviewer |
| Wave-close gate / blind A/B | T4 read-only cross to the coordinator: `gpt-6-astra` xhigh | at most one per wave close; coordinator writes its position first, then TESTS the conclusions before folding any in |
| Wave-close cross-family pass | one read-only cross-family review over everything merged since the last wave close (astra or Fable per the gate row; no Go model holds this role for now) | the doctrine-(b) substitute for per-PR cross review on `low` |

## Cross-family review rules (form (b), ruled 2026-09-07)

1. Reviewer family never equals builder family on `medium`, `high`, and any seam ticket. On `low`
   with a script oracle a same-family fresh-session reviewer is allowed. Every wave close gets one
   cross-family read-only pass.
2. The reviewer sees the diff, the contract, the run log and the PR body; never the builder's
   transcript or worktree.
3. The reviewer must run. A read-only pass is a gate review, not a staff review, and is labelled so.
4. The reviewer files `BLOCKING` / `SHOULD` / `NIT`; the coordinator disposes each finding and the
   disposition is recorded per reviewer model. The expensive model judges; the cheaper one probes.
5. Fix round to the same builder role; verify to the same reviewer model. A second
   `REQUEST CHANGES` on the same finding class escalates the reviewer one tier, staying cross.
6. Two-vendor floor: where cross is mandatory and only one family is available, the review is
   queued as "blocked: one vendor" rather than faked. A `low` ticket may proceed same-family and
   the ledger records that it did.
7. `high` gets a third read: astra build, Fable review, Opus second read on privacy or data-loss
   seams.
8. Calibration is a ledger table: findings filed, confirmed, overruled per reviewer model; rounds
   per builder model by class. Re-cut this table from it monthly.
9. A PR is never built and reviewed by the same *session*. `scripts/codex-ticket.sh` picks the
   model from role + label; `CODEX_MODEL` / `CODEX_EFFORT` override per dispatch;
   `scripts/codex-ask.sh` runs the read-only pass.

## Budget rules

Pools: Claude 5x (5-hour and weekly windows); ChatGPT Pro (ONE pool across luna, terra, sol and
astra: a **rolling seven-day window**, not a calendar reset, and as of 2026-09-07 **no five-hour
cap active on Pro**, which OpenAI may restore); OpenCode Go ($12 / 5 h, $30 / week, $60 / month,
one pool for every Go model). Codex meters by a published credit rate card (credits per 1M tokens
in / cached / out: astra 250 / 25 / 1,250; sol 100 / 10 / 500; terra 50 / 5 / 300; luna 5 / 0.5 /
30) and every `codex exec --json` stream reports the live `rate_limits` percentages, so Codex
budget is read, never estimated. The 2026-09-05 marlo run drained the Codex week in ~8 hours at
5–8 concurrent xhigh sessions, then the Claude 5-hour limit took every subagent at 03:41; one day
of Opus builders alone burned 18% of a weekly top-plan window.

1. On the Codex side, luna is the `low` build default once A/B 3 passes (ten times cheaper than
   terra in pool credits); terra stays the `low` reviewer (PR #61 evidence) and the fallback
   builder; sol is reserved for `medium`; astra for `high` builds and at most ONE read-only gate
   or A/B per wave close. Go's qwen/mimo carry mechanical work and the cross-family reviews of
   Codex and Luna builds.
2. `high` effort for builds, `xhigh` only for reviews. `max` / `ultra` never without the user.
3. Re-tier UP only after the lower tier has failed the ticket, with a comment saying why.
4. Plan the week: ≲15% of each pool per day, ≤4 concurrent worker sessions, ≤2 concurrent gates.
   The machine's slot lock is the real ceiling (load >900 with six simulators on 09-05).
5. A usage-limit message is a fleet death: parse the reset time, record it in the run log and the
   handoff, chain wakeups, and never replay the burst on the other fleet.
6. Degrade down, never up: when a pool is over its daily target or in quota death, builds drop one
   tier within the same family; reviews switch to the other family's cheapest runnable tier; if
   neither family can serve, the ticket waits as `BLOCKED_QUOTA` with the reset time.
7. **Capacity death** (`ERROR: Selected model is at capacity`, 2026-09-09): the session ends with no
   verdict and no `tokens used` line, on any tier (marlo #103 astra, #124 sol verify, #136 terra).
   It is not a quota event — do not parse a reset time or switch fleets. Push what is committed,
   post a continuation note that embeds the original review, re-spawn the SAME role once on the
   same tier; only on a second death fall back one tier, and never for design-level work.

## Model re-evaluation cadence (Nick, 2026-09-07)

Rosters, allowances and prices change silently, so the table above is re-checked on a schedule
and never edited from memory. Mechanics in the helm CLI (spec D18); until it exists the
coordinator runs the steps by hand at a wave close.

- **Weekly (automated once `helm models recheck` exists):** diff `opencode models opencode-go`
  against `[models]`; diff the Go allowance page (https://opencode.ai/docs/go/) against the
  recorded numbers; summarise pool usage (`opencode stats`) and the ledger's per-model
  calibration (rounds per build, findings filed / confirmed / overruled). Write
  `docs/research/models-recheck-<date>.md` in the helm-cli repo; one inbox item with the diff.
- **Monthly (probed):** re-run the vendored probe harness (`helm-cli/probes/go-<date>/`: the
  build task and the planted-defect review task) on every enabled model plus any new id from a
  publisher in `go_publishers`, spend cap $2; record any published SWE-bench, Terminal-Bench or
  Aider numbers with source URLs.
- **Ruling:** the coordinator proposes re-tiers as a diff to `[models]`, citing the report.
  Enabling a model, adding a publisher, or changing the T0 default needs Nick's OK, recorded in
  `decisions.md`; disabling or moving to reserve is the coordinator's call.
- **Publisher rule:** Go models dispatch only from `go_publishers` (today xiaomi, qwen, meta).
  A model with an undisclosed publisher (Omen Alpha) is never enabled, whatever it scores.

## Data policy

`allow_training_models = false` per repo by default. Contributor-tier models (Muse Spark 1.3 / 1.2
Contributor: heavily discounted in exchange for Meta training on prompts and completions; not ZDR;
geo-restricted by Meta's policy) may be enabled on a repo ONLY with Nick's explicit OK for that
named repo (ruling 2026-09-07). Never marlo or admiral by default. The ledger records which repo,
when, and on whose ruling.

## Rejected and dropped (2026-09-07)

- Gemini by API key: rejected. Antigravity CLI on a Google AI subscription is a conditional second
  pilot only if Go proves insufficient. Headless state 2026-09-07: stdout-under-pipe bug closed
  2026-07-12; print mode still emits no conversation id (open), so no resume by id. Google
  publishes no numeric Pro quota; community reports range from a handful of prompts per window to
  normal use, against Go's measured 938–1,480 tickets per $12 window
  (`~/code/other/helm-cli/docs/research/antigravity-pro-vs-go-2026-09-07.md`).
- OpenRouter free: dropped. 50 requests a day account-wide (1,000 after a $10 lifetime credit),
  silently rotating roster, training-on-prompts on its best model. If ever wanted it is a provider
  entry under the same `opencode` adapter, not a new lane.

## When there is no Codex allowance

Fall back to Claude on the same tiers: coordinator Fable; `high` worked by the coordinator or an
Opus builder with a Fable review; `medium` Opus builder with a cross review from Go T1 where
available (else Sonnet fresh session); `low` and mechanical Go T0/T1 where available, else
Sonnet. Budget rules 4–6 apply unchanged to the Claude fleet.
