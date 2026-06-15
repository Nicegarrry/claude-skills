# Proofing Room

A self-contained, drop-in wrapper that turns **any** HTML page into a review
surface. Reviewers pin comments to elements and edit copy in place, then export
an **anchored JSON** an agent (or you) can act on. No backend, no build step —
one vanilla-JS file, state stored in `localStorage`.

It's the review half of a tight loop: an agent generates HTML → a human marks it
up in proofing mode → exports JSON → the agent applies the feedback.

![Proofing mode: thick border, badge, and a docked panel for comments + edits]

## Quick start

1. Copy `proofing-room.js` next to the page you want to review.
2. Add one tag before `</body>`:
   ```html
   <script src="proofing-room.js"></script>
   ```
3. Open the page with **`?proof`** on the end of the URL:
   ```
   mypage.html?proof
   ```

That's it. Without the flag the page is completely normal — the wrapper stays
dormant, so you can ship the tag to production and only reviewers who know the
flag see the tool.

> Opening a local file directly (`file://`)? Use `mypage.html#proof` instead —
> some browsers drop the query string on file URLs. `?proof=1` also works.

Try it now with the included demo:

```bash
cd proofing-room
python3 -m http.server 8799
# then open http://127.0.0.1:8799/example.html?proof
```

## What you can do in proofing mode

| Action | How |
|--------|-----|
| **Comment** on anything | Click **+ Comment**, then click an element, type, Save. |
| **Edit copy in place** | Click **✎ Edit text**, click prose, rewrite it (original is kept). |
| **Name yourself** | Fill the **Reviewer** field — stamps your comments/edits. |
| **Export** | Click **Extract JSON** → downloads `proofing-<page>-<date>.json`. |
| **Get it out of the way** | Click the header to **collapse** to a floating toolbar (keeps the buttons, hides the list); **drag** the header to move it anywhere. |
| **Clear** | **Clear all** wipes comments + reverts edits for this page. |

A thick plum border and a **"Proofing mode"** badge make it obvious the page is
under review. Everything is saved per page path in `localStorage`, so a reload
never loses your notes.

## The handoff JSON

`Extract JSON` gives you a file with `comments[]`, `edits[]`, and a `document[]`
map of the page — each item anchored by CSS `selector`, visible `anchorText`,
nearest `section` heading, and `tag`. Hand it to an agent and ask it to apply the
edits and action the comments. See [`SKILL.md`](./SKILL.md) for the full schema
and the agent-side instructions.

## Use it as a Claude Code skill

Copy the folder into your skills directory and Claude will wire the wrapper into
pages for you and act on the exported JSON:

```bash
cp -R proofing-room ~/.claude/skills/
```

## How it's built

- One file, `proofing-room.js`, ~570 lines of dependency-free vanilla JS.
- Self-gating on `?proof` / `#proof` — no framework integration needed.
- State (comments, edits, panel position, collapsed state, reviewer name) lives
  in `localStorage`, keyed by page path.
- Styling is inline (SapphireOS sapphire + ClimatePulse plum) so it never
  collides with the host page's CSS, and the UI carries `#pr-*` ids it excludes
  from its own extraction.

## License

[MIT](../LICENSE) © Nick Pinidiya
