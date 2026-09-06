# Helm templates

Copy, fill, trim. Every brief ends with a reply-shape cap — uncapped agents return essays. Doctrine:
`../SKILL.md`. Who to dispatch: `routing.md`. How the brief reaches the worker and what a repo
contract must already carry: `fleet-mechanics.md`.

## Builder dispatch brief

```
Builder for ticket #<N> "<title>" in <repo path> (gh authenticated). Claim #<N>.
Read: CLAUDE.md; ticket body (`gh issue view N`); <the 2–4 docs THIS ticket needs, by name,
with the binding rules called out — e.g. "docs/doc-model.md CA-1..CA-7 (BINDING)">; the run
logs of the tickets whose seams you inherit.
Pull main; worktree `git worktree add <the path this repo's contract fixes> -b <branch> origin/main`;
work only there. <CURRENT MAIN: what merged since this ticket was written — moved files, renamed
seams, the baseline test count at dispatch time.>

<PARALLEL-SAFETY: which sibling agents are running, which files/seams each owns, registries
are append-only, declare any shared-file touch in the PR body.>

Scope:
1. <numbered deliverable with its acceptance criterion>
2. ...

Verify: <the full local gate — lint/typecheck/test/build/e2e> green before PR — do not hand
back red. <Known flakes by issue number so they aren't re-debugged.>
Run log logs/tickets/<N>-<slug>.md (decisions, gotchas, what the docs got wrong — flag, don't
silently deviate). Commit as you go (conventional, explicit paths, never `git add -A`).
Push, open PR `[#N] <title>` with `Closes #N` + verification evidence tails.
Do NOT merge, do NOT touch main. Final reply max <10–15> lines: PR URL, verification
one-liners, deviations/flags, what <next tickets> need to know about your seams.
```

## Staff review brief

```
Staff-engineer review of PR #<P> ([#N] <title>) in <repo> (gh authenticated). Branch at
../<repo>-worktrees/<branch>. Wait for CI before final verdict (until-loop on `gh pr checks`);
probe locally meanwhile. <Sibling PRs in flight — flag any touch outside declared seams.>

Context: <binding docs + rule numbers this PR must conform to; the builder's run log;
findings carried from earlier PRs by name>.

Dimensions (priority order):
1. <conformance to the binding doc — cite rules by number, verify claims against installed
   package sources, not memory>
2. <live probing — run the app/server, two contexts, the specific adversarial scenarios
   worth constructing for THIS ticket>
3. <the harness/tests — are they real, no sleeps, would they catch the regression class>
3b. For every assertion in a refusal/error message and every test over live output, ask
    "what would make this false, and does the code guarantee it?" — a claim wider than
    its instrument (Admiral L24: pgrep -f, a string loopback check, a hash race that
    still spawned the server) is a finding even when the behaviour looks right.
4. <UX by eye if user-facing — screenshot and LOOK>
5. <scope hygiene — declared seams only, deps pinned, registry discipline>

File review via `gh pr review P --comment` titled "Staff review — verdict: <APPROVE|REQUEST
CHANGES>" with findings by severity: BLOCKING / SHOULD / NIT. (Formal request-changes is
impossible on same-account PRs — the verdict line is authoritative.) Do NOT edit files, do
NOT merge. Final reply max 12 lines: verdict + one line per finding.
```

## Fix-pass message (to the SAME builder ROLE)

Resumable worker: send this to the agent that built it. Stateless worker: a fresh invocation carrying
the PR number and the review body says the same thing (`fleet-mechanics.md`).

```
Staff review on PR #<P>: REQUEST CHANGES — read the full review on the PR. Fix all BLOCKING:
<one line each, restating the finding sharply and the shape of the required fix — including
"make it fail as a test against the old code">. Take the SHOULDs. <Known operational notes:
e2e contention, rebase-onto-main instructions when siblings merged ahead.>
Re-verify everything, push same branch, disposition reply max <8–10> lines
(finding → fixed-how, or pushed back with source-verified evidence). Do not merge.
```

## Verification-pass message (to the SAME reviewer ROLE — resumed, or re-invoked with the thread)

```
<Builder> pushed fixes to PR #<P> (head <sha>, disposition on the PR): <one line per fix>.
CI green. Verify each original BLOCKING is genuinely closed by re-running YOUR original
probes <name the key ones>. Post "Re-review — verdict: ..." on the PR. Reply max 5 lines.
```

## Repo CLAUDE.md contract skeleton

`AGENTS.md` is a committed git symlink to this file, so one contract serves both fleets.

```
# <repo> — working contract for every agent in this repo
## What this is            <one paragraph + north-star pointer>
## Non-negotiables         <the product invariants reviewed on every PR>
## Workflow                <backlog=issues; PR-only; worktrees; explicit staging; conventional
                            commits; PR evidence; do-not-merge; declared shared touches>
## Logs & memory           <logs/tickets/ run logs committed with PRs; docs/decisions.md
                            orchestrator-only>
## Stack                   <fixed choices + "copy imports from docs/research/..., never memory">
## Testing                 <suites; no sleeps — poll predicates; CI budget; "done = exercised
                            in the running app">
## Quality bar             <the product feel sentence + icon/style rules>
## Worker conventions      <instantiated from references/fleet-mechanics.md, with THIS repo's paths>
## Reviewer conventions    <instantiated from references/fleet-mechanics.md, with THIS repo's gate>
## Mixed fleet             <one line: routing lives in the helm skill's references/routing.md>
```

## Map decision line (append per merged ticket, before "## Not yet specified")

```
- [T<N>: <title>](<issue url>) — merged (PR #<P>; <review journey gist>): <what landed, one line>.
```

## Orchestrator post-merge checklist

1. `gh pr merge P --merge` (check `mergeable` first; conflicts → same builder resolves,
   keep-both-sides, re-verify, then merge).
2. `git pull` main; `git worktree remove` the branch worktree.
3. Map line appended (template above).
4. Deploy pipeline (if live): new deployment reaches Ready; logs on error.
5. Dispatch whatever the merge unblocked (check the dependency edges, not your memory).
