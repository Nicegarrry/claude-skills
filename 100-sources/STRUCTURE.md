# The Structure of a 100-sources run

The contract every run fills. Read this before changing a phase in
`workflow/100-sources.workflow.js`. It is topic-agnostic: only the topic and the
`args` knobs change; the shape below is constant.

---

## 1. The output tree (the qubit wiki, by default)

Raw evidence and structured synthesis live in two homes, mirroring the practice's
source-vs-wiki split:

```
PM/_sources/research/<slug>/      RAW EVIDENCE (append-only)        [args.sourcesOut]
  <angleKey>/                       scrapes saved by each scanner
  <angleKey>.md                     the scanner's tiered note

PM/_wiki/research/<slug>/         STRUCTURED SYNTHESIS              [args.out]
  index.md                          wiki front door for this run
  principles/<themeKey>.md          one deduped file per theme
  principles.md                     canonical, globally-numbered set (P1..)
  principles.json                   [{ id, theme, statement, tier, source }]
  narrative.md                      the top-down answer-first narrative (headline artefact)
  report.html                       self-contained long-form report (if 'html' in formats)
  deck.html                         self-contained ~20-slide deck (if 'slides' in formats)
```

Defaults are the qubit (PM) wiki. Override both via `args.out` (synthesis) and
`args.sourcesOut` (raw) to run the engine elsewhere. Raw scrapes are append-only
evidence; the principle files and narrative are compiled understanding.

---

## 2. The principle object (the atom)

Every candidate and every final principle carries:

| Field | Meaning |
|---|---|
| `statement` | the finding as a durable, prescriptive claim (no platitudes) |
| `theme` / `themeKey` | one of the run's 8-12 themes (or `other`) |
| `tier` | `canon` / `secondary` / `forum` (see tiering) |
| `source` | the named source the claim rests on |
| `evidence` | a one-line quote / number / proof (optional but preferred) |

**Tiering (the integrity mechanism).**
- `canon` - a named primary source, official report, standard, or peer-reviewed study.
- `secondary` - a reputable interpreter or synthesis of primary work.
- `forum` - blog / coaching / vendor / forum post. Lowest confidence; treat single-source
  `forum` claims as provisional and say so.

Weight `canon` heavily; never launder `forum` as `canon`; attribute market stats to their
source (they are evidence, not the engine's own results).

---

## 3. The scaling mechanism

`sourceTarget` (100..1000) drives the swarm:

```
anglesNeeded   = ceil(sourceTarget / sourcesPerAngle)      // sourcesPerAngle default 12
angleCount     = clamp(anglesNeeded, 8, 100)
sourcesAchieved ~= sum of sources actually read across all scan agents
```

**MECE is the lever** that makes a large source count *cover* the topic rather than re-read
the same few pages. The Plan phase produces a MECE decomposition - mutually exclusive (no two
angles overlap) and collectively exhaustive (no gap) - partitioned by sub-question, stakeholder,
source-type, geography, time, value-chain stage, and a contrarian angle. Each angle carries a
**boundary** (what it owns, what it must not touch) handed to its scanner as its brief, so the
swarm stays in its lanes and does not all find the same sources. The scan model is small (`haiku`
by default) and parallel - the "swarm" - with `sonnet` available via `args.scanModel` for
harder/technical corpora.

---

## 4. The narrative (whittle top-down)

`narrative.md` is a Minto pyramid built FROM the principle set, answer-first:

1. **Governing thought** - the single-sentence answer to the topic.
2. **Executive summary** - a short paragraph.
3. **3-6 pillars** - each a full-sentence message, with supporting points, every point cited
   to specific principles (Pn / source / tier).
4. **Read with care** - the honest caveats: the weak-tier, contested, or single-source claims.

The narrative *whittles*: hundreds of principles collapse into a few load-bearing pillars.
Lead with the answer; the research supports it, it does not meander to it.

---

## 5. The render contract

Both renders are **single self-contained HTML files** (inline CSS from
`templates/house-style.css`, no external assets, render offline), and carry **zero em/en
dashes** (verified by grep before return).

- **report.html** (`body.doc-mode > .wrap`): a `header.doc` (kicker / h1 / `.sub` governing
  thought / `.meta` pills), `<main>` with one `<h2>` per pillar (tier-tagged `.stat`s, a
  "So what" line), a `.callout.warn` "Read with care", and a `footer.doc` source note.
- **deck.html** (`body.deck-mode > .deck`): ~`slideTarget` `.slide` sections (cover ->
  exec-summary -> per pillar: a `.divider` then 1-3 content slides -> "read with care" ->
  sources/close). Every content slide has an **action title** (`h2.action-title`, a
  full-sentence conclusion) and a `.src` line where it carries a stat. Arrow-key + scroll nav.

Formal on-brand decks are a future format: feed the narrative + slide arc to
`skills/slide-types` + `skills/frontend-slides` + `/systems/design-system` (SapphireOS).

---

## 6. The self-learning contract

`LEARNINGS.md` is the engine's memory and the mechanism by which it improves.

- **Plan reads it** at the start of every run and applies its guidance to theme/angle
  generation and method (the `appliedLearnings` field records which entries were used).
- **Learn appends to it** at the end of every run (never overwrites; stamps the date via
  `date +%F`). Each entry: what worked, what underperformed, 3-6 concrete **tactical
  improvements** phrased as guidance the Plan phase can apply automatically next run, and a
  **"Proposed structural changes (human review)"** subsection for any code/CONFIG change.

**Boundary:** the engine improves its **data and heuristics** automatically (via the log the
Plan phase consumes); it does **not** rewrite its own running workflow code. Structural changes
are proposed for a human to apply. This keeps self-improvement safe and inspectable.

---

## 7. Phase / model map

| Phase | Model | Owns |
|---|---|---|
| Plan | sonnet | MECE topic decomposition (themes + bounded angles); reads + applies LEARNINGS |
| Scan | haiku (swarm) | parallel source reading within a MECE boundary + tiered principle extraction |
| Ingest | sonnet | per-theme dedupe/merge + compile canonical principles |
| Narrative | opus | whittle to the top-down answer-first story |
| Render | sonnet | self-contained HTML report + ~20-slide deck |
| Learn | opus | self-review + append improvements to LEARNINGS |
