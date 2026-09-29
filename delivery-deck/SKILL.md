---
name: delivery-deck
description: Build the end-of-sprint delivery deck for Nick in VG: what shipped (PRs, preview URLs, screenshots), deploys and rollbacks, gate/claims/review stats, spend against budget, open issues and the asks that need him. Use at sprint close (after budget_close and the scorecard), or when Nick says "what shipped", "sprint report", "delivery deck".
---

# delivery-deck: sprint close report in VG

Input: project slug and the sprint's budget id. Output: a VG deck link sent to Nick, reviewed.

## 1. Gather (summaries only)

- `scorecard_export {project, budgetId}`: tickets, clean/rework/failed rates, retries by kind, review verdicts, claims, spend, Codex tokens, deploys.
- `budget_status {project}`: cap vs spent.
- Merged PRs in the sprint window: `gh pr list --state merged --search "merged:>=<opened date>" --json number,title,url,mergedAt`.
- Deploys (if Helm has C2a): `deploy_status {project}`: target, env, sha, state, url; note rollbacks.
- Open issues: `gh issue list --state open --json number,title,labels` (map issue checklist first).
- Asks for Nick: NEEDS-NICK items, taps pending, `needs_human` questions, anything blocked.

## 2. Build

Call `vg_guide` first and follow its contract, kit and bound style. Answer-first, one idea per slide:

1. **Headline:** what the sprint delivered in one sentence, plus 3 numbers (tickets shipped, clean rate, spend vs cap).
2. **Shipped:** one row per feature: PR link, preview URL, one-line outcome. For user-facing features add a screenshot (preview URL; upload with `vg_upload_asset`).
3. **Deploys:** targets, what went where, any rollbacks and why.
4. **Quality:** gate first-pass rate, retries by kind, review REQUEST_CHANGES count, claims flags, disputed reviews (chart via VG chart spec).
5. **Spend:** USD and Codex tokens against the budget cap (chart).
6. **Open:** remaining tickets and follow-ups.
7. **Asks for Nick:** each ask with the decision needed and a recommended answer. Last slide.

Keep numbers from the scorecard; don't recount by hand.

## 3. Review

1. `vg_push_deck`, send Nick the review link.
2. `vg_wait_for_review`; apply pins and edits (`vg_propose_change` for ones he should confirm), `vg_resolve_comments`, push again until approved.

## 4. Publish (external action)

Publishing makes the deck public: `envelope_check {project, actions: ['vg_publish_deck <deck id>'], kind: 'external.message'}`. On `tap`: `tap_request` with the same action, `tap_confirm` Nick's code, then call `vg_publish_deck` once (it takes no tapId; the confirmed tap is the go-ahead). On `never`, don't. Never publish unasked.
