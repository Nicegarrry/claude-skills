---
name: video-ingest
description: Ingest any video link (YouTube, Instagram reels, TikTok, X, Vimeo, Facebook, Loom, LinkedIn posts) — pull metadata + transcript (captions, else local whisper, else frames for silent video), save the raw to `_sources/briefings/video/`, then write an AI-summary wiki note in `_wiki/ai-ingested/` with cross-links to relevant domain pages. Use when Nick drops a video URL in Discord, mentions "ingest this video/reel", or asks for a digest of something he's watching.
---

# video-ingest

Capture a video as a permanent source + a structured AI digest, with reverse-links back into Nick's compiled wiki. Keep the transcript, caption and frames, never the video. Audio is downloaded only to transcribe locally, then deleted.

## Inputs

- A video URL yt-dlp can read: YouTube (`watch`, `youtu.be`, `shorts`), Instagram reels/posts, TikTok, X/Twitter, Vimeo, Facebook/`fb.watch`, Loom, LinkedIn posts.
- Optional Nick context ("listening to this for AI builds work", "for teaching unit 5") — use to bias the cross-link target.

## Prerequisites

```bash
brew upgrade yt-dlp 2>/dev/null || brew install yt-dlp   # stale yt-dlp breaks often
command -v uvx >/dev/null || brew install uv
ffmpeg -version >/dev/null 2>&1 || brew reinstall ffmpeg   # brew updates can break its dylibs
command -v whisper >/dev/null || brew install openai-whisper   # models cache in ~/.cache/whisper
```

The dedupe parser reads SRT or VTT, stdlib only.

**Login walls** (common on Instagram: "login required" or "empty media response"): add `--cookies-from-browser chrome` to every yt-dlp call. Private accounts need Chrome signed in to an account that can see them.

**YouTube "Video unavailable":** retry with `--extractor-args "youtube:player_client=web,ios,mweb"`. If that fails, **double-check the video ID** (`l` vs `I` look identical). `https://www.youtube.com/oembed?url=<URL>&format=json` returning `Not Found` means the ID is dead; ask Nick to re-paste.

## Flow

### 1. Pull metadata + transcript

```bash
WORK=$(mktemp -d)
yt-dlp --skip-download --write-info-json -o "$WORK/v.%(ext)s" "$URL"   # metadata only
```

`v.info.json` has title, uploader, upload date, duration, description (the post caption on Instagram/TikTok/X), chapters.

Transcript, first that works:

- **A, YouTube only:** `uvx --from youtube-transcript-api youtube_transcript_api "<11-char id>" --languages en --format srt > "$WORK/v.srt"`. yt-dlp's YouTube caption URL is often rate-limited (HTTP 429); this endpoint is not.
- **B, site captions:** `yt-dlp --skip-download --write-auto-sub --write-sub --sub-lang en -o "$WORK/v.%(ext)s" "$URL"` gives `v.en.vtt`. On YouTube, if 429, retry once with `--cookies-from-browser chrome`.
- **C, local whisper** (no captions; reels and TikToks usually have none):
  ```bash
  yt-dlp -f bestaudio -x --audio-format m4a -o "$WORK/a.%(ext)s" "$URL"
  whisper "$WORK/a.m4a" --model small.en --output_format srt --output_dir "$WORK" && rm "$WORK/a.m4a"
  ```
  Gives `a.srt` (a 60s reel takes under a minute). Non-English: `--model small`. Over 60 minutes: ask Nick first.

### 1b. Frames for little or no speech

Music over on-screen text, a product demo, or a short with a thin transcript: pull frames and read them as images.

```bash
yt-dlp -f "best[height<=720]/best" -o "$WORK/v.mp4" "$URL"
ffmpeg -loglevel error -i "$WORK/v.mp4" -vf "fps=1/5,scale=720:-1" -frames:v 8 "$WORK/f%02d.jpg" && rm "$WORK/v.mp4"
```

Note on-screen text and what is shown, cited as `[frame N, ~mm:ss]`.

### 2. Normalise the transcript

Auto-caption files (YouTube especially) use a **rolling-display format**: each cue's text appears in the next 1–2 cues again because the caption box scrolls line by line. A naive timestamp-stripper produces text repeated 3x. The parser below dedupes by *first appearance per unique line*, sentence-breaks the result, and stamps `[mm:ss]` markers every ~30s so the digest can cite quotes.

Run with the SRT path passed as `$1` and the output path as `$2`:

```bash
python3 - "$WORK/<v.srt | v.en.vtt | a.srt>" "$WORK/transcript.txt" << 'PY'
import re, sys, pathlib
src = pathlib.Path(sys.argv[1]).read_text()

cues = []
for block in re.split(r"\n\n+", src.strip()):
    lines = block.strip().split("\n")
    # SRT has an index line before the timing line; VTT does not.
    i = next((i for i, l in enumerate(lines[:2]) if "-->" in l), None)
    if i is None: continue
    m = re.match(r"(?:(\d{2}):)?(\d{2}):(\d{2})", lines[i])
    if not m: continue
    ts = int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    for line in lines[i + 1:]:
        line = re.sub(r"<[^>]+>", "", line).strip()
        if line:
            cues.append((ts, line))

# Dedupe by first appearance per unique line (kills the rolling-caption triplication).
seen = {}
ordered = []
for ts, line in cues:
    if line not in seen:
        seen[line] = ts
        ordered.append((ts, line))

# Stitch into prose, marking timestamps every ~30s at sentence boundaries.
text, ts_at = "", []
for ts, line in ordered:
    if text and not text.endswith(" "):
        text += " "
    ts_at.append((len(text), ts))
    text += line

sentences = re.split(r"(?<=[.!?])\s+", text)
out, last_marked, char_pos = [], -1000, 0
for sent in sentences:
    ts = 0
    for cp, t in ts_at:
        if cp <= char_pos:
            ts = t
        else:
            break
    if ts - last_marked >= 30:
        mm, ss = divmod(ts, 60)
        out.append(f"\n\n[{mm:02d}:{ss:02d}] {sent}")
        last_marked = ts
    else:
        out.append(sent)
    char_pos += len(sent) + 1

prose = " ".join(out).strip()
prose = re.sub(r"\s+\n", "\n", prose)
prose = re.sub(r" {2,}", " ", prose)
pathlib.Path(sys.argv[2]).write_text(prose)
PY
```

**Why a parser, not awk/sed:** caption files come in two distinct caption layouts — pre-recorded ("static") captions where each cue is one chunk of text, and auto-generated ("rolling") captions where each cue overlaps with neighbours. The parser handles both correctly because it dedupes on text content, not on cue position.

### 3. Save the source

Filename: `_sources/briefings/video/YYYY-MM/YYYY-MM-DD-<uploader-slug>-<title-slug>.md` (older YouTube sources live in `_sources/briefings/youtube/`; leave them)

```markdown
---
type: source
source-kind: video
platform: youtube  # instagram, tiktok, x, vimeo, facebook, loom, linkedin
url: …
video-id: …
channel: …  # uploader
channel-url: …
title: …
duration: 47:12
published: 2026-04-22
captured: 2026-04-29
transcript-source: youtube-transcript-api  # or: captions, whisper-small, frames-only
nick-context: "listening live, AI-native company framing"
---

# <title>

**Channel:** <channel> · **Duration:** 47:12 · **Published:** 2026-04-22

## Description
<from info.json>

## Chapters
- 00:00 — …
- 04:21 — …

## Transcript
[00:00] …
[01:00] …
```

This file is **append-only** like every other source. Never re-edit.

### 4. Analyse and write the AI-ingested wiki note

Filename: `_wiki/ai-ingested/YYYY-MM-DD-<title-slug>.md`

```markdown
---
type: ai-ingested
source: _sources/briefings/video/2026-04/2026-04-29-…md
source-kind: video
platform: youtube
url: …
title: …
channel: …
duration: 47:12
ingested: 2026-04-29
domain: 04_AI builds  # primary domain this maps to
related:
  - "[[04_AI builds/01_climate pulse]]"
  - "[[companies/openai]]"
  - "[[people/some-founder]]"
tags: [ai-native, founders, hiring]
---

# <title> — AI digest

> AI-generated digest. Not Nick's own notes. Cross-check against the source before quoting externally.

## TL;DR
3–5 bullets. The thesis the speaker actually argues, not a topic list.

## Key claims
- Claim → reasoning → timestamp `[mm:ss]`
- Strongest claims first; flag any that contradict Nick's compiled wiki.

## Frameworks / models introduced
Named frameworks, formulas, or rules of thumb worth keeping.

## Notable quotes
> "…verbatim…" — `[mm:ss]`

## Open questions / things to verify
Where the speaker is hand-wavy, contradicts sources Nick has, or makes a strong empirical claim worth fact-checking.

## Relevance to Nick
Why this matters given current projects. Be concrete: which project, which decision, what action.

## Cross-links applied
- Added timeline entry to `[[04_AI builds/01_climate pulse]]` — see line X
- Created stub `[[people/firstname-lastname]]` for the speaker
```

### 5. Cross-link into compiled wiki

For every entity mentioned (person, company, framework, project), follow the wiki-pages skill rules:

- People → `_wiki/people/firstname-lastname.md`. Create stub if missing. Add a one-line timeline entry: `2026-04-29: Cited in [[ai-ingested/2026-04-29-…]] — <one-line takeaway>.`
- Companies → same pattern in `_wiki/companies/`.
- Projects (`04_AI builds/*`, `05_teaching/*`): if the digest changes a decision or adds a useful framework, append a timeline entry on the project page linking to the ai-ingested note. **Do not** rewrite compiled truth from a video alone — flag instead.

Match-by-alias before creating any new entity (see `wiki-pages.md`). Ambiguous match → flag, don't guess.

### 5b. Reflect into `reflections.md` (when relevant)

If the digest contains an insight that bears on **sidekick's own architecture** (folder structure, memory addressing, skill loading, dream cadence, the sources/wiki/outputs triad, agent-vs-routing model, etc.), do not bury it in the digest:

- Read `reflections.md` at the vault root.
- If the insight **validates** an existing Confirmed bet, append a one-line "Validated:" entry linking back to the digest.
- If the insight **raises a new architectural question**, draft a `proposed:` entry under **Under consideration** with: the question, what would push it to Confirmed, what would push it to Decided-not-to-do, and a link to the digest.
- If the insight **directly contradicts** a Confirmed bet or a Decided-not-to-do entry, flag in the Discord reply and the digest's "Open questions" — do **not** auto-edit `reflections.md` against an existing decision.
- Do not move entries between sections — only Nick promotes/demotes.

This is how external evidence (videos, articles, talks) accumulates into sidekick's self-thinking instead of evaporating after the digest is written. Dream sweeps `reflections.md` nightly anyway; this just gets the evidence in the right section on first contact.

### 6. Discord confirmation

Always reply in `#inbox` — never auto-post the digest to `#daily` or any domain channel. `#inbox` is the single confirmation surface so Nick can correct on the spot.

> Ingested `<title>` (`<duration>`, `<channel>`). Source filed; digest at `_wiki/ai-ingested/<filename>.md`. Cross-linked: `<n>` people, `<n>` projects.

Append flags inline: missing captions, ambiguous entity matches, contradictions with compiled truth.

## Failure modes

- **No captions, whisper failed, frames carry nothing** → save the source with metadata only, mark `transcript-source: none`, write a minimal ai-ingested note flagging "transcript pending". Do not invent content.
- **Age-restricted / region-blocked / private video** → `yt-dlp` exits non-zero. Retry with `--cookies-from-browser chrome`; still failing, file a stub source with the URL + error, ping Nick.
- **Live stream still in progress** → skip; ask Nick to re-drop after the stream ends.
- **Non-English video** → `--sub-lang <lang>,en` for captions, `--model small` for whisper; translate in the digest only if Nick has asked for one. Otherwise file as source and flag.

## When NOT to ingest

- Music videos / entertainment with no ideas in it — file as source only, skip digest.
- Short-form (reels, TikToks) — ingest when Nick drops it; keep the digest proportionate (TL;DR + key claims, skip empty sections).
- Anything Nick flags as casual viewing rather than research.

## Logging

This skill is part of live capture, not a routine — no separate log file. Discord reply + the source/wiki files are the trace. The next `dream` run will sweep `_wiki/ai-ingested/` for cross-link gaps.
