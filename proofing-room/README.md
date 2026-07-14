# Proofing Room

A self-contained, drop-in wrapper (v7.0) that turns **any** HTML page into a
review surface — on desktop **and** mobile, sharing one unified floating
toolbar across both. Reviewers pin comments, edit copy in place, answer
inline questions the page declares, react, approve sections, and set
reminders — then export (or optionally send) an **anchored JSON** an agent
(or you) can act on. No backend, no build step — one vanilla-JS file, state
stored in `localStorage`.

It's the review half of a tight loop: an agent generates HTML → a human marks
it up in proofing mode → exports JSON → the agent applies the feedback.

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
> On a phone the touch UI kicks in automatically; to preview it on a desktop
> browser use `?proof=mobile`.

Try it now with the included demo:

```bash
cd proofing-room
python3 -m http.server 8799
# then open http://127.0.0.1:8799/example.html?proof
# or       http://127.0.0.1:8799/example.html?proof=mobile
```

## What you can do in proofing mode

Desktop and mobile share the same floating pill + notes drawer — they only
differ in how you *start* annotating something.

| Action | Desktop | Mobile |
|--------|---------|--------|
| **Comment** on anything | Arm **comment** mode (pill button or `C`), click an element, type, Save. | Long-press an element → **Comment**. |
| **Edit copy in place** | Arm **edit** mode (pill button or `E`), click prose, rewrite it (original is kept). | Long-press → **Edit text**. |
| **React** | 👍/👎 from the comment popover. | Long-press → Looks right / Off the mark. |
| **Answer a declared question** | Tap the rendered control (buttons / slider / checkbox) wherever the page put it — same on both. | |
| **Approve a section** | Tap the circle in a `data-proof-section` heading — same on both. | |
| **Set a reminder** | From the comment popover. | Long-press → **Remind me**. |
| **Name yourself** | From the notes drawer (tap/click the pill's count). | Same. |
| **Export** | **Extract JSON** from the notes drawer. | Same. |
| **Send** *(optional — only if a webhook is configured)* | Send segment in the floating pill. | Same. |
| **Theme** | Auto / Light / Dark / OLED, from the notes drawer. | Same. |
| **Clear** | **Clear all** wipes notes + reverts edits for this page, from the drawer. | Same. |
| **Jump between docs** *(optional)* | ☰ button (top-left) opens a docs drawer — see below. | Same. |

Everything is saved per page path in `localStorage`, so a reload never loses
your notes.

## Docs menu (optional)

Set `window.PROOFING_DOCS` before the script loads to a list of
`{ title, url, source }` entries and a **☰** button appears (both platforms)
opening a slide-in drawer linking between them — handy for a reviewer hopping
between several related pages in one session. Links preserve the current
`?proof` mode. No list set → no button, no change in behaviour.

## Optional: wire a return channel

There's nothing to configure by default — **Extract JSON** always works and
needs no setup. If you want reviewers to be able to hit **Send** instead of
downloading a file:

- **Discord** — set `data-proofing-webhook` on `<body>` to your own channel's
  webhook URL. Send then POSTs a summary + the full JSON as a file attachment
  to that channel. The URL is a secret (anyone who has it can post into your
  channel) — keep the page private, and rotate it if it ever leaks.
  ```html
  <body data-proofing-webhook="https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN">
  ```
- **Any static host** — the page is just static HTML with one script tag, so
  hosting it anywhere is enough to hand a reviewer a link.

Neither is wired up for you — you provide your own webhook/host if you want
the round-trip; without one, Extract JSON is the whole loop.

## The handoff JSON

`version: "6"` — the export schema is unchanged (only the review UI is v7.0).
Beyond `comments[]` and `edits[]`, it also carries `answers[]` / `reactions[]`
/ `approvals[]` / `done[]` / `reminders[]` for anything the page declared with
`data-proof-ask` / `data-proof-section`, plus a `document[]` map of the whole
page. Each item is anchored by CSS `selector`, visible `anchorText`, nearest
`section` heading, and `tag` (+ `askId` for declared asks). See
[`SKILL.md`](./SKILL.md) for the full schema and the agent-side instructions.

## For design — restyle freely, keep the plumbing

**Safe to restyle:** all tokens/colours/spacing (the `cssMobile` / `cssDesktop`
/ `cssDocs` blocks near the top of `proofing-room.js`), the pill / menu / card
/ composer / drawer look, icons, copy, theme values (`:root` +
`prefers-color-scheme`, plus the `light` / `dark` / `oled` overrides). It's
already monochrome-tokenised, so most reskins are just swapping the `--pr-*`
custom-property values.

**Don't rename / remove** (the JS queries these):
- ids/classes: `#pr-pill #pr-menu #pr-card #pr-composer #pr-scrim #pr-hairline
  #pr-pins #pr-tabs #pr-shortcuts #pr-burger #pr-docs`, `.pr-dot .pr-ask
  .pr-ask-btn .pr-check .pr-scale .pr-approve .pr-doc-link`, and desktop
  `#pr-pop`.
- `selectorFor` / `locate` anchoring, the long-press recognizer, the webhook
  `FormData` shape, the `data-proof-tab` / `data-proof-ask` / `data-ask-type`
  / `data-proof-section` contract, the `window.PROOFING_DOCS` shape, and the
  `localStorage` blob shape (older blobs load without migration).

## iOS notes

Handled already: 16px inputs (no focus zoom), `touch-action: manipulation`,
long-press magnifier suppression, `visualViewport` keyboard tracking, and
safe-area insets.

## Files in this folder

- `proofing-room.js` — the whole thing. Dependency-free vanilla JS.
- `example.html` — a demo page: two tabs, one of every declared ask
  (yes/no, scale, done), a `data-proof-section` approve, and a
  `window.PROOFING_DOCS` list.
- `SKILL.md` — the Claude Code skill definition (what it is, how to wire it
  in, the declaration reference, acting on the returned JSON).

## License

MIT
