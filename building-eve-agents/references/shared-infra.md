# Registering a new agent with shared infrastructure

Never print, echo or commit a token. Scripts that print a token once (`agents:create`, qwiki `consumer.ts create`) run inside one command that captures and pipes it, e.g. `npx convex run --prod agents:create '{"agent":"<name>"}' | <extract token> | vercel env add AGENT_BACKEND_TOKEN production --sensitive`; inspect the output shape on a dry run with the token field masked first. Mark steps that need Nick with **Nick**; batch them into one list with exact clicks.

## Vercel project
1. `eve link --non-interactive --project <name>`; `eve deploy --non-interactive --yes`.
2. Connect the GitHub repo (prod deploys on merge to main). Add domain `<name>.qubitstudio.app`.
3. **Nick:** AI Gateway budget for the project (Vercel dashboard, the project, AI Gateway, Budgets; confirm the path live; QOS has US$200/mo; check with `vercel ai-gateway budgets ls`). A card must be on file; payment is Nick's.

## agent-backend (Convex, `~/code/QOS/agent-backend`, Nicegarrry/agent-backend)
Storage-only HTTP API; every row keyed by the agent behind the bearer token, so agents never collide. Routes in `docs/api.md`.
1. `npx convex run --prod agents:create '{"agent":"<name>"}'` (confirm `--prod`; token prints once). Rotate with `agents:rotate`.
2. `AGENT_BACKEND_URL` (same as qos) and `AGENT_BACKEND_TOKEN` (sensitive) in Vercel.
3. Add `<name>` to `AGENTS=(...)` in `~/.local/bin/agent-backend-archive`; token in keychain service `agent-backend-token`, account `<name>`.

## qwiki (key + memory scopes)
Keys are a module (`~/code/web/qwiki/docs/keys.md`). The CLI is `scripts/keys.ts` (`profiles`, `list`, `show`, `create`, `grant`, `rotate`, `revoke`, `audit`, `refusals`), run against the **prod** Convex env (`NEXT_PUBLIC_CONVEX_URL=https://decisive-jaguar-336.convex.cloud`, `QWIKI_SERVER_SECRET` from `npx convex env get QWIKI_SERVER_SECRET --prod`); the local `.env.local` is dev. Nick and Lucas can also revoke or rotate at `https://qwiki.qubitstudio.app/wiki/admin/keys`.
1. Create from a profile, which needs a human admin's yes: `npx tsx scripts/keys.ts create <name> --profile company-agent|pa-agent|ephemeral-agent|service --write memory/channels/<id>.md <page globs>... [--catalog-write] [--file-add] --approved-by <nick or lucas email> --token-file <scratch>/t`.
   - `company-agent` gives read `**` minus PA/people memory, plus write `memory/_inbox/**` and `memory/_dreams/<name>/**`.
   - `pa-agent` names end in `-pa` and own `os/memory/<name>/**`.
   - Channel memory is per channel: `memory/channels/<slackChannelId>.md`.
   - `memory/company.md` and the shared rule files are protected: only keys with `--protected <path>` (the librarian, human admins) can write them.
   - Widening a key later is `grant … --approved-by`.
2. Vercel: `QWIKI_URL=https://qwiki.qubitstudio.app`. Set `QWIKI_TOKEN` (sensitive) straight from the token file: `vercel env add QWIKI_TOKEN production --sensitive < <scratch>/t`, then delete the file. Never echo the token.
3. Subscribe once with the agent's key (prod domain, HTTPS): `POST /api/v1/subscribe {"url":"https://<domain>/hooks/qwiki/memory","filters":["memory/company.md","memory/channels/*"]}`. Store the returned secret as `QWIKI_WEBHOOK_SECRET` in the same piped way.
4. Check live with the key: `whoami` shows the effective grants, and a forbidden path returns 403. Refusals show in `scripts/keys.ts refusals`.

## qskills (`~/code/QOS/qskills`, Nicegarrry/qskills)
1. PR in qskills (pnpm workspace: `pnpm install`): `agents.yaml` entry `<name>: [skills]` (+ new skill folders); `pnpm test && pnpm typecheck && pnpm build`; bump version; merge; `pnpm pack` script (`release/qubit-qskills-<v>.tgz`).
   Porting a Mac skill (`~/qubit-wiki/os/skills/<name>/SKILL.md`): rewrite for eve per the qskills `AGENTS.md` and decision 0004 in the agent repo: drop Claude Code, Bash, local paths and `qos` CLI; point wiki lookups at `qwiki__*`; scripts need the sandbox.
2. Agent repo: copy `release/qubit-qskills-<v>.tgz` to `vendor/`, `npm install ./vendor/...`, `agent/extensions/qskills.ts` with `qskills({ agent: "<name>" })`, delete the old tarball, add `evals/skills/<skill>-loads.eval.ts`.
3. Every listed skill's tool dependencies (`slide_render`, `ingest_fetch`, `file_store`, `image_generate`, `drive_*`, `qwiki__*`, `qwork__*`) must exist in the agent.

## Slack (own app per agent, via Vercel Connect)
1. **Nick:** Vercel dashboard, Connect, Create, Slack (never the CLI link: it expires in minutes). Unique name and handle (check existing bots first). Advanced: bot scopes `app_mentions:read`, `channels:read`, `channels:history`, `groups:read`, `groups:history`, `users:read`, `reactions:read`, `files:write`, `chat:write` (+ `im:read`, `im:history` if DMs); cross-check `.output/vercel-connect-manifest.json` after `npx eve build`; events `message.channels`, `message.groups`, `message.im` (if DMs), `app_mention`, `reaction_added`. Install to the workspace, attach to the project.
2. `eve add channel/slack --non-interactive` to wire the connector into `agent/channels/slack.ts`.
3. **Nick:** `/invite @<handle>` in each channel on the card.
4. Adding scopes later needs no reinstall; verify by behaviour or logs, not the UI.

## Google (Vercel Connect, user-scoped OAuth only)
1. **Nick:** in GCP project `qubit-cos`, enable the APIs; consent screen Internal; add scopes; OAuth client type Web, redirect `https://connect.vercel.com/callback`; download the client JSON.
2. You: write a temp `--data` file outside the repo, `npx -y vercel@65.9.0 connect create google --connection-method oauth --name <name>-google --data @<tmp>`, delete the temp, `npx -y vercel@65.9.0 connect attach google/<name>-google --project <name> --environment production --yes`. Ask Nick to delete the download.
3. `connect({ connector: "google/<name>-google", tokenParams: { scopes } })` in `lib/google.ts`. Each user approves a sign-in link on first use and again on each scope widening.
4. Schedules cannot use it (`principal_required`). PAs need Gmail and Calendar write; company agents do not.

## qWork
1. **Nick:** qWork Settings, Agents, New agent `<handle>`, role editor; copy the key; type `! qwork-key-swap` (validates the clipboard key, writes `QWORK_API_KEY` without printing; currently hard-wired to `~/code/QOS/qos`: pass the repo or generalise it first).
2. Comment turns: `QWORK_WEBHOOK_SECRET` (`whsec_` + base64, 32+ chars), `QWORK_AGENT_HANDLE`, deploy, then `node scripts/qwork-subscribe.ts` (edit its hard-coded URL).

## Web and rail
- Clerk prod instance `clerk.qubitstudio.app`; prod keys only work on the custom domain, so previews cannot test sign-in.
- qubit-rail `agent` option is typed `"qos"`: a second embeddable agent needs a rail release first.

## Shared-system rules
- One owner per channel memory file until per-agent paths exist; only one agent auto-replies per channel.
- The old Mac Slack app stays installed for quick Mac-run agents (Nick, 2026-11-01); don't uninstall it when personas move.
