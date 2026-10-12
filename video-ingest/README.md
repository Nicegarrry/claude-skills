# youtube-ingest

Capture a YouTube video as a permanent source plus a structured AI digest, with reverse-links back
into a compiled markdown wiki. Use when a YouTube URL is dropped in chat, "ingest this video", or a
digest of something being watched is wanted.

The skill (`SKILL.md`) pulls metadata + transcript via `yt-dlp`, saves the raw to the vault's
`_sources/briefings/youtube/`, and writes an AI-summary note to `_wiki/ai-ingested/` with cross-links
to relevant domain pages.

**Shared layer.** Moved into `~/code/skills` (2026-07-01) as a shared non-coding skill both the
personal-admin (sidekick) and Head-of-Engineering surfaces can install. Output paths currently follow
the sidekick vault layout; when invoked from another surface, target that surface's `_sources/` +
`_wiki/ai-ingested/`. (Fuller path-parameterisation is a small follow-up if needed.)

## Install

```bash
cp -R youtube-ingest ~/.claude/skills/   # or symlink to avoid drift
```

Requires `yt-dlp` on PATH.
