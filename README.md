# Skills

A collection of [Claude Code](https://claude.com/claude-code) skills I use and
share. Each folder is a self-contained skill with its own `SKILL.md` (what Claude
reads) and `README.md` (for humans).

## Skills

| Skill | What it does |
|-------|--------------|
| [`generate-image`](./generate-image) | Generate & edit images, illustrations, icons, diagrams, avatars, and product shots from natural language via Google's Nano Banana (Gemini) image models. Brand-styled archetype presets + guided key setup. |
| [`100-sources`](./100-sources) | Topic-agnostic research engine — scans 100–1000 real sources, distils a tiered principle set, and renders an answer-first narrative as markdown + HTML report + ~20-slide deck. Self-improving via a learnings loop. |
| [`climatepulse`](./climatepulse) | Generate a personalised daily climate / energy / sustainability intelligence digest into a local Markdown wiki — deterministic RSS fetch, dedup, score/tag, synthesised briefing, self-tuning from feedback. |

## Installing a skill

Copy the skill folder into your Claude Code skills directory:

```bash
cp -R generate-image ~/.claude/skills/
```

Then follow that skill's own `README.md` for any one-time setup (API keys, etc.).
Claude Code auto-discovers skills in `~/.claude/skills/` and loads them when the
`description` in their `SKILL.md` matches what you're doing.

> Tip: to avoid drift, you can symlink instead of copy —
> `ln -s "$PWD/generate-image" ~/.claude/skills/generate-image`.

## Notes

- `climatepulse` previously lived in its own repo
  ([`Nicegarrry/climatepulse-skill`](https://github.com/Nicegarrry/climatepulse-skill),
  now archived) — this collection is its home.
- No secrets live in this repo — skills read API keys from local config files /
  environment variables at runtime, never from committed files.

## License

[MIT](./LICENSE) © Nick Pinidiya
