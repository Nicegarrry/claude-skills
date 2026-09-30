# Qubit Ink components

Recipes lifted from the two live pages. Class names use the `.qi-` prefix from `assets/tokens.css`. The live code uses `styles.*` (qubit-site CSS modules) and `.lp-*` (VG). Sizes are desktop first. Phone overrides are listed at the end of each recipe.

## Page anatomy

```
nav (96px, bottom hairline inset to gutters)
hero: text 46% | film/art 54%, bleeding off the right edge
  eyebrow · headline (2–3 short lines) · subhead (32–40ch) · CTA row · facts
[ink-journey wrapper: left ink rail runs down this whole block, desktop ≥1100]
  proof moment: stat (60%) or interactive demo, border-top rule
  section · section on band · section (each: eyebrow, display h2, content)
close: navy band, centred, rust brush stroke, title, one line, CTA
footer: mark + note | links | © line
```

## Nav

- `height: 96px; display:flex; gap: 24–40px`. A hairline `::after` runs from gutter to gutter (it is not full-bleed).
- Brand on the left: the QS lockup plus the "Qubit Studio" name in Mincho 500 at 34px. VG shows the Q and "VG".
- On the right: 3 anchor links at 14–15px in ink, turning sapphire and underlined on hover, then an optional meta note ("Sydney, Australia", 11px uppercase, left hairline). An app nav has a text link plus a small rust button (`.qi-btn-sm`).
- The brand docks into the left rail on scroll (see ink-and-motion.md). Nav links fade out with `opacity: var(--brand-fade)`.
- Phone: height 68–76px. Hide the name and the first link.

## Hero

```css
.hero { max-width:1440px; margin:auto; display:grid; grid-template-columns:46% 54%; padding:60px var(--qi-gutter) 46px; }
.film { grid-column:2; grid-row:1/3; margin:-20px calc(-1*var(--qi-gutter)) 0 -6%; }
.filmFrame { aspect-ratio:6/5; position:relative; overflow:hidden;
  mask-image: linear-gradient(to right,transparent 0,#000 9%,#000 97%,transparent 100%),
              linear-gradient(to bottom,transparent 0,#000 8%,#000 86%,transparent 100%);
  mask-composite:intersect; }   /* feather the print into the paper: no frame, no border */
```

- Headline: `.qi-headline`, 2–3 lines, each in a `display:block` span. Use one inked word at most. The ink is a sapphire word with a pale `Brush` underline (VG "pls fix").
- Subhead: 18px/1.65, ink-2, max 32–40ch.
- CTA row: a rust `.qi-btn` with an arrow-right icon, then sapphire `.qi-link`s (a secondary action and "See how it works").
- Facts: 11px ink-3. Each fact is a 13px Heroicon plus text (date, time, place, price, seats).
- Fine print: 13px ink-3 ("Free to use. Nothing to install.").
- Phone: the hero becomes a column. The film sits below the text at full width with only the vertical mask. The button is full width.
- **No film yet?** In order of preference:
  - a sumi spot painting (or a still from an existing film) in the right column with the same feathered mask;
  - a text-only hero with a facts column on the right: Mincho 20px lines with a sapphire hairline on the left;
  - empty paper.
  Never use a placeholder illustration, a gradient or a photo in a card.

## Stat moment

- The numeral is real HTML: `.qi-stat` (150–235px rust Mincho, `-0.04em`). Grid: numeral in column 1, label in column 2 (Mincho 32–46px navy, max 19ch, balanced).
- The pre-label is 12px sapphire uppercase. The footnote is 11px ink-3, with a real source.
- An enso sumi spot (opacity .65) sits behind the numeral. The painting never contains the number.

## Section header

`eyebrow` → `.qi-display` h2 (max 20–21ch, `text-wrap: balance`) → optional `.qi-lede`. Content starts 52–60px below.

## Offers / tiers (3 columns)

```css
.offers { display:grid; grid-template-columns:repeat(3,1fr); gap:38px; margin-top:52px; }
.offer { display:flex; flex-direction:column; }
.offer + .offer { border-left:1px solid var(--qi-rule); padding-left:35px; }
.tier { display:flex; align-items:center; gap:16px; font-size:11px; color:var(--qi-ink-3); }
.tier span { font-family:var(--qi-display); font-size:23px; color:var(--qi-ink); }  /* 01 */
```

- Order inside each column: tier (`01 · A morning`) → sumi spot (7:4) → h3 (Mincho 32px) → body 15px/1.75 → `dl` facts (dt 600, dd ink-2) → link pinned to the bottom (`margin-top:auto`).
- Phone: one column. The dividers become top hairlines.

## Benefit list (4 columns, washcards)

- `li { border-top:1px solid var(--qi-ink); padding-top:26px }`. The navy top rule is the only "card" edge.
- Each item: a brush icon (96px, `margin-left:-14px`) over a watercolour wash, then h3 (Mincho 25px), then body 15.5px/1.7.
- Hover: the wash blooms, the icon tilts −2°, the h3 turns sapphire-deep and the top rule turns sapphire. On touch the wash sits at 0.7 permanently.
- Phone: one column, with a 56px icon on the left.

## Numbered moments (how it works)

- Rows separated by hairlines. Each row has a 38px circle numeral (Mincho 20px, rule border) and a title in Mincho 30px.
- The active row has a navy fill with a paper numeral. A done row has a band fill, pale border and sapphire numeral.
- Pair it with a live demo (VG FixDemo: phone frame with a 10px navy border and 44px radius, rust pins, a sweep, a rust double-border seal stamp "Approved" at −9°).

## Audience / people

- 3 columns with hairline dividers. Top line: a sapphire numeral `01` and a 110px brush icon. Then h3 in Mincho 36px with a 15px ink-3 sub-line, then body 16px/1.75, max 38ch.
- Portraits: 88×100, `filter: grayscale(1)`, radius 2px. Name in Mincho 600 33px, role in 13px ink-3.

## Close band

`.qi-close`: navy, with two faint radial sapphire/pale glows. Centred content: a rust brush stroke 240px wide (stroke-width 9), then the title (Mincho clamp(38–68px), max 18ch), one line of 18px `#c4d3e3`, a rust button and an on-dark link.

## Footer

Hairline top, 36–45px padding. Left: the QS lockup at 24px plus "A partnership of…" in 12px ink-3. Right: links at 13px. Below: the © line at 10–12px ink-3. VG adds "Made by Qubit Studio" with the QS pair at 16px and an up-right arrow icon.

## Controls on art

A film pause/replay control sits on the art itself: bottom-left at 12%/14–16%. Paper at 82–85% via `color-mix`, a hairline border, radius 2px, 11–12px text, 12–14px icon, min-height 36–40px.

## Focus, a11y, overflow

- Focus ring: `2px solid sapphire; outline-offset: 4–5px`. On navy it turns pale.
- Include a skip link. Headlines with visual splits keep one real `h1`. Decorative art is `aria-hidden`.
- The root has `overflow-x: clip`. The film bleeds with a negative margin, never with `100vw`.
