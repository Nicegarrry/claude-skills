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

## The ladder

| Tier | Models (family) | Pool |
|---|---|---|
| T0 bulk | OpenCode Go models with ≥4,000 requests per 5 h under the plan's dollar metering: Muse Spark 1.3 Contributor 45,300 (meta; trains on prompts, geo-restricted), MiMo-V2.5 30,100 (xiaomi), Omen Alpha 11,600, LongCat-2.0 11,400, DeepSeek V4 Flash 7,600 (deepseek), Qwen3.8 Flash 5,400 (qwen), Qwen3.7 Plus 4,300, Hy3 4,300 | Go: $12 / 5 h, $30 / week, $60 / month, ONE pool for every Go model |
| T1 mid | Go models with 1,000–4,000 per 5 h: DeepSeek V4 Flash Vision 3,800, MiniMax M2.7 3,400, Qwen3.6 Plus 3,300, MiMo-V2.5-Pro 3,250, MiniMax M3 3,200, GPT 5.6 Luna 2,050 (openai), GLM-5.3-Flash 1,580, Kimi K2.7 Code 1,350, Hy4 1,350, Kimi K2.6 1,150, DeepSeek V4 Pro 1,050 | same Go pool |
| T2 workhorse | Codex `gpt-5.6-terra` (openai); Claude Sonnet (anthropic) | ChatGPT Pro weekly; Claude 5x |
| T3 strong | Codex `gpt-5.6-sol` (openai); Claude Opus (anthropic) | same |
| T4 frontier | Codex `gpt-6-astra` (openai); Claude Fable, coordinator only (anthropic) | same |

**DeepSeek V4 Flash and Pro are gated** behind an explicit China-hosted opt-in at the Go console
(refused from this machine 2026-09-07); `allow_china_hosted = false` by default, pending Nick's
ruling. The T0 default is therefore MiMo-V2.5. Observed cost per trivial turn (2026-09-07, each
turn carries ~15k tokens of OpenCode's system prompt): MiniMax M2.7 $0.00004, GLM-5.3-Flash
$0.0012, Muse Spark 1.3 Contributor $0.0016, MiMo-V2.5 $0.0020, Hy3 $0.0022, Omen Alpha $0.0032,
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
| Builder `low`, script oracle | T2 `gpt-5.6-terra`, effort high; T1 Go in pilot | one ticket, worktree, PR-only |
| Builder `low`, research digest | T2 terra; T0/T1 long-context Go in pilot | citation check is mandatory in review |
| Builder `medium` | T3 `gpt-5.6-sol`, effort high | one ticket, worktree, PR-only |
| Builder `high` | T4 `gpt-6-astra`, effort xhigh | **Fable reviews**; astra never reviews its own build |
| Mechanical (tracker ops, bulk edits, config) | T0 Go in pilot; terra effort medium until then | script oracle, no review |
| **Floor: UI by eye** (any label) | T3 build with the simulator loop | T3 cross review, screenshots looked at; no cheap-tier success exists |
| **Floor: privacy / security / data-loss seam** (any label) | T4 build | T4 cross review; Opus second read when the build was Codex; the supervisor never dispatches these |
| Staff review `low` | T2, fresh session, runnable; cross preferred (Sonnet for a Codex build, terra for a Claude build) | same-family fresh session allowed |
| Staff review `medium` | T2 **cross** (Sonnet reviews Codex builds; terra reviews Claude builds); T3 cross when the slice crosses two or more seams | effort xhigh |
| Staff review `high` | Fable (coordinator or fork) | Opus second read on seams |
| Fix round | build tier, or one tier down within the same family (the 2026-09-07 re-tier: `medium` fix rounds → terra) | back to the build tier only on a design-level blocker; same builder role |
| Verify pass | same reviewer model, its own probes | never a fresh cold reviewer |
| Wave-close gate / blind A/B | T4 read-only cross to the coordinator: `gpt-6-astra` xhigh | at most one per wave close; coordinator writes its position first, then TESTS the conclusions before folding any in |
| Wave-close cross-family pass | one read-only cross-family review over everything merged since the last wave close | the doctrine-(b) substitute for per-PR cross review on `low` |

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

Pools: Claude 5x (5-hour and weekly windows); ChatGPT Pro (ONE weekly pool across terra, sol and
astra); OpenCode Go ($12 / 5 h, $30 / week, $60 / month, one pool for every Go model). The
2026-09-05 marlo run drained the Codex week in ~8 hours at 5–8 concurrent xhigh sessions, then the
Claude 5-hour limit took every subagent at 03:41; one day of Opus builders alone burned 18% of a
weekly top-plan window.

1. terra is the default for `low` and mechanical until Go carries them; sol is reserved for
   `medium`; astra for `high` builds and at most ONE read-only gate or A/B per wave close.
2. `high` effort for builds, `xhigh` only for reviews. `max` / `ultra` never without the user.
3. Re-tier UP only after the lower tier has failed the ticket, with a comment saying why.
4. Plan the week: ≲15% of each pool per day, ≤4 concurrent worker sessions, ≤2 concurrent gates.
   The machine's slot lock is the real ceiling (load >900 with six simulators on 09-05).
5. A usage-limit message is a fleet death: parse the reset time, record it in the run log and the
   handoff, chain wakeups, and never replay the burst on the other fleet.
6. Degrade down, never up: when a pool is over its daily target or in quota death, builds drop one
   tier within the same family; reviews switch to the other family's cheapest runnable tier; if
   neither family can serve, the ticket waits as `BLOCKED_QUOTA` with the reset time.

## Data policy

`allow_training_models = false` per repo by default. Contributor-tier models (Muse Spark 1.3 / 1.2
Contributor: heavily discounted in exchange for Meta training on prompts and completions; not ZDR;
geo-restricted by Meta's policy) may be enabled on a repo ONLY with Nick's explicit OK for that
named repo (ruling 2026-09-07). Never marlo or admiral by default. The ledger records which repo,
when, and on whose ruling.

## Rejected and dropped (2026-09-07)

- Gemini by API key: rejected. Antigravity CLI on a Google AI subscription is a conditional second
  pilot only if Go proves insufficient, and only after its headless bugs close (stdout dropped
  under a non-TTY pipe; no session id in print mode).
- OpenRouter free: dropped. 50 requests a day account-wide (1,000 after a $10 lifetime credit),
  silently rotating roster, training-on-prompts on its best model. If ever wanted it is a provider
  entry under the same `opencode` adapter, not a new lane.

## When there is no Codex allowance

Fall back to Claude on the same tiers: coordinator Fable; `high` worked by the coordinator or an
Opus builder with a Fable review; `medium` Opus builder with a cross review from Go T1 where
available (else Sonnet fresh session); `low` and mechanical Go T0/T1 where available, else
Sonnet. Budget rules 4–6 apply unchanged to the Claude fleet.
