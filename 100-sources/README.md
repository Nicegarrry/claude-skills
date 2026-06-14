# 100-sources

A topic-agnostic **research engine** for Claude Code. Point it at any topic and it
scans 100–1000 real sources, distils them into a tiered principle set, and renders
an answer-first narrative as markdown, a self-contained HTML report, and a ~20-slide
deck. It self-improves — each run appends what worked to a `LEARNINGS.md` log that
the next run reads and applies.

> Not a quick lookup — a "scan 100+ sources and tell me what's true and what it
> means" job. For a single fact, just use web search.

## How it works

It's a Claude Code **Workflow** (deterministic multi-agent orchestration). Six phases:

1. **Plan** (sonnet) — decompose the topic into 8–12 themes and N **MECE** search angles, each with a boundary brief so the swarm doesn't all find the same sources. Reads `LEARNINGS.md`.
2. **Scan** (swarm, haiku) — one small agent per angle reads ~12 real sources, files raw notes, returns tier-tagged candidate principles + citations.
3. **Ingest** (sonnet) — one owner per theme dedupes/merges into a clean principle set; compiles canonical `principles.md` + `.json`.
4. **Narrative** (opus) — whittles principles into a Minto top-down story: one governing thought, 3–6 pillars, cited support, honest caveats.
5. **Render** (sonnet) — self-contained HTML report and/or ~20-slide deck, styled from `templates/house-style.css`.
6. **Learn** (opus) — reviews the run and appends improvements to `LEARNINGS.md`.

## Run it

Invoke with the Workflow tool, passing the topic in `args`:

```js
Workflow({
  scriptPath: '~/.claude/skills/100-sources/workflow/100-sources.workflow.js',
  args: {
    topic: 'the question or topic',        // REQUIRED
    sourceTarget: 300,                      // 100..1000 (default 300)
    scanModel: 'haiku',                     // swarm model: 'haiku' | 'sonnet'
    formats: ['markdown', 'html', 'slides'],
    out: '/abs/synthesis/dir',              // optional; default <wiki>/research/<slug>
    sourcesOut: '/abs/raw/evidence/dir',    // optional; raw scrapes
    narrativeHint: 'optional angle steer',
    slideTarget: 20,
  },
})
```

**Scale knob:** `sourceTarget` drives the swarm — angles ≈ `ceil(sourceTarget / 12)`.
300 → ~25 angles; 1000 → ~83. Bigger = more agents/tokens; choose deliberately.

## Sourcing integrity (non-negotiable)

Real sources only — never fabricate a source, stat, quote, or URL. Every claim is
**tiered**: `canon` (primary / official / peer-reviewed) · `secondary` (reputable
synthesis) · `forum` (blog / vendor / forum, lowest confidence). Weak-tier claims
are flagged, never laundered as canon. Flag, don't guess. Draft, never send.

## Files

- `workflow/100-sources.workflow.js` — the runnable engine (knobs read from `args`)
- `SKILL.md` — what Claude reads
- `STRUCTURE.md` — output structure, principle/narrative schemas, self-learning contract
- `LEARNINGS.md` — append-only learning log (the engine's memory)
- `templates/house-style.css` — shared report + deck stylesheet
