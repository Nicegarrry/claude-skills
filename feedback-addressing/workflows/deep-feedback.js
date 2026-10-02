export const meta = {
  name: 'deep-feedback',
  description: 'Multi-agent feedback-addressing over one or more commented .docx files: understand, cross-doc consistency, research and check, targeted writing in the owner voice, spirit review, tracked changes as the owner plus threaded Claude replies',
  whenToUse: 'Complex feedback rounds: several related commented .docx files, a call transcript or rules file, research-heavy or cross-document fixes (feedback-addressing skill, workflow mode)',
  phases: [
    { title: 'Understand', detail: 'one deep reader per document: every comment, its thread, the transcript' },
    { title: 'Consistency', detail: 'cross-document pass: terms, numbers, cross-references, round-wide asks' },
    { title: 'Plan', detail: 'buckets (incl. mandatory audits) and research questions per document' },
    { title: 'Research', detail: 'researchers then adversarial checkers, one retry' },
    { title: 'Write', detail: 'targeted change blocks plus one reply per comment' },
    { title: 'Check', detail: 'address-completeness and style gate, up to 2 rework rounds' },
    { title: 'Review', detail: 'spirit, voice and accuracy lenses, then targeted fixes' },
    { title: 'Apply', detail: 'tracked changes as the owner, threaded replies, verification' },
  ],
}

// args: {
//   run_id: "2026-10-03T1000", author: "Owner Name" (tracked-change author), reply_author: "Claude",
//   context: "one paragraph on what these documents are and who they are for",
//   transcript: "/abs/path" | null, rules_file: "/abs/path" | null (binding rules distilled from the reviewer),
//   style_guide: "/abs/path" | null, voice: "/abs/path" | null, ai_tells: "/abs/path" | null,
//   reference_folders: ["/abs/dir", ...] (downloaded sources to use first),
//   forbid: ["footnote"] (change types not allowed), mandatory_buckets: ["references-integrity", "tables-figures"],
//   units: [{ key: "u2", label: "Unit 2", doc: "/abs/in.docx", dir: "/abs/run/dir", notes: "document-specific rules" }]
// }
const A = args || {}
const UNITS = A.units || []
const AUTHOR = A.author || 'Document Owner'
const REPLY = A.reply_author || 'Claude'
const RUN = A.run_id || 'run'
const SKILL = '/Users/sa/.claude/skills/feedback-addressing'
const VOICE = A.voice || (SKILL + '/local/reviewer-voice.md')
const STYLE_LINE = [A.style_guide && `Owner prose style guide: "${A.style_guide}".`, `Owner voice notes: "${VOICE}".`, A.ai_tells && `AI tells previously caught in the owner's work: "${A.ai_tells}".`].filter(Boolean).join(' ')
const SOURCES = [A.transcript && `The reviewer call transcript is at "${A.transcript}"; read it in full, it explains the intent behind many comments.`, A.rules_file && `BINDING rules distilled from the reviewer: "${A.rules_file}"; read it first and apply it.`].filter(Boolean).join(' ') || 'No transcript or rules file was supplied.'
const REFS = (A.reference_folders || []).length ? `Downloaded sources to check first: ${A.reference_folders.map(x => `"${x}"`).join(', ')}.` : ''
const FORBID = (A.forbid || []).length ? `Forbidden change types: ${A.forbid.join(', ')}.` : ''
const MANDATORY = ['spellcheck-grammar-style'].concat(A.mandatory_buckets || [])
const SHARED = UNITS.length ? `${UNITS[0].dir}/../consistency-${RUN}.md` : ''

const CTX = (u) => `You are part of a multi-agent run addressing reviewer feedback. ${A.context || ''} Document owner: ${AUTHOR}. Document: ${u.label}, "${u.doc}". Run folder (all your artefacts go here): "${u.dir}".${u.notes ? ' Notes for this document: ' + u.notes : ''}
Method: follow the feedback-addressing skill at ${SKILL}/SKILL.md (read it; its rules A to L bind you). ${STYLE_LINE} ${SOURCES} ${REFS} ${FORBID} Cross-document consistency file (once written): "${SHARED}".
Hard rules: tracked changes are authored "${AUTHOR}"; the reviewer's existing tracked changes and comments are never accepted, rejected, removed or overwritten (do not anchor before_text across their insertions or deletions; if their edit is wrong, say so in a reply); never remove any comment (no remove_comment rows); every comment gets exactly one reply_comment (reply_author: ${REPLY}) saying what was done and why, or the decision the owner must make; changes are targeted (word, sentence or paragraph), never wholesale rewrites; match the document's language variety (Australian English unless clearly otherwise); no em or en dashes; no AI tells.`

const COUNT = { type: 'object', properties: { unit: { type: 'string' }, items: { type: 'number' }, notes: { type: 'string' } }, required: ['unit', 'items'] }
const PLAN = {
  type: 'object',
  properties: {
    buckets: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, feedback_ids: { type: 'array', items: { type: 'string' } }, thematic: { type: 'boolean' } }, required: ['id', 'feedback_ids'] } },
    research: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, question: { type: 'string' }, feedback_ids: { type: 'array', items: { type: 'string' } } }, required: ['id', 'question'] } },
  },
  required: ['buckets', 'research'],
}
const VERDICT = { type: 'object', properties: { id: { type: 'string' }, ok: { type: 'boolean' }, issues: { type: 'string' } }, required: ['id', 'ok'] }
const REWORK = { type: 'object', properties: { rework: { type: 'array', items: { type: 'object', properties: { bucket: { type: 'string' }, feedback_id: { type: 'string' }, reason: { type: 'string' } }, required: ['bucket', 'reason'] } } }, required: ['rework'] }
const ISSUES = { type: 'object', properties: { lens: { type: 'string' }, issues: { type: 'array', items: { type: 'object', properties: { feedback_id: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' } }, required: ['problem', 'fix'] } } }, required: ['lens', 'issues'] }
const RESULT = { type: 'object', properties: { unit: { type: 'string' }, out_doc: { type: 'string' }, applied: { type: 'number' }, skipped: { type: 'number' }, comments: { type: 'number' }, replied: { type: 'number' }, reviewer_revisions_preserved: { type: 'boolean' }, escalations: { type: 'array', items: { type: 'string' } }, summary_file: { type: 'string' } }, required: ['unit', 'out_doc', 'comments', 'replied'] }

if (!UNITS.length) { log('No documents passed in args.units; nothing to do.'); return { error: 'no units' } }

// ---------------------------------------------------------------- Understand
phase('Understand')
const understood = await parallel(UNITS.map(u => () => agent(`${CTX(u)}
Task: deep understanding of every comment (skill steps 1 to 4).
1. Create the run folder, then run: python3 ${SKILL}/helpers/extract_feedback.py "${u.doc}" > "${u.dir}/01-feedback.json" and python3 ${SKILL}/helpers/extract_inline_notes.py "${u.doc}" --owner "${AUTHOR}" > "${u.dir}/01-inline-notes.json". Reviewers often write feedback INLINE (tracked insertions such as "(what does this stand for?)", "Source: ???", "(needs reference)", and highlighted text) rather than as Word comments. Classify every inline row: a feedback note (becomes a feedback item with id N###, anchored by paragraph_id and its note text) or an ordinary reviewer edit (leave alone). Duplicate notes on the same issue can share one item.
2. Read the WHOLE document (python-docx or zipfile) to understand its argument, structure and voice. Also count the existing tracked revisions by author (w:ins, w:del) and record them in ${u.dir}/00-brief.md as the baseline that must survive.
3. For every comment (reviewer and owner), read its thread, the anchor paragraph plus one before and one after, and related transcript or rules passages. Work out the SPIRIT of the comment, not just its letter: the distinct asks, what a good fix looks like, what would be over-reach, whether it needs new evidence, whether the reviewer may be mistaken, and whether it touches the other documents in this run.
4. Treat inline notes exactly like comments from here on. Write ${u.dir}/00-brief.md (skill step 1), ${u.dir}/02-internal-table.md (skill steps 3 and 4: all 11 columns) and ${u.dir}/02-intent.md: per feedback_id, comment_wid (or, for inline notes, paragraph_id and the exact note text), author, distinct asks, spirit in one line, transcript or rules evidence (quote), cross-document flag.
Return the document key, the number of items and one line of notes.`, { label: `understand:${u.key}`, phase: 'Understand', schema: COUNT, effort: 'high' })))
log(`Understood: ${understood.filter(Boolean).map(r => `${r.unit} ${r.items}`).join(', ')}`)

// --------------------------------------------------------------- Consistency
phase('Consistency')
const docList = UNITS.map(u => `- ${u.label}: doc "${u.doc}", run folder "${u.dir}"`).join('\n')
await agent(`You are the cross-document consistency reviewer for a feedback round on several related documents (owner ${AUTHOR}). ${A.context || ''}
${docList}
${SOURCES}
Read each document's 02-intent.md and 02-internal-table.md and skim each document. Find:
- comments, transcript or rules points whose fix should be applied consistently across documents (terminology, definitions, notation, number formats, citation and reference style, table and figure naming and source conventions, activity formatting, cross-references between documents);
- facts, figures or reference details (same source cited with different years or editions) that conflict between documents;
- fixes planned in one document that would contradict another.
Write "${SHARED}" with a numbered list X01, X02 ... each naming the documents affected, the rule to apply, and exact locations. Append those rows to each affected document's 02-internal-table.md and 02-intent.md (feedback_id X01 etc., source cross-document consistency, no comment_wid). Return a one-line summary.`, { label: 'consistency', phase: 'Consistency', effort: 'high' })

// ----------------------------------------------- per-document pipeline onward
const results = await pipeline(UNITS,
  // Plan
  (prev, u) => agent(`${CTX(u)}
Read ${u.dir}/02-internal-table.md, 02-intent.md and the consistency file. Do skill step 5: group items into buckets (always include ${MANDATORY.join(', ')}, even if no comment asks; a mandatory bucket audits the WHOLE document for its theme and adds its own rows S01, S02 ...; give each thematic item its own bucket), write ${u.dir}/02a-grouping.md, and write a brief per bucket to ${u.dir}/briefs/<bucket>.md with the rows, plan, full anchor paragraph plus one before and one after, intent notes, and the style guard. List research questions for every knowledge_gap item and every reference that needs verifying or updating (rule K), each answerable from public or downloaded sources. Return buckets and research questions.`, { label: `plan:${u.key}`, phase: 'Plan', schema: PLAN, effort: 'high' }),

  // Research then adversarial check (one retry)
  async (plan, u) => {
    const rs = (plan && plan.research) || []
    await parallel(rs.map(r => async () => {
      const brief = `${CTX(u)}
Research question ${r.id} (for ${(r.feedback_ids || []).join(', ')}): ${r.question}
Use web search and open primary sources (see ${SKILL}/local/sources.md and any downloaded sources listed above). For references verify the exact edition, year, authors, title, and that the URL resolves (fetch it); prefer the latest edition of recurring reports and update figures that changed. Optionally cross-check with Codex: run ~/.local/bin/codex exec -m gpt-6-astra -c 'web_search="live"' --skip-git-repo-check -s read-only "<question>" via Bash with the sandbox disabled. Never invent a figure or reference. Write ${u.dir}/03-research/${r.id}.md: the answer, each claim with number, vintage, reference with URL, confidence, and what the document should say in one or two sentences.`
      await agent(brief, { label: `research:${u.key}:${r.id}`, phase: 'Research' })
      let v = await agent(`${CTX(u)}
Adversarially check ${u.dir}/03-research/${r.id}.md against its question: "${r.question}". Open the cited sources yourself and try to refute each claim (wrong number, wrong year or edition, misattribution, dead link, overreach, secondary used when a primary exists). Default to ok=false if a load-bearing claim cannot be verified. Append your verdict under "## Check".`, { label: `check-research:${u.key}:${r.id}`, phase: 'Research', schema: VERDICT, effort: 'high' })
      if (v && !v.ok) {
        await agent(`${brief}\nA checker rejected the first pass: ${v.issues}. Fix every issue and rewrite the file.`, { label: `research-retry:${u.key}:${r.id}`, phase: 'Research' })
        v = await agent(`${CTX(u)}\nRe-check ${u.dir}/03-research/${r.id}.md as before; ok=false if anything load-bearing is still unverified, and say so in the file so writers escalate instead of asserting.`, { label: `recheck:${u.key}:${r.id}`, phase: 'Research', schema: VERDICT, effort: 'high' })
      }
      return v
    }))
    return plan
  },

  // Write per bucket, then check gate with up to 2 rework rounds
  async (plan, u) => {
    const buckets = (plan && plan.buckets) || []
    const writeBucket = (b, extra) => agent(`${CTX(u)}
You are the writer for bucket "${b.id}" (items ${b.feedback_ids.join(', ')}). Read ${u.dir}/briefs/${b.id}.md, ${u.dir}/02-intent.md, the consistency file, any ${u.dir}/03-research/*.md for your items (use only claims whose "## Check" passed), and the style guide.
Write targeted change blocks (skill step 7 format, target_locator = paragraph paraId) to ${u.dir}/05-proposed/${b.id}.md (overwrite). Principles: meet the spirit of each comment with the smallest change that fully satisfies it; match the surrounding sentences' words and register; the owner's voice per the style guide; no new claims without a checked source.
For EVERY comment in your bucket that has a comment_wid, add exactly one reply_comment block (comment_id = that wid, reply_author: ${REPLY}). Reply text: one to three plain sentences to the owner: what changed and where, or why no change, or the decision needed. Include the owner's own comments. For EVERY inline-note item (N###, no comment_wid), add exactly one add_comment block instead (target_locator = its paragraph_id, anchor_text = the exact note text, comment_author: ${REPLY}, comment_text as for replies). Never delete or edit the reviewer's note text itself; fix the surrounding content and say in the comment that the note can be removed. No em dashes, no AI tells.${extra ? '\nRework required: ' + extra : ''}
Return a one-line summary.`, { label: `write:${u.key}:${b.id}`, phase: 'Write' })
    await parallel(buckets.map(b => () => writeBucket(b)))
    for (let round = 1; round <= 2; round++) {
      const gate = await agent(`${CTX(u)}
Run the skill's step 8 check gate over every file in ${u.dir}/05-proposed/ against ${u.dir}/02-intent.md and 02-internal-table.md: literal correctness (before_text exists verbatim in the target paragraph and does not span the reviewer's tracked insertions or deletions), address-completeness (rule D, every distinct ask), inferred-intent and style guard (rule L plus the style guide's banned list), research claims used only if checked, no remove_comment rows, no forbidden change types, exactly one reply_comment per comment_wid and exactly one add_comment per inline-note item across all files (list any missing), and no change that edits or deletes the reviewer's own inserted notes. Write ${u.dir}/06-check-results-r${round}.md. Return the rework list (empty if all pass).`, { label: `gate:${u.key}:r${round}`, phase: 'Check', schema: REWORK, effort: 'high' })
      const rw = (gate && gate.rework) || []
      if (!rw.length) break
      log(`${u.key}: gate round ${round} sent ${rw.length} items back`)
      const byB = {}
      rw.forEach(x => { (byB[x.bucket] = byB[x.bucket] || []).push(`${x.feedback_id || ''}: ${x.reason}`) })
      await parallel(buckets.filter(b => byB[b.id]).map(b => () => writeBucket(b, byB[b.id].join(' | '))))
    }
    return plan
  },

  // Review fleet: three lenses, then one targeted fixer
  async (plan, u) => {
    const lenses = [
      ['spirit', 'For each comment, does the proposed change meet the SPIRIT of what the reviewer (and the transcript or rules file) wanted, not just the letter? Flag literal-but-hollow fixes, over-reach beyond the ask, and asks left unmet. Check each reply is accurate about what changed.'],
      ['voice', 'Read every after_text in the context of its paragraph. Does it sound like the owner (style guide, voice notes) and like the surrounding text? Flag any AI feel: colon reveals, "not X but Y" pivots, tricolons, summary closers, hedges, intensifiers, abstract-noun sentences, dashes, wrong spelling variety. Flag any change bigger than it needs to be.'],
      ['accuracy', 'Check every factual claim, number, citation and reference entry introduced by the changes against the research files and the sources themselves, and against the consistency file. Flag anything unsupported, any reference with a wrong year or edition, and any citation missing from the reference list.'],
    ]
    const found = await parallel(lenses.map(([lens, ask]) => () => agent(`${CTX(u)}
You are a reviewer on the "${lens}" lens. Inputs: the document, ${u.dir}/02-intent.md, ${u.dir}/05-proposed/*.md, ${u.dir}/03-research/, the consistency file, the style guide. ${ask}
Return issues (feedback_id, problem, concrete fix).`, { label: `review-${lens}:${u.key}`, phase: 'Review', schema: ISSUES, effort: 'high' })))
    const issues = found.filter(Boolean).flatMap(f => f.issues.map(i => ({ ...i, lens: f.lens })))
    log(`${u.key}: review fleet raised ${issues.length} issues`)
    if (issues.length) {
      await agent(`${CTX(u)}
Apply these review findings by editing the change blocks in ${u.dir}/05-proposed/*.md directly. Keep edits targeted; if a finding is wrong, leave the block and note why. Findings:
${JSON.stringify(issues, null, 1)}
Write ${u.dir}/06d-review-actions.md listing each finding and what you did. Return a one-line summary.`, { label: `review-fix:${u.key}`, phase: 'Review', effort: 'high' })
    }
    return plan
  },

  // Apply and verify (single writer per document)
  (plan, u) => agent(`${CTX(u)}
You are the single writer to the document (skill steps 9 to 12).
1. Concatenate ${u.dir}/05-proposed/*.md into ${u.dir}/06c-aggregated-changes.md, resolving overlaps per skill step 9 (log to 06b-overlap-reconciliation.md). Ensure no remove_comment rows, no forbidden change types, exactly one reply_comment per comment and one add_comment per inline-note item.
2. Run: python3 ${SKILL}/helpers/apply_changes_docx.py "${u.doc}" "${u.dir}/06c-aggregated-changes.md" --out "${u.dir}/<input stem>-tracked-${RUN}.docx" --author "${AUTHOR}"
3. Verify: re-run extract_feedback.py on the output; every original comment must have a ${REPLY} reply in its comment_thread and every inline-note item a ${REPLY} comment; count w:ins and w:del by author in input and output and confirm every pre-existing revision survives (compare with the baseline in 00-brief.md); confirm python-docx opens it. If a change was skipped, find out why, fix the block if it is a locator or text-match problem, and re-apply from the ORIGINAL input (never stack runs).
4. Fill the final 02-internal-table.md (skill step 10) and write ${u.dir}/09-summary.md using the skill's summary template, listing escalations and decisions the owner needs to make.
Return the result fields.`, { label: `apply:${u.key}`, phase: 'Apply', schema: RESULT, effort: 'high' }),
)

return { run: RUN, results }
