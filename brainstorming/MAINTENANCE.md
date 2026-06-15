# Maintenance notes — brainstorming skill

## What this is

A **personal fork/replacement** of the superpowers `brainstorming` skill. It changes the flow from
the upstream "spec → writing-plans → build" handoff to: **align on ambition → adversarially
stress-tested spec → human HTML review (proofing-room) → attacked build plan → autonomous
execution**. See `SKILL.md`.

## Where it lives

- **Source of truth:** this directory, `/Users/sa/code/skills/brainstorming/`, in the
  `Nicegarrry/claude-skills` git repo.
- **Activation:** symlinked to `~/.claude/skills/brainstorming`, so Claude Code loads it as a
  *personal* skill. Personal skills outrank plugin skills of the same name
  (precedence: enterprise > personal > project > plugin), so this shadows the plugin's
  `superpowers:brainstorming` automatically — no need to disable the plugin.
- **Upstream original:** `~/.claude/plugins/cache/claude-plugins-official/superpowers/<version>/skills/brainstorming/`
  (was `5.1.0` when this fork was created). The plugin copy is **untouched** and is replaced on
  every superpowers update.

## Upkeep — check on each superpowers update

When the superpowers plugin updates (the version dir under the plugin cache changes), **diff the
new upstream `brainstorming` against this fork** and decide what's worth pulling in:

```bash
# find the current plugin version dir, then diff
ls ~/.claude/plugins/cache/claude-plugins-official/superpowers/
diff ~/.claude/plugins/cache/claude-plugins-official/superpowers/<new-version>/skills/brainstorming/SKILL.md \
     ~/.claude/skills/brainstorming/SKILL.md
```

Look for upstream improvements worth keeping in sync: the **visual-companion** guidance (we inline a
one-liner; upstream has a fuller `visual-companion.md`), scope-decomposition wording, the spec
self-review checklist, and any new gates or anti-rationalization patterns. Fold the good parts into
this fork; keep our pipeline (Phases 0–4, the Workflow templates, the proofing-room HTML loop). The
fork deliberately diverges on the core flow — don't blindly overwrite it.

> Because this is a *replacement*, upstream changes never reach the user automatically. This file is
> the reminder to reconcile them by hand.
