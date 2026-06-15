# Workflow templates

Three Workflow scripts back the full pipeline. **They are templates — adapt the prompts, personas, and schemas to the task.**

**Prerequisite / fallback:** these run via the `Workflow` tool (enabled under ultracode / `CLAUDE_CODE_WORKFLOWS=1`). If it isn't available in the session, run the same fan-outs with parallel `Agent`/`Task` subagents — identical personas and schemas. Either way, use *fresh-context subagents*; don't simulate the personas in your own context.

**Determinism rules that bite:** no `Date.now()` / `Math.random()` / argless `new Date()` in scripts — resolve dates (e.g. the `YYYY-MM-DD` artifact folder) in the main session and pass them in. Vary agents by index, not randomness. Pass the draft spec / plan in via `args`, and **normalize `args` at the top of every script** (it may arrive as an object, a JSON string, or `undefined`).

---

## 1. spec-stress-test  (Phase 1)

Research + adversarial agents probe the draft spec **before the user sees it**. Single pass by design — its job is to harden the draft and surface what the *user* must decide (carried into the Phase-2 HTML as open questions). Pass the draft spec as `args.spec`.

```js
export const meta = {
  name: 'spec-stress-test',
  description: 'Research + adversarially stress-test a draft spec before human review',
  phases: [{ title: 'Research' }, { title: 'Attack' }, { title: 'Synthesize' }],
}

const input = typeof args === 'string'
  ? (() => { try { return JSON.parse(args) } catch { return { spec: args } } })()
  : (args ?? {})
const SPEC = input.spec
if (!SPEC) throw new Error('spec-stress-test: pass the draft spec via args.spec')

const RESEARCH_ANGLES = input.researchAngles ?? [
  'prior art and how others have solved this',
  'relevant library/API/SDK facts and current best practice (use context7/firecrawl/web)',
  'existing-codebase patterns and constraints this must fit',
]
const ATTACK_LENSES = input.attackLenses ?? [
  'unstated assumptions — what is being taken for granted that could be false',
  'gaps and missing requirements — what will bite us that the spec ignores',
  'feasibility and scope — is this too big, mis-sequenced, or over-ambitious for the goal',
]

const FINDINGS = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['issue', 'severity', 'recommendation'],
        properties: {
          issue: { type: 'string' },
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
          recommendation: { type: 'string' },
          needsUserDecision: { type: 'boolean' },
        },
      },
    },
  },
}

phase('Research')
const research = (await parallel(RESEARCH_ANGLES.map((a, i) => () =>
  agent(`Research this angle for the spec below and report concrete, sourced facts.\nAngle: ${a}\n\nSPEC:\n${SPEC}`,
    { label: `research:${i}`, phase: 'Research' })
))).filter(Boolean)

phase('Attack')
const attacks = (await parallel(ATTACK_LENSES.map((lens, i) => () =>
  agent(`You are a skeptical reviewer. Attack the spec below through ONE lens: ${lens}.\n` +
        `Use this research context:\n${research.join('\n\n')}\n\nSPEC:\n${SPEC}`,
    { label: `attack:${i}`, phase: 'Attack', schema: FINDINGS })
))).filter(Boolean)

phase('Synthesize')
const all = attacks.flatMap(a => a.findings)
const synthesis = await agent(
  `Synthesize these findings into (a) concrete fold-ins to apply to the spec and ` +
  `(b) open questions that need the USER to decide. Dedup and rank by severity.\n\n` +
  `FINDINGS:\n${JSON.stringify(all, null, 2)}\n\nRESEARCH:\n${research.join('\n\n')}`,
  { phase: 'Synthesize' })

return { research, findings: all, synthesis }
```

Apply the fold-ins to the spec yourself; carry the open questions into the HTML (Phase 2).

---

## 2. plan-gauntlet  (Phase 3)

Writes the build plan, then ≥3 **distinct-persona** attackers hit it in parallel; **all** issues (every severity) are fed back to a resolver each round, looping until a round surfaces nothing or the cap is hit. Finally it extracts a structured task list (numeric `phase`) so Phase 4 can consume it. Pass the approved spec as `args.spec`.

```js
export const meta = {
  name: 'plan-gauntlet',
  description: 'Write a build plan, harden it against 3 adversarial personas, emit a structured task list',
  phases: [{ title: 'Plan' }, { title: 'Gauntlet' }, { title: 'Resolve' }, { title: 'Extract' }],
}

const input = typeof args === 'string'
  ? (() => { try { return JSON.parse(args) } catch { return { spec: args } } })()
  : (args ?? {})
const SPEC = input.spec
if (!SPEC) throw new Error('plan-gauntlet: pass the approved spec via args.spec')
const MAX_ROUNDS = input.maxRounds ?? 3

const PERSONAS = [
  { id: 'staff-eng',  brief: 'Skeptical staff engineer. Attack correctness, sequencing, hidden coupling, "this won\'t compose", and underestimated tasks.' },
  { id: 'ops-sec',    brief: 'Ops/security/reliability paranoid. Attack failure modes, data/auth/RLS/secrets, irreversibility, missing rollback, deploy gotchas.' },
  { id: 'minimalist', brief: 'Scope minimalist (YAGNI). Attack over-engineering and gold-plating; argue what phase 1 could drop and still deliver the ambition.' },
]
const VERDICT = {
  type: 'object',
  required: ['issues'],
  properties: {
    issues: {
      type: 'array',
      items: {
        type: 'object',
        required: ['issue', 'severity', 'fix'],
        properties: {
          issue: { type: 'string' },
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
          fix: { type: 'string' },
        },
      },
    },
  },
}
const TASKS_SCHEMA = {
  type: 'object',
  required: ['tasks'],
  properties: {
    tasks: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'phase', 'title'],
        properties: {
          id: { type: 'string' },
          phase: { type: 'integer', description: '1 = first workstream' },
          title: { type: 'string' },
          files: { type: 'array', items: { type: 'string' } },
          tests: { type: 'string' },
          acceptance: { type: 'string' },
        },
      },
    },
  },
}

phase('Plan')
let plan = await agent(
  `Write a detailed, engineer-grade build plan from this spec. Group tasks by workstream/phase ` +
  `(phase 1 = the first workstream). Per task: order, files touched, tests, acceptance, risk/rollback.\n\nSPEC:\n${SPEC}`,
  { phase: 'Plan' })

let round = 0, lastIssues = []
while (round < MAX_ROUNDS) {
  round++
  phase('Gauntlet')
  const verdicts = (await parallel(PERSONAS.map(p => () =>
    agent(`${p.brief}\nAttack this build plan. Report EVERY real issue (any severity) with a concrete fix.\n\nPLAN:\n${plan}`,
      { label: `attack:${p.id}:r${round}`, phase: 'Gauntlet', schema: VERDICT })
  ))).filter(Boolean)

  const issues = verdicts.flatMap(v => v.issues)
  if (issues.length === 0) { lastIssues = []; break }
  lastIssues = issues

  phase('Resolve')
  plan = await agent(
    `Revise the build plan to resolve EVERY issue below (fix the majors/blockers fully; address minors too). ` +
    `Keep it concrete and buildable.\n\nISSUES:\n${JSON.stringify(issues, null, 2)}\n\nCURRENT PLAN:\n${plan}`,
    { label: `resolve:r${round}`, phase: 'Resolve' })
}
const hardened = lastIssues.length === 0

phase('Extract')
const taskList = await agent(
  `Extract a structured task list from this build plan. Each task needs an id, an integer phase ` +
  `(1 = first workstream), a title, and (where known) files/tests/acceptance.\n\nPLAN:\n${plan}`,
  { phase: 'Extract', schema: TASKS_SCHEMA })

return { plan, tasks: taskList.tasks, hardened, openIssues: hardened ? [] : lastIssues, rounds: round }
```

After it returns: if `hardened` is false, **stop and surface `openIssues` to the user** — do not proceed to Phase 4. Otherwise save `plan` to `docs/specs/YYYY-MM-DD-<topic>/plan.md`, commit, and carry `tasks` into execute-plan.

---

## 3. execute-plan  (Phase 4)

Executes the chosen depth in **one checkout** (run it from inside the feature worktree you created in Phase 4 — see SKILL.md). Each task builds then verifies, with a bounded retry on failure so the autonomous run doesn't finish broken. Pass `args.tasks` (from plan-gauntlet) and `args.depth` (`'phase1'` | `'full'`).

```js
export const meta = {
  name: 'execute-plan',
  description: 'Autonomously execute the build plan (phase 1 or full) with per-task verify + bounded retry',
  phases: [{ title: 'Build' }, { title: 'Verify' }, { title: 'Final check' }],
}

const input = typeof args === 'string'
  ? (() => { try { return JSON.parse(args) } catch { return {} } })()
  : (args ?? {})
const ALL = Array.isArray(input.tasks) ? input.tasks : []
const DEPTH = input.depth === 'full' ? 'full' : 'phase1'
const TASKS = DEPTH === 'full' ? ALL : ALL.filter(t => t.phase === 1)
if (TASKS.length === 0) {
  throw new Error(`execute-plan: no tasks to run for depth='${DEPTH}'. Check args.tasks (need integer phase fields; phase 1 = first workstream).`)
}
const MAX_RETRY = input.maxRetry ?? 2
const VERIFY = {
  type: 'object',
  required: ['pass', 'notes'],
  properties: { pass: { type: 'boolean' }, notes: { type: 'string' } },
}

// Sequenced tasks share one checkout so verify sees the build's commits.
const results = []
for (let i = 0; i < TASKS.length; i++) {
  const t = TASKS[i]
  let attempt = 0, verdict = null, lastNotes = ''
  while (attempt < MAX_RETRY) {
    attempt++
    await agent(
      `Implement this task per the plan. Follow existing patterns; commit when done.` +
      (lastNotes ? `\n\nThe previous attempt failed verification:\n${lastNotes}\nFix it.` : '') +
      `\n\nTASK:\n${JSON.stringify(t)}`,
      { label: `build:${t.id}:a${attempt}`, phase: 'Build' })
    verdict = await agent(
      `Verify the task is actually done and correct: run tests/typecheck for the touched area and report pass + notes.\n\nTASK:\n${JSON.stringify(t)}`,
      { label: `verify:${t.id}:a${attempt}`, phase: 'Verify', schema: VERIFY })
    if (verdict?.pass) break
    lastNotes = verdict?.notes ?? ''
  }
  results.push({ task: t.id, attempts: attempt, verdict })
}

phase('Final check')
const final = await agent(
  `Run the full verification for what was built (build + typecheck + test suite) and report pass/fail with failing output if any.`,
  { phase: 'Final check', schema: VERIFY })

return { tasks: results, final, failed: results.filter(r => !r.verdict?.pass).map(r => r.task), depth: DEPTH }
```

After it returns: if `final.pass` is false or `failed` is non-empty, **hard-stop and surface it to the user** (per the `autonomy` skill's "stop on a hard blocker"). Otherwise summarize what shipped, and — if `depth === 'phase1'` — ask whether to continue to the next phase.

> **Token/context note:** `'phase1'` is the default for large builds — it keeps the main context lean and gives a natural checkpoint. Choose `'full'` only when the plan is small enough to run in one go. If a phase's tasks are genuinely independent (not sequenced), you can parallelize them with `parallel()` + per-task `isolation: 'worktree'` — but then add a merge-back step before Verify so it sees the changes.
