# session-handoff — Design

Date: 2026-06-15 · Status: built

## Goal

Automate session continuity in Claude Code. Wrapping/clearing a session writes a
handoff memory; the next session in that folder surfaces it immediately. Primary
path is the deliberate `/wrap` (live agent, full context, best quality); a hook-driven
fallback catches bare `/clear`.

## The core constraint that shaped everything

Hooks are **shell commands the harness runs — not the agent.** A `SessionEnd` hook
firing on `/clear` can't "ask the agent to write a thoughtful handoff" (the agent gets
no turn, and `SessionEnd` can't block). So the problem splits:

- **Recall (easy, robust):** a `SessionStart` hook injects the latest handoff. ✅
- **Write (the real fork):** *who* writes it — the live agent via a custom command, or
  a headless `claude -p` spawned by the hook?

**Decision: hybrid.** `/wrap` = live-agent write (primary). `SessionEnd` fallback =
headless write (backup, for when you forget and just `/clear`).

## Verified Claude Code hook contract (claude-code-guide, 2026-06-15)

- `/clear` fires `SessionEnd(reason="clear")` then `SessionStart(source="clear")`.
- Every hook payload includes `session_id`, `transcript_path`, `cwd`, `hook_event_name`
  (+ `source`/`reason`). **Session id is NOT an env var** — only in the payload.
- `SessionStart` injects context via plain stdout (or JSON `additionalContext`).
- `SessionEnd` **cannot block**; default timeout **~1.5s** (configurable). → the fallback
  must spawn a **detached** worker and return instantly.
- Hooks inherit the parent env. This machine's `settings.json` `env.PATH` has
  `/opt/homebrew/bin` (python3 ✓) but not `~/.local/bin` (claude ✗) → call `claude` by
  absolute path.

## Architecture

One Python helper, two hooks, one skill.

- **`handoff.py`** — single source of truth for naming, the `MEMORY.md` pointer block,
  pruning, and **locking** (`fcntl.flock` + atomic `os.replace`). Subcommands:
  - `write` — body on stdin → unique `handoffs/<date>-<time>-<topic>-<rand>.md`;
    refresh `MEMORY.md` block (rolling, last 5); prune to last 40; drop `.last-wrap`.
  - `recall` — newest handoff in full + up to 4 pointers → stdout (SessionStart).
    Silent if newest > 14 days old, or if run inside the headless summariser.
  - `fallback` — SessionEnd: gate on `reason=="clear"`, dedup vs `.last-wrap`, then
    spawn a detached `_runfallback` worker and return.
  - `_runfallback` — detached: `claude -p` summarises the transcript tail → `write --source auto`.
- **`/wrap` skill** (`SKILL.md`) — live agent composes the handoff and calls `write --source wrap`.
- **Hooks** (`~/.claude/settings.json`): `SessionStart` matcher `startup|resume|clear` →
  `recall`; `SessionEnd` matcher `clear` → `fallback`.

## Key decisions

- **Per-project, derived from `transcript_path`** (exact) for hooks; slugified `cwd`
  (`re.sub(r'[^a-zA-Z0-9]','-', cwd)`, verified against real project dirs) for `/wrap`.
  → different folders are fully isolated.
- **`MEMORY.md` stays clean:** exactly one marked block, rolling to the last 5 pointers,
  *replaced* (never appended) under lock. Addresses the "don't let MEMORY.md become a mess" concern.
- **Concurrency:** unique filenames + per-project lock → simultaneous same-folder `/clear`s
  never corrupt state or drop a handoff. No attempt to auto-pair new↔old sessions (no stable
  id exists); recall lists recent threads instead.
- **Dedup:** `/wrap` writes `.last-wrap` (epoch); fallback skips if a wrap ran < 180s ago →
  no double-write, no needless headless cost.
- **Recursion guards:** fallback no-ops unless `reason=="clear"`, plus a `HANDOFF_HEADLESS=1`
  env guard so the summariser's own session can't re-trigger anything.
- **Escape hatch:** `FALLBACK_DISABLED` flag file turns off the headless path.

## Risks / limitations (accepted)

- Fallback lands a few seconds after `/clear` (SessionEnd can't block); written by a cheaper
  headless agent; costs a small background API call. `/wrap` avoids all three.
- Same-folder concurrent clears: recall can surface the "wrong" thread first → user/agent picks
  from the listed others. Nothing lost.

## Out of scope (YAGNI)

- Auto-invoking `/clear` from the skill (impossible — a skill can't).
- Perfect new↔old session auto-pairing (no stable id).
- Cross-folder coordination (already isolated by design).
