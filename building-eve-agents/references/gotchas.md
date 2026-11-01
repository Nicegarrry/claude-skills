# Gotchas already paid for (symptom -> fix -> rule)

## Setup and tooling
- eve won't run -> shell on Node 22 -> `source ~/.nvm/nvm.sh && nvm use 24` in every command.
- `vercel connect create` lacks `--connection-method/--data` -> local CLI too old -> `npx -y vercel@65.9.0 connect ...`.
- Slack Connect approval link expired / "Request code is already in use" -> CLI links expire in minutes -> create connectors in the Vercel dashboard, then `eve add`.
- Bot name clash with the old `@qos` -> pick a unique handle; check existing bots first.
- Helm worktree on T7 has an empty `node_modules` -> symlink the main checkout's, and remove the symlink before commit or `helm pr`.
- `codex` missing in background shells -> absolute path; always `< /dev/null`; 15 min watchdog (no `timeout` on macOS: background `kill` after `sleep 900`).
- Scratchpad wiped mid-session -> never keep anything Nick needs in tmp; briefs that matter go in the repo or wiki.
- No CI beyond a light check: the local gate is the gate.

## Web and auth
- `placeholderAuth()` error -> the chat's own XHRs carried no Basic auth -> signed session cookie, later Clerk -> test auth in a fresh headless browser, not curl.
- Clerk prod keys fail on `*.vercel.app` -> use the custom domain.
- Passwords/secrets for Nick go as a file (SendUserFile), never in chat; keep a recoverable copy outside tmp.

## Routing and webhooks
- Webhook 401 with a login page -> only `/eve/v1/*` reached the agent -> route `/hooks/*` explicitly in `vercel.ts`.
- Only the scheduled catch-up moves a sync cursor; a webhook must not skip past a missed one.

## Memory and traces
- Trace end events dropped -> start/end share an id -> dedup key = event name + id.
- Traces rarely flushed on serverless -> flush on every `turn.settled`.
- Memory scope null in prod -> OIDC principal ids contain colons -> allow them; check principal id formats per auth type.
- Dream could erase memory with an empty rewrite, and skipped messages past 400 -> guard empty rewrites, paginate.
- Client/backend disagreed on the tree format -> contract tests against the real backend.

## Slack
- Hourly pull never ran -> `users.conversations` with private types needs `groups:read` -> degrade to public and log.
- Without `users:read` everyone is external and the agent never replies -> request it up front.
- `users.info` failure defaulted to human, letting guests start turns -> fail closed to external; members only when their team equals the installation team; never trust a display name that looks like the agent.
- Unverified callers (preview, OIDC, service) got human grants and could write HubSpot -> default to `external`.
- Agent wrote `#C0C95T0D76D` -> Slack renderer rewrites standalone ids to `<#ID>` (skip URLs, links, code).
- Archived channels keep their names reserved -> rename the old one (`#x-old`) before archiving, then rename the new one.
- The undeletable default channel may not be #general (here `#all-qubit-studio`, `is_general`) -> check before planning renames.
- Renames keep channel ids, so ids in config survive.
- Two bots in one channel both reply -> one auto-replier per channel; silence the old system the same day.
- `vercel logs` shows 50-100 lines by default -> use `-q "<text>" -n 100 -j` and parse timestamps; success is often silent, so prove with data (backend rows, qwiki files) or the user's test.

## Google
- `principal_required` on schedules -> user-scoped OAuth has no user on cron -> keep Google out of schedules.
- Calendar HTTP 400 -> model sent date-only or local times -> normalise to RFC 3339 in Sydney time; surface the API message with tokens redacted.
- Drive search ignored later pages -> paginate everything.
- Client secret JSON left in Downloads -> ask Nick to delete it.

## Files
- Corrupt 14 KB PDF and duplicates -> `file_store` timed out at 3 s, rejected absolute paths, and the model hand-typed base64 into raw `file_add` -> `pdf_render`, `slack_send_file`, path-only `file_store` with a 120 s timeout and no blind retry, raw byte tools removed from the model.
- Local HTML to PDF lost assets -> load via `file://` URL.
- Slide render opened srcdoc with JS on via `file://` (local file disclosure, SSRF) -> render inert: JS off, request routing, CSP.

## qwiki, qWork, data
- Prompt injection reaching persistent writes -> writes only for verified members; capture tools that take channel/trust (`append_inbox`) stay code-only.
- Using another agent's qWork key made edits look like theirs -> own key before cutover.
- Never call `qw feedback` in read-only work (mutates prod).
- Company context JSON-encoded in the prompt read badly -> wrap as plain quoted text.

## Old Mac QubitOS (cutover)
- Two personas claiming one channel crash-loops the daemon (`channel "x" is claimed by both`) -> one owner per channel name; check `daemon.err.log` after every restart.
- A colon-space in persona frontmatter `description` breaks YAML and the persona silently skips -> no `: ` in descriptions.
- Watchers hard-code `persona: 'librarian'` (Granola, Wispr); reminders target channels by name -> inventory before retiring.

## Models and spend
- Gateway budget is approximate: the crossing request completes.
- Do not use AI Gateway BYOK for Bedrock (falls back to Anthropic direct on Vercel credit).
