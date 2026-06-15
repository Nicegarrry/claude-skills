# The human-facing HTML spec (Phase 2)

The HTML is the one artifact the **human** reads to approve the work. It is not the engineering spec and not the build plan — it's the ambition and shape, made scannable, with the decisions that need a verdict pulled to the surface.

## What "human-focused" means

- **Ambition first.** Top of the page: what we're building and *why it matters*, in plain language. A busy reader should get it in 20 seconds.
- **Workstreams/phases as the spine.** One scannable section per workstream — what it delivers, the high-level approach, rough sequence. Altitude, not task lists.
- **Decisions and open questions called out.** Anything that needs the user's verdict gets its own clearly-marked block (a tinted callout), phrased as a question with your recommendation. These are what the proofing pins land on.
- **No eng dump.** No file paths, no schemas, no task breakdowns — those live in `plan.md` (Phase 3). If you're tempted to paste code, it belongs in the plan, not here.

## Suggested structure

```
1. Title + one-line ambition
2. Why this / what great looks like        (2–4 sentences)
3. The approach at a glance                (a diagram or a short narrative)
4. Workstreams                             (one card/section each)
5. Key decisions — needs your verdict      (callout blocks, each a question + recommendation)
6. Open questions / unknowns               (from the Phase-1 stress-test)
7. Risks & what's explicitly out of scope
```

## Styling

- Clean, editorial, credible — invoke the user's `anti-ai-design` skill; avoid the generic-AI look.
- Self-contained single file (inline CSS); readable measure, real hierarchy, generous whitespace.
- Icons: Heroicons only, never Unicode glyphs as icons (per repo convention). Inline the SVG you need.
- Make decision/open-question blocks visually distinct so they're obvious pin targets.

## Wiring proofing-room

1. Save the page at `docs/specs/<date>-<topic>/spec.html`, where `<date>` is today's date as `YYYY-MM-DD` (resolve it in the main session and substitute it — don't write the literal `YYYY-MM-DD`). Keep `spec.html`, `spec.md`, and later `plan.md` together in this one folder so the human artifact and the buildable plan stay paired.
2. Copy `proofing-room.js` next to it, from wherever the `proofing-room` skill is installed:
   `cp "$(ls ~/.claude/skills/proofing-room/proofing-room.js ../proofing-room/proofing-room.js 2>/dev/null | head -1)" docs/specs/<date>-<topic>/`
   (tries the installed path and the sibling `proofing-room/` in this skills repo; copy it by hand if neither resolves).
3. Add once, just before `</body>`:
   ```html
   <script src="proofing-room.js"></script>
   ```
4. **Get it in front of the user — don't make them run commands.** Either open the file directly and hand them the proofing URL, or start a static server yourself and give them the link:
   - `file://…/spec.html#proof` (use `#proof`, not `?proof`, for `file://` — some browsers drop the query string), or
   - `python3 -m http.server` in that dir → `http://localhost:8000/spec.html?proof`.
5. Tell them what they can do: **+ Comment** to pin notes (especially on the decision/open-question blocks), **✎ Edit text** to rewrite copy in place, **Extract JSON** when done. Or they can just respond in chat — both are fine.

## Reconciling the feedback

When you get the exported `proofing-*.json` (or chat feedback):

1. Apply `edits` literally (approved copy changes).
2. Action each `comment` against its anchored block — interpret, implement, and note what you changed per comment `id`. Use `selector` first, fall back to `anchorText` + `tag`.
3. Answer every open question with the user's verdict folded in.
4. Re-render the HTML, confirm the changes, and ask if it's **agreed**. Loop until it is.

That "agreed" is the Iron Gate — Phase 3 starts only after it.

See the `proofing-room` skill for the full JSON contract and the agent-side apply steps.
