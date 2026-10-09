#!/usr/bin/env python3
"""Diff a tracked output against the owner's edited version of it (rule P).

Usage: owner_pass_diff.py <tracked-output.docx> <owner-version.docx>
                          [--reply-author Claude] [--out 10-owner-pass.md]

Reports, as Markdown:
  * comment counts by author in each file;
  * Claude comments the owner deleted, with word counts (kept vs deleted medians);
  * comments new in the owner's version, each with the thread root it sits under
    and any Claude sibling in that thread (the reply it answers);
  * tracked revisions that disappeared (accepted or rejected) and new ones, by author.
Read-only. Never opens Word.
"""
from __future__ import annotations

import argparse
import statistics
import sys
import zipfile
from collections import Counter

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
W14 = "{http://schemas.microsoft.com/office/word/2010/wordml}"
W15 = "{http://schemas.microsoft.com/office/word/2012/wordml}"


def _xml(z: zipfile.ZipFile, name: str):
    return etree.fromstring(z.read(name)) if name in z.namelist() else None


def load(path: str) -> dict:
    z = zipfile.ZipFile(path)
    doc = _xml(z, "word/document.xml")
    comments, by_pid = [], {}
    c = _xml(z, "word/comments.xml")
    if c is not None:
        for e in c.iter(W + "comment"):
            ps = e.findall(W + "p")
            pid = ps[-1].get(W14 + "paraId") if ps else None
            item = {"pid": pid, "author": e.get(W + "author") or "",
                    "text": " ".join("".join(e.itertext()).split())}
            comments.append(item)
            if pid:
                by_pid[pid] = item
    parent = {}
    ce = _xml(z, "word/commentsExtended.xml")
    if ce is not None:
        for x in ce.iter(W15 + "commentEx"):
            parent[x.get(W15 + "paraId")] = x.get(W15 + "paraIdParent")
    revs = []
    for tag in ("ins", "del"):
        for e in doc.iter(W + tag):
            t = "".join(x.text or "" for x in e.iter(W + "t", W + "delText"))
            revs.append((tag, e.get(W + "author") or "", t))
    return {"comments": comments, "by_pid": by_pid, "parent": parent, "revs": revs}


def words(t: str) -> int:
    return len(t.split())


def med(xs: list[int]) -> str:
    return f"{statistics.median(xs):.0f}" if xs else "n/a"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tracked")
    ap.add_argument("owner")
    ap.add_argument("--reply-author", default="Claude")
    ap.add_argument("--out")
    a = ap.parse_args()
    t, o = load(a.tracked), load(a.owner)
    R = a.reply_author
    key = lambda c: (c["author"], c["text"])  # noqa: E731
    tk, ok = {key(c) for c in t["comments"]}, {key(c) for c in o["comments"]}

    out = [f"# Owner pass diff\n\n- Tracked output: `{a.tracked}`\n- Owner version: `{a.owner}`\n"]
    ca = Counter(c["author"] for c in t["comments"])
    cb = Counter(c["author"] for c in o["comments"])
    out.append("## Comments by author\n\n| author | tracked | owner |\n|---|---|---|")
    for au in sorted(set(ca) | set(cb)):
        out.append(f"| {au} | {ca.get(au, 0)} | {cb.get(au, 0)} |")

    mine = [c for c in t["comments"] if c["author"] == R]
    deleted = [c for c in mine if key(c) not in ok]
    kept = [c for c in mine if key(c) in ok]
    out.append(f"\n## {R} comments\n\n- {len(mine)} in tracked output; {len(deleted)} deleted by the owner, {len(kept)} kept")
    out.append(f"- Words: all median {med([words(c['text']) for c in mine])}, "
               f"deleted median {med([words(c['text']) for c in deleted])}, "
               f"kept median {med([words(c['text']) for c in kept])}, "
               f"max {max([words(c['text']) for c in mine], default=0)}")
    out.append(f"- Over 30 words: {sum(words(c['text']) > 30 for c in mine)}\n")
    for c in sorted(deleted, key=lambda c: words(c["text"])):
        out.append(f"- deleted ({words(c['text'])}w): {c['text'][:240]}")

    new = [c for c in o["comments"] if key(c) not in tk]
    out.append(f"\n## New comments in the owner's version ({len(new)})\n")
    for c in new:
        root_pid = o["parent"].get(c["pid"])
        root = o["by_pid"].get(root_pid)
        sib = [o["by_pid"][k] for k, v in o["parent"].items()
               if v == root_pid and k != c["pid"] and k in o["by_pid"] and o["by_pid"][k]["author"] == R] if root_pid else []
        out.append(f"- **{c['author']}**: {c['text'][:300]}")
        if root:
            out.append(f"  - under {root['author']}: {root['text'][:160]}")
        for s in sib[:2]:
            out.append(f"  - {R} reply in thread ({words(s['text'])}w): {s['text'][:160]}")

    rt, ro = set(t["revs"]), set(o["revs"])
    gone, added = Counter((r[0], r[1]) for r in rt - ro), Counter((r[0], r[1]) for r in ro - rt)
    out.append("\n## Tracked revisions\n\n| change | author | resolved (gone) | new |\n|---|---|---|---|")
    for k in sorted(set(gone) | set(added)):
        out.append(f"| {k[0]} | {k[1]} | {gone.get(k, 0)} | {added.get(k, 0)} |")

    text = "\n".join(out) + "\n"
    if a.out:
        open(a.out, "w").write(text)
        print(f"wrote {a.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
