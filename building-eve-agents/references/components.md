# Components (copy from `~/code/QOS/qos`)

G = generic, copy and rename prefixes. P = pattern generic, values agent-specific. Q = QOS only, don't copy. Verify every component with `source ~/.nvm/nvm.sh && nvm use 24 && npm test && npx tsc -p . && npx eve build`.

## Core
| Component | Files | | Env / connector |
|---|---|---|---|
| Config | `agent/agent.ts` (model, `reasoning`, `experimental.workflow.retention: "default"`) | P | Gateway OIDC (local: `vercel env pull` gives `VERCEL_OIDC_TOKEN`, ~12 h) |
| Package | `package.json` (`"#*": "./agent/*"`, `engines.node 24.x`, `test` script), `tsconfig.json` | G | |
| Routing | `vercel.ts` (`withEve`, `/hooks/*` -> eve service, rest -> web) | G | needed for any custom webhook path |
| Instructions | `agent/instructions.md` (layer 1), `agent/instructions/company-memory.ts` (dynamic, wrapped as quoted data) | Q text / G loader | backend env |

## Identity and access
| Component | Files | | Notes |
|---|---|---|---|
| People | `agent/people.ts` (Slack id, team id, emails, role) | P | team `T0C93PV64HY` |
| Access | `agent/lib/access.ts` (`AccessContext`, `Grants`, `decide`, `accessFromRuntime`, `slackChannelKind`) | P | Grants lists this agent's tool families; `least` and `full` |
| Channel labels | `agent/lib/channel-labels.ts` (`internal`, `auto-reply`, later `clients`, `shared`) | P | ids |
| Audit | `agent/lib/audit.ts`, `agent/hooks/audit.ts` (`call.settled` for MCP writes) | G | update the write-tool set |

## Channels
| Component | Files | | Env / connector |
|---|---|---|---|
| Slack | `channels/slack.ts`, `lib/slack-credentials.ts`, `lib/slack-ingest.ts`, `lib/slack-format.ts` | P | Connect `slack/<name>`; spoof guard regex uses the agent name |
| Web chat + embed | `channels/eve.ts`, `lib/web-session.ts`, `apps/web/**` (`/embed`, `/api/bubble/{auth,session}`, `next.config.ts` frame-ancestors) | P | `<NAME>_WEB_SESSION_SECRET`, Clerk keys (prod keys only on the custom domain) |
| qWork comments | `channels/qwork-events.ts`, `scripts/qwork-subscribe.ts` | P | `QWORK_WEBHOOK_SECRET`, `QWORK_AGENT_HANDLE`, `QWORK_API_KEY` |
| qwiki push | `channels/qwiki-hooks.ts`, `lib/qwiki-sync.ts`, `schedules/qwiki-sync.ts` | G | `QWIKI_URL`, `QWIKI_TOKEN`, `QWIKI_WEBHOOK_SECRET` |

## Memory and traces
| Component | Files | | Env |
|---|---|---|---|
| Backend client | `lib/backend.ts` | G | `AGENT_BACKEND_URL`, `AGENT_BACKEND_TOKEN` |
| Traces | `instrumentation/trace-store.ts`, `lib/trace-fold.ts` | G | backend |
| Channel memory | `memory/channel.ts`, `lib/memtree/{index,provider,summarise}.ts` | G (sender name, event name) | backend, Gateway |
| Slack backfill | `lib/slack-pull.ts`, `schedules/slack-pull.ts` (`15 * * * *`, resumable, time budget) | G | Slack connector |
| Dream | `lib/dream.ts`, `schedules/dream.ts` | P (receipt path, author, prompt) | qwiki write on own memory scopes |

## Connectors and tools
| Component | Files | | Env / connector |
|---|---|---|---|
| qwiki MCP | `connections/qwiki.ts` (READ_TOOLS / WRITE_TOOLS allowlists by grant), `lib/qwiki.ts` (per-call timeout) | G | qwiki env |
| qWork MCP | `connections/qwork.ts` (no `file_share`, `ops_undo`) | G | `QWORK_API_KEY` |
| Other REST sources (GitHub, Stripe, Granola) | copy the HubSpot pattern: `lib/<source>.ts` client with timeout + redacted errors, `tools/<source>_*`, token in sensitive env (GitHub fine-grained token or app, Stripe restricted key, Granola API key). Catalog rules per source: `~/qubit-wiki/os/connectors/<source>/catalog.md` | P | per source |
| HubSpot | `lib/hubspot.ts`, `tools/hubspot_{search,get,reference,write}.ts` | G | `HUBSPOT_TOKEN` (private app; HubSpot remote MCP fails Connect) |
| Google | `lib/google.ts` (scopes, 401/403 re-auth, GET-only retry), `lib/calendar.ts`, `lib/drive-write.ts`, `lib/drive-tool.ts`, `tools/drive_*`, `tools/calendar_*` | P | Connect `google/<name>-google`, user-scoped |
| Files | `tools/pdf_render.ts`, `tools/slack_send_file.ts`, `lib/sandbox-file.ts`, `tools/file_store.ts` | G | Slack `files:write` |
| Ingest, slides, images | `tools/ingest_fetch.ts`, `tools/slide_render.ts`, `tools/image_generate.ts` | G | Gateway, qWork |
| Sandbox | `agent/sandbox.ts` (Chromium, markitdown/yt-dlp venv) | G | drop installs the agent does not need (~1.5 min build each) |
| Skills | `agent/extensions/qskills.ts` + `vendor/qubit-qskills-<v>.tgz` | P | `qskills({ agent: "<name>" })` |
| Rhythm | `lib/rhythm.ts`, `schedules/*` | P | channel id, Sydney DST double cron |

## Patterns to keep
- QOS gives `admin`, `member` and unregistered humans (`none`) the full grant. An agent with sensitive writes (librarian on `memory/company.md`, PAs on mail) must give `none` the least grant and gate those paths by role inside the tool or connection, not just by tool family. If catalog writes need separate control, add a `catalog` family to `Grants` (QOS ties `catalog_upsert` to qwiki write).
- Ingress resolves trust once and stores verified auth attributes; `decide()` is pure; connections are `defineDynamic` returning `null` or a narrower allowlist; tools re-check grants in `execute`.
- Everything recalled (memory, company context, pages, tool output) is wrapped as quoted data, not instructions.
- Every remote call has a timeout; instrumentation, memory and hooks never throw into eve; long jobs keep resumable state in backend memory paths under a time budget.
- Webhooks verify the signature on the raw body (300 s skew, constant-time), answer within 10 s, use `idempotencyKey`.
- Rare tools `deferred: true`; skills not deferred unless an eval proves they are still found.

## Rename list (hard-coded in QOS today)
Put these in one `agent/config.ts` before copying anything:
- attribute keys `qosTrust`, `qosChannelKind`, `qosSlackUserId`, `qosTeamId`, `qosEmail`; authenticators `qos-web`, `qos-qwork`; cookie `qos_session`; env `QOS_*`; Clerk metadata `qosBubble`; backend event `qos.channel`; memtree sender "QOS"; spoof regex `/^@?qos\b/`; dream author `qos-dream`, path `memory/_dreams/qos/` and prompt "Nightly QOS dream" (`lib/dream.ts`); memtree turn prefix `qos:turn:` (`lib/memtree/provider.ts`).
- Slack team id, channel ids (labels, rhythm fallback), connector ids `slack/qos`, `google/qos-google`.
- URLs `https://qos.qubitstudio.app` (bubble auth route, qwork-subscribe script), embed origins (`lib/bubble.ts`, `next.config.ts`).
- qskills key, qubit-rail `agent` option (typed `"qos"` only: needs a rail change for a second embeddable agent).
- models (`agent.ts`, memtree summariser, image, ingest), timezone Australia/Sydney.

Better than copying: extract the G components into a shared package (`@qubit/agent-kit`) once the second agent starts, so fixes land once.
