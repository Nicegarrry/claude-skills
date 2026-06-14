# Nano Banana Prompting Guide

Distilled from Google's official Nano Banana prompting guidance. Load this when a
generation needs more than a one-line prompt — posters, product shots, character
consistency, infographics, or editing.

## The five principles

1. **Be specific.** Concrete subject, setting, lighting, composition. Vague in → generic out.
2. **Positive framing.** Say what *should* be there ("an empty plaza"), never what shouldn't ("no people").
3. **Direct the camera.** Photographic/cinematic terms: "low-angle", "aerial", "macro", "wide-angle", "shallow depth of field (f/1.8)".
4. **Iterate conversationally.** Generate, then refine with a follow-up edit (`-i`) rather than rewriting from scratch.
5. **Start with a strong verb.** "Generate…", "Create…", "Transform…".

## Template — text-to-image

`[Subject] + [Action] + [Location/context] + [Composition] + [Style]`

> A striking fashion model wearing a tailored brown dress, sleek boots, and holding a
> structured handbag. Posing with a confident, statuesque stance, slightly turned.
> A seamless, deep cherry-red studio backdrop. Medium-full shot, center-framed.
> Fashion-magazine editorial, shot on medium-format analog film, pronounced grain,
> high saturation, cinematic lighting.

## Template — with reference images (`-i`)

`[Reference images] + [Relationship instruction] + [New scenario]`

> Using the attached napkin sketch as the structure and the attached fabric sample as
> the texture, transform this into a high-fidelity 3D armchair render. Place it in a
> sun-drenched, minimalist living room.

## Creative-director levers

- **Lighting:** "three-point softbox setup", "chiaroscuro, harsh high contrast", "golden-hour backlighting, long shadows".
- **Camera & lens:** name hardware for a look — GoPro (immersive action), Fujifilm (authentic color), disposable camera (nostalgic). "low-angle, f/1.8 shallow DoF", "macro lens" for detail.
- **Color grade / film stock:** "1980s color film, slightly grainy", "cinematic muted teal grade".
- **Materiality:** specify materials — not "suit jacket" but "navy-blue tweed"; not "armor" but "ornate elven plate etched with silver-leaf patterns".

## Text inside images

Use `-m pro` for anything text-heavy (sharper typography, ~94% accuracy).

1. **Quote the exact words:** `the words "URBAN EXPLORER"`.
2. **Name the font/style:** `bold white sans-serif`, `flowing Brush Script`, `heavy blocky Impact`.
3. **Localize:** write the prompt in English, then "…translate the text into Korean and Arabic".
4. **Text-first hack:** decide the copy in conversation first, then generate the image with that finalized text.

> A high-end glossy beauty shot of a minimalist nude-coloured moisturizer jar. Top line:
> the word "GLOW" in a flowing elegant Brush Script. Middle line: "10% OFF" in heavy
> blocky Impact. Bottom line: "Your First Order" in thin minimalist Century Gothic.

Typographic cut-out trick:

> A typographic poster, solid black background, bold letters spell "NEW YORK" filling the
> center. The text acts as a cut-out window: a photo of the NYC skyline is visible ONLY
> inside the letterforms.

## Editing (pass the image with `-i`)

- **Be explicit about what to keep.** "Keep the pose and background exactly; change only the jacket to red."
- **Remove/add:** "Remove the man on the left." / "Add a steaming coffee cup on the table."
- **Style transfer:** pass a photo, then "recreate this exact scene as a Van Gogh oil painting."

## Subject / character consistency

Pass a reference image with `-i` and tie new generations to it:

> Using the attached character as reference, keep the same face, hair, and outfit. Show
> them now sitting at a café reading a newspaper, soft morning light.

Flash takes up to 10 object + 4 character references; Pro up to 6 object + 5 character.

## Resolution & aspect quick picks

- **Icons / avatars / stickers:** `-a 1:1 -s 1K`.
- **Slides / hero banners:** `-a 16:9 -s 2K` (bump `4K` only for print).
- **Phone / story:** `-a 9:16`.
- **Posters with text:** `-m pro -s 2K` (or `4K`).

## Gotchas

- Keyword lists underperform full sentences — always describe a scene.
- Negatives confuse the model — rephrase positively.
- One big change per edit beats five at once; iterate.
- Knowledge cutoff Jan 2025; Pro can pull live facts via Google Search grounding.
