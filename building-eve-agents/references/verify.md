# Live verification

After every merge: deploy Ready (`vercel ls --prod`, `vercel inspect <url>`), then prove the piece in prod. Until proven, report "merged, not yet seen live".

| Piece | Proof |
|---|---|
| Model | web agents: headless browser sign-in, "Reply with exactly: <name> is alive"; Slack-only agents: the same line as a mention in a test channel; schedule-only agents: trigger the schedule in a preview or read its first run in logs |
| Budget | `vercel ai-gateway budgets ls` |
| Evals | `npx eve eval --tag quality --verbose` (about US$0.20 for 5 cases) |
| Backend | authed 200 / unauthed 401; a test turn row with channel, model, tokens |
| Slack | 4-step script for Nick: plain message stored with no reply; mention gets a thread reply; follow-up answered; reaction recorded |
| Slack scopes | the hourly pull stops logging "missing scope" |
| qwiki push | signed test webhook 200, stale timestamp 401; seed a page and see the backend copy update |
| qwiki grants | qWiki session confirms forbidden paths refused |
| Connectors | one live read in a real turn; grep prod logs for 4xx after each new tool |
| Writes | one real write per family, audit line in logs (`-q audit`) |
| qWork comments | `/hooks/qwork/events` 200s in logs after an @mention |
| Schedules | the post lands in the right channel at the right Sydney time; dream receipt page exists next morning |
| Cutover | one reply only in the auto-reply channel; old daemon log clean after restart |

Logs: `vercel logs --no-branch --environment production --since 2h -q "<text>" -n 100 -j` and parse JSON. Give Nick one prompt that exercises a whole new path end to end.
