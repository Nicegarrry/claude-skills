#!/usr/bin/env bash
# Idempotent installer for the session-handoff skill.
#   1. symlinks the skill into ~/.claude/skills/
#   2. merges SessionStart (recall) + SessionEnd (fallback) hooks into
#      ~/.claude/settings.json without disturbing existing settings (backs up first)
# Safe to re-run; it replaces only its own hook entries.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
LINK="$SKILLS_DIR/session-handoff"
SETTINGS="$HOME/.claude/settings.json"
PY="$(command -v python3 || echo /opt/homebrew/bin/python3)"
HANDOFF="$LINK/handoff.py"   # reference via the installed (symlinked) path

chmod +x "$REPO_DIR/handoff.py" "$REPO_DIR/install.sh"

# 1) symlink ------------------------------------------------------------------
mkdir -p "$SKILLS_DIR"
if [ -L "$LINK" ] || [ ! -e "$LINK" ]; then
  ln -sfn "$REPO_DIR" "$LINK"
else
  echo "!! $LINK exists and is not a symlink — remove it first, then re-run." >&2
  exit 1
fi
echo "✓ symlinked $LINK -> $REPO_DIR"

# 2) merge hooks --------------------------------------------------------------
[ -f "$SETTINGS" ] && cp "$SETTINGS" "$SETTINGS.bak.$(date +%Y%m%d%H%M%S)"

PY="$PY" HANDOFF="$HANDOFF" SETTINGS="$SETTINGS" "$PY" <<'PYEOF'
import json, os

settings_path = os.environ["SETTINGS"]
py = os.environ["PY"]
handoff = os.environ["HANDOFF"]
marker = "session-handoff/handoff.py"

data = {}
if os.path.exists(settings_path):
    with open(settings_path) as f:
        data = json.load(f)

hooks = data.setdefault("hooks", {})

def strip_ours(event):
    groups = hooks.get(event, [])
    kept = []
    for g in groups:
        cmds = " ".join(h.get("command", "") for h in g.get("hooks", []))
        if marker not in cmds:
            kept.append(g)
    hooks[event] = kept

strip_ours("SessionStart")
strip_ours("SessionEnd")

hooks["SessionStart"].append({
    "matcher": "startup|resume|clear",
    "hooks": [{"type": "command",
               "command": "%s %s recall" % (py, handoff),
               "timeout": 10}],
})
hooks["SessionEnd"].append({
    "matcher": "clear",
    "hooks": [{"type": "command",
               "command": "%s %s fallback" % (py, handoff),
               "timeout": 10}],
})

with open(settings_path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
print("✓ hooks merged into %s" % settings_path)
PYEOF

echo "✓ session-handoff installed. Use /wrap before /clear; recall is automatic."
