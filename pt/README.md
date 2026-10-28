# pt

A Claude Code skill that turns Claude into a text-message personal trainer. You text sets as you
lift (`bench 60x8,8 @8`), it replies with the next target, and at the end it logs the session,
updates a progress page and renders a phone-sized dashboard.

> Claude reads `SKILL.md`; this README is for humans.

## What it does

- **Onboarding**: asks about you (age range, training age, injuries, lifts to avoid), imports your
  existing data (Strong or Hevy CSV, or pasted sessions), your goal (strength, hypertrophy, fat
  loss, general, event) and your typical week (days, session length, equipment, split, running).
  It generates a program from that and waits for your OK before the first session.
- **Coaching**: double progression in each lift's rep range, stall handling, e1RM-based loads after
  breaks or rep-range changes, deload triggers, weekly hard sets per muscle, running load before leg
  days, swaps within the same movement pattern that carry your load across.
- **Logging**: terse text syntax, kg or lb, per-side, timed, bodyweight and assisted sets, RPE.
- **Outputs**: `progress.md` (lifts, trends, stalls, next targets, weekly sets, peaks) and a
  dashboard PNG per session.

All maths is deterministic Python in `bin/pt`; Claude only talks to you and runs the CLI.

## Install

```bash
cp -R pt ~/.claude/skills/
pip install "pillow>=10.1"   # only for the dashboard PNG
alias pt="python3 ~/.claude/skills/pt/bin/pt"   # optional, for running it yourself
```

Python 3.9+, macOS or Linux. Data lives in `~/.pt/` by default; set `PT_DATA` or pass `--data <dir>` to put it
elsewhere (a synced folder works well). Nothing leaves your machine.

## Use

In Claude Code, say `/pt` or "set me up with a training program". First run walks you through
onboarding. After that, `/pt` at the gym plans today's session; text your sets; say `done`.

Run it from your phone by pairing Claude Code with a chat channel, or just use it in a terminal.

## CLI

```bash
pt onboard --template          # answers JSON to fill in
pt onboard answers.json        # profile + generated program
pt onboard --confirm           # accept it
pt import-strong strong.csv    # or: pt import-hevy hevy.csv
pt plan                        # today's session
pt add "squat 80x6,6,5 @8"
pt done
```

## Tests

```bash
python3 -m unittest discover -s pt/tests
```

Not medical advice. Pain rules stop a lift; they don't diagnose anything.
