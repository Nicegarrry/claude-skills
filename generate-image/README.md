# generate-image

A Claude Code skill for generating and editing images, illustrations, icons,
diagrams, avatars, and product shots from natural language — via Google's **Nano
Banana** (Gemini) image models. Ships brand-styled archetype presets and a guided
first-run key setup.

> Claude reads `SKILL.md`; this README is for humans. They overlap by design.

## Install

```bash
# Copy the folder into your Claude Code skills directory
cp -R generate-image ~/.claude/skills/

# One-time API key setup (opens Google AI Studio, hidden paste)
~/.claude/skills/generate-image/setup.sh
```

You need a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
`setup.sh` walks you through it and stores the key at
`~/.config/nano-banana/credentials.env` (chmod 600). `$GEMINI_API_KEY` in the
environment overrides the file.

Requires [`uv`](https://docs.astral.sh/uv/) — the helper is a single-file script
that auto-installs its own dependencies (`google-genai`, `pillow`) on first run.

## Usage

```bash
G=~/.claude/skills/generate-image/generate_image.py

$G -p "a watercolour fox reading a book" -o fox.png
$G -P illustration -p "an electric-type fox with a lightning-bolt tail"   # preset
$G -P hyperreal    -p "white wireless earbuds in an open charging case"   # product
$G -p "make the sky a dramatic storm" -i photo.png -o photo_storm.png     # edit
$G --list-presets
```

In Claude Code you usually don't call it directly — just ask ("make me an icon
of a rocket", "generate a slide background for…") and the skill triggers.

### Options

| Flag | Default | Notes |
|------|---------|-------|
| `-p/--prompt` | — | Prompt / subject (also positional) |
| `-P/--preset` | — | Archetype preset (see below) |
| `-S/--style` | auto | `sapphireos`, `sapphireos-dark`, or `none` |
| `-o/--out` | `./nano-banana.png` | Output path (extension sets format) |
| `-m/--model` | `flash` | `flash` (Nano Banana 2) · `pro` · `nano-banana` |
| `-a/--aspect` | `1:1` | `16:9 9:16 3:2 2:3 4:3 3:4 4:5 5:4 21:9` |
| `-s/--size` | `2K` | `512 1K 2K 4K` |
| `-i/--input` | — | Input image(s) to edit/reference (repeatable) |
| `--profile` | `GEMINI_API_KEY` | Key var to read (e.g. `SLIDES_GEMINI_API_KEY`) |

## Presets

| Preset | Defaults | For |
|--------|----------|-----|
| `infographic` | pro · 4:3 · 2K | Labelled explainer diagrams (sharp text) |
| `abstract-title` | flash · 16:9 · 2K | Slide title / transition backgrounds |
| `illustration` | flash · 1:1 · 2K | Friendly cel-shaded creature/character |
| `hyperreal` | pro · 1:1 · 2K | Photorealistic product shots |
| `avatar` | flash · 1:1 · 1K | Profile portraits |
| `icon` | flash · 1:1 · 1K | Flat vector icons on white |
| `diagram` / `diagram-dark` | pro · 16:9 · 2K | Line-art schematics / flows |
| `icon-line` / `icon-line-dark` | flash · 1:1 · 1K | Single-stroke line icons |

`-P` picks the archetype, `-p` is the subject; explicit `-m/-a/-s` override.

## Brand styling

Slide-bound presets (`infographic`, `abstract-title`) apply a **SapphireOS**
house style by default (cool sapphire-blue palette, clean grotesque type,
generous radii). Opt out with `-S none`, force light/dark with
`-S sapphireos` / `-S sapphireos-dark`, or brand any raw prompt with `-S`. The
`diagram*` / `icon-line*` presets bake the palette into the template directly.
Edit the `STYLES` / `PRESETS` dicts at the top of `generate_image.py` to retune.

## Models & cost

| Model | ID | Notes |
|-------|-----|-------|
| Nano Banana 2 (`flash`) | `gemini-3.1-flash-image` | Default. ~$0.05–0.15/img |
| Nano Banana Pro (`pro`) | `gemini-3-pro-image` | Best text/realism. ~$0.13–0.24/img |
| Nano Banana (`nano-banana`) | `gemini-2.5-flash-image` | Legacy |

Prompting tips: see [`PROMPTING.md`](./PROMPTING.md). All output carries an
invisible SynthID watermark + C2PA credentials (Google policy).

## Files

- `SKILL.md` — what Claude reads
- `generate_image.py` — the CLI helper (uv single-file script)
- `setup.sh` — guided API key installer
- `PROMPTING.md` — prompting reference with worked examples
