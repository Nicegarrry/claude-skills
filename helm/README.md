# helm

A thin Claude Code skill for driving the **Helm MCP server** — a small harness that lets an
orchestrator agent dispatch coding work to cheap worker agents, each in its own git worktree,
and get back gates, PRs, cross-family reviews and merges.

The skill teaches the orchestration loop (brief → spawn → wait → gate → PR → review → merge)
and the rules that keep a long run cheap and correct. The harness itself lives in its own
repo:

**→ [github.com/Nicegarrry/helm3](https://github.com/Nicegarrry/helm3)** — install, daemon,
dashboard, configuration and the full tool reference (`helm/README.md`).

## Setup

1. Install Helm from the [helm3 repo](https://github.com/Nicegarrry/helm3) and sign in to the
   worker lanes you want (Pi providers, the Codex CLI, `gh`).
2. Add the server to your project's `.mcp.json`:

   ```json
   {
     "mcpServers": {
       "helm": {
         "command": "/path/to/helm3/helm/bin/helm.js",
         "args": ["serve", "--stdio", "--port", "4747"],
         "env": { "HELM_SPEND_CAP_USD": "5" }
       }
     }
   }
   ```

3. Install this skill:

   ```bash
   cp -R helm ~/.claude/skills/
   ```

Claude Code loads it when you hand over a build to run with agents and the helm tools are
connected.

## History

This folder used to hold a much longer "helm doctrine" skill that ran the fleet through Claude
subagents and the earlier `helm-cli`. The MCP server replaced that machinery, so the skill is
now just the how-to. The old doctrine is in this repo's git history.
