#!/usr/bin/env python3
"""session-handoff: Claude Code session-continuity helper.

Subcommands
-----------
  write     Write a handoff file + refresh the MEMORY.md pointer block.
            Body markdown is read from stdin (or --body-file). Used by the
            /wrap skill (--source wrap) and by the auto fallback (--source auto).
  recall    Print the newest handoff (+ pointers to other recent ones) so a
            SessionStart hook injects it into the new session's context.
  fallback  SessionEnd hook entrypoint. On reason==clear, spawn a detached
            worker that summarises the transcript into a handoff. Returns fast
            (SessionEnd has a ~1.5s budget); never blocks the wipe.

All file mutations go through a per-project lock + atomic replace, so concurrent
/clear's in the same folder can't corrupt MEMORY.md or lose a handoff.

The project memory dir is derived from the hook's transcript_path when available
(exact), else slugified from cwd the way Claude Code names project dirs
(every non-alphanumeric char -> '-').
"""

import argparse
import fcntl
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta

# ---------------------------------------------------------------- config ----
MAX_POINTERS = 5            # handoff pointer lines kept in MEMORY.md
MAX_HANDOFFS = 40           # handoff files retained in handoffs/
RECALL_FULL = 1            # newest N handoffs injected in full on recall
RECALL_POINTERS = 4        # additional recent handoffs listed as one-liners
RECALL_MAX_AGE_DAYS = 14   # don't nag with handoffs older than this
RECALL_FULL_CHAR_CAP = 8000  # max chars of a single handoff injected in full
EXPIRE_DAYS = 90           # handoff frontmatter expiry
WRAP_DEDUP_WINDOW = 180    # s; skip auto-fallback if a /wrap ran this recently
TRANSCRIPT_CHAR_CAP = 120_000  # chars of transcript tail fed to the summariser

BLOCK_START = "<!-- handoff:start -->"
BLOCK_END = "<!-- handoff:end -->"
BLOCK_HEADING = "### ↩ Recent session handoffs"

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
FALLBACK_DISABLED_FLAG = os.path.join(SKILL_DIR, "FALLBACK_DISABLED")
LOG_PATH = os.path.expanduser("~/.claude/session-handoff.log")


def log(msg):
    """Best-effort debug log. Never raises."""
    try:
        with open(LOG_PATH, "a") as f:
            f.write("%s  %s\n" % (datetime.now().isoformat(timespec="seconds"), msg))
    except Exception:
        pass


def read_stdin_json():
    """Parse a JSON object from stdin (hook payload). {} if none/invalid."""
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
    except Exception:
        return {}
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def slugify_cwd(cwd):
    return re.sub(r"[^a-zA-Z0-9]", "-", os.path.abspath(cwd))


def resolve_mem_dir(mem_dir=None, transcript_path=None, cwd=None):
    """Resolve the project memory dir, creating it + handoffs/ if needed."""
    if mem_dir:
        base = os.path.expanduser(mem_dir)
    elif transcript_path:
        # ~/.claude/projects/<slug>/<uuid>.jsonl -> <slug>/memory
        base = os.path.join(os.path.dirname(os.path.expanduser(transcript_path)), "memory")
    elif cwd:
        slug = slugify_cwd(cwd)
        base = os.path.expanduser(os.path.join("~/.claude/projects", slug, "memory"))
    else:
        raise SystemExit("resolve_mem_dir: need mem_dir, transcript_path, or cwd")
    os.makedirs(os.path.join(base, "handoffs"), exist_ok=True)
    return base


def handoffs_dir(mem_dir):
    return os.path.join(mem_dir, "handoffs")


class lock:
    """Per-project advisory file lock (fcntl.flock). Serialises writers."""

    def __init__(self, mem_dir):
        self.path = os.path.join(mem_dir, ".handoff.lock")
        self.fh = None

    def __enter__(self):
        self.fh = open(self.path, "w")
        fcntl.flock(self.fh, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        try:
            fcntl.flock(self.fh, fcntl.LOCK_UN)
            self.fh.close()
        except Exception:
            pass


def atomic_write(path, text):
    tmp = "%s.tmp.%d" % (path, os.getpid())
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)


def slug(text, maxlen=40):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:maxlen].strip("-")) or "session"


def rand_suffix():
    return os.urandom(2).hex()


def parse_frontmatter(text):
    """Return (meta_dict, body) from a '---' YAML-ish frontmatter block."""
    meta = {}
    body = text
    if text.startswith("---"):
        parts = text.split("\n", 1)
        if len(parts) == 2:
            rest = parts[1]
            end = rest.find("\n---")
            if end != -1:
                fm = rest[:end]
                body = rest[end + 4:].lstrip("\n")
                for line in fm.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip()
    return meta, body


# ---------------------------------------------------------------- write -----
def update_memory_block(mem_dir, pointer_line):
    mem_md = os.path.join(mem_dir, "MEMORY.md")
    content = ""
    if os.path.exists(mem_md):
        with open(mem_md) as f:
            content = f.read()

    if BLOCK_START in content and BLOCK_END in content:
        pre, rest = content.split(BLOCK_START, 1)
        _old_block, post = rest.split(BLOCK_END, 1)
        existing = [l for l in _old_block.splitlines() if l.strip().startswith("- ")]
    else:
        pre = (content.rstrip() + "\n\n") if content.strip() else ""
        existing = []
        post = ""

    lines = ([pointer_line] + existing)[:MAX_POINTERS]
    new_block = "%s\n%s\n%s\n%s" % (BLOCK_START, BLOCK_HEADING, "\n".join(lines), BLOCK_END)
    new_content = pre + new_block + post
    if not new_content.endswith("\n"):
        new_content += "\n"
    atomic_write(mem_md, new_content)


def prune_handoffs(mem_dir):
    files = sorted(
        glob.glob(os.path.join(handoffs_dir(mem_dir), "*.md")),
        key=lambda p: os.path.getmtime(p),
        reverse=True,
    )
    for stale in files[MAX_HANDOFFS:]:
        try:
            os.remove(stale)
        except OSError:
            pass


def cmd_write(args):
    body = ""
    if args.body_file:
        with open(args.body_file) as f:
            body = f.read()
    else:
        if not sys.stdin.isatty():
            body = sys.stdin.read()
    body = (body or "").strip()
    if not body:
        body = "_(no body provided)_"

    mem_dir = resolve_mem_dir(args.mem_dir, args.transcript, args.cwd)
    now = datetime.now()
    datestr = now.strftime("%Y-%m-%d")
    timestr = now.strftime("%H%M")
    expires = (now + timedelta(days=EXPIRE_DAYS)).strftime("%Y-%m-%d")
    topic = slug(args.topic)
    fname = "%s-%s-%s-%s.md" % (datestr, timestr, topic, rand_suffix())
    hook = (args.hook or "").strip() or "session handoff"
    cwd_val = os.path.abspath(args.cwd) if args.cwd else ""

    frontmatter = (
        "---\n"
        "type: episodic\n"
        "created: %s\n"
        "expires: %s\n"
        "source: %s\n"
        "topic: %s\n"
        "hook: %s\n"
        "cwd: %s\n"
        "---\n\n" % (datestr, expires, args.source, topic, hook.replace("\n", " "), cwd_val)
    )
    file_text = frontmatter + body + "\n"
    pointer = "- [%s](handoffs/%s) — %s · %s %s" % (
        topic, fname, hook.replace("\n", " "), datestr, now.strftime("%H:%M"))

    with lock(mem_dir):
        atomic_write(os.path.join(handoffs_dir(mem_dir), fname), file_text)
        update_memory_block(mem_dir, pointer)
        prune_handoffs(mem_dir)
        if args.source == "wrap":
            try:
                atomic_write(os.path.join(handoffs_dir(mem_dir), ".last-wrap"),
                             str(int(time.time())))
            except Exception:
                pass

    print(os.path.join(handoffs_dir(mem_dir), fname))


# --------------------------------------------------------------- recall -----
def cmd_recall(args):
    if os.environ.get("HANDOFF_HEADLESS") == "1":
        return  # don't inject into our own headless summariser
    payload = read_stdin_json()
    mem_dir = resolve_mem_dir(
        args.mem_dir, payload.get("transcript_path") or args.transcript,
        payload.get("cwd") or args.cwd)

    files = sorted(
        glob.glob(os.path.join(handoffs_dir(mem_dir), "*.md")),
        key=lambda p: os.path.getmtime(p),
        reverse=True,
    )
    if not files:
        return
    newest_age_days = (time.time() - os.path.getmtime(files[0])) / 86400.0
    if newest_age_days > RECALL_MAX_AGE_DAYS:
        return  # dormant project; stay quiet

    out = []
    out.append("↩ SESSION HANDOFF — from your previous session in this "
               "folder. If you're starting something unrelated, ignore this.\n")

    for path in files[:RECALL_FULL]:
        try:
            with open(path) as f:
                meta, text = parse_frontmatter(f.read())
        except Exception:
            continue
        body = text.strip()
        if len(body) > RECALL_FULL_CHAR_CAP:
            body = body[:RECALL_FULL_CHAR_CAP] + "\n…(truncated; full file: handoffs/%s)" % os.path.basename(path)
        out.append("### %s  (%s)\nfile: handoffs/%s\n\n%s\n" % (
            meta.get("topic", "session"), meta.get("created", ""), os.path.basename(path), body))

    others = files[RECALL_FULL:RECALL_FULL + RECALL_POINTERS]
    if others:
        out.append("── Other recent handoffs in this folder "
                   "(open the file to resume that thread) ──")
        for path in others:
            try:
                with open(path) as f:
                    meta, _ = parse_frontmatter(f.read())
            except Exception:
                meta = {}
            out.append("- %s — handoffs/%s · %s — %s" % (
                meta.get("topic", "session"), os.path.basename(path),
                meta.get("created", ""), meta.get("hook", "")))

    sys.stdout.write("\n".join(out) + "\n")


# ------------------------------------------------------------- fallback -----
def find_claude():
    cand = shutil.which("claude")
    if cand:
        return cand
    for p in ("~/.local/bin/claude", "~/.claude/local/claude",
              "/opt/homebrew/bin/claude", "/usr/local/bin/claude"):
        ep = os.path.expanduser(p)
        if os.path.exists(ep):
            return ep
    return None


def cmd_fallback(args):
    """SessionEnd entrypoint. Fast: gate, dedup, spawn detached worker, return."""
    payload = read_stdin_json()
    reason = payload.get("reason", "")
    if reason != "clear":
        return  # only act on /clear; also blocks headless-session recursion
    if os.environ.get("HANDOFF_HEADLESS") == "1":
        return
    if os.path.exists(FALLBACK_DISABLED_FLAG):
        return

    transcript = payload.get("transcript_path")
    cwd = payload.get("cwd")
    if not transcript or not os.path.exists(os.path.expanduser(transcript)):
        return
    mem_dir = resolve_mem_dir(None, transcript, cwd)

    # Dedup: a /wrap in the last WRAP_DEDUP_WINDOW already produced a handoff.
    last_wrap = os.path.join(handoffs_dir(mem_dir), ".last-wrap")
    if os.path.exists(last_wrap):
        try:
            with open(last_wrap) as f:
                if time.time() - int(f.read().strip()) < WRAP_DEDUP_WINDOW:
                    return
        except Exception:
            pass

    if not find_claude():
        log("fallback: no claude binary found; skipping auto-handoff")
        return

    worker = [sys.executable, os.path.abspath(__file__), "_runfallback",
              "--transcript", os.path.expanduser(transcript), "--mem-dir", mem_dir]
    if cwd:
        worker += ["--cwd", cwd]
    env = dict(os.environ)
    env["HANDOFF_HEADLESS"] = "1"
    try:
        devnull = open(os.devnull, "wb")
        subprocess.Popen(worker, stdin=subprocess.DEVNULL, stdout=devnull,
                         stderr=devnull, start_new_session=True, env=env)
        log("fallback: spawned worker for %s" % transcript)
    except Exception as e:
        log("fallback: spawn failed: %r" % e)


SUMMARY_PROMPT = (
    "You are summarising a Claude Code session transcript (JSONL on stdin) into a "
    "handoff note for the NEXT session in this folder. Do not use any tools. Output "
    "ONLY GitHub-flavored markdown, no preamble, with exactly these sections:\n"
    "## Summary  (what was done this session)\n"
    "## Next steps  (what to do next, concrete)\n"
    "## Gotchas / open questions\n"
    "## Key files & commands\n"
    "Be specific and terse. Start your reply with a single line `TOPIC: <kebab-topic>` "
    "before the markdown."
)


def cmd_runfallback(args):
    """Detached worker: summarise transcript via headless claude, then write."""
    claude = find_claude()
    if not claude:
        return
    try:
        with open(args.transcript, "r", errors="replace") as f:
            data = f.read()
    except Exception as e:
        log("_runfallback: read transcript failed: %r" % e)
        return
    if len(data) > TRANSCRIPT_CHAR_CAP:
        data = data[-TRANSCRIPT_CHAR_CAP:]

    try:
        proc = subprocess.run(
            [claude, "-p", SUMMARY_PROMPT],
            input=data, capture_output=True, text=True, timeout=300,
            env=dict(os.environ, HANDOFF_HEADLESS="1"),
        )
        summary = (proc.stdout or "").strip()
    except Exception as e:
        log("_runfallback: claude -p failed: %r" % e)
        return
    if not summary:
        log("_runfallback: empty summary; skipping")
        return

    topic = "session"
    m = re.match(r"\s*TOPIC:\s*(.+)", summary)
    if m:
        topic = m.group(1).strip()
        summary = summary[m.end():].lstrip("\n")
    hook = ""
    for line in summary.splitlines():
        s = line.strip().lstrip("#").strip()
        if s and not s.lower().startswith("summary"):
            hook = s
            break
    if not hook:
        hook = "auto handoff from /clear"

    wargs = argparse.Namespace(
        body_file=None, mem_dir=args.mem_dir, transcript=args.transcript,
        cwd=args.cwd, topic=topic, hook=hook[:120], source="auto")
    # feed body via temp file to reuse cmd_write
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tf:
        tf.write(summary)
        wargs.body_file = tf.name
    try:
        cmd_write(wargs)
        log("_runfallback: wrote auto handoff (topic=%s)" % topic)
    finally:
        try:
            os.remove(wargs.body_file)
        except OSError:
            pass


# ------------------------------------------------------------------ cli -----
def main():
    p = argparse.ArgumentParser(prog="handoff.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write", help="write a handoff + refresh MEMORY.md")
    w.add_argument("--topic", required=True)
    w.add_argument("--hook", default="")
    w.add_argument("--source", choices=["wrap", "auto"], default="wrap")
    w.add_argument("--cwd", default=None)
    w.add_argument("--transcript", default=None)
    w.add_argument("--mem-dir", default=None)
    w.add_argument("--body-file", default=None)
    w.set_defaults(func=cmd_write)

    r = sub.add_parser("recall", help="print newest handoff for SessionStart")
    r.add_argument("--cwd", default=None)
    r.add_argument("--transcript", default=None)
    r.add_argument("--mem-dir", default=None)
    r.set_defaults(func=cmd_recall)

    fb = sub.add_parser("fallback", help="SessionEnd entrypoint")
    fb.set_defaults(func=cmd_fallback)

    rf = sub.add_parser("_runfallback", help=argparse.SUPPRESS)
    rf.add_argument("--transcript", required=True)
    rf.add_argument("--mem-dir", required=True)
    rf.add_argument("--cwd", default=None)
    rf.set_defaults(func=cmd_runfallback)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
