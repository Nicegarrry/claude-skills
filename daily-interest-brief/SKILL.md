---
name: daily-interest-brief
description: Create concise, sourced morning-brief updates for any user interest, topic, beat, entity, event, market, sport, policy area, product, or cultural niche. Use when Codex needs to discover the best free sources for a topic, poll RSS or Google News, cross-check with web search, and return 3-5 link-rich bullets plus an optional relevant image for a daily briefing. Assumes no Firecrawl or paid data tools are available.
---

# Daily Interest Brief

## Overview

Turn any user interest into a small, reliable morning-brief module. The output is not a full research memo: it is 3-5 timely bullets with embedded source links, a short source note, and optionally one useful image from today's update.

## Operating Principles

1. Determine the interest precisely enough to search. Use the user's wording when clear; ask one short clarifying question only if the topic is too broad to source responsibly.
2. Prefer deterministic, free sources before model judgment: official RSS feeds, Google News RSS, public schedules/results pages, agency feeds, standards bodies, reputable specialist outlets, and broad wires.
3. Use the model for source choice, relevance ranking, deduplication judgment, and synthesis. Do not invent facts, dates, scores, quotes, or images.
4. Cross-check high-impact or surprising claims against at least two sources when possible.
5. Keep the brief skimmable: 3-5 bullets, each with one clear update and one sentence on why it matters to the user's interest.

## Workflow

### 1. Define the Beat

Extract:
- `interest`: the topic to brief, e.g. "World Cup", "AI regulation", "battery recycling", "Sydney restaurants", "OpenAI".
- `angle`: what the user cares about, if stated, e.g. scores, business impact, policy, science, releases, local relevance.
- `window`: default to overnight / last 24 hours for a morning brief; use a wider window only if the topic is slow-moving.
- `region/language`: infer from the user's request and locale if available.

### 2. Choose Sources

Build a source set before searching deeply:

- Official or primary sources: event organizers, leagues, regulators, company blogs, court/agency pages, standards bodies, databases, project pages.
- Specialist sources: credible beat reporters, industry publications, scientific or policy newsletters, local outlets for local topics.
- Broad discovery: Google News RSS search and general web search for "what changed overnight".
- Social media only as a pointer, not as a sole source, unless the account is official and the claim is low-risk.

For examples:
- World Cup: official tournament site, FIFA/regional confederation feeds, team/league pages, reputable sports live/news outlets, Google News RSS for fixtures/results/injuries.
- Company/product: company newsroom/blog, SEC or exchange filings when relevant, docs/changelog/status pages, reputable business/tech outlets.
- Policy/law: official government or regulator pages, bill trackers, court dockets, specialist legal/policy outlets, wires.
- Science/research: journal pages, preprint servers, institution newsrooms, PubMed/Crossref/arXiv where relevant, specialist science outlets.

### 3. Collect Candidate Updates

Use the best available method:

- If shell and network are available, run `python3 scripts/collect_updates.py "<interest>" --days 1` and add `--feed <rss-url>` for known feeds.
- If the script cannot access the network, use the agent's web search and web fetch tools directly.
- If neither direct feed access nor web search is available, explain the limitation and provide a source plan, not a fabricated brief.

Recommended search sequence:

1. Search for official sources and RSS feeds: `"<interest>" official news RSS`, `"<interest>" schedule results official`, or the topic-specific equivalent.
2. Poll Google News RSS for the interest with a recency operator such as `when:1d`.
3. Search the open web for overnight developments, using the date and region when useful.
4. Open the strongest sources and record title, URL, source, publish time, and the key fact.

### 4. Filter and Rank

Keep an item only if it is:

- Fresh for the requested window, or still consequential today.
- Relevant to the user's angle.
- Credibly sourced.
- Not a duplicate of a stronger item.

Rank by relevance, novelty, source quality, and practical usefulness. Prefer primary-source confirmation for the final facts; use news outlets for interpretation and context.

### 5. Write the Brief Module

Default format:

```markdown
### <Interest>

- **<Update headline>** - <one sentence on what changed>, with source links embedded naturally ([Source](https://...)). <One short clause on why it matters.>
- **<Update headline>** - ...

Sources checked: <short list of source names or source categories>.
Image: <markdown image link or source page link, if a useful and licensed/embeddable image was found>.
```

Rules:
- Use 3-5 bullets unless the user asks otherwise.
- Embed links in the bullets; do not dump bare URLs.
- Mention uncertainty and conflicts plainly.
- Include an image only when it adds real context, such as a match photo, map, chart, product shot, satellite image, official poster, or primary-source graphic. Prefer official/open-license images or link to the page containing the image if reuse rights are unclear.
- Keep each bullet to 1-2 sentences.

## Script

`scripts/collect_updates.py` is a no-dependency RSS/Atom collector. It builds a Google News RSS query for the topic, optionally fetches known feeds, dedups by URL/title, and emits JSON for the agent to rank and synthesize. It is a helper, not the whole skill: still cross-check important claims with web search.
