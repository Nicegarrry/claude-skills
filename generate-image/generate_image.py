#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "google-genai>=1.33",
#   "pillow>=10.0",
# ]
# ///
"""Generate or edit images with Google's Nano Banana (Gemini) image models.

Key resolution order:
  1. $GEMINI_API_KEY / $GOOGLE_API_KEY  (or whatever --profile names)
  2. ~/.config/nano-banana/credentials.env  (KEY=VALUE lines)

Examples:
  ./generate_image.py -p "a watercolour fox reading a book" -o fox.png
  ./generate_image.py -p "isometric icon of a rocket, flat design, on white" -a 1:1 -s 1K
  ./generate_image.py -p "make the sky a dramatic storm" -i photo.png -o photo_storm.png
  ./generate_image.py -p "..." -m pro -s 4K          # Nano Banana Pro, 4K
"""
from __future__ import annotations

import argparse
import mimetypes
import os
import sys
from pathlib import Path

CONFIG_FILE = Path(
    os.environ.get("NANO_BANANA_CREDENTIALS", Path.home() / ".config" / "nano-banana" / "credentials.env")
).expanduser()
SETUP_SCRIPT = Path(__file__).resolve().parent / "setup.sh"

# Friendly aliases -> current Gemini model ids (verified June 2026).
MODEL_ALIASES = {
    "flash": "gemini-3.1-flash-image",          # Nano Banana 2 (default: fast, cheap)
    "nano-banana-2": "gemini-3.1-flash-image",
    "nb2": "gemini-3.1-flash-image",
    "pro": "gemini-3-pro-image",                # Nano Banana Pro (best text/reasoning)
    "nano-banana-pro": "gemini-3-pro-image",
    "nano-banana": "gemini-2.5-flash-image",    # original Nano Banana
    "nb1": "gemini-2.5-flash-image",
}
DEFAULT_MODEL = "gemini-3.1-flash-image"

# ---------------------------------------------------------------------------
# ARCHETYPE PRESETS — edit freely to tune your house style.
# `{prompt}` is replaced with whatever you pass via -p. Explicit -m/-a/-s
# flags always override a preset's defaults.
# ---------------------------------------------------------------------------
PRESETS: dict[str, dict] = {
    "infographic": {
        "desc": "Clean explanatory infographic with labels (uses pro for sharp text).",
        "model": "pro", "aspect": "4:3", "size": "2K", "slide": True,
        "template": (
            "A clean, modern infographic that explains {prompt}. Clear visual "
            "hierarchy with a few labelled sections, simple line iconography, a "
            "limited harmonious colour palette, generous whitespace, and legible "
            "sans-serif labels. Flat vector design, professional editorial quality."
        ),
    },
    "abstract-title": {
        "desc": "Abstract background for slide title / transition pages (room for text).",
        "model": "flash", "aspect": "16:9", "size": "2K", "slide": True,
        "template": (
            "An abstract, atmospheric background artwork evoking {prompt}. Flowing "
            "organic gradients, soft depth-of-field bokeh, elegant minimal "
            "composition with large areas of calm negative space for overlaying "
            "text, sophisticated muted colour palette, premium and modern. "
            "No text, no lettering, no figures."
        ),
    },
    "illustration": {
        "desc": "Friendly cel-shaded creature/character illustration (your 'pokemon' aesthetic — tune me).",
        "model": "flash", "aspect": "1:1", "size": "2K",
        "template": (
            "A charming cel-shaded illustration of {prompt}, in a friendly "
            "collectible-creature art style: bold clean outlines, vibrant "
            "saturated flat colours with soft cel shading, expressive and "
            "approachable, a simple uncluttered background, polished "
            "anime-influenced game-art quality."
        ),
    },
    "hyperreal": {
        "desc": "Hyperrealistic studio product shot for demos (uses pro for max realism).",
        "model": "pro", "aspect": "1:1", "size": "2K",
        "template": (
            "A hyperrealistic, photorealistic commercial studio product photograph "
            "of {prompt}. Shot on a medium-format camera with an 85mm lens at f/4, "
            "soft three-point softbox lighting, subtle realistic reflections, "
            "shallow depth of field, a seamless gradient studio backdrop, "
            "ultra-detailed, advertising-catalogue quality."
        ),
    },
    "avatar": {
        "desc": "Profile-picture avatar, head-and-shoulders, clean background.",
        "model": "flash", "aspect": "1:1", "size": "1K",
        "template": (
            "A friendly avatar portrait of {prompt}. Centered head-and-shoulders "
            "composition, clean solid-colour background, soft even lighting, modern "
            "illustrated style with clean lines and warm colours, suitable for a "
            "profile picture."
        ),
    },
    "icon": {
        "desc": "Minimal flat vector icon on white.",
        "model": "flash", "aspect": "1:1", "size": "1K",
        "template": (
            "A minimal flat vector icon representing {prompt}. Simple geometric "
            "shapes, bold clean lines, a limited two-or-three colour palette, "
            "centered on a plain white background, crisp app-icon quality, no text."
        ),
    },
    # SapphireOS line-art variants — brand baked into the template (don't slide-tag,
    # so the heavier STYLES overlay isn't also appended).
    "diagram": {
        "desc": "SapphireOS line-art diagram / schematic / flow (sapphire on white).",
        "model": "pro", "aspect": "16:9", "size": "2K",
        "template": (
            "A clean line-art diagram of {prompt}. Thin, uniform sapphire-blue "
            "(#306FA8) strokes on a pure white background; minimal labelled nodes "
            "and boxes connected by clean lines and simple arrows; generous "
            "whitespace, balanced layout, flat with no fills, gradients or shadows. "
            "Small legible sans-serif labels. Technical, editorial, precise."
        ),
    },
    "icon-line": {
        "desc": "SapphireOS line-art icon (single-weight sapphire stroke on white).",
        "model": "flash", "aspect": "1:1", "size": "1K",
        "template": (
            "A minimal line-art icon representing {prompt}. A single "
            "consistent-weight sapphire-blue (#306FA8) stroke on a pure white "
            "background, rounded line caps, simple geometric construction, centered "
            "with even padding, flat with no fills or shading, crisp and modern. "
            "No text."
        ),
    },
    "diagram-dark": {
        "desc": "SapphireOS dark line-art diagram (bright sapphire on charcoal).",
        "model": "pro", "aspect": "16:9", "size": "2K",
        "template": (
            "A clean line-art diagram of {prompt}. Thin, uniform bright sapphire-blue "
            "(#4F9EDB) strokes on a deep charcoal background (#1F2227); minimal "
            "labelled nodes and boxes connected by clean lines and simple arrows; "
            "generous whitespace, balanced layout, flat with no fills, gradients or "
            "heavy shadows. Small legible light-grey sans-serif labels. Technical, "
            "editorial, precise."
        ),
    },
    "icon-line-dark": {
        "desc": "SapphireOS dark line-art icon (bright sapphire stroke on charcoal).",
        "model": "flash", "aspect": "1:1", "size": "1K",
        "template": (
            "A minimal line-art icon representing {prompt}. A single "
            "consistent-weight bright sapphire-blue (#4F9EDB) stroke on a deep "
            "charcoal background (#1F2227), rounded line caps, simple geometric "
            "construction, centered with even padding, flat with no fills or "
            "shading, crisp and modern. No text."
        ),
    },
}

# ---------------------------------------------------------------------------
# BRAND STYLES — appended to the prompt to enforce a house look.
# Sourced from qubit-os/platform/design (SapphireOS, the canonical Qubit system).
# Slide-bound presets (those tagged "slide": True) get DEFAULT_BRAND_STYLE
# automatically unless you pass --style none or a different --style.
# ---------------------------------------------------------------------------
DEFAULT_BRAND_STYLE = "sapphireos"

STYLES: dict[str, dict] = {
    "sapphireos": {
        "desc": "Qubit SapphireOS — light, cool sapphire-blue, clean grotesque, editorial.",
        "fragment": (
            " Rendered in the SapphireOS brand style: a clean, premium, editorial "
            "aesthetic on a white / cool-paper background (#FFFFFF, #F7FAFC). "
            "Primary accent sapphire blue #306FA8 with deep navy #11375A and "
            "cool-steel ink #141A21; restrained secondary teal #347890 and warm "
            "brass #C2791A highlights. Generous rounded corners, soft subtle "
            "shadows, abundant whitespace, thin cool rule lines, restrained "
            "tinted-translucency washes. Any text in a clean geometric grotesque "
            "sans-serif. Calm, modern, professional — uncluttered, not decorative."
        ),
    },
    "sapphireos-dark": {
        "desc": "Qubit SapphireOS — dark facet, charcoal canvas + bright sapphire.",
        "fragment": (
            " Rendered in the SapphireOS dark brand style: a premium editorial "
            "aesthetic on a deep cool charcoal background (#1F2227, #06070B). "
            "Bright sapphire-blue accent #4F9EDB on cool-steel surfaces (#293844) "
            "with light ink (#E8EEF2); restrained teal #3CA7C2 and brass highlights. "
            "Generous rounded corners, soft glows, abundant negative space, thin "
            "translucent rule lines and subtle tinted washes. Any text in a clean "
            "geometric grotesque sans-serif. Calm, modern, professional — "
            "uncluttered, not decorative."
        ),
    },
}


def lookup_vars(profile: str) -> list[str]:
    """Ordered, de-duplicated list of var names to check for the key."""
    seen: dict[str, None] = {}
    for var in (profile, "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        seen.setdefault(var, None)
    return list(seen)


def load_key(profile: str) -> str | None:
    """Find the API key in env first, then the credentials file."""
    lookups = lookup_vars(profile)
    for var in lookups:
        val = os.environ.get(var)
        if val and val.strip():
            return val.strip()
    if CONFIG_FILE.exists():
        data: dict[str, str] = {}
        for line in CONFIG_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            data[k.strip()] = v.strip().strip('"').strip("'")
        for var in lookups:
            if data.get(var):
                return data[var]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate/edit images with Nano Banana (Gemini).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("prompt", nargs="?", help="Text prompt / subject (or use -p).")
    ap.add_argument("-p", "--prompt", dest="prompt_flag", help="Text prompt / subject.")
    ap.add_argument("-P", "--preset", help="Archetype preset (see --list-presets).")
    ap.add_argument("-S", "--style", default=None,
                    help="Brand style: sapphireos, sapphireos-dark, or none. "
                         "Slide presets default to sapphireos; use 'none' to opt out.")
    ap.add_argument("-o", "--out", help="Output path (default: ./nano-banana.png).")
    ap.add_argument("-m", "--model", default=None,
                    help="Model id or alias: flash, pro, nano-banana (default: flash or preset).")
    ap.add_argument("-a", "--aspect", default=None,
                    help="Aspect ratio: 1:1 16:9 9:16 3:2 2:3 4:3 3:4 4:5 5:4 21:9 (default 1:1 or preset).")
    ap.add_argument("-s", "--size", default=None,
                    help="Resolution: 512 1K 2K 4K (512 = flash only; default 2K or preset).")
    ap.add_argument("-i", "--input", action="append", default=[],
                    help="Input image for editing/reference. Repeatable (up to ~14).")
    ap.add_argument("--profile", default="GEMINI_API_KEY",
                    help="Env/credentials var to read the key from (e.g. SLIDES_GEMINI_API_KEY).")
    ap.add_argument("--list-presets", action="store_true", help="List archetype presets and exit.")
    ap.add_argument("--selftest", action="store_true",
                    help="Verify the SDK installs/imports, then exit (no API call).")
    args = ap.parse_args()

    if args.list_presets:
        print("Archetype presets (use with -P/--preset, fill the subject with -p):\n")
        for name, spec in PRESETS.items():
            brand = f"  +{DEFAULT_BRAND_STYLE} by default" if spec.get("slide") else ""
            print(f"  {name:<14} [{spec['model']}, {spec['aspect']}, {spec['size']}]  {spec['desc']}{brand}")
        print("\nBrand styles (use with -S/--style, or 'none' to opt out):\n")
        for name, spec in STYLES.items():
            print(f"  {name:<16} {spec['desc']}")
        return 0

    if args.selftest:
        import google.genai  # noqa: F401
        print("OK: google-genai imported successfully")
        return 0

    # Resolve preset (if any) and compose the final prompt.
    preset = None
    if args.preset:
        preset = PRESETS.get(args.preset)
        if preset is None:
            ap.error(f"unknown preset '{args.preset}'. Options: {', '.join(PRESETS)}")

    subject = args.prompt_flag or args.prompt
    if preset:
        if not subject:
            ap.error(f"preset '{args.preset}' needs a subject via -p (e.g. -P {args.preset} -p \"...\")")
        prompt = preset["template"].replace("{prompt}", subject)
    else:
        prompt = subject
    if not prompt and not args.input:
        ap.error("a prompt is required (positional or -p)")

    # Brand style: explicit --style wins; else slide presets default to the brand.
    style_name = args.style
    if style_name is None and preset and preset.get("slide"):
        style_name = DEFAULT_BRAND_STYLE
    if style_name in ("none", "off", "no", ""):
        style_name = None
    if style_name:
        if style_name not in STYLES:
            ap.error(f"unknown style '{style_name}'. Options: {', '.join(STYLES)}, none")
        prompt = (prompt or "") + STYLES[style_name]["fragment"]
        print(f"[style: {style_name}]", file=sys.stderr)

    # Flag > preset > built-in default.
    args.model = args.model or (preset and preset["model"]) or DEFAULT_MODEL
    args.aspect = args.aspect or (preset and preset["aspect"]) or "1:1"
    args.size = args.size or (preset and preset["size"]) or "2K"

    key = load_key(args.profile)
    if not key:
        tried = ", ".join("$" + v for v in lookup_vars(args.profile))
        print(
            "error: no API key found.\n"
            f"  Looked for {tried},\n"
            f"  then {CONFIG_FILE}\n"
            f"  Guided setup (run it in your terminal):  {SETUP_SCRIPT}\n"
            "  Or set it manually — get a key at https://aistudio.google.com/apikey then:\n"
            f"    printf 'GEMINI_API_KEY=%s\\n' YOUR_KEY > {CONFIG_FILE} && chmod 600 {CONFIG_FILE}",
            file=sys.stderr,
        )
        return 2

    model = MODEL_ALIASES.get(args.model, args.model)

    from google import genai
    from google.genai import types

    contents: list = []
    for ip in args.input:
        p = Path(ip).expanduser()
        if not p.exists():
            print(f"error: input image not found: {ip}", file=sys.stderr)
            return 2
        mime = mimetypes.guess_type(p.name)[0] or "image/png"
        contents.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))
    if prompt:
        contents.append(prompt)

    client = genai.Client(api_key=key)
    try:
        resp = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=args.aspect,
                    image_size=args.size,
                ),
            ),
        )
    except Exception as e:  # noqa: BLE001 - surface a clean message to the agent
        msg = str(e)
        print(f"error: generation failed: {msg}", file=sys.stderr)
        if "NOT_FOUND" in msg or "not found" in msg or "404" in msg:
            print(f"hint: model '{model}' may need a '-preview' suffix during rollout; "
                  "try -m gemini-3.1-flash-image-preview", file=sys.stderr)
        return 1

    images: list[bytes] = []
    texts: list[str] = []
    cand = resp.candidates[0] if resp.candidates else None
    parts = (cand.content.parts if cand and cand.content and cand.content.parts else [])
    for part in parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            images.append(inline.data)
        elif getattr(part, "text", None):
            texts.append(part.text)

    if not images:
        print("error: no image returned.", file=sys.stderr)
        if texts:
            print("model said:", " ".join(texts), file=sys.stderr)
        if cand and getattr(cand, "finish_reason", None):
            print(f"finish_reason: {cand.finish_reason}", file=sys.stderr)
        return 1

    # Resolve output path(s).
    if args.out and len(images) == 1:
        paths = [Path(args.out).expanduser()]
    else:
        base = Path(args.out).expanduser() if args.out else Path.cwd() / "nano-banana.png"
        stem, suf = base.stem, (base.suffix or ".png")
        paths = [base.with_name(f"{stem}-{i + 1}{suf}") for i in range(len(images))]

    # Nano Banana may return JPEG or PNG bytes regardless of the requested
    # extension (the Gemini Developer API ignores output_mime_type), so re-encode
    # to match the extension the user asked for.
    import io
    from PIL import Image

    for data, path in zip(images, paths):
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            img = Image.open(io.BytesIO(data))
            if path.suffix.lower() in (".jpg", ".jpeg") and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(path)
        except Exception:  # noqa: BLE001 - fall back to raw bytes if re-encode fails
            path.write_bytes(data)
        print(f"saved {path}  ({path.stat().st_size // 1024} KB)")
    if texts:
        print("note:", " ".join(texts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
