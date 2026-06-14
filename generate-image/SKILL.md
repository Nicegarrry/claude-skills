---
name: generate-image
description: Use when asked to generate, create, make, draw, or edit an image, illustration, icon, logo, poster, diagram, mockup, sticker, avatar, or any visual/picture from a text description — produces real PNG files via Google's Nano Banana (Gemini) image API.
---

# Generate Image (Nano Banana)

## Overview

Turn a text description into a real image file using Google's Nano Banana (Gemini)
image models. The helper script handles the API call, key loading, and saving —
your job is to write a good prompt and pick the right model/size.

**Core principle:** describe a *scene* in natural language (subject, action,
setting, lighting, style) — not a list of keywords.

## When to use

- "Make me an illustration / icon / logo / poster / diagram / mockup of …"
- "Generate an image of …", "draw …", "create a picture of …"
- "Edit this image: …" (change, add, remove, restyle — pass it with `-i`)
- Hero art, avatars, stickers, textures, concept art, marketing visuals

**Not for:** charts from data (use a plotting lib), vector/SVG icon sets (use
Heroicons per global prefs), or anything needing exact pixel-perfect logos.

## Quick start

```bash
~/.claude/skills/generate-image/generate_image.py -p "PROMPT" -o out.png
```

The script auto-installs its dependencies via `uv` on first run. It saves a PNG
and prints the path. Default model is Nano Banana 2 at 2K, 1:1.

## First run / no API key

The helper exits `2` with "no API key found" until a key is configured. **When
that happens, do NOT retry blindly — walk the user through setup, then retry:**

1. Tell them to get a free key from **Google AI Studio**: https://aistudio.google.com/apikey
   ("Create API key" → copy).
2. Have them run the guided installer **in their own terminal** (so the key is
   pasted hidden, never into this chat):
   ```bash
   ~/.claude/skills/generate-image/setup.sh
   ```
   It opens AI Studio, prompts for the key with hidden input, writes it to
   `~/.config/nano-banana/credentials.env` (chmod 600), and offers a test gen.
3. If they'd rather not run the script, the one-liner is:
   ```bash
   printf 'GEMINI_API_KEY=YOUR_KEY\n' > ~/.config/nano-banana/credentials.env && chmod 600 ~/.config/nano-banana/credentials.env
   ```

`$GEMINI_API_KEY` in the env overrides the file. A separate slides key can be
added as `SLIDES_GEMINI_API_KEY` (run `setup.sh SLIDES_GEMINI_API_KEY`) and
selected with `--profile SLIDES_GEMINI_API_KEY`.

## Models — pick one

| Alias | Model id | Use for |
|-------|----------|---------|
| `flash` (default) | `gemini-3.1-flash-image` | Most work: illustrations, icons, concepts. Fast, ~$0.05–0.13/img. |
| `pro` | `gemini-3-pro-image` | Heavy text-in-image (posters, infographics), complex/precise scenes, max realism. Slower, ~$0.13–0.24/img. |
| `nano-banana` | `gemini-2.5-flash-image` | Legacy / fallback. |

Reach for `pro` when the image must contain **legible text** or many precise elements.

## Presets (archetypes)

Common image types come pre-styled. Pass `-P <preset>` and put the *subject* in
`-p`; the preset supplies the style + sensible model/aspect/size. Any explicit
`-m/-a/-s` flag overrides the preset.

```bash
generate_image.py -P illustration -p "an electric-type fox with a lightning-bolt tail" -o fox.png
generate_image.py -P hyperreal    -p "white wireless earbuds in an open charging case" -o buds.png
generate_image.py -P abstract-title -p "the future of AI" -o slide_bg.png
```

| Preset | Model / aspect / size | For |
|--------|----------------------|-----|
| `infographic` | pro · 4:3 · 2K | Labelled explainer diagrams (sharp text) |
| `abstract-title` | flash · 16:9 · 2K | Slide title / transition backgrounds (text-safe negative space) |
| `illustration` | flash · 1:1 · 2K | Friendly cel-shaded creature/character ("pokemon" house style) |
| `hyperreal` | pro · 1:1 · 2K | Photorealistic studio product shots for demos |
| `avatar` | flash · 1:1 · 1K | Profile-picture portraits |
| `icon` | flash · 1:1 · 1K | Minimal flat vector icons on white (multi-colour) |
| `diagram` | pro · 16:9 · 2K | SapphireOS line-art schematic / flow (sapphire on white) |
| `diagram-dark` | pro · 16:9 · 2K | Same, dark facet (bright sapphire on charcoal) |
| `icon-line` | flash · 1:1 · 1K | SapphireOS single-stroke line icon (sapphire on white) |
| `icon-line-dark` | flash · 1:1 · 1K | Same, dark facet (bright sapphire on charcoal) |

The `diagram*` / `icon-line*` presets bake the SapphireOS palette into the
template itself (so they're *not* double-styled by `-S`); use the `-dark`
variants for dark decks.

`--list-presets` prints them. **To tune a house style, edit the `PRESETS` dict at
the top of `generate_image.py`** — each entry is a prompt template (`{prompt}` =
your subject) plus default model/aspect/size.

## Brand style (SapphireOS)

Slide-bound presets (`infographic`, `abstract-title`) apply the **SapphireOS**
brand by default — cool sapphire-blue palette (#306FA8), white/cool-paper
surfaces, clean grotesque type, generous radii, restrained translucency. Sourced
from `qubit-os/platform/design`.

```bash
generate_image.py -P infographic -p "how an agent works"        # sapphireos (default)
generate_image.py -P abstract-title -p "lab" -S sapphireos-dark # dark facet
generate_image.py -P infographic -p "..." -S none               # opt out, plain
generate_image.py -p "a dashboard mockup" -S sapphireos         # brand any raw prompt
```

| Flag | Effect |
|------|--------|
| `-S sapphireos` | Light brand (white canvas, sapphire accent). |
| `-S sapphireos-dark` | Dark facet (charcoal canvas, bright sapphire). |
| `-S none` | Opt out — no brand styling. |
| (omitted) | Slide presets → `sapphireos`; everything else → none. |

Non-slide presets (illustration, hyperreal, avatar, icon) are **not** branded by
default — add `-S sapphireos` to opt in. To change the default-on set, flip the
`"slide": True` tag on a preset; to retune the look, edit the `STYLES` dict (built
from the SapphireOS tokens). Default brand = `DEFAULT_BRAND_STYLE` constant.

## Options

| Flag | Default | Notes |
|------|---------|-------|
| `-p/--prompt` | — | Prompt (also positional). |
| `-o/--out` | `./nano-banana.png` | Output path. |
| `-m/--model` | `flash` | Alias or raw model id. |
| `-a/--aspect` | `1:1` | `16:9 9:16 3:2 2:3 4:3 3:4 4:5 5:4 21:9` (+ `1:4 4:1 1:8 8:1` on flash). |
| `-s/--size` | `2K` | `512`(flash) `1K` `2K` `4K`. Drop to `1K` for drafts; `4K` for print. |
| `-i/--input` | — | Input image(s) to edit/reference. Repeatable (up to ~14). |
| `--profile` | `GEMINI_API_KEY` | Which key var to read (e.g. `SLIDES_GEMINI_API_KEY`). |

## Prompting cheat-sheet

Write a sentence or two, not tags. Hit these beats:

**`[subject] + [action/pose] + [setting] + [composition] + [style/lighting]`**

- **Name the medium up front:** "a watercolour illustration of…", "a 3D clay render of…", "a flat vector icon of…", "a photorealistic photo of…".
- **Use positive framing:** "an empty street" not "a street with no cars".
- **Add camera/light for realism:** "low angle, shallow depth of field (f/1.8), golden-hour backlight".
- **Text in the image:** put the exact words in quotes and name the font — `the words "LAUNCH DAY" in a bold sans-serif`. Use `-m pro` for anything text-heavy.
- **Editing:** pass the image with `-i` and say what to keep — "keep the composition, change only the season to winter".
- **Consistency across images:** pass a reference with `-i` and say "same character/style as the reference".

For the full guide with worked examples (product shots, posters, character
consistency, style transfer), see `PROMPTING.md` in this folder.

## Common mistakes

- **Keyword soup** ("fox, book, cozy, 4k, trending") → weak results. Write a scene.
- **Negatives** ("no text", "without people") → describe the positive instead.
- **Tiny text on `flash`** → use `-m pro` for legible/long text.
- **`-s 4K` everywhere** → slower + pricier; use `1K`/`2K` unless it's for print.
- **Model `NOT_FOUND`** → during rollout the id may need a `-preview` suffix; the script prints the hint. Try `-m gemini-3.1-flash-image-preview`.

## Note

All output carries an invisible SynthID watermark + C2PA credentials (Google policy).
