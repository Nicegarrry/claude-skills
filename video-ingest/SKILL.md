---
name: video-ingest
description: Retired. Video ingest now lives in the ingest-anything skill (it handles video links plus web pages, PDFs, docs and data sources). Use ingest-anything instead.
---

# video-ingest (retired)

Merged into **ingest-anything** on 2026-10-14. Use that skill: `ingest scrape <video-url>` (or `ingest video <url>`) runs the same pipeline as before (yt-dlp metadata → youtube-transcript-api → captions → local whisper → frames), with the same vault filing flow.
