# session-handoff

Never lose the thread between Claude Code sessions. Wrap a session and the next one
picks up exactly where you left off.

- **`/wrap`** — before you `/clear`, the live agent (full context) writes a handoff
  note: *what was done · what's next · gotchas · key files*. Best quality.
- **Auto-recall** — a `SessionStart` hook injects the newest handoff into the next
  session in that folder. (Same mechanism Claude Code uses to load `MEMORY.md`.)
- **Auto-fallback** — forgot to `/wrap` and just hit `/clear`? A `SessionEnd` hook
  spawns a headless summariser as a best-effort backup.

## How it works

```
/wrap ─► handoff.py write ─► <project-memory>/handoffs/<date>-<topic>.md   (full handoff)
                          └► MEMORY.md  ◄── rolling pointer block (last 5, replaced)

/clear ─► SessionEnd hook ─► handoff.py fallback ─► (detached) claude -p ─► write   [if no /wrap]
new session ─► SessionStart hook ─► handoff.py recall ─► injects newest handoff + pointers
```

Handoffs are **per project**. The memory dir is derived from the hook's
`transcript_path` (exact) or, for `/wrap`, slugified from `cwd` the way Claude Code
names project dirs. So windows open in *different* folders never interfere; windows
in the *same* folder are safe too — writes are file-locked with unique filenames, and
recall lists the other recent threads so you choose which to resume.

### Storage layout

```
~/.claude/projects/<cwd-slug>/memory/
  MEMORY.md                       # native index + one rolling handoff pointer block
  handoffs/
    2026-06-15-1432-<topic>-ab12.md   # full handoffs (last 40 kept)
    .last-wrap                          # dedup marker (so fallback won't double-write)
```

## Install

```bash
./install.sh
```

Idempotent. It symlinks the skill into `~/.claude/skills/` and merges two hooks into
`~/.claude/settings.json` (backing it up first). Re-run any time to update.

## Configuration

Tunables are constants at the top of `handoff.py`:

| Constant | Default | Meaning |
|---|---|---|
| `MAX_POINTERS` | 5 | pointer lines kept in `MEMORY.md` |
| `MAX_HANDOFFS` | 40 | handoff files retained per project |
| `RECALL_FULL` | 1 | newest handoffs injected in full on recall |
| `RECALL_POINTERS` | 4 | additional recent handoffs listed as one-liners |
| `RECALL_MAX_AGE_DAYS` | 14 | don't inject handoffs older than this |
| `WRAP_DEDUP_WINDOW` | 180s | suppress fallback if `/wrap` ran this recently |

**Disable the headless fallback** (keep only `/wrap` + recall):

```bash
touch ~/.claude/skills/session-handoff/FALLBACK_DISABLED
```

## Limitations (honest)

- **Fallback is best-effort, not instant.** `SessionEnd` can't block the wipe (~1.5s
  budget), so the auto-handoff lands a few seconds *after* `/clear`, written by a
  cheaper headless agent. `/wrap` has neither drawback — it's synchronous and you write it.
- **Same-folder concurrent clears aren't auto-paired.** When you `/clear` two windows
  in the *same* folder at once, there's no stable id linking a new session to its exact
  predecessor, so recall shows the newest in full and lists the rest — you (or the agent)
  pick the right one. No handoff is ever lost.
- The fallback calls `claude -p` by absolute path and costs a small background API call.

## Files

| File | Role |
|---|---|
| `SKILL.md` | what Claude reads when you say `/wrap` |
| `handoff.py` | `write` / `recall` / `fallback` — all file logic, locking, pruning |
| `install.sh` | symlink + idempotent hook merge |
| `DESIGN.md` | design rationale + decisions |
