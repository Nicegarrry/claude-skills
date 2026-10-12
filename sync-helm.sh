#!/bin/sh
# Refresh the Helm v5 skills from a helm3 checkout (source of truth: helm3/skills).
set -e
SRC="${1:-$HOME/code/other/helm3}/skills"
cd "$(dirname "$0")"
for s in "$SRC"/*; do rm -rf "./$(basename "$s")"; cp -R "$s" ./; done
echo "synced $(ls "$SRC" | wc -l | tr -d ' ') skills from $SRC"
