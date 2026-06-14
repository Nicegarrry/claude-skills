#!/usr/bin/env bash
# Guided first-time setup for the generate-image (Nano Banana) skill.
# Walks you through getting a Google Gemini API key and saves it privately.
#
# Run it yourself in a terminal:
#     ~/.claude/skills/generate-image/setup.sh
# Optional arg = a different var name (e.g. for the slides key):
#     ~/.claude/skills/generate-image/setup.sh SLIDES_GEMINI_API_KEY
#
# The key is typed hidden (read -s): not echoed, not in argv, not in shell history.
set -euo pipefail

VAR="${1:-GEMINI_API_KEY}"
CRED="${NANO_BANANA_CREDENTIALS:-$HOME/.config/nano-banana/credentials.env}"
URL="https://aistudio.google.com/apikey"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Nano Banana image skill — API key setup"
echo "---------------------------------------"
echo "Setting variable : $VAR"
echo "Credentials file : $CRED"
echo

# Already populated?
if [ -f "$CRED" ] && grep -qE "^${VAR}=.+" "$CRED"; then
  echo "✓ $VAR already has a value."
  printf "Replace it? [y/N] "
  read -r ans
  case "$ans" in y|Y|yes|YES) ;; *) echo "Keeping existing key. Nothing to do."; exit 0 ;; esac
fi

echo "Step 1 — Open Google AI Studio and sign in with your Google account:"
echo "         $URL"
if command -v open >/dev/null 2>&1; then
  printf "         Open it in your browser now? [Y/n] "
  read -r o; case "$o" in n|N) ;; *) open "$URL" >/dev/null 2>&1 || true ;; esac
fi
echo "Step 2 — Click 'Create API key' (→ 'in a new project' if asked), then Copy."
echo "Step 3 — Paste it below. Input is hidden."
echo

printf "Paste %s: " "$VAR"
read -rs KEY
echo
KEY="$(printf '%s' "$KEY" | tr -d '[:space:]')"

if [ -z "$KEY" ]; then
  echo "No key entered — aborted." >&2; exit 1
fi
case "$KEY" in
  AIza*) : ;;
  *) printf "⚠ That doesn't look like a Google key (they usually start 'AIza'). Save anyway? [y/N] "
     read -r c; case "$c" in y|Y|yes|YES) ;; *) echo "Aborted." >&2; exit 1 ;; esac ;;
esac

# Write, preserving any other vars/comments already in the file.
mkdir -p "$(dirname "$CRED")"; chmod 700 "$(dirname "$CRED")" 2>/dev/null || true
tmp="$(mktemp)"
[ -f "$CRED" ] && grep -vE "^${VAR}=" "$CRED" > "$tmp" 2>/dev/null || true
printf '%s=%s\n' "$VAR" "$KEY" >> "$tmp"
mv "$tmp" "$CRED"
chmod 600 "$CRED"
echo "✓ Saved $VAR to $CRED (chmod 600)."
echo

if [ "$VAR" = "GEMINI_API_KEY" ]; then
  printf "Run a quick test generation now? [Y/n] "
  read -r t
  case "$t" in
    n|N) echo "Setup complete." ;;
    *) echo "Generating a test image…"
       if "$DIR/generate_image.py" -p "a friendly waving robot mascot, flat vector, on white" \
            -s 1K -o /tmp/nano-banana-setup-test.png; then
         echo "✓ Success — wrote /tmp/nano-banana-setup-test.png. The skill is ready."
       else
         echo "✗ Test failed. Double-check the key, then re-run this script." >&2; exit 1
       fi ;;
  esac
else
  echo "Setup complete. Use this key with:  generate_image.py --profile $VAR ..."
fi
