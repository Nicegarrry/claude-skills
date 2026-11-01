# Build order

The QOS sequence (Nicegarrry/qos PRs #3-#45, 28 Oct to 1 Nov 2026), generalised. Each step = one ticket = one PR unless noted. Skip steps the agent card does not need.

| # | Step | What lands | QOS ref |
|---|---|---|---|
| 0 | Scaffold | `eve init` in a new repo (repo root = agent, `package.json` at root); `docs/decisions/`; `.vercelignore` has `docs`; CLAUDE.md -> AGENTS.md; Node 24 `engines` | 0214bdd, decision 0001 |
| 1 | Contracts | one `agent/config.ts` (name, handle, connector ids, origin, channel ids, timezone; `components.md` rename list), `agent/people.ts`, and the `Grants` shape + `decide()` stub in `agent/lib/access.ts` (ingress in step 5 sets the trust attributes it reads) | QOS added these late (#22, #34): do them first |
| 2 | Deploy | `eve link --non-interactive --project <name>`; `eve deploy --non-interactive --yes`; AI Gateway via OIDC (no keys); connect GitHub so merge = prod deploy; custom domain `<name>.qubitstudio.app` | da48b75 |
| 3 | Guardrails | Gateway budget per project (dashboard), 3-5 quality evals with private frozen fixtures, `experimental.workflow.retention: "default"` | 43fad2e |
| 4 | Backend + traces | backend token, `lib/backend.ts`, `lib/trace-fold.ts`, `instrumentation/trace-store.ts`, test runner (`node --test agent/lib/**/*.test.ts`), add to nightly archive | #3, #6 |
| 5 | Slack ingress | Connect connector created in dashboard, `eve add channel/slack`, ingest every message to memtree with trust, turns only for humans on mention/DM/auto-reply/subscribed thread, reaction signals, channel-link renderer | #10, #11, #45 |
| 6 | Memory | memtree slot `memory/channel.ts`, hourly `slack-pull` backfill, qwiki memory push webhook + 10-min catch-up, company memory dynamic instruction | #5, #7-#9, #12-#15 |
| 7 | Read connectors | one per ticket; probe the live API yourself first; allowlisted MCP or REST tools; deferred if rare | #16, #17, #26, #28 |
| 8 | Skills | qskills `agents.yaml` entry, vendored tarball, `extensions/qskills.ts`, skill-load evals | #20, #31, #33 |
| 9 | Access enforcement + audit | `decide()` gating every connection and tool, path-level gates for sensitive writes, `audit.ts` + `hooks/audit.ts` | #22, #34 |
| 10 | Write tools | grant check inside `execute`, audit line, destructive verbs absent | #27, #35, #38 |
| 11 | Files | `pdf_render`, `slack_send_file`, `file_store` (paths in, never bytes) | #37 |
| 12 | Schedules | eve crons are UTC. A post at a fixed Sydney time needs the DST double cron + `shouldPost` gate (`lib/rhythm.ts`); jobs whose exact hour doesn't matter (dream, pulls) use one cron. App principal only | #21 |
| 13 | Dream | nightly own-channel memory rewrite + receipt `memory/_dreams/<name>/<date>.md`; empty-rewrite guard | #23 |
| 14 | Web / embed / qWork comments | Clerk session, `/embed` for the rail, qWork `comment.created` webhook; only if the card lists them | #40-#42, #44 |
| 15 | Instructions v1 | layer 1 only (identity, judgement, ask-for-a-yes list, privacy, how you work with tool names, phone-first replies); one line per tool family added in that tool's PR | #19 |
| 16 | Cutover | draft PR with final ids, checklist, old persona silenced | #39, `cutover.md` |

Per ticket brief (helm `brief.md`): objective, settled design, acceptance tests with fakes (no network), verify command, out of scope (name the files other running tickets own), "no credentials anywhere, name paths when staging".

Parallelism: tickets touching different files run together, max 2-3 (the Mac mini chokes on more). Shared helpers in `agent/lib/` are written by the lead first.
