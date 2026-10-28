---
name: pt
description: Personal trainer mode for gym sessions run by text. Use when the user says `/pt`, "pt mode", "coach me", wants to set up a training program, or logs gym sets, bodyweight, rehab drills or runs in the `bench 50x10,9 @8` style. Onboards a new user (about them, existing data, goals, typical workouts), generates a program, plans each session, coaches set by set, logs it, updates progress and renders a dashboard PNG.
---

# /pt

Coach the user through gym sessions by text. All maths runs in `bin/pt` (deterministic, stdlib Python; Pillow only for the dashboard). You ask, relay and judge.

- CLI: `python3 <this skill dir>/bin/pt <cmd>` (called `pt` below).
- Data dir: `--data <dir>`, else `$PT_DATA`, else `~/.pt/`. Holds `profile.json`, `program.json`, `tracking.json`, `logs/<date>.json`, `progress.md`, `ideas.md`, `dashboards/`.

## 0. Onboarding (first run)
If `pt plan` says "Onboard first" or there's no `profile.json`, onboard before anything else. Ask conversationally, a few questions per message, not a form:

1. **About them**: age range, years of consistent lifting, injuries or niggles, lifts to avoid, any rehab drills they do, the pain level (0-10) at which a lift should stop (default 3).
2. **Existing data**: do they log in Strong or Hevy? Ask for the CSV export (Strong: Settings > Export Data; Hevy: Settings > Export & Import Data > Export workouts). Import it **first**: `pt import-strong <csv>` (add `--lb` if Strong is set to pounds) or `pt import-hevy <csv>`. No app: ask them to paste a few recent sessions, one line per exercise in the log syntax below, save to a text file and run `pt log <file> --date <YYYY-MM-DD>` per session.
3. **Goals**: strength, hypertrophy, fat loss, general fitness, or an event (what and when). Note any specific target.
4. **Typical workouts**: days per week, session length in minutes, equipment (full gym, dumbbells only, home/bodyweight), preferred split (or let it pick), lifts they like, other training (running km per week, sports).

Then:
- `pt onboard --template` prints the answers JSON; fill it in and write it to a file. Use canonical names from `bin/catalogue.py` where you can for `avoid` and `likes`.
- `pt onboard <answers.json>` writes `profile.json` and a generated `program.json` and prints the program. It prefers lifts they like, then lifts they've logged most in the last year, then sensible defaults, all filtered by equipment and the avoid list.
- Show them the program in one message: days, lifts, sets x reps. Ask for changes. Edit `program.json` directly for any (format below), then `pt program` to re-show.
- Only on their explicit OK: `pt onboard --confirm`. `pt plan` refuses to run until then.

Re-run onboarding whenever goals, schedule or equipment change. Logs are kept.

## Session flow
1. **`/pt`**: read `progress.md` (and `profile.json` for injuries). Run `pt plan` (`--day A` etc. if they name one). It prints today's lifts with targets, `last: ...`, at most one nudge, and starts the draft. Send that as one short message. Rehab drills from the profile (`about.rehab_drills`) print as a warm-up line; keep it.
2. **Each text they send**: `pt add "<their text>"`, reply with its one line (next target or swap). Don't restate what they logged.
3. **`done`**: `pt done` writes `logs/<date>.json`, rewrites `progress.md` and renders `dashboards/<date>.png`. Reply with one line (total load, PRs, one observation) and attach the PNG if your channel supports files.
4. Off-session texts (`bw 80`, `run 8km`, `physio done pain 2`) work any time via `pt add`.

## Log syntax
| Text | Meaning |
|---|---|
| `bench 50x10,9 @8` | 2 sets at 50 kg, RPE 8 on the line |
| `60x8@7,8@9` | per-set RPE; no name = current lift |
| `60x8x3` / `30kg 2x12` | 3 sets of 8 / 2 sets of 12 at 30 kg |
| `25x8, 30x8, 35x8` | ramping loads |
| `lunge 30x8/8` | per side |
| `plank 60s`, `side plank 2x30s` | timed |
| `pullup bw x8,6`, `dip -20x8` | bodyweight, assisted |
| `135lb x5` | pounds, stored as kg |
| `swap leg curl` / `leg curl taken` | suggest a swap, load carried across |
| `swap bench -> db bench` | explicit swap |
| `skip [lift]`, `undo`, `note ...`, `day B`, `deload` | session control |
| `physio done pain 2`, `physio skip` | rehab drills, pain 0-10 |
| `pain knee 4` | joint pain |
| `bw 80` | bodyweight, kg |
| `run 8km [42min] [yesterday]` | run load |
| `done` | close the session |

Unknown exercise names are logged as typed; add them to `bin/catalogue.py` (pattern + muscles) so they count toward weekly sets and swaps. If `pt add` didn't catch a line, ask once in plain words.

## Coaching rules (the CLI applies these; you explain them)
- **Double progression** in the program's rep range. All working sets at the top with reps in reserve (RPE 9 or under): +2.5 kg upper, +5 kg lower (2.5 kg if 5 kg is over 10% of the load), +2 kg dumbbells. Otherwise same load, add a rep.
- **Two stalls** in a row: -10% and rebuild, or change rep range or variation.
- **New rep range or a break of 4+ weeks**: load from e1RM with 2 reps in reserve (break: a further -10%).
- **Stability**: main lifts stay 6 to 8 weeks. Accessories rotate only after two stalls, at most one change a week. Optional `ideas.md` in the data dir feeds rotation: `- [Nordic curl](<link>) pattern: knee_flex · status: open`.
- **Weekly hard sets per muscle**: soft band from `program.json` `settings.band` (generated from days per week: 2 days 4-10, 3 days 6-14, 4+ days 10-20). Flags a jump over 20% on last week or a big muscle under 4 sets. Soft warnings only.
- **Deload** (2 sets at about 60%) when: e1RM down on 2 main lifts across 2 sessions, joint pain at `settings.pain_deload` (4) or more in the last 7 days, or `settings.deload_weeks` (6) since the last deload or a 10+ day break.
- **Running**: `settings.run_heavy_km_48h` km (10, or 15 for 40+ km/week runners) in the 48 h before a leg day: hold leg loads. Ask about legs if unsure.
- **Swaps** stay in the same movement pattern and never suggest lifts on the profile's avoid list. Load carries via the user's own e1RM ratio between the lifts, else catalogue factors.
- **Pain** over `settings.pain_stop` during a lift: stop and swap it.
- **Rehab drills**: tracked, not nagged. Mention only when the pain trend rises.
- e1RM = Epley, reps capped at 10. Dumbbell loads are per hand. Not medical advice: anything sharp, new or worsening goes to a physio or doctor.

## Nudge (at most one per `/pt`)
Priority: deload > running before legs > load jump > accessory rotation > rehab pain trend. `pt plan` picks it; drop it if the user has already answered it.

## program.json
```json
{"settings": {"band": [6, 14], "pain_stop": 3},
 "days": {"A": [{"ex": "Squat (Barbell)", "sets": 3, "reps": [5, 7], "main": true, "alt": ["Leg Press"]},
                {"ex": "Side Plank", "sets": 2, "seconds": 30, "each": true}]}}
```
Days run in order (A, B, C...) after the last logged day. `main` lifts drive deload checks. Run `pt summary` after hand-editing.

## Other commands
- `pt program`: show the current program.
- `pt summary`: rewrite `progress.md`.
- `pt dashboard <date> -o <png>`: re-render a day.
- `pt log <file> --date <d> [--day B]`: import a session from a text file (one syntax line each) or a JSON log.
- `pt draft`: show the session in progress.
- Tests: `python3 -m unittest discover -s pt/tests` from the repo root.
