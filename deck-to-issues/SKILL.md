---
name: deck-to-issues
description: Turn an approved factory-plan VG deck into GitHub issues a single coding worker can finish in one session. Drafts one issue per feature slide, checks each with Jev (testable, too_big), dedupes against open issues, then creates them under the project map issue. Use after factory-plan is approved, or when Nick says "make tickets from the deck".
---

# deck-to-issues: approved deck to worker-sized tickets

Input: an approved deck id (from `factory-plan`) and the project map issue number. Output: new issues on the map checklist, and no duplicates.

## 1. Draft

`vg_get_deck <deck id>`. For each feature slide, read its notes block (`feature`, `acceptance`, `files hint`, `depends on`) and draft:

```
Title: <feature>
Objective: <one paragraph>
Acceptance: <commands, tests or observable behaviour a gate can verify>
Files hint: <paths>
Depends on: <#issue or none>
Deck: <deck id>, slide <n>
```

Write each draft to `drafts/<slug>.md` in a scratch dir.

## 2. Check with Jev

For each draft:

```
helm jev check --preset issue --file drafts/<slug>.md --json
```

- `testable` flagged (below 0.5): rewrite the acceptance into concrete checks and re-run.
- `too_big` flagged (0.5 or above): split into two drafts along the most natural seam and re-run each.
- At most 2 rewrites per draft. Still flagged: ask Nick with the draft and the flag.
- `complexity` is advice for the lane (large → `luna:high`).

## 3. Dedupe

```
gh issue list --state open --limit 200 --json number,title,body > open.json
helm jev check --preset dedupe --file <{candidate, against}> --json
```

Pass at most 40 open issues per call (the most recent, plus any whose title shares a word with the draft).

- P(same) ≥ 0.5: do **not** create. Comment on the existing issue with the deck link and any acceptance it lacks.
- "Related": create, and cross-link both issues.

## 4. Create

For each surviving draft:

```
gh issue create --title "<title>" --label <project label> --body-file drafts/<slug>.md
```

Then add `- [ ] <feature> <url>` to the map issue checklist (`gh issue edit <map> --body-file ...`, keeping the existing body), and fill `Depends on` with real issue numbers.

## Rules

- Every created issue has passed `testable`. No exceptions.
- A duplicate feature produces no new issue.
- Without a Jev key the CLI returns `{ok:false, reason:'no key'}`: stop and tell the supervisor; do not skip the checks silently.
