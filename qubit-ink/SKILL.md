---
name: qubit-ink
description: Use when designing or building any Qubit Studio or VG surface (web page, landing page, section, email, deck, doc, social card) that should match qubitstudio.app and the VG landing, or when asked for "qubit ink", "the ink style", "on brand for qubit", or "make it look like the homepage".
---

# Qubit Ink

The Qubit Studio design system: a woodblock-and-sumi print on cool paper. Prussian-navy ink, one sapphire accent, one vermilion seal, a calligraphic Mincho serif, hairline rules and a lot of untouched paper. Live references: qubitstudio.app (homepage) and vg.qubitstudio.app (landing).

**Core idea:** the page is a print, not an app. Ink goes on paper; colour is pulled like a woodblock (lightest to darkest, rust last); motion is a brush being drawn, never a fade-and-slide.

## The rules that make it read as Qubit Ink

1. **Paper:** `#f6f8fb` with the `paper.svg` grain. Light only; ignore saved dark preferences (`color-scheme: light`, `data-theme="light"`).
2. **Ink:** headings and marks in navy `#132a45`; body `#36495e`; meta `#566a80`.
3. **Sapphire `#306fa8` is the one accent:** eyebrows, links, focus rings, active state, one inked word.
4. **Rust `#b0552e` is the seal.** One per view: the primary CTA, a stat numeral or a stamp. Never for body text, borders or decoration.
5. **Type:** Shippori Mincho B1 500 for display (big, tight, `-0.012em` to `-0.02em`), Hanken Grotesk for everything else. Eyebrows are 12px, 600, uppercase, `.15em` tracking, sapphire.
6. **Structure comes from hairlines** (`1px #cfd8e3`): a rule on top of each section and between columns. No cards, shadows, gradients or rounded boxes. Radius 2px, and buttons are hand-cut at `2px 1px 3px 1px`.
7. **Rhythm:** max 1440, gutter `clamp(20px,5.55vw,80px)`, sections ~104px tall padding, alternate sections on the `#e9eff6b3` band, close on a navy band.
8. **Art is code-drawn and deterministic.** It includes a woodblock hero film, scroll-drawn sumi spots, a left ink rail and brush underlines. There is no stock art, image-generator art or icon-font decoration. Heroicons 24 outline are used for UI glyphs only.
9. **Motion reverses and rests.** Scroll maps to brush travel. There are no idle loops. Reduced motion or `data-motion="off"` shows every stroke finished, and no-JS shows the poster.
10. **Voice:** short declaratives ending with a full stop, like "Take your time back." or "Say pls fix. Get it back done." Sentence case, no em dashes, no hype.

## Quick reference

| Need | Use |
|---|---|
| Tokens + base classes (`.qi-*`) | `assets/tokens.css` |
| Q / S / QS woodblock marks | `assets/QubitMark.tsx`, `assets/brand/*.svg`, rules in `references/brand-marks.md` |
| Brush underline + draw-on-scroll | `assets/Brush.tsx` + CSS in `references/ink-and-motion.md` |
| Page anatomy, hero, offers, stat, lists, close band, footer | `references/components.md` |
| Sumi spots, ink rail, washes, hero film, docking brand | `references/ink-and-motion.md` |
| Decks, docs and emails in this style | `references/decks-and-docs.md` (VG style "Qubit Ink") |
| Where the live code and generators are | `references/sources.md` |
| Fonts (OFL) and paper grain | `assets/fonts/`, `assets/paper.svg` |

## Building a new page

1. Copy `assets/tokens.css`, the fonts and `paper.svg` into the app. Scope the page under `.qi`.
2. Lay out from `references/components.md`. Order: nav → hero (headline plus film or art) → one proof moment (stat or demo) → 2–3 sections separated by rules and a band → navy close → footer.
3. Choose **one** rust moment per view. Then give each section **one** ink gesture: a spot painting, a brush underline or a wash.
4. Write copy last, to the voice rule. Keep each headline to one idea and 4–8 words.
5. Verify at 1440 and 390: no horizontal overflow, CTA above the fold, reduced motion shows the finished art, no-JS keeps the posters, focus rings are visible, text contrast is AA.

## Common mistakes

- **Rust everywhere** (links, borders, icons). It stops being a seal. Links are sapphire.
- **Card grids with shadows.** Use columns divided by hairlines instead.
- **Fade-up on everything.** Ink draws along a stroke. Reveals are at most opacity plus 16px, and only below the fold.
- **Bold Mincho.** Display weight is 500. Use 700 only for the seal or stamp.
- **Dark mode variants.** There are none. The navy close band is the only dark surface.
- **Generated illustrations.** They break the print. Draw with the sumi/woodblock generators (see sources) or leave the paper empty.
- **Two accents competing in one view** (a sapphire underline next to a rust CTA is fine; two rust objects are not).

## Iterating the system

This is v1 (2026-10-01), distilled from the homepage (#42) and VG landing v2 (#467). When a new page changes a token or pattern, update `tokens.css` and the relevant reference file here, bump the changelog in `README.md`, and update the VG style and the Common Ground page (`team/qubit-ink-design-system`) so all three stay in step.
