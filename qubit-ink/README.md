# qubit-ink

The Qubit Studio design system, distilled from the ink homepage (qubitstudio.app) and the VG landing v2 (vg.qubitstudio.app). Agents read `SKILL.md`. People can start here.

**Look:** a woodblock-and-sumi print on cool paper, with navy ink, a sapphire accent and one vermilion seal. Display type is Shippori Mincho B1 and body type is Hanken Grotesk. Hairlines replace boxes. The art is code-drawn and draws itself as you scroll.

## Contents

```
SKILL.md                     rules, quick reference, build steps, common mistakes
assets/tokens.css            CSS custom properties + .qi-* base classes
assets/QubitMark.tsx         Q / S woodblock marks + lockup
assets/Brush.tsx             brush underline + InkReveal observer
assets/brand/*.svg           mark, S, QS pair, reversed
assets/fonts/                Shippori Mincho B1 500/700 (latin woff2, SIL OFL 1.1)
assets/paper.svg             paper grain tile
references/components.md     page anatomy and component recipes
references/ink-and-motion.md sumi spots, rail, washes, hero film, docking brand, motion
references/brand-marks.md    mark construction and usage
references/decks-and-docs.md VG style "Qubit Ink", email, social cards
references/sources.md        live code, generators, screenshots, known divergences
```

## Also recorded in

- **VG:** style "Qubit Ink" (`mh7e9taa9zvm84kft6xwf0dnz58fdq7g`) for decks and docs.
- **Common Ground:** `team/qubit-ink-design-system`.

## Changelog

- **v1 (2026-10-01):** first cut. It covers tokens, components, ink/motion and marks from homepage PR #42 and VG PR #467. It also sets up the VG style v1. Rust is standardised on `#b0552e`.
