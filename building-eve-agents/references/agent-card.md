# Agent card

Fill this in the design chat before the apex. Every blank is a question for Nick (with your recommendation).

```yaml
name: <kebab, also the handle on every system: slack app, qwork, qwiki consumer, backend agent, qskills key>
kind: durable | ephemeral      # durable = own repo, Vercel project, memory, Slack presence; ephemeral = spawned per job, no channel memory
purpose: <one sentence>
replaces: <old persona / routines / watchers, or none>
surfaces:                      # where turns start
  slack: { channels: [<name: C…>], auto_reply: [<ids>], mention_only: true, dms: false }
  web_embed: false             # rail bubble on qwork/qwiki/site
  qwork_comments: false        # @<handle> in qWork comments
  schedules: [<name: Sydney time; converted to UTC cron, double cron if the local hour matters>]
  webhooks: [<source>]         # e.g. qwiki memory push, GitHub, HubSpot
people_and_grants:             # roles in agent/people.ts; grants in agent/lib/access.ts
  admin: full
  member: <...>
  external/guest: least
tools:                         # per family: none/read/write, and the verbs cut at the allowlist
  - <hubspot: read+write, no delete/merge>
memory:
  channel_memory: own | read-only | none   # who owns memory/channels/<id>.md
  private_memory: <PAs only>
  dream: <nightly receipt memory/_dreams/<name>/>
  company_memory: read (write only for librarian, propose-only for others)
skills: [<qskills names>]      # each skill's tool dependencies must exist in this agent
model: <default deepseek flash for volume; frontier for judgement. Direct Claude (Max plan API credit) must be wrapped in withFallback from qos agent/lib/model-fallback.ts so it drops to DeepSeek on outage or spend cap>
never: [<things this agent must never do>]
cutover: <what moves on day one, what stays, what is retired>
done_when: [<observable checks>]
```

Rules of thumb:
- Durable agents own one area and one Slack app. Specialists in shared channels are mention-only.
- Anything personal (mail, calendar edit, private memory) belongs to a PA, not a company agent.
- If the agent mainly runs a pipeline (classify, build, review, PR), consider an ephemeral agent driven by a durable dispatcher (see `roster.md`, issues/factory).
