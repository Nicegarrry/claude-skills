---
name: building-eve-agents
description: Use when building, scaffolding or planning a new Qubit eve agent (librarian, PA, pipeline, issues, slide maker, coding or specialist agents), giving an eve agent channels, tools, connectors, memory or skills, registering it with agent-backend, qwiki, qskills, qWork, Slack or Google, or cutting an old Mac QubitOS persona over to eve.
---

# Building eve agents

## Overview

Every Qubit agent is an eve app on Vercel modelled on QOS (`~/code/QOS/qos`, Nicegarrry/qos), plugged into shared infrastructure: agent-backend (traces, memtree, memory), qwiki (wiki, catalog, files, memory push), qskills (skills), qWork, Slack and Google via Vercel Connect. **Copy the pattern from QOS, register the agent with each shared system, and prove every piece live.** QOS is the reference implementation; read its code before writing new code.

## When to use

- A new durable agent (one repo, one Vercel project, own identity everywhere) or an ephemeral one (spawned per job, no Slack presence).
- Adding a channel, connector, tool family, memory, schedule or skill to any eve agent.
- Retiring an old Mac QubitOS persona (`~/qubit-wiki/os/personas/<name>`) in favour of its eve replacement.

Not for: editing QOS instructions text only (edit `agent/instructions.md`), or writing a qskills skill (qskills repo).

## The loop

Run it under the helm skill (**REQUIRED SUB-SKILL:** helm). Documents go wiki master + qWork (`qdoc.mjs`).

1. **Shape the agent with Nick** (numbered questions, at most two per round, each with a recommendation). Settle the agent card in `references/agent-card.md`: purpose, durable or ephemeral, surfaces, people and grants, tools, memory, schedules, skills, what it must never do, what it replaces.
2. **Apex** (wiki + qWork) from the card, plus a from-to table for the old persona's routines, channels and watchers.
3. **Plan issue** in the agent repo: lettered tickets. Shared contracts first, by you (backend schema, `access.ts` grants shape, people, names). Then 2-3 helm workers in parallel.
4. **Build in this order** (`references/build-order.md`): scaffold and deploy, guardrails, backend and traces, ingress channels, memory, read connectors, skills, access and audit, write tools, schedules, dream, web/embed, cutover.
5. **Register with shared infra** as each piece lands (`references/shared-infra.md`). Most steps need Nick's hands; batch them into one short list with exact clicks.
6. **Review and merge** each PR: read the diff, Codex read-only review (`codex exec -s read-only -o <file> ... < /dev/null`, 15 min watchdog), fix P1/P2, gate `npm test && npx tsc -p . && npx eve build` on Node 24, squash merge (prod deploys on merge).
7. **Live check after every merge** (`references/verify.md`). Say "merged, not yet seen live" until a real turn proves it, and give Nick one prompt that exercises the path.
8. **Cutover in one day**: draft PR with the final channel ids prepared in advance, Slack checklist for Nick, silence the old persona the same day, single-reply check.
9. **Handoff** (`/session-handoff`) and a decision doc per decision (`docs/decisions/NNNN-*.md`, next free number (QOS has duplicate 0005 and 0007: don't repeat that), supersede, never rewrite).

## Non-negotiables (Nick's rules)

| Rule | Why |
|---|---|
| Credentials only in Vercel sensitive env or Connect; swap scripts never print; payment is Nick's | Repo, brief, log, PR and chat are all readable |
| People and roles in the agent repo (`agent/people.ts`), never the wiki | The agent can write the wiki; it must never edit its own permissions |
| Writes follow grants, no approval click; guests and unknown callers get least grants | "IF member has write permission ... their agent should get it too" |
| Unverified principals default to `external` | Preview, OIDC and service callers once got human grants |
| Destructive ops cut at the allowlist (no delete/merge/share; Drive trash only) | Grants decide writes, so the dangerous verbs must not exist |
| Every write audited (requester, channel, tool, target, outcome) | Who asked must be answerable later |
| Tools take paths; bytes never pass through the model | The model hand-typed base64 and corrupted a PDF |
| Personal data stays with the PAs; company agents need no shared Google login | "the brief to me should come from my pa not qos" |
| One identity per agent per system (own Slack app, qWork key, qwiki token, backend token) | Edits and feedback must be attributable |
| Skills live in qskills (`agents.yaml`), not the agent repo or wiki | Skill changes go through eval-gated PRs |
| Rules (layer 1) in repo instructions; company context in the wiki | Nick approves rules only |

## Quick reference

| Need | Copy from QOS | Notes |
|---|---|---|
| Template components and what to rename | `references/components.md` | G = copy, P = parameterise, Q = QOS only |
| Register backend, qwiki, qskills, Slack, Google, qWork, Vercel | `references/shared-infra.md` | Includes Nick's exact clicks |
| Failures already paid for | `references/gotchas.md` | Read before briefing workers |
| Planned agents and their seeds | `references/roster.md` | Librarian, PAs, pipeline, issues, slides, factory |

## Common mistakes

- Forking QOS by copy-paste and leaving `qos*` names, Slack/channel ids, connector ids and URLs hard-coded. Introduce one `AGENT` config module first (`references/components.md`, "Rename list").
- Two agents in one channel both answering: only one agent may auto-reply in a channel; specialists are mention-only.
- Two agents dreaming into the same `memory/channels/<id>.md`: give each channel one memory owner, or per-agent paths, before the second agent dreams.
- User-scoped Google tools in schedules (`principal_required`): schedules run as the app.
- Creating Connect connectors from the CLI: the approval link expires; create in the Vercel dashboard, then run `eve add`.
- Retiring an old persona without checking what still depends on it (watchers hard-wired to it, catalog feeds, PA dream threads, reminders by channel name). Inventory first (`references/cutover.md`).
