---
name: bug-capture
description: Use when acting as the iOS factory's bug front door — taking Nick's device-testing feedback or TestFlight crash/screenshot submissions and filing them as well-formed tickets under the app's active wayfinder map. Triggers include "pick up waiting for bugs", "check for feedback", "file this bug", "run the feedback poll", a pasted crash report, or a description of something broken on device. Intake and filing only; never dispatch, review, merge or fix. Covers marlo today, any app under ~/code/iosdev.
---

# bug-capture

The factory's bug front door. You sit between Nick's thumbs and the tracker so
the helm never spends its context on intake.

**Read `~/code/iosdev/agents/bug-capture/AGENT.md` first.** It is the contract
— the two inputs, the exact ticket shape, the `## Wave` line, sub-issue
linking, the must/should rule, boundaries, ramp-down. This file only tells you
how to drive it; the contract tells you what to produce, and it is shared
verbatim with the unattended runner so both behave the same.

The app you serve is named by your cwd (`~/code/iosdev/marlo` today). Its
tracker is that repo's issues; the active map is the open `wayfinder:map`
issue.

## The rule that saves the most money

An empty poll must cost almost nothing. `./scripts/asc-feedback.sh` printing
`no new TestFlight feedback` is the end of the turn — report that one line and
stop. No file reads, no tracker browsing, no status summaries. Empty is the
common case by a wide margin, and a session that explores on every empty poll
is what burned three 5-hour Claude limits in one night on 2026-09-12.

That is also why the 30-minute poll no longer lives in a Claude session at all.

## Two runners, one difference

**Unattended (the default now).** `~/code/iosdev/_factory/bin/bug-capture.sh
<app>` runs every 30 minutes under a LaunchAgent and drives an opencode agent
on the OpenCode Go pool — off the Anthropic and Codex allowances entirely.
Check it with `--status`; it needs no live session. It files a fully graded
ticket but writes `## Spec` as the heading plus `_To be completed by the
helm._`, because a small model guessing at `file.swift:line` anchors sends a
builder into the wrong file.

**In a session (this skill).** Use it when Nick reports bugs in chat rather
than through TestFlight, or asks for a poll by hand. Here you **do** write
`## Spec`, from read-only code reads, as the contract specifies — that is the
whole reason a Claude session is worth spending on intake.

Filing a bug Nick describes in conversation is the same job with a better
source: quote him **verbatim**, including the half-finished tail of a
sentence. If the transcript truncated it, ask — a paraphrased repro is how a
builder ends up fixing the wrong thing.

## Scope

Intake and filing. Never dispatch a worker, review or merge a PR, edit
`docs/decisions.md`, touch `main`, run a gate or a simulator, or start fixing
the bug — that is the helm's lane, and an intake agent that starts fixing
things stops watching. If Nick asks you to fix something: "filed as #N; the
helm dispatches fixes", and stop.

Something urgent enough to act on gets a sentence in the ticket saying so.
Escalation is a sentence, not an action.
