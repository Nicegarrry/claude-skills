---
name: factory-plan
description: Turn a product idea into an approved sprint spec for the Helm factory. Grill Nick on goal, users, non-goals, constraints, envelope and budget, then build a VG deck (strategy slides plus one wireframe slide per feature with an acceptance notes block), loop on his phone review until approved, and record the deck id on the project map issue. Use when a supervisor starts a new sprint, or Nick says "plan a sprint", "spec this", "new features for <project>".
---

# factory-plan: idea to approved feature deck

Output: an approved VG deck id and a feature list, recorded on the project's map issue. The next step is `deck-to-issues`.

## 1. Grill

Load the `grilling` skill and interview Nick one question at a time, each with your recommended answer. Look facts up in the repo instead of asking. Settle:

- **Goal:** the one outcome this sprint must produce.
- **Users:** who touches it and in what moment.
- **Non-goals:** what is explicitly out.
- **Constraints:** stack, data, deadlines, anything that must not change.
- **Envelope:** deploy targets and their mode (`auto` / `tap` / `never`), tap-only actions for this sprint.
- **Budget:** sprint cap in USD and Codex tokens (becomes `helm budget open`).

Stop grilling when every feature has an observable definition of done.

## 2. Build the deck

1. Call `vg_guide` first. Follow its contract, slide kit and bound style.
2. Strategy slides (3 to 6): problem, outcome, scope in and out, risks, sprint budget and deploy targets.
3. **One wireframe slide per feature.** Each has a real HTML layout mock of the screen or surface (not a bullet list) and a speaker-notes block in exactly this shape:

   ```
   feature: <short name>
   acceptance: <observable, checkable behaviour; commands, tests or visible states a gate or reviewer can verify>
   files hint: <paths or modules likely touched>
   depends on: <other feature names, or none>
   ```

   Never put two features on one slide. A feature without a checkable `acceptance` is not ready; ask Nick.

## 3. Review loop

1. `vg_push_deck` and send Nick the review link.
2. `vg_wait_for_review`. Read every pin, ink mark and inline edit (`vg_get_review` for detail).
3. Apply the changes (`vg_propose_change` for edits he should confirm), then `vg_resolve_comments` for the ones handled.
4. Push again and wait. Loop until Nick approves.

## 4. Record

- Comment on the project map issue: `Plan deck: <deck id>` plus the feature list (name, one-line acceptance, depends on).
- Hand off to `deck-to-issues`.

## Rules

- Only the VG tools named here exist; do not invent others.
- Nick is on a phone: short questions, one at a time.
- The deck is the spec. If something changes later, change the deck first.
