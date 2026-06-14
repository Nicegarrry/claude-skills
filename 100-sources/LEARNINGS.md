# 100-sources - LEARNINGS

The engine's memory. The **Plan** phase reads this at the start of every run and applies
the guidance below; the **Learn** phase appends a new dated section after every run. Newest
entries are the most load-bearing. Keep entries tight and actionable. Append, do not rewrite.

How to use this file when planning a run:
- Read the tactical improvements and fold them into theme/angle generation and method.
- Honour the "carry-forward guidance" list - these are durable rules distilled from past runs.
- Check "Proposed structural changes" for changes a human may have since applied to the workflow.

---

## Carry-forward guidance (durable, distilled across runs)

- **Fix the taxonomy in Plan, not after.** Define the 8-12 themes up front and make every scan
  agent map each principle to a themeKey. Letting parallel agents invent their own taxonomies
  causes mismatches that have to be reconciled later (cost a remediation pass on the precursor run).
- **MECE angles, not just diverse ones.** Many sources re-reading the same few pages is not 100
  sources. The Plan phase must produce a MECE partition (mutually exclusive, collectively
  exhaustive) and hand each scanner a boundary brief stating what it owns and must not touch, so
  the swarm does not all find the same things. Differ by sub-question, stakeholder, source-type,
  geography, time, value-chain stage, and at least one contrarian/counter-evidence angle.
  (Enforced in the workflow + schema as of 2026-06-11.)
- **Tier honestly and flag the weak ones.** Always carry a "read with care" set: single-source
  forum stats, vendor reports, and any figure the primary source could not be confirmed for. Do
  not let a forum number get presented as canon.
- **Always grep-verify dashes after every render.** Render agents drift back to em dashes despite
  instructions; verify zero em/en dashes before returning. (Spaced hyphen only.)
- **Self-contained renders only.** No external assets, no web fonts - the reader opens the file
  offline. Confirmed: this is what the human actually wants to receive.
- **Answer-first wins.** The preferred consumption format is a top-down narrative and a ~20-slide
  deck (action-titled), not many pages. Lead with the governing thought.

---

## 2026-06-11 - seed (from the exec-ai-fitness precursor build)

The engine generalises a bespoke run that scanned ~100 sources on executive AI fitness into a
tiered principle set, a capability model, and a narrative, then rendered a readable HTML report
and (separately) a deck-style brief that the human preferred over long pages.

**What worked.**
- Parallel cluster scan -> tiered principles -> adversarial critique -> narrative produced a
  defensible, differentiated result that the human rated highly.
- An adversarial critique pass caught real defects (a taxonomy mismatch between two artefacts; two
  stats mis-tiered as canon that were actually forum/secondary). Critique earns its keep.
- Self-contained, tier-badged HTML was exactly the deliverable shape wanted.

**What to improve next run.**
- The swarm scan model (`haiku`) is unproven at the 300-1000 source scale - on the FIRST real run,
  spot-check that haiku scanners are finding genuine canon sources and writing real URLs; if canon
  discovery is thin, bump `scanModel` to `sonnet` for that run and log it.
- For technical / academic topics, add an explicit "peer-reviewed / primary-paper" angle and an
  "official statistics / regulator" angle so canon coverage does not depend on luck.
- Dedup quality depends on the theme taxonomy being clean - if a theme owner reports a very high
  count, it probably needs splitting; consider a second dedup pass on oversized themes.

**Proposed structural changes (human review).**
- Consider an optional adversarial "verify the top-N principles" mini-phase between Ingest and
  Narrative for high-stakes runs (refute each headline claim; drop or down-tier the ones that fail).
- Consider wiring the formal slide-types / SapphireOS render as a real `slides-formal` format once
  a deck render loop is proven here.
