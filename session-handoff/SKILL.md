---
name: session-handoff
description: Use when wrapping up a Claude Code session so the next session resumes cleanly — write a handoff before clearing/ending. Triggers include "/wrap", "wrap up", "wrap the session", "write a handoff", "hand this off", "I'm about to /clear", "save context before clearing", or any request to checkpoint what was done + what's next before the conversation is reset. Pairs with SessionStart/SessionEnd hooks that auto-recall the handoff next session and auto-write one if you forget to /wrap.
---

# Session Handoff (`/wrap`)

## What this does

Writes a **handoff memory** for the current project capturing what was done, what's
next, and any gotchas — so the **next** session in this folder resumes with full
context. A `SessionStart` hook injects the newest handoff automatically; this skill
is the high-quality, deliberate write path (you, the live agent, with full context).

This is the path to use **instead of just `/clear`** when you want a clean resume.

## When invoked

Do all of the following, then stop:

### 1. Compose the handoff body

Reflect on THIS session and write terse, information-dense markdown with exactly
these sections (skip a section only if genuinely empty):

```markdown
## Summary
<what was accomplished this session — decisions, what changed, current state>

## Next steps
<concrete next actions, in order; name the first thing to do>

## Gotchas / open questions
<anything non-obvious: blockers, things tried that failed, decisions pending>

## Key files & commands
<paths touched, how to run/test, branch names, URLs — what the next session needs>
```

Write for your future self with **zero memory of this conversation**. Prefer specifics
(file paths, command lines, function names, branch, PR/issue numbers) over generalities.
Don't restate things already obvious from the code or git history.

### 2. Pick a topic + one-line hook

- **topic**: a short kebab-case slug for the work (e.g. `auth-refactor`, `climatepulse-rss-dedup`).
- **hook**: a single sentence (≤120 chars) that will become the pointer line in
  `MEMORY.md` — the thing that tells the next session whether this is the thread to resume.

### 3. Write it via the helper

Run (pipe the body via a quoted heredoc so nothing expands):

```bash
/opt/homebrew/bin/python3 ~/.claude/skills/session-handoff/handoff.py write \
  --source wrap --cwd "$PWD" \
  --topic "<topic-slug>" \
  --hook "<one-line hook>" <<'HANDOFF'
## Summary
...
## Next steps
...
## Gotchas / open questions
...
## Key files & commands
...
HANDOFF
```

The helper stamps the timestamp, names the file uniquely, writes it to
`<project-memory>/handoffs/`, refreshes the single rolling pointer block in
`MEMORY.md` (kept to the last 5, newest first), prunes to the last 40 handoffs,
and records a dedup marker so the automatic fallback won't double-write.

### 4. Report and hand back

Tell the user the saved path and that it's **safe to `/clear` now**. Do **not** try
to run `/clear` yourself — a skill can't; the user runs it. On the next session in
this folder, the handoff is injected automatically.

## Notes

- **This is project-scoped.** Each folder has its own handoffs; clearing windows in
  different folders never interfere. Multiple windows in the *same* folder are safe
  too (locked writes, unique filenames) — recall shows the newest + lists the others
  so you can pick which thread to resume.
- **Forgot to `/wrap` and just hit `/clear`?** A `SessionEnd` hook spawns a headless
  summariser as a best-effort fallback (lower quality, a small background cost). Disable
  it by creating `~/.claude/skills/session-handoff/FALLBACK_DISABLED`.
- **Setup / reinstall:** run `~/.claude/skills/session-handoff/install.sh` (idempotent).
