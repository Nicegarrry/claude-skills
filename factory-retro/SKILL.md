---
name: factory-retro
description: Turn a closed Helm sprint's scorecard into at most five evidence-backed lessons, label Jev's calls with real outcomes, and open skill PRs for lessons that change how agents work. Use after scorecard.export (budget close), when a supervisor finishes a sprint, or when Nick says "run the retro", "what did we learn".
---

# factory-retro: scorecard to lessons

Input: a project slug and the sprint's budget id. Output: up to 5 lesson pages in project memory, labelled Jev calls, and skill PRs waiting on a tap.

## 1. Gather

- `scorecard_export {project, budgetId}` (or the scorecard page it already wrote: `memory_list {project, type: 'scorecard'}`).
- Retry reasons: `worker_inspect` on workers with retries or failures (events only, `tail` small).
- REQUEST_CHANGES comments on merged PRs: `gh pr list --state merged --search "<sprint window>" --json number` then `gh pr view N --comments`. Read only the verdict comments.
- `disputed` reviews (Jev disagreed with the stated verdict) from the scorecard.
- Jev calls for the sprint, read-only:
  `sqlite3 -readonly ~/.helm/helm.sqlite "select id,purpose,workerId,answers,confidence,label from jev_calls where project='<slug>' and at >= '<opened>'"`

## 2. Write lessons (max 5)

Pick patterns that recur (2+ tickets) or cost a retry round. For each:

```
memory_write {
  scope: 'project', project: '<slug>', type: 'lesson',
  title: '<short name>',
  summary: '<one-line rule an agent can follow>',
  truth: '<evidence: what happened, how often, which fix worked>',
  refs: [{kind: 'gh', key: 'pr/<N>', title: '<pr title>', checked: '<today>'}]
}
```

- Summary is an instruction, not a story ("Test conflict parsing against real git, not a fake grep"), under 120 chars.
- Every lesson has at least one `gh:pr/N` ref. No ref, no lesson.
- Team-wide lessons (not repo-specific) use `scope: 'team'`.
- `memory_log` is for short dated notes on an existing page; never use it to create a lesson.

## 3. Label Jev

For each Jev call whose outcome is now known, `jev_label {id, label}`:

- triage: `correct` / `wrong:<actual>` (e.g. `wrong:answerable`).
- claims / verdict: `agree` / `disagree`.
- issue / routing: the real band or `split-needed` if the ticket had to be split.

Skip calls you can't judge. Labels feed routing and selection; a wrong label is worse than none.

## 4. Skill PRs (lessons that change agent behaviour)

For each lesson that should change a skill (briefing rule, review checklist, supervisor loop):

1. `worker_spawn` a Codex worker (`codex/gpt-5.6-luna:medium`) on the skills repo, objective = the lesson plus the exact skill file and section to edit; keep the edit under 15 lines.
2. Claude review (Agent tool, opus): ONE comment, last line `APPROVE: ` / `REQUEST_CHANGES: `; then `review_record`.
3. Merging a skill is tap-only (`skill.merge`): `tap_request {project, kind: 'skill.merge', action: 'pr_merge <skills repo>#<N> <head sha>'}`. When Nick sends `tap <id> <code>`, `tap_confirm {id, code}`; then `pr_merge {number: <N>, project: <skills repo>, expectedHead: <head sha>}` exactly once (keeps Helm's approving-review guard) and note the tap id in the PR comment. No tap, no merge.

## Rules

- Five lessons maximum; fewer good ones beat many weak ones.
- Evidence comes from PRs, gates and events, not from memory of the session.
- Never edit an existing lesson's truth to fit a new story; write a new lesson and reference the old one.
