---
name: 100-sources
description: >
  Use when you need a deep, broadly-sourced, fact-tiered research brief, narrative,
  or deck on ANY topic - not a quick lookup but a "scan 100 to ~1000 sources and tell
  me what is true and what it means" job. A topic-agnostic research engine: it
  decomposes a topic into many search angles, fans out a swarm of small-model agents
  to read a large number of real sources, ingests everything into a large tiered
  principle set (canon / secondary / forum), whittles the principles into a top-down
  answer-first narrative, and renders it as markdown + a readable HTML report + a
  ~20-slide deck. It self-improves: each run appends what worked and what to fix to a
  LEARNINGS log the next run reads and applies. Real sources only; never fabricate;
  attribute and tier every claim. The generalised engine behind em-guide-maker and
  ai-readiness-assessment.
---

# 100-sources - the topic-agnostic research engine

## What this is

A reusable factory that turns a topic into a defensible, broadly-sourced answer. It
scales the deep-scan -> principles -> narrative pattern (proven in
`ai-readiness-assessment` and `em-guide-maker`) up to **100 to ~1000 sources** by
fanning out a **swarm of small-model agents**, then distils everything **top-down**:
a large tiered principle set whittled into one governing thought with a few pillars,
rendered for reading or presenting.

It is a **workflow factory**, not a discipline rule. Point it at a topic, run it,
review the output, and feed the LEARNINGS loop.

## When to use

- "Research X deeply and tell me what the best are doing" / "what is actually true here".
- Building a knowledge base, a point of view, a market scan, or a board-style brief from
  many sources.
- You want the output as a **narrative**, a **readable HTML report**, and/or a **~20-slide
  deck** - all grounded and tier-tagged.

Do **not** use it for a single-fact lookup or a 2-3 source question - that is just web search.

## How to run

It is a Claude Code Workflow. Run it with the **Workflow tool**, passing the topic in `args`:

```
Workflow({
  name: '100-sources',                       // or scriptPath to workflow/100-sources.workflow.js
  args: {
    topic: 'the question or topic',          // REQUIRED
    sourceTarget: 300,                        // 100..1000 (default 300)
    scanModel: 'haiku',                       // the swarm model: 'haiku' (default) | 'sonnet'
    formats: ['markdown','html','slides'],    // any subset (markdown is always produced)
    out: '/abs/wiki/dir',                     // synthesis dir; default PM/_wiki/research/<slug>
    sourcesOut: '/abs/sources/dir',           // raw evidence; default PM/_sources/research/<slug>
    narrativeHint: 'optional steer',          // optional angle/answer steer
    slideTarget: 20,                          // deck size (default 20)
  },
})
```

**Scale knob.** `sourceTarget` drives the swarm: angles = `ceil(sourceTarget / sourcesPerAngle)`
(default 12 sources/angle, capped at 100 angles). 300 -> ~25 angles; 1000 -> ~83 angles.
Bigger targets cost more (more agents, more tokens) - choose deliberately.

**Where outputs land (the qubit wiki, by default).** Raw evidence (scrapes + per-angle
notes) goes to `PM/_sources/research/<slug>/` (append-only); the structured synthesis
(`principles/` + `principles.md` + `.json`, `narrative.md`, `index.md`, `report.html`,
`deck.html`) goes to `PM/_wiki/research/<slug>/`. Override with `args.out` (synthesis dir)
and `args.sourcesOut` (raw dir) to run the engine outside the practice wiki.

## The pipeline (six phases)

1. **Plan** (sonnet) - decompose the topic into ~8-12 themes and N **MECE** search angles
   (mutually exclusive, collectively exhaustive); each angle carries a **boundary** brief
   stating what it owns and must not cover. Reads `LEARNINGS.md` and applies its guidance.
2. **Scan** (the swarm, **haiku** by default) - one small agent per angle, each given its
   MECE boundary so it stays in its lane and the swarm does not all find the same sources,
   reads ~12 real sources, files raw notes to `_sources`, returns tier-tagged candidate
   principles + citations.
3. **Ingest** (sonnet) - one owner per theme dedupes/merges candidates into a clean
   principle set; a compile step writes the canonical `principles.md` + `.json`.
4. **Narrative** (opus) - whittles the principle set into a Minto-style top-down story:
   one governing thought, 3-6 pillars, supporting points cited to principles, honest caveats.
5. **Render** (sonnet) - markdown is already there; renders a self-contained HTML **report**
   and/or a ~20-slide **deck**, both styled from `templates/house-style.css`.
6. **Learn** (opus) - reviews the run and **appends** improvements to `LEARNINGS.md`.

## Output formats

- **markdown** - `principles.md` (+ `.json`) and `narrative.md`. Always produced.
- **html** - `report.html`: a readable, tier-badged long-form report (self-contained).
- **slides** - `deck.html`: ~20 self-contained slides, answer-first, action-titled - the
  "20 slides not many pages" view.
- **formal slides (future)** - compose with `skills/slide-types` + `skills/frontend-slides`
  + `/systems/design-system` (SapphireOS) for a fully on-brand deck. The narrative + slide
  arc this engine produces are the input to that render.

## Sourcing integrity (non-negotiable)

Real sources only. Every claim is **tiered**: `canon` (named primary / official report /
peer-reviewed), `secondary` (reputable interpreter / synthesis), `forum` (blog / coaching /
vendor / forum - lowest confidence). Weak-tier claims are flagged, never laundered as canon;
market stats are attributed to source, not presented as the author's own results. No em
dashes. Flag, don't guess; never fabricate a source, stat, quote, or URL.

## The self-learning loop

`LEARNINGS.md` is the engine's memory. The **Plan** phase reads it and applies its guidance;
the **Learn** phase appends a dated entry after every run: what worked, what underperformed,
concrete tactical improvements (auto-applied next run via Plan), and a **"Proposed structural
changes (human review)"** list for any code/CONFIG change (the engine proposes, a human edits
the workflow - it does not rewrite its own running code). So the workflow gets better each run
on the data/heuristic level automatically, and surfaces deeper changes for sign-off.

## Pointers

- `workflow/100-sources.workflow.js` - the runnable engine (knobs read from `args`).
- `STRUCTURE.md` - the canonical output structure, the principle/narrative schemas, and the
  self-learning contract. Read before changing a phase.
- `templates/house-style.css` - the shared doc + deck stylesheet the render agents embed.
- `LEARNINGS.md` - the append-only learning log.

## Lineage

Instance lineage of the deep-scan -> principles -> narrative pattern: `ai-readiness-assessment`
(#1) and `em-guide-maker` (#2) are **bespoke instance producers**; **100-sources is the
generalised engine** - topic-agnostic, scaled to a source swarm, with rendering and a learning
loop. Use those for their specific artefacts; use this for any new topic. Does not auto-run;
you invoke it. Draft, never send.
