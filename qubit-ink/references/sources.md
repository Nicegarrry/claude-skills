# Live sources

Read these before you invent anything. They are the ground truth, and this skill is only a distillation of them.

## qubitstudio.app homepage (repo `Nicegarrry/qubit-site`, PR #42)

- `app/page.tsx`: page anatomy and copy
- `app/_home/home.module.css`: tokens and every layout rule
- `app/_home/{DockingBrand,QubitMark,ScrollInk,HeroFilm,Beliefs,BeliefDetails,Reveal}.tsx`
- `app/_home/{beliefs,docking-brand,scroll-ink}.module.css`
- `scripts/ink/`: `paper.mjs` (grain), `sumi.mjs` / `sumi-render.mjs` / `sumi-check.mjs` (spots), `hero-*.mjs` (film), `verify.mjs` (browser acceptance)
- `scripts/ink/{sumi,hero}-notes.md`: art direction and craft reviews
- `docs/homepage-ink/{brief,README}.md` + `screens/`: brief, verification and screenshots
- `public/ink/*`: posters, film, washes, `paper.svg`, NOTICE. `public/fonts/*`: Shippori, Hanken, JetBrains. `public/brand/*`: marks

## vg.qubitstudio.app landing v2 (repo `Nicegarrry/VG`, PR #467)

- `app/components/landing/Landing.tsx`: anatomy (hero, how, why, who, close)
- `app/landing.css`: the whole ink landing under `.vg-landing`, with `--lp-*` tokens
- `app/components/landing/{DockingBrand,HeroFilm,SumiInk,InkReveal,Marks,FixDemo}.tsx`
- `scripts/landing-ink/sumi.mjs`: brush icons and washes
- `docs/landing-v2/screens/`: desktop 1440 and mobile 390 screenshots, including demo states

## Known divergences to converge on

- Homepage primary button rust is `#a8422e`, VG is `#b0552e`. Standard: `#b0552e`.
- Homepage headline is 64–100px, VG is 46–82px (longer headline). Choose by line count: 2 lines → large, 3 lines → VG size.
- Earlier notes (brief.md) mention Cormorant Garamond and warm paper. Both were superseded by Shippori Mincho B1 on cool paper.
