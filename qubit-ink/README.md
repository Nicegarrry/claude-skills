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
assets/fonts/                Shippori Mincho B1 500/700 + Hanken Grotesk variable (SIL OFL 1.1)
assets/paper.svg             paper grain tile
references/components.md     page anatomy and component recipes
references/ink-and-motion.md sumi spots, rail, washes, hero film, docking brand, motion
references/brand-marks.md    mark construction and usage
references/decks-and-docs.md VG style "Qubit Ink", email, social cards
references/sources.md        live code, generators, screenshots, known divergences
```

## Also recorded in

- **VG:** style "Qubit Ink" (`mh7e9taa9zvm84kft6xwf0dnz58fdq7g`) for decks and docs.
- **Claude Design System:** "Qubit Ink", https://claude.ai/artifact/9GBg6sHEFg82BQL6CD4uMS. It holds the live tokens, 17 animated component previews, the brush icons, paintings and films, and the ink engine.
- **Common Ground:** `team/concept/qubit-ink-design-system`.

## Changelog

- **v1.1 (2026-10-01):** adds a pointer to the external skill (anidoodle) with install lines and references, and the repo generators. The VG style is now v12 with the brush icons and spots, and 33 ink assets are in the VG library. Adds the Claude Design System.

- **v1 (2026-10-01):** first cut. It covers tokens, components, ink/motion and marks from homepage PR #42 and VG PR #467. It also sets up the VG style v1. Rust is standardised on `#b0552e`. After a fresh-agent test build, it adds a scoped reset, bundled Hanken, `.qi-subhead`, `.qi-cta-row`, `.qi-facts` and `.qi-cols`, a rust-per-screen rule, a no-film hero fallback and a vanilla brush script.
