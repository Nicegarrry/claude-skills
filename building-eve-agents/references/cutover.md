# Cutover from an old Mac QubitOS persona

The old system: `~/code/QubitOS` daemon (`com.qubitos.daemon`, logs `data/logs/daemon{,.err}.log`), config `qos.config.json`, personas `~/qubit-wiki/os/personas/<name>/agent.md` (frontmatter `channels`, `aliases`), routines `~/qubit-wiki/schedule/routines/*.md` (`agent:`, `schedule:`, `channel:`), reminders and tasks in `schedule/reminders`, `schedule/tasks`. Retire a file by moving it to `schedule/_retired/` or `os/personas/_retired/` (the loader skips `_*`). Restart: `launchctl kickstart -k gui/$(id -u)/com.qubitos.daemon`, then read both logs.

## Before (read-only inventory, delegate to a subagent)
1. Everything the persona does: channels it claims, aliases, routines, reminders, tasks with `agent: <name>`, watchers that wake it in code (`grep -rn "persona: '<name>'" src`), what consumes its output (catalog rows read by eve agents, dream threads other personas append to).
2. Last-7-day use from `data/qubitos.db` (`turn_runs`, `schedule_runs`) so you know what is live.
3. Decide per item: moves to eve, stays on the Mac until its replacement, or retired. Flag losses to Nick before switching off.

## Day of
1. Draft PR in the eve repo with final channel ids, merged after the Slack changes.
2. Slack checklist for Nick in order (rename old -> archive -> rename new -> archive the rest -> `/invite`).
3. Old persona: drop its Slack channels and channel-name aliases, retire its routines, repoint reminders whose channel names changed, keep exactly one persona per channel name, no `: ` in descriptions, restart, check `daemon.err.log` and that the daemon is up.
4. Merge, confirm deploy Ready, post a short note in the agent's channel (Nick posts it), check one reply only.

## Still on the Mac (2026-11-01)
PA mail triage (nick@, lucas@, hello@ every 90 s, in daily use), catalog feeds (catalog-daily for Slack/GitHub/HubSpot/Stripe, Granola/Wispr watchers waking the librarian persona, qWork mirror, local catalog -> qwiki mirror), nightly git/DB backups, `dream-open` for the PA dreams, the 13 Nov workshop task, `helm-sync`. The daemon can be switched off only after the librarian and PAs run on eve and these have owners.
