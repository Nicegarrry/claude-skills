export const meta = {
  name: '100-sources',
  description: 'Topic-agnostic research engine: decompose a topic into many search angles, fan out a swarm of small-model agents to scan 100 to ~1000 real sources, ingest everything into a large tiered principle set (canon/secondary/forum), whittle the principles into a top-down answer-first narrative, render it (markdown + readable HTML + a ~20-slide deck), and self-improve by appending what worked / what to fix to a LEARNINGS log the next run reads. Generalised from the deep-scan -> principles -> narrative pattern. Pass the topic via args.',
  whenToUse: 'Produce a deep, broadly-sourced, tiered research brief + narrative + deck on any topic.',
  phases: [
    { title: 'Plan' },
    { title: 'Scan', model: 'haiku' },
    { title: 'Ingest', model: 'sonnet' },
    { title: 'Narrative', model: 'opus' },
    { title: 'Render', model: 'sonnet' },
    { title: 'Learn', model: 'opus' },
  ],
};

// ---------------------------------------------------------------------------
// THE 100-SOURCES RESEARCH ENGINE.
// Plan -> Scan (swarm) -> Ingest (dedup into principles) -> Narrative (whittle
// top-down) -> Render (md/html/slides) -> Learn (self-improve the skill).
// No-fs orchestrator: ALL I/O happens inside agents. The orchestrator only fans
// out, gathers JSON, and logs. Determinism: no Date.now/Math.random here; the
// Learn agent stamps the date by running `date` in bash.
// ---------------------------------------------------------------------------
const ROOT = '/Users/sa/qubit';
const SKILL = `${ROOT}/skills/100-sources`;
const HARD = 'opus';      // narrative synthesis, self-learning review
const BUILD = 'sonnet';   // plan, ingest/dedup, render
const LEARNINGS = `${SKILL}/LEARNINGS.md`;
const STYLE = `${SKILL}/templates/house-style.css`;

// --- args: { topic, slug?, out?, sourceTarget?, sourcesPerAngle?, scanModel?, formats?, narrativeHint?, slideTarget? }
const input = typeof args === 'string'
  ? (() => { try { return JSON.parse(args); } catch { return { topic: args }; } })()
  : (args || {});
const TOPIC = input.topic;
if (!TOPIC) throw new Error('100-sources needs a topic. Run: Workflow({ name: "100-sources", args: { topic: "..." } })');

const SLUG = input.slug || TOPIC.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48);
// Default home is the qubit (PM) wiki: structured synthesis -> _wiki/research,
// raw evidence -> _sources/research (append-only). Override with args.out / args.sourcesOut.
const PM = `${ROOT}/PM`;
const OUT = input.out || `${PM}/_wiki/research/${SLUG}`;
const SRC = input.sourcesOut || `${PM}/_sources/research/${SLUG}`;
const SOURCE_TARGET = Math.max(100, Math.min(1000, input.sourceTarget || 300));
const SOURCES_PER_ANGLE = Math.max(6, Math.min(20, input.sourcesPerAngle || 12));
const ANGLE_COUNT = Math.max(8, Math.min(100, Math.ceil(SOURCE_TARGET / SOURCES_PER_ANGLE)));
const SCAN_MODEL = input.scanModel || 'haiku';   // the "massive swarm of small models"
const FORMATS = input.formats || ['markdown', 'html', 'slides'];
const NARRATIVE_HINT = input.narrativeHint || '';
const SLIDE_TARGET = input.slideTarget || 20;

const CTX = [
  `100-SOURCES RESEARCH ENGINE - context for every agent.`,
  `Topic: "${TOPIC}".`,
  `You are part of a topic-agnostic research factory: scan a large number of REAL sources, distil tiered`,
  `principles, and whittle them into a top-down narrative. Non-negotiable quality bars:`,
  `- REAL sources only. Never invent a source, a statistic, a quote, a finding, or a URL.`,
  `- TIER every claim: canon (named primary / official report / peer-reviewed), secondary (reputable`,
  `  interpreter or synthesis), forum (blog / coaching / vendor / forum - lowest confidence). Flag weak-tier`,
  `  claims honestly; never launder a forum stat as canon.`,
  `- Market stats are EVIDENCE attributed to their source, not the author's own results.`,
  `- No em dashes or en dashes anywhere (use a spaced hyphen "-"). Concrete, no platitudes.`,
].join('\n');

const PLAN_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['themes', 'angles', 'spineHint', 'appliedLearnings'],
  properties: {
    themes: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['key', 'label'],
      properties: { key: { type: 'string' }, label: { type: 'string' } } } },
    angles: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['key', 'angle', 'queries', 'seek', 'boundary'],
      properties: { key: { type: 'string' }, angle: { type: 'string' }, queries: { type: 'array', items: { type: 'string' } }, seek: { type: 'string' }, boundary: { type: 'string' } } } },
    spineHint: { type: 'string' }, appliedLearnings: { type: 'array', items: { type: 'string' } },
  },
};
const SCAN_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['angleKey', 'sourcesRead', 'principles', 'citations', 'notePath'],
  properties: {
    angleKey: { type: 'string' }, sourcesRead: { type: 'number' }, notePath: { type: 'string' },
    principles: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['statement', 'themeKey', 'tier', 'source'],
      properties: { statement: { type: 'string' }, themeKey: { type: 'string' }, tier: { enum: ['canon', 'secondary', 'forum'] }, source: { type: 'string' }, evidence: { type: 'string' } } } },
    citations: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['title', 'url'], properties: { title: { type: 'string' }, url: { type: 'string' } } } },
  },
};
const OWNER_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['themeKey', 'label', 'count', 'top'],
  properties: { themeKey: { type: 'string' }, label: { type: 'string' }, count: { type: 'number' },
    top: { type: 'array', items: { type: 'string' } }, note: { type: 'string' } },
};
const NARR_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['governingThought', 'pillars'],
  properties: {
    governingThought: { type: 'string' },
    pillars: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['title', 'message'],
      properties: { title: { type: 'string' }, message: { type: 'string' } } } },
    note: { type: 'string' },
  },
};
const OK = { type: 'object', additionalProperties: false, required: ['ok'], properties: { ok: { type: 'boolean' }, format: { type: 'string' }, path: { type: 'string' }, note: { type: 'string' } } };

// ===========================================================================
// Phase 1 - PLAN. Decompose the topic; read accumulated LEARNINGS and apply them.
// ===========================================================================
phase('Plan');
log(`Topic: "${TOPIC}" | target ~${SOURCE_TARGET} sources across ${ANGLE_COUNT} angles | out: ${OUT}`);
const plan = await agent([
  CTX, ``,
  `You are the LEAD RESEARCHER planning a ${SOURCE_TARGET}-source scan of: "${TOPIC}".`,
  NARRATIVE_HINT ? `Steer: ${NARRATIVE_HINT}` : ``,
  ``,
  `FIRST: read ${LEARNINGS} (the engine's self-learning log) and APPLY its accumulated guidance to this plan.`,
  `Then run: mkdir -p ${SRC} && mkdir -p ${OUT}`,
  ``,
  `Produce:`,
  `1. THEMES: 8-12 mutually-distinct themes the principles will be organised under (key + label).`,
  `2. ANGLES: exactly ${ANGLE_COUNT} search angles forming a MECE decomposition of the topic - Mutually`,
  `   Exclusive (NO two angles overlap in what they search for) and Collectively Exhaustive (together they`,
  `   cover the whole topic, no gap). Partition along clear axes (sub-question, stakeholder, source-type,`,
  `   geography, time, value-chain stage, and at least one contrarian/counter-evidence angle). For EACH`,
  `   angle give: a short key, the angle, 2-3 concrete search queries, what to seek, and a BOUNDARY - one`,
  `   line stating what this angle OWNS and what it must NOT cover because a sibling owns it. The boundary`,
  `   is the MECE brief each swarm agent gets so they do not all find the same sources.`,
  `   ${ANGLE_COUNT} angles x ~${SOURCES_PER_ANGLE} sources each = ~${SOURCE_TARGET} sources.`,
  `3. spineHint: a first guess at the top-line answer + the candidate pillars (to be tested by the research).`,
  `4. appliedLearnings: which LEARNINGS entries you applied (empty list if the log is empty).`,
].join('\n'), { label: 'plan', phase: 'Plan', model: BUILD, schema: PLAN_SCHEMA });

const themeList = plan.themes.map((t) => `${t.key}: ${t.label}`).join(' | ');
log(`Plan: ${plan.themes.length} themes, ${plan.angles.length} angles. Applied ${plan.appliedLearnings.length} prior learnings.`);

// ===========================================================================
// Phase 2 - SCAN. The swarm: one small-model agent per angle.
// ===========================================================================
phase('Scan');
const scans = (await parallel(plan.angles.map((a) => () =>
  agent([
    CTX, ``,
    `You are ONE scanner in a MECE research swarm. Your angle: "${a.angle}" (key: ${a.key}).`,
    `Search queries to start from: ${a.queries.join(' | ')}. Seek: ${a.seek}`,
    `YOUR BOUNDARY (stay in your lane): ${a.boundary}`,
    `MECE rule: cover ONLY your slice. Do not chase material a sibling angle owns - if you stumble on it,`,
    `note it in one line and move on. This is what stops the swarm all finding the same sources.`,
    ``,
    `METHOD (Bash + Read + web tools - Firecrawl CLI / WebSearch / WebFetch):`,
    `1. Find and READ ${SOURCES_PER_ANGLE} REAL, authoritative, recent sources for this angle. Real URLs only.`,
    `2. Save key scrapes to ${SRC}/${a.key}/ and write a short tiered note to ${SRC}/${a.key}.md.`,
    `3. Extract crisp, prescriptive PRINCIPLES (findings stated as durable claims). For EACH: a themeKey from`,
    `   this list [${themeList}] (use the closest; if none fit, use "other"), a tier (canon/secondary/forum),`,
    `   the source, and a one-line evidence/quote. No platitudes; every principle ties to a real source.`,
    `Return angleKey, sourcesRead (how many you actually read), the principles, citations, and notePath.`,
  ].join('\n'), { label: `scan:${a.key}`, phase: 'Scan', model: SCAN_MODEL, schema: SCAN_SCHEMA })
))).filter(Boolean);

const sourcesAchieved = scans.reduce((n, s) => n + (s.sourcesRead || 0), 0);
const rawPrincipleCount = scans.reduce((n, s) => n + (s.principles ? s.principles.length : 0), 0);
log(`Scan: ${scans.length}/${plan.angles.length} angles returned, ~${sourcesAchieved} sources read, ${rawPrincipleCount} candidate principles.`);

// Group candidate principles by theme (plain code - no agent needed).
const byTheme = {};
for (const t of plan.themes) byTheme[t.key] = { label: t.label, items: [] };
byTheme.other = { label: 'Other / uncategorised', items: [] };
for (const s of scans) for (const p of (s.principles || [])) {
  const k = byTheme[p.themeKey] ? p.themeKey : 'other';
  byTheme[k].items.push({ ...p, angle: s.angleKey });
}

// ===========================================================================
// Phase 3 - INGEST. One owner per theme dedups+merges into a clean principle set.
// ===========================================================================
phase('Ingest');
const owners = (await parallel(Object.entries(byTheme).filter(([, v]) => v.items.length).map(([key, v]) => () =>
  agent([
    CTX, ``,
    `You OWN the theme "${v.label}" (key: ${key}). Below are ${v.items.length} candidate principles scanned`,
    `from many sources (with duplicates and overlaps). DEDUPE and MERGE them into a clean, numbered set of`,
    `distinct principles for this theme. For each: keep the sharpest statement, the STRONGEST-tier source`,
    `(prefer canon), note corroborating sources, and keep the tier honest. Drop platitudes and unsourced claims.`,
    ``,
    `WRITE ${OUT}/principles/${key}.md (mkdir -p ${OUT}/principles first): a numbered list, each principle with`,
    `its tier tag and source. Return themeKey, label, the final count, and up to 5 "top" principle statements.`,
    ``,
    `CANDIDATES (JSON):`,
    JSON.stringify(v.items).slice(0, 60000),
  ].join('\n'), { label: `ingest:${key}`, phase: 'Ingest', model: BUILD, schema: OWNER_SCHEMA })
))).filter(Boolean);

// Compile the per-theme files into one principles.md + a compact digest for the narrative.
const compile = await agent([
  CTX, ``,
  `Compile the per-theme principle files in ${OUT}/principles/ into ONE canonical document.`,
  `Run: ls ${OUT}/principles/ and Read each .md. Then WRITE ${OUT}/principles.md: a short intro, then the`,
  `themes in a sensible order, principles renumbered globally (P1..), each keeping its tier tag + source.`,
  `Also WRITE ${OUT}/principles.json (a machine-readable array of {id, theme, statement, tier, source}).`,
  `Return ok + note with the total principle count.`,
].join('\n'), { label: 'ingest:compile', phase: 'Ingest', model: BUILD, schema: OK });
log(`Ingest: ${owners.length} themes deduped; ${compile.note || 'principles compiled'}.`);

// ===========================================================================
// Phase 4 - NARRATIVE. Whittle the principle set into a top-down, answer-first story.
// ===========================================================================
phase('Narrative');
const narrative = await agent([
  CTX, ``,
  `WHITTLE the full principle set into a TOP-DOWN, answer-first narrative. Read ${OUT}/principles.md first.`,
  NARRATIVE_HINT ? `Steer: ${NARRATIVE_HINT}. ` : ``,
  `Provisional spine from planning (test it, do not assume it): ${plan.spineHint}`,
  ``,
  `Build a Minto-style pyramid: ONE governing thought (the single-sentence answer to "${TOPIC}"), then 3-6`,
  `PILLARS (each a full-sentence message), and under each pillar the supporting points, every point grounded`,
  `in specific principles (cite Pn / source / tier). End with the honest "read with care" caveats (the`,
  `weak-tier or contested claims). Lead with the answer; the research supports it, it does not meander to it.`,
  ``,
  `WRITE ${OUT}/narrative.md (the full top-down narrative: governing thought, an executive summary, each`,
  `pillar with its supporting points + citations, and the caveats). ALSO write ${OUT}/index.md - a short`,
  `wiki front door for this research: the topic, the governing thought, links to principles.md, narrative.md,`,
  `report.html and deck.html, a pointer to the raw evidence dir ${SRC}, and a one-line scope note.`,
  `Return the governingThought and the pillars (title + message) so the render phase can build from them.`,
].join('\n'), { label: 'narrative', phase: 'Narrative', model: HARD, schema: NARR_SCHEMA });
log(`Narrative: "${narrative.governingThought}" with ${narrative.pillars.length} pillars.`);

// ===========================================================================
// Phase 5 - RENDER. markdown is done; render HTML and/or a ~20-slide deck.
// ===========================================================================
phase('Render');
const renderThunks = [];
if (FORMATS.includes('html')) renderThunks.push(() => agent([
  CTX, ``,
  `Render the research as ONE polished, SELF-CONTAINED HTML document (inline CSS only, no external assets,`,
  `renders offline). Read ${OUT}/narrative.md and ${OUT}/principles.md. Embed the stylesheet at ${STYLE}`,
  `verbatim inside a <style> tag (read it).`,
  `STRUCTURE: a <header class="doc"> (kicker "Research / 100-sources", h1 = a title for "${TOPIC}", a .sub =`,
  `the governing thought, a .meta line with pills: "~${sourcesAchieved} sources", "${owners.length} themes",`,
  `"Tiered: canon / secondary / forum"); then <main> with a .lead headline para and one <h2> section per`,
  `pillar, each carrying its key findings with attributed, tier-tagged stats (wrap numbers in`,
  `<span class="stat">, tiers in <span class="tier canon|secondary|forum">), and a "So what" line; then a`,
  `"Read with care" .callout.warn listing the weak-tier claims; then a <footer class="doc"> with the source`,
  `note. NO em dashes or en dashes. Open with <!doctype html>.`,
  `WRITE ${OUT}/report.html. Verify zero em/en dashes by grep before returning. Return ok + format "html" + path.`,
].join('\n'), { label: 'render:html', phase: 'Render', model: BUILD, schema: OK }));

if (FORMATS.includes('slides')) renderThunks.push(() => agent([
  CTX, ``,
  `Render the research as a SELF-CONTAINED HTML DECK of about ${SLIDE_TARGET} slides (target ${SLIDE_TARGET - 2} to ${SLIDE_TARGET + 2}).`,
  `Read ${OUT}/narrative.md and ${OUT}/principles.md. Embed the stylesheet at ${STYLE} verbatim, and use its`,
  `.deck / .slide classes (each slide a 1280x720 .slide section; simple arrow-key + scroll navigation via a`,
  `small inline <script>; a slide counter).`,
  `DECK ARC (answer-first, ~${SLIDE_TARGET} slides): cover (title + governing thought) -> an executive-summary`,
  `slide -> for EACH pillar a divider slide then 1-3 content slides (the message as the slide's action title,`,
  `3-5 evidence bullets with tier-tagged stats) -> a "read with care" slide -> a sources/method close.`,
  `Every slide has an ACTION-TITLE (a full-sentence conclusion) and, where it carries a stat, a source line.`,
  `Readable and uncluttered - this is the "20 slides not many pages" view. NO em dashes or en dashes.`,
  `WRITE ${OUT}/deck.html. Verify zero em/en dashes by grep. Return ok + format "slides" + path.`,
].join('\n'), { label: 'render:slides', phase: 'Render', model: BUILD, schema: OK }));

const renders = renderThunks.length ? (await parallel(renderThunks)).filter(Boolean) : [];
log(`Render: ${renders.map((r) => r.format).join(', ') || 'markdown only'}.`);

// ===========================================================================
// Phase 6 - LEARN. Self-review the run and append improvements to LEARNINGS.md.
// ===========================================================================
phase('Learn');
const learn = await agent([
  CTX, ``,
  `You are the engine's SELF-LEARNING reviewer. Critically review THIS run and append a dated entry to the`,
  `engine's learning log so the NEXT run is better.`,
  ``,
  `RUN STATS: topic "${TOPIC}"; target ${SOURCE_TARGET} sources, achieved ~${sourcesAchieved}; ${plan.angles.length}`,
  `angles planned, ${scans.length} scans returned; ${rawPrincipleCount} candidate -> ${owners.length} themes deduped;`,
  `${narrative.pillars.length} pillars; formats: ${renders.map((r) => r.format).concat(['markdown']).join(', ')}.`,
  `Read ${OUT}/narrative.md and skim ${OUT}/principles.md to judge quality. Read the existing ${LEARNINGS}.`,
  ``,
  `Then APPEND to ${LEARNINGS} (do not overwrite; stamp the date by running: date +%F) a new "## <date> - ${SLUG}"`,
  `section with: (a) what WORKED, (b) what UNDERPERFORMED (coverage gaps, redundant angles, weak dedup, thin`,
  `pillars, render issues), (c) 3-6 CONCRETE TACTICAL IMPROVEMENTS phrased as guidance the Plan phase can apply`,
  `next run (e.g. "for technical topics, add an academic-paper angle and bump scanModel to sonnet"), and (d)`,
  `under a "Proposed structural changes (human review)" subhead, any CODE/CONFIG changes to the workflow that`,
  `need a human (e.g. default knob changes, a new phase). Keep it tight and actionable. No em dashes.`,
  `Return ok + a one-line note of the single highest-value improvement you logged.`,
].join('\n'), { label: 'learn', phase: 'Learn', model: HARD, schema: OK });

return {
  topic: TOPIC,
  wiki: OUT,            // structured synthesis (qubit wiki)
  rawSources: SRC,     // raw evidence (_sources, append-only)
  sourcesTarget: SOURCE_TARGET,
  sourcesAchieved,
  angles: plan.angles.length,
  scansReturned: scans.length,
  candidatePrinciples: rawPrincipleCount,
  themes: owners.length,
  governingThought: narrative.governingThought,
  pillars: narrative.pillars.map((p) => p.title),
  artefacts: {
    index: `${OUT}/index.md`,
    narrative: `${OUT}/narrative.md`,
    principles: `${OUT}/principles.md`,
    renders: renders.map((r) => ({ format: r.format, path: r.path })),
  },
  learned: learn.note || 'appended to LEARNINGS.md',
};
