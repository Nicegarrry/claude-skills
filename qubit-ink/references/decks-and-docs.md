# Decks, docs and other surfaces

## VG decks

- VG style **"Qubit Ink"**: `styleId mh7e9taa9zvm84kft6xwf0dnz58fdq7g` (v1, not the workspace default). Pass `styleId` on `vg_push_deck`, or pick "Qubit Ink" in VG's Styles tab.
- It carries the palette (paper bg, navy ink, sapphire accent, rust signal), Shippori Mincho B1 as `--font-serif`, Hanken Grotesk as sans, the QS logos, deck rules and 3 exemplars (cover, big stat, 01/02/03 offers). Sample deck: `jh7cjgpz9mb7z3xknerfzdy5qd8fdhrd`.
- Use the compiled CSS variables (`--bg`, `--ink`, `--accent`, `--rust`, `--font-serif`). Never hard-code the hex values in slides.
- Slide craft in ink:
  - Mincho 500 headlines ending in a full stop.
  - A 12px sapphire uppercase kicker above the headline.
  - Hairline-divided columns, no cards.
  - One rust element per slide: a stat numeral, a seal or the key bar.
  - Charts lead in sapphire with rust for the highlighted series. Everything else is navy/pale/grey (the `chartOrder` handles this).
  - The closing slide can use the navy band.
- **Known compromises** (VG presets, v1):
  - The chrome preset `bordered-square` gives 0px radii, where the sites use 2px.
  - The emphasis preset `weight-underline` is 800 weight with a rust underline, where the sites use a sapphire brush underline. Prefer a sapphire `<span>` over `<em>` for the inked word.
  - Bricolage sits in the serif fallback stack.
- **Changing the style:** use `vg_update_style({ styleId, … })`, which creates a new immutable version. Fonts can't go through the plain MCP call without base64, so re-create them via a bundle (`vg_create_style` with `bundle`) from a script that reads the woff2 files from disk. `vg_create_style` returns a version `_id` that is not the styleId. Use the styleId above with `vg_get_style`.

## Docs, emails, social

- **Docs (VG `flow`):** the style applies automatically. Keep headings short and declarative, and use one pull-stat per doc at most.
- **Email (Resend, e.g. the /book ticket):**
  - Paper `#f6f8fb` background, a navy wordmark and Mincho only via web-safe fallback (`Georgia, serif`). Email clients drop webfonts.
  - One rust button. Sapphire links underlined in `#8ea9c6`. A hairline `#cfd8e3` between blocks.
- **Social / OG cards (1200×630):**
  - Paper with grain and a Mincho 500 headline of 2 lines at most.
  - The QS mark bottom-left, one sumi spot or a film still on the right.
  - Rust only for a seal or numeral.
