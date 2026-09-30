# Ink and motion

Every ink effect follows the same contract:

- **Poster first.** A finished static SVG/WebP is in the server HTML. JS swaps in the animated version only after its data loads. The poster remains if there is no JS or the fetch fails.
- **Scroll maps to progress.** One shared rAF is requested on scroll or resize. There is no idle loop, no timers and nothing clock-dependent. Scrolling back reverses the drawing to the same state.
- **Finished when still.** `prefers-reduced-motion: reduce` or `html[data-motion="off"]` forces every mask to complete (`stroke-dashoffset: 0 !important`) in CSS, before JS runs.
- **Offscreen is culled** with IntersectionObserver, and drawing pauses on `document.hidden`.
- **Art is `aria-hidden` with `pointer-events: none`** and never carries text. Numerals and words stay HTML.

## 1. Brush underline (cheapest ink gesture)

`assets/Brush.tsx` (`Brush` + `InkReveal`). CSS:

```css
.qi-brush { display:block; pointer-events:none; overflow:visible; aspect-ratio:10/1; }
.qi-brush path { fill:none; stroke:var(--qi-pale); stroke-width:7; stroke-linecap:round; stroke-dasharray:1 1; stroke-dashoffset:0; opacity:.85; }
.qi-brush .qi-brush-dry { stroke-width:2.2; opacity:.55; transform:translate(6px,5px); }   /* dry-brush echo */
.qi-brush[data-tone="rust"] path { stroke:var(--qi-rust); }
.qi-brush[data-tone="navy"] path { stroke:var(--qi-ink); }
.qi[data-ink-live] .qi-brush:not([data-inked]) path { stroke-dashoffset:1; }
.qi[data-ink-live] .qi-brush path { transition:stroke-dashoffset 1.1s var(--qi-ease-brush) .15s; }
.qi[data-ink-live] .qi-brush .qi-brush-dry { transition-delay:.45s; }
.qi-inked { position:relative; display:inline-block; white-space:nowrap; isolation:isolate; }
.qi-under { position:absolute; left:-2%; right:-2%; bottom:-.16em; width:104%; z-index:-1; }
.qi-under path { stroke-width:11; }
@media (prefers-reduced-motion:reduce) { .qi[data-ink-live] .qi-brush path { stroke-dashoffset:0 !important; } }
```

No React? Use the same markup plus this script. The CSS already shows finished strokes when JS is absent:

```html
<span class="qi-inked">for you.<svg class="qi-brush qi-under" data-ink viewBox="0 0 400 40" preserveAspectRatio="none" aria-hidden="true"><path d="M8 24 C80 12 250 30 392 14" pathLength="1"/><path class="qi-brush-dry" d="M8 24 C80 12 250 30 392 14" pathLength="1"/></svg></span>
<script>
  const root = document.querySelector('.qi');
  if (root && 'IntersectionObserver' in window) {
    root.dataset.inkLive = 'true';
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.dataset.inked = 'true'; io.unobserve(e.target); } }), { rootMargin: '0px 0px -12% 0px' });
    root.querySelectorAll('[data-ink]').forEach(s => io.observe(s));
  }
</script>
```

Usage (React): `<span class="qi-inked">signed off<Brush className="qi-under" d="M6 26 C90 14 200 30 394 16"/></span>`. Use one per heading at most. Pale on paper, rust on the navy close band.

## 2. Sumi spot paintings (scroll-drawn)

- Generator: `scripts/ink/sumi.mjs` (qubit-site) and `scripts/landing-ink/sumi.mjs` (VG). Paintings are authored as gesture point lists. `stroke(points, width, tone, dry)` samples a Catmull-Rom curve, varies the pressure (loaded press, lifted end, seeded jitter) and cuts **flying-white channels out of the fill** with even-odd slits. It never paints white on top.
- Tone picks the fill: `>=.6` → `#0b1f36`, `>=.35` → `#1d3f66`, else `#306fa8`.
- Outputs: `public/ink/sumi-<kind>.svg` posters plus `sumi-data.json` (`{kind:{width,height,strokes:[{d,route,width,tone}]}}`). The script prints a deterministic SHA-256.
- Host: `app/_home/ScrollInk.tsx` (`InkSpot kind=…`) and VG `SumiInk.tsx` (`SumiIcon`, `SumiInk`). Each stroke's `route` becomes a `stroke="white"` mask path with `pathLength=1`. Progress trails the scroll target at a capped speed (spots 1.6–2.4s, rail 6s). Reverse runs at 2× speed.
- Subject rules: **one subject per spot, lots of untouched paper**, and a meaning tied to the section. Examples: tea table = workshop, forked branch = advisory choice, sheets carried by ink = VG, bamboo/sparrow/falling leaf = beliefs, an enso framing the stat, a phone/link/pin/versions icon set.
- Spot box: 7:4 (stat 7:5). Brush icons are 160×160 sheets shown at 56–110px.

## 3. Left ink rail

- One continuous winding stalk with sparse leaves. It is absolutely positioned in the wrapper around the below-hero sections: `inset:0 auto 0 12px; width:44px; opacity:.9`. Progress runs across the whole wrapper (`journey`).
- It is hidden below 1100px. It never overlaps copy and never changes focus order.

## 4. Watercolour washes

- Each brush icon has a sibling wash SVG. The wash is a glaze with a pooled rim, turbulence displacement for the wet edge and a grain mask for granulation. It is re-laid "boneless", a few px off register.
- Hover (`@media (hover:hover)`): opacity 0 → 1, `scale(.82) rotate(-4deg) blur(3px)` → none, `mix-blend-mode:multiply`, over .7–.9s with `var(--qi-ease)`. The card `::before` blooms a soft radial sapphire/ochre wash with an organic `border-radius: 42% 58% 55% 45% / 50% 44% 56% 50%`.
- Touch (`hover:none`): the wash stays at 0.7.
- Homepage beliefs: when a belief opens, three wash layers (pale, indigo, warm) bloom under the ink. There is **one warm accent per spot** (ochre sun, ochre sparrow or rust leaf).

## 5. Hero film (nishiki-e woodblock)

- Silent, 16–20s at 24fps, 1200×1000 (6:5) master. VG uses 16:10 on desktop and 1:1 on mobile. It plays once and holds its last frame, which is also the poster.
- Pause and replay controls. It pauses offscreen and on a hidden tab. Reduced motion shows the poster only. Pick the video `src` in JS, because an unmatched `<source media>` made React mark the film as failed.
- Method: a navy keyblock plus one block per colour, each printed by multiply a hair off register. Wood grain in the flats, bokashi for all tone, and a baren rub mask for colour pulls in the order pale → mid → deep → ochre → **vermilion last** → green.
- Story shape: one transformation (grey, repetitive rain → colour, daylight, people talking). One recurring token (a paper sheet, the clock). End on a vermilion Q seal press and a declared hold.
- Build: `scripts/ink/hero-{kit,figures,art,render}.mjs`. Headless Chrome renders it with a determinism check, then 2-pass x264 with `-tune grain` (1450 kbps desktop, 700 kbps mobile). Homebrew ffmpeg may be broken. Use a working libx264 ffmpeg via `FFMPEG_PATH`.
- Encode check: Playwright's Chromium lacks h264, so judge video in real Chrome.

## 6. Docking brand

- A pure function of `scrollY` over 280px of travel. In the first 35% the name and nav fade (`--brand-fade`) and the Q–S gap closes. After that the pair travels, shrinks from 30 to 18px and the S swings under the Q (90°). It docks into the ink rail at x38/y26 on desktop, or into the top-left corner at 22px on phones, where a paper chip with a hairline appears behind it.
- Code: `app/_home/DockingBrand.tsx` (qubit-site). VG docks the Q only (`app/components/landing/DockingBrand.tsx`).

## 7. Small motions

- Reveal: `[data-reveal]` blocks below the fold rise by opacity plus 16px, staggered by `--i`. Nothing is hidden in the server HTML or in print (`beforeprint` releases all). Code: `app/_home/Reveal.tsx`.
- Button arrow: `translateX(3px)` on hover. Pin drop: `cubic-bezier(.3,1.5,.6,1)` .38s. Seal stamp: `scale(1.7)` → 1 at −9°, `cubic-bezier(.3,1.4,.5,1)` .45s. Changed region: a `#dbe8f3` flash fading out over 1.8s.
- Easing: `--qi-ease` (.2,.8,.2,1) for UI and `--qi-ease-brush` (.6,.05,.25,1) for strokes.

## Tools

- **anidoodle skill** (github.com/alexgreensh/anidoodle). See "External skills" in SKILL.md for the install lines and which references to read for each medium (`styles/sumiE.md`, `styles/woodcut.md`, `workflows/interactive.md`, `craft-bar.md`). Its tools are:
  - `tools/still.mjs` for stills
  - `tools/render.mjs` for loops and films
  - `tools/emit.mjs` for a single offline HTML file
  - `tools/gate.mjs` for determinism and dead air
  - `tools/verify-export.mjs` to decode the shipped file
- **Reference implementation** of every effect on this page, vanilla and dependency-free: `components/bundle.js` (`window.QubitInk`) in the Claude Design System "Qubit Ink" (https://claude.ai/artifact/9GBg6sHEFg82BQL6CD4uMS). Each component there has a live preview.

## Provenance

The art is original and code-drawn, with guidance from the anidoodle skill (Alex Greenshpun, Apache-2.0). No engine source is vendored. Keep a `NOTICE` next to the generated art, as `public/ink/NOTICE` does.
