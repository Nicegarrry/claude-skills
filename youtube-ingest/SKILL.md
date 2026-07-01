---
name: youtube-ingest
description: Ingest a YouTube URL — pull metadata + transcript via yt-dlp, save the raw to `_sources/briefings/youtube/`, then write an AI-summary wiki note in `_wiki/ai-ingested/` with cross-links to relevant domain pages. Use when Nick drops a YouTube URL in Discord, mentions "ingest this video", or asks for a digest of something he's watching.
---

# youtube-ingest

Capture a YouTube video as a permanent source + a structured AI digest, with reverse-links back into Nick's compiled wiki.

## Inputs

- A YouTube URL (`youtube.com/watch?v=…`, `youtu.be/…`, `youtube.com/shorts/…`).
- Optional Nick context ("listening to this for AI builds work", "for teaching unit 5") — use to bias the cross-link target.

## Prerequisites

```bash
brew list yt-dlp >/dev/null 2>&1 || brew install yt-dlp
```

If `yt-dlp` is missing, install it before running. No Python venv needed — the dedupe parser uses stdlib only.

**If yt-dlp returns "Video unavailable" on first try:** YouTube changes its default extractor frequently. Retry with explicit player clients before giving up:

```bash
yt-dlp ... --extractor-args "youtube:player_client=web,ios,mweb" "$URL"
```

If both attempts fail, **double-check the video ID**. Common cause: `l` (lowercase L) vs `I` (capital i) in the URL — they look identical in most fonts. Confirm by hitting `https://www.youtube.com/oembed?url=<URL>&format=json` — `Not Found` means the ID itself is dead, ask Nick to re-paste.

## Flow

### 1. Pull metadata + transcript

```bash
WORK=$(mktemp -d)
yt-dlp \
  --skip-download \
  --write-auto-sub --write-sub --sub-lang en --convert-subs srt \
  --write-info-json \
  -o "$WORK/%(id)s.%(ext)s" \
  "$URL"
```

Outputs in `$WORK`:
- `<id>.info.json` — title, channel, upload date, duration, description, chapters
- `<id>.en.srt` (or `.en-US.srt`, `.en-auto.srt`) — captions

If no `.srt` file appears, captions are missing — fall through to the Whisper fallback (§3).

### 2. Normalise the transcript

YouTube auto-caption SRT files use a **rolling-display format**: each cue's text appears in the next 1–2 cues again because the caption box scrolls line by line. A naive timestamp-stripper produces text repeated 3x. The parser below dedupes by *first appearance per unique line*, sentence-breaks the result, and stamps `[mm:ss]` markers every ~30s so the digest can cite quotes.

Run with the SRT path passed as `$1` and the output path as `$2`:

```bash
python3 - "$WORK/<id>.en.srt" "$WORK/transcript.txt" << 'PY'
import re, sys, pathlib
src = pathlib.Path(sys.argv[1]).read_text()

cues = []
for block in re.split(r"\n\n+", src.strip()):
    lines = block.strip().split("\n")
    if len(lines) < 2: continue
    m = re.match(r"(\d{2}):(\d{2}):(\d{2})", lines[1])
    if not m: continue
    ts = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    for line in lines[2:]:
        line = line.strip()
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

**Why a parser, not awk/sed:** YouTube ships two distinct caption layouts — pre-recorded ("static") captions where each cue is one chunk of text, and auto-generated ("rolling") captions where each cue overlaps with neighbours. The parser handles both correctly because it dedupes on text content, not on cue position.

### 3. Whisper fallback (only if no captions)

```bash
yt-dlp -x --audio-format mp3 -o "$WORK/audio.%(ext)s" "$URL"
# Local, free:
whisper "$WORK/audio.mp3" --model base.en --output_format txt --output_dir "$WORK"
# Or OpenAI API (~$0.006/min) if local whisper isn't installed.
```

Note in frontmatter `transcript-source: whisper-base.en` so quality is traceable.

### 4. Save the source

Filename: `_sources/briefings/youtube/YYYY-MM/YYYY-MM-DD-<channel-slug>-<title-slug>.md`

```markdown
---
type: source
source-kind: youtube
url: https://www.youtube.com/watch?v=…
video-id: …
channel: …
channel-url: …
title: …
duration: 47:12
published: 2026-04-22
captured: 2026-04-29
transcript-source: youtube-auto-captions  # or: whisper-base.en
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

### 5. Analyse and write the AI-ingested wiki note

Filename: `_wiki/ai-ingested/YYYY-MM-DD-<title-slug>.md`

```markdown
---
type: ai-ingested
source: _sources/briefings/youtube/2026-04/2026-04-29-…md
source-kind: youtube
url: https://www.youtube.com/watch?v=…
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

### 6. Cross-link into compiled wiki

For every entity mentioned (person, company, framework, project), follow the wiki-pages skill rules:

- People → `_wiki/people/firstname-lastname.md`. Create stub if missing. Add a one-line timeline entry: `2026-04-29: Cited in [[ai-ingested/2026-04-29-…]] — <one-line takeaway>.`
- Companies → same pattern in `_wiki/companies/`.
- Projects (`04_AI builds/*`, `05_teaching/*`): if the digest changes a decision or adds a useful framework, append a timeline entry on the project page linking to the ai-ingested note. **Do not** rewrite compiled truth from a video alone — flag instead.

Match-by-alias before creating any new entity (see `wiki-pages.md`). Ambiguous match → flag, don't guess.

### 6b. Reflect into `reflections.md` (when relevant)

If the digest contains an insight that bears on **sidekick's own architecture** (folder structure, memory addressing, skill loading, dream cadence, the sources/wiki/outputs triad, agent-vs-routing model, etc.), do not bury it in the digest:

- Read `reflections.md` at the vault root.
- If the insight **validates** an existing Confirmed bet, append a one-line "Validated:" entry linking back to the digest.
- If the insight **raises a new architectural question**, draft a `proposed:` entry under **Under consideration** with: the question, what would push it to Confirmed, what would push it to Decided-not-to-do, and a link to the digest.
- If the insight **directly contradicts** a Confirmed bet or a Decided-not-to-do entry, flag in the Discord reply and the digest's "Open questions" — do **not** auto-edit `reflections.md` against an existing decision.
- Do not move entries between sections — only Nick promotes/demotes.

This is how external evidence (videos, articles, talks) accumulates into sidekick's self-thinking instead of evaporating after the digest is written. Dream sweeps `reflections.md` nightly anyway; this just gets the evidence in the right section on first contact.

### 7. Discord confirmation

Always reply in `#inbox` — never auto-post the digest to `#daily` or any domain channel. `#inbox` is the single confirmation surface so Nick can correct on the spot.

> Ingested `<title>` (`<duration>`, `<channel>`). Source filed; digest at `_wiki/ai-ingested/<filename>.md`. Cross-linked: `<n>` people, `<n>` projects.

Append flags inline: missing captions, ambiguous entity matches, contradictions with compiled truth.

## Failure modes

- **No captions and Whisper unavailable** → save the source with metadata only, mark `transcript-source: none`, write a minimal ai-ingested note flagging "transcript pending". Do not invent content.
- **Age-restricted / region-blocked / private video** → `yt-dlp` exits non-zero. File a stub source with the URL + error, ping Nick.
- **Live stream still in progress** → skip; ask Nick to re-drop after the stream ends.
- **Non-English video** → use `--sub-lang <lang>,en` and translate in the digest only if Nick has asked for one. Otherwise file as source and flag.

## When NOT to ingest

- Music videos / non-talk content — file as source only, skip digest.
- Videos under ~3 minutes — usually not worth a wiki note; ask Nick first.
- Anything Nick flags as casual viewing rather than research.

## Logging

This skill is part of live capture, not a routine — no separate log file. Discord reply + the source/wiki files are the trace. The next `dream` run will sweep `_wiki/ai-ingested/` for cross-link gaps.
