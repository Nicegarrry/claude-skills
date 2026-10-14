---
name: delivery-deck
description: Build the end-of-sprint delivery deck for Nick in qWork: what shipped (PRs, preview URLs, screenshots), deploys and rollbacks, gate/claims/review stats, spend against budget, open issues and the asks that need him. Use at sprint close (after budget_close and the scorecard), or when Nick says "what shipped", "sprint report", "delivery deck".
---

# delivery-deck: sprint close report in qWork

Input: project slug and the sprint's budget id. Output: a qWork deck link sent to Nick, reviewed.

## 1. Gather (summaries only)

- `scorecard_export {project, budgetId}`: tickets, clean/rework/failed rates, retries by kind, review verdicts, claims, spend, Codex tokens, deploys.
- `budget_status {project}`: cap vs spent.
- Merged PRs in the sprint window: `gh pr list --state merged --search "merged:>=<opened date>" --json number,title,url,mergedAt`.
- Deploys (if Helm has C2a): `deploy_status {project}`: target, env, sha, state, url; note rollbacks.
- Open issues: `gh issue list --state open --json number,title,labels` (map issue checklist first).
- Asks for Nick: NEEDS-NICK items, taps pending, `needs_human` questions, anything blocked.

## 2. Build

Read the qWork skill (`~/qubit-wiki/os/connectors/qwork/skills/qwork/SKILL.md`), then `qw create deck` and refine with `qw ops`. Answer-first, one idea per slide:

1. **Headline:** what the sprint delivered in one sentence, plus 3 numbers (tickets shipped, clean rate, spend vs cap).
2. **Shipped:** one row per feature: PR link, preview URL, one-line outcome. For user-facing features add a screenshot (`qw upload <deck id> <png>`, then place it as an image element).
3. **Deploys:** targets, what went where, any rollbacks and why.
4. **Quality:** gate first-pass rate, retries by kind, review REQUEST_CHANGES count, claims flags, disputed reviews (a chart element).
5. **Spend:** USD and Codex tokens against the budget cap (chart).
6. **Open:** remaining tickets and follow-ups.
7. **Asks for Nick:** each ask with the decision needed and a recommended answer. Last slide.

Keep numbers from the scorecard; don't recount by hand.

## 3. Review

1. Send Nick the link: `https://qwork.qubitstudio.app/s/<id>`.
2. When he says he has reviewed, `qw comment <id>`; apply with `qw ops`, reply and `--resolve` each thread; repeat until approved.

## 4. Publish (external action)

Sharing beyond Nick is his call. Only when he asks, tell him to set General access to "Anyone with the link" in the deck's Share sheet (agents cannot change sharing). Never share unasked.
