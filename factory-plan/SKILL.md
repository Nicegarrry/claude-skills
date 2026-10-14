---
name: factory-plan
description: Turn a product idea into an approved sprint spec for the Helm factory. Grill Nick on goal, users, non-goals, constraints, envelope and budget, then build a qWork deck (strategy slides plus one wireframe slide per feature with an acceptance box), loop on his phone review until approved, and record the deck id on the project map issue. Use when a supervisor starts a new sprint, or Nick says "plan a sprint", "spec this", "new features for <project>".
---

# factory-plan: idea to approved feature deck

Output: an approved qWork deck id and a feature list, recorded on the project's map issue. The next step is `deck-to-issues`.

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

1. Read the qWork skill (`~/qubit-wiki/os/connectors/qwork/skills/qwork/SKILL.md`) for the `qw` CLI and deck ops. Create the deck with `qw create deck --title "<project>: sprint plan" spec.json`, then refine with `qw ops`.
2. Strategy slides (3 to 6): problem, outcome, scope in and out, risks, sprint budget and deploy targets.
3. **One wireframe slide per feature.** Each has a layout mock of the screen or surface built from shapes and text boxes (not a bullet list), and a text box named `Acceptance` (bottom strip of the slide) in exactly this shape:

   ```
   feature: <short name>
   acceptance: <observable, checkable behaviour; commands, tests or visible states a gate or reviewer can verify>
   files hint: <paths or modules likely touched>
   depends on: <other feature names, or none>
   ```

   Never put two features on one slide. A feature without a checkable `acceptance` is not ready; ask Nick.

## 3. Review loop

1. Send Nick the link: `https://qwork.qubitstudio.app/s/<id>`.
2. When he says he has reviewed, `qw comment <id>` and read every thread. His direct edits are already in the deck.
3. Apply the changes with `qw ops` (small groups, one slide at a time), reply on each thread and `--resolve` the handled ones.
4. Tell him it is ready again. Loop until Nick approves.

## 4. Record

- Comment on the project map issue: `Plan deck: <deck id>` plus the feature list (name, one-line acceptance, depends on).
- Hand off to `deck-to-issues`.

## Rules

- Use only the `qw` commands in the qWork skill; do not invent others. VG is frozen (2026-10-14).
- Nick is on a phone: short questions, one at a time.
- The deck is the spec. If something changes later, change the deck first.
