---
name: slide-presenter
description: >
  Turn a static HTML slide deck into a self-contained, hostable presentation and
  publish it to a live URL. Use when someone has an HTML deck (e.g. the combined
  output of a deck renderer, or any HTML file made of fixed-size 1280x720 .slide
  stages) and wants it shown in presentation mode — fullscreen slides, arrow-key
  / button navigation, and a thumbnail switcher — and/or deployed to here.now.
  Triggers: "make this deck a presentation", "add a present/slideshow mode to
  this HTML", "wrap these slides in a viewer", "publish this deck to here.now",
  "host this slide deck", "turn this render into a slideshow".
---

# slide-presenter

Two jobs, usually run together:

1. **Wrap** a static HTML deck in a presentation viewer (screen-only; print is
   untouched, so PDF export still gives one slide per page).
2. **Publish** the wrapped file to a live URL via the `here-now` skill.

The viewer it injects:
- Fullscreen, one slide at a time, scaled to fit the viewport.
- Navigate: arrow keys, space, PageUp/PageDown, Home/End, or on-screen buttons.
- **Switcher**: a thumbnail grid of all slides (grid button or press `g`); click
  any thumbnail to jump to it; `Esc` or the Slideshow button returns.
- Fullscreen toggle (button or press `f`).

It is self-contained vanilla JS + CSS — no build step, no dependencies, no
network. Icons are inline SVG (no Unicode glyphs).

## Input requirements

A single HTML **document** (`<head>` + `<body>`) containing one or more slide
elements. By default each slide is an element with class `slide`, sized 1280x720
(the shape produced by consulting-style deck renderers). The slides should be
direct children of one container. If your slides use a different class, pass
`--slide-class`.

This skill does **not** generate slides — it wraps an existing rendered deck. If
you only have separate per-slide HTML files, concatenate their `.slide` elements
into one document first (one `<head>` with the shared CSS, all slides in one
container in `<body>`).

## Usage

### 1. Wrap

```bash
python3 scripts/present-wrap.py --in deck.html --out deck.present.html
# or edit in place:
python3 scripts/present-wrap.py --in deck.html --in-place
# custom slide class:
python3 scripts/present-wrap.py --in deck.html --slide-class my-slide
```

It prints the output path. Re-running on an already-wrapped file is a no-op
(detected via the injected `pv-style` marker).

### 2. Publish (via the here-now skill)

here.now serves a directory whose root is `index.html`. Stage the wrapped file
as `index.html`, then publish:

```bash
mkdir -p /tmp/deck-pub && cp deck.present.html /tmp/deck-pub/index.html
~/.claude/skills/here-now/scripts/publish.sh /tmp/deck-pub \
  --title "My deck" --client claude-code
# update an existing site (same URL):
~/.claude/skills/here-now/scripts/publish.sh /tmp/deck-pub --slug <existing-slug>
```

With saved here.now credentials the site is permanent; otherwise it is anonymous
(24h) and the script prints a claim URL. Publishing to the public web is an
external action — confirm with the user before doing it, and share the live URL
they get back. See the `here-now` skill for access control (password /
invite-only) and custom domains.

## Verifying before you publish

Serve locally and check it works, especially if the deck used a non-default slide
class:

```bash
cd /tmp/deck-pub && python3 -m http.server 8766   # open http://127.0.0.1:8766/
```

Present mode should show one slide; arrows advance; `g` opens a multi-column
thumbnail grid; clicking a thumbnail returns to that slide.

## Notes

- The viewer reads `--accent` (CSS custom property) for the thumbnail hover
  outline if the deck defines it; otherwise falls back to a sapphire blue.
- Thumbnail grid density auto-adjusts by viewport (`--pv-ts`: ~3 cols on a
  laptop, more on wide screens).
- For an *in-app* presentation view inside a web product (rather than a static
  hosted file), this skill is the wrong tool — build a component that renders the
  slides in-platform. (Example: the managed-EM `DeckPresenter`.)
