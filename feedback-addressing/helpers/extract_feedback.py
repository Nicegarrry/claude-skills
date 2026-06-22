#!/usr/bin/env python3
"""
extract_feedback.py — pull reviewer comments out of a .docx and (optionally)
splice in dot-point feedback, emitting a normalised JSON list per the
feedback-addressing skill (SKILL.md step 2).

WHAT IT DOES
------------
- Reads `word/comments.xml` from the supplied `.docx`.
- Reads `word/document.xml` to determine the document anchor order of comments
  (i.e. the order in which their `<w:commentRangeStart>` elements appear in the
  body), and to extract the run-text actually anchored by each comment.
- Emits a JSON list with one entry per feedback item, fields:
    {feedback_id, source_type, source_locator, reviewer, raw_text,
     anchor_text, anchor_location, anchor_paragraph_id, anchor_paragraph_index,
     comment_wid, date}
- `feedback_id` is `F01..FN` in DOCUMENT-ANCHOR order (NOT comment-id order),
  inline first then dotpoint items appended in input order.

WHAT IT DOESN'T DO
------------------
- Does NOT confuse `<w:ins>` / `<w:del>` track-change markup with comments —
  these are independent OOXML elements; we only walk `<w:comment*>` elements.
- v0.4: DOES resolve threaded comment replies via `commentsExtended.xml`
  (`w15:paraIdParent` linking child paraIds to the parent comment's first
  paragraph). Each row gets a `comment_thread` field listing the parent +
  ordered replies.
- Does NOT rewrite the docx; pure read-only.

EDGE CASES (logged to stderr, never silently dropped)
-----------------------------------------------------
- Comment with no body → raw_text = "" and a warning.
- Comment anchored to nothing matchable in document.xml → anchor_text = "" and
  a warning; still emitted with its comments.xml metadata.
- Multi-paragraph anchor → runs concatenated with " ⏎ " delimiter; truncated
  to 240 chars in `anchor_text`.
- Dotpoint stream missing → silently allowed; only inline items emitted.

USAGE
-----
    extract_feedback.py <doc.docx> [--dotpoints PATH|-] [--out PATH]

`--dotpoints -` reads from stdin. Output goes to --out if given, else stdout.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
W15_NS = "http://schemas.microsoft.com/office/word/2012/wordml"
NS = {"w": W_NS, "w14": W14_NS, "w15": W15_NS}

ANCHOR_TEXT_TRUNCATE = 240


def _q(tag: str, ns: str = W_NS) -> str:
    return f"{{{ns}}}{tag}"


def _warn(msg: str) -> None:
    print(f"[extract_feedback] WARN: {msg}", file=sys.stderr)


def _read_xml_part(zf: zipfile.ZipFile, part: str) -> ET.Element | None:
    try:
        data = zf.read(part)
    except KeyError:
        return None
    return ET.fromstring(data)


def _comment_text(comment_el: ET.Element) -> str:
    """Concatenate all <w:t> text in a <w:comment> element."""
    parts: list[str] = []
    for t in comment_el.iter(_q("t")):
        if t.text:
            parts.append(t.text)
    return "".join(parts).strip()


def _walk_anchored_runs(doc_root: ET.Element) -> dict[str, dict[str, Any]]:
    """
    Walk document.xml in document order and, for every comment id, capture:
      - anchor_text (concatenated <w:t> between commentRangeStart/End for that id;
        runs in different paragraphs joined with " ⏎ ")
      - anchor_paragraph_index (0-based index of the FIRST paragraph that
        contains this comment's commentRangeStart)
      - anchor_paragraph_id (w14:paraId of that paragraph if present, else
        "para-{idx}")
      - anchor_order (the ordinal position of commentRangeStart in document
        order, used to determine F01..FN ordering)

    Returns: {wid: {...}} for every commentRangeStart found.
    """
    result: dict[str, dict[str, Any]] = {}
    open_ranges: dict[str, dict[str, Any]] = {}  # wid -> {parts: [...], current_para_text: [...]}
    body = doc_root.find(_q("body"))
    if body is None:
        _warn("document.xml has no <w:body> — anchor extraction will be empty")
        return result

    # We need stream-order traversal at the body level: walk paragraphs.
    para_idx = -1
    anchor_order_counter = 0

    def collect_text_in_run(run_el: ET.Element) -> str:
        return "".join(t.text or "" for t in run_el.iter(_q("t")))

    # We use a depth-first iter and track paragraph boundaries by entering
    # each <w:p>. Within a paragraph we maintain a per-wid buffer of text
    # collected between Start and End for that wid.
    for p in body.iter(_q("p")):
        para_idx += 1
        para_id_attr = p.get(_q("paraId", W14_NS))
        para_id = para_id_attr if para_id_attr else f"para-{para_idx}"

        # For each open range, push a paragraph break marker before any new
        # text in this paragraph (only after we collected at least 1 char).
        # We do this lazily inside the per-element walk below.
        para_started_for_range: dict[str, bool] = {wid: False for wid in open_ranges}

        # Walk children of paragraph in document order. We need to process:
        #   <w:commentRangeStart w:id=...>
        #   <w:commentRangeEnd w:id=...>
        #   <w:r> (regular run) — collect text into all open ranges
        #   <w:ins><w:r>...</w:r></w:ins> — treat inserted runs as text too
        #   <w:del><w:r><w:delText>...</w:delText></w:r></w:del> — collect delText too
        for el in p.iter():
            tag = el.tag
            if tag == _q("commentRangeStart"):
                wid = el.get(_q("id"))
                if wid is None:
                    continue
                anchor_order_counter += 1
                open_ranges[wid] = {"parts": [], "current_para_text": []}
                para_started_for_range[wid] = True
                result.setdefault(
                    wid,
                    {
                        "wid": wid,
                        "anchor_paragraph_index": para_idx,
                        "anchor_paragraph_id": para_id,
                        "anchor_order": anchor_order_counter,
                        "anchor_text": "",
                    },
                )
            elif tag == _q("commentRangeEnd"):
                wid = el.get(_q("id"))
                if wid is None or wid not in open_ranges:
                    continue
                # close it
                buf = open_ranges.pop(wid)
                # flush current paragraph to parts
                cur = "".join(buf["current_para_text"]).strip()
                if cur:
                    buf["parts"].append(cur)
                full = " ⏎ ".join(buf["parts"]).strip()
                if len(full) > ANCHOR_TEXT_TRUNCATE:
                    full = full[: ANCHOR_TEXT_TRUNCATE - 1] + "…"
                if wid in result:
                    result[wid]["anchor_text"] = full
            elif tag == _q("t"):
                # Append this run-text to every currently-open range.
                txt = el.text or ""
                if not txt:
                    continue
                for wid, buf in open_ranges.items():
                    if not para_started_for_range.get(wid, False):
                        # Range opened in a previous paragraph; flush its
                        # current_para_text into parts as an entry from the
                        # earlier paragraph, then start a fresh para buffer.
                        prev = "".join(buf["current_para_text"]).strip()
                        if prev:
                            buf["parts"].append(prev)
                        buf["current_para_text"] = []
                        para_started_for_range[wid] = True
                    buf["current_para_text"].append(txt)
            elif tag == _q("delText"):
                # Inside <w:del>: this is the original (deleted) text. We DO
                # include it for anchor reconstruction so the user sees what
                # the comment was anchored to even if a later edit deleted
                # part of it.
                txt = el.text or ""
                if not txt:
                    continue
                for wid, buf in open_ranges.items():
                    if not para_started_for_range.get(wid, False):
                        prev = "".join(buf["current_para_text"]).strip()
                        if prev:
                            buf["parts"].append(prev)
                        buf["current_para_text"] = []
                        para_started_for_range[wid] = True
                    buf["current_para_text"].append(txt)

        # Paragraph done. For every still-open range, flush the per-paragraph
        # buffer into parts so the next paragraph starts fresh.
        for wid, buf in open_ranges.items():
            cur = "".join(buf["current_para_text"]).strip()
            if cur:
                buf["parts"].append(cur)
            buf["current_para_text"] = []

    # Any range left open after walking the entire body is unbalanced.
    for wid in list(open_ranges.keys()):
        _warn(f"comment id={wid} has commentRangeStart but no matching End")
        buf = open_ranges.pop(wid)
        full = " ⏎ ".join(buf["parts"]).strip()
        if len(full) > ANCHOR_TEXT_TRUNCATE:
            full = full[: ANCHOR_TEXT_TRUNCATE - 1] + "…"
        if wid in result:
            result[wid]["anchor_text"] = full

    return result


def parse_dotpoints(text: str) -> list[str]:
    """
    Split a free-text feedback dump into discrete items.

    Heuristics, in order:
      1. Lines starting with bullet markers (-, *, •, ·).
      2. Lines starting with `\\d+[.\\)]` (numbered).
      3. Otherwise paragraph-blocks separated by one-or-more blank lines.

    Empty or whitespace-only items are dropped.
    """
    text = text.strip()
    if not text:
        return []

    # Normalise newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    bullet_re = re.compile(r"^\s*([-*•·]|\d+[.\)])\s+(.*)$")
    items: list[str] = []
    has_bullets = any(bullet_re.match(ln) for ln in lines)

    if has_bullets:
        current: list[str] = []
        for ln in lines:
            m = bullet_re.match(ln)
            if m:
                if current:
                    joined = " ".join(s.strip() for s in current).strip()
                    if joined:
                        items.append(joined)
                current = [m.group(2)]
            elif ln.strip():
                current.append(ln.strip())
            else:
                # blank line within a bullet — close it
                if current:
                    joined = " ".join(s.strip() for s in current).strip()
                    if joined:
                        items.append(joined)
                    current = []
        if current:
            joined = " ".join(s.strip() for s in current).strip()
            if joined:
                items.append(joined)
    else:
        # paragraph blocks
        block: list[str] = []
        for ln in lines:
            if ln.strip():
                block.append(ln.strip())
            else:
                if block:
                    items.append(" ".join(block))
                    block = []
        if block:
            items.append(" ".join(block))

    return [i for i in items if i]


def _build_comment_threads(
    comments_root: ET.Element, comments_ext_root: ET.Element | None
) -> dict[str, list[dict[str, Any]]]:
    """
    Parse `commentsExtended.xml` to surface comment reply chains. Returns a
    dict mapping comment_wid → ordered list of `{comment_id, author, text,
    role, date}` thread entries (parent first, then replies in date order).
    Where a comment is itself a reply, the chain includes its parent.

    Mapping note: `comments.xml` `w:comment` elements contain `w:p` paragraphs
    each with a `w14:paraId`. `commentsExtended.xml` `w15:commentEx` elements
    use `w15:paraId` to point at the FIRST paragraph of a comment, and
    `w15:paraIdParent` to point at the parent comment's first-paragraph
    paraId. We normalise paraId to uppercase hex for comparison.
    """
    if comments_ext_root is None:
        return {}

    # 1. paraId → comment metadata, using each comment's first <w:p>
    paraid_to_comment: dict[str, dict[str, Any]] = {}
    for c in comments_root.findall(_q("comment")):
        cid = c.get(_q("id"))
        if cid is None:
            continue
        first_p = c.find(_q("p"))
        if first_p is None:
            continue
        pid = first_p.get(_q("paraId", W14_NS))
        if not pid:
            continue
        paraid_to_comment[pid.upper()] = {
            "comment_id": cid,
            "author": c.get(_q("author")) or "(unknown)",
            "text": _comment_text(c),
            "date": c.get(_q("date")) or "",
            "paraId": pid.upper(),
        }

    # 2. paraId → paraIdParent map from commentsExtended
    parent_of: dict[str, str | None] = {}
    for el in comments_ext_root.findall(_q("commentEx", W15_NS)):
        pid = el.get(_q("paraId", W15_NS))
        parent = el.get(_q("paraIdParent", W15_NS))
        if pid:
            parent_of[pid.upper()] = parent.upper() if parent else None

    # 3. Build children index: parent_paraId → [child_paraId, ...]
    children_of: dict[str, list[str]] = {}
    for child, parent in parent_of.items():
        if parent:
            children_of.setdefault(parent, []).append(child)

    # 4. For each comment, walk to root, then collect siblings ordered by date
    threads: dict[str, list[dict[str, Any]]] = {}
    for paraid, meta in paraid_to_comment.items():
        # find root of this comment's chain
        root = paraid
        seen = set()
        while parent_of.get(root) and parent_of[root] not in seen:
            seen.add(root)
            root = parent_of[root]  # type: ignore[assignment]
        # collect root + all descendants (depth-first, ordered by date)
        chain: list[dict[str, Any]] = []
        if root in paraid_to_comment:
            root_entry = dict(paraid_to_comment[root])
            root_entry["role"] = "self" if root == paraid else "parent"
            chain.append(root_entry)
        # children of root, sorted by date
        kids = sorted(
            (k for k in children_of.get(root, []) if k in paraid_to_comment),
            key=lambda k: paraid_to_comment[k]["date"],
        )
        for kid in kids:
            kid_entry = dict(paraid_to_comment[kid])
            kid_entry["role"] = "self" if kid == paraid else "reply"
            chain.append(kid_entry)
        # only emit thread if there's > 1 entry (otherwise no reply chain to read)
        if len(chain) > 1:
            cid = meta["comment_id"]
            # strip paraId from outward-facing entries
            slim = [
                {k: v for k, v in entry.items() if k != "paraId"} for entry in chain
            ]
            threads[cid] = slim
    return threads


def extract(doc_path: Path, dotpoint_text: str | None = None) -> list[dict[str, Any]]:
    if not doc_path.exists():
        raise SystemExit(f"file not found: {doc_path}")
    with zipfile.ZipFile(doc_path) as zf:
        comments_root = _read_xml_part(zf, "word/comments.xml")
        comments_ext_root = _read_xml_part(zf, "word/commentsExtended.xml")
        document_root = _read_xml_part(zf, "word/document.xml")

    inline_items: list[dict[str, Any]] = []
    if comments_root is None:
        _warn(f"{doc_path.name} has no word/comments.xml — no inline comments")
        anchored: dict[str, dict[str, Any]] = {}
    else:
        if document_root is None:
            raise SystemExit("document.xml missing — cannot resolve anchor order")
        anchored = _walk_anchored_runs(document_root)

        # comments.xml metadata: build wid -> {author, date, body}
        comment_meta: dict[str, dict[str, str]] = {}
        for c in comments_root.findall(_q("comment")):
            wid = c.get(_q("id"))
            if wid is None:
                continue
            comment_meta[wid] = {
                "author": c.get(_q("author")) or "(unknown)",
                "date": c.get(_q("date")) or "",
                "body": _comment_text(c),
            }
            if not comment_meta[wid]["body"]:
                _warn(f"comment id={wid} (author={comment_meta[wid]['author']}) has empty body")

        # Order by anchor_order (document order), fall back to comments.xml order
        # for any with no anchor.
        for wid, meta in comment_meta.items():
            if wid not in anchored:
                _warn(f"comment id={wid} has no commentRangeStart anchor in document.xml")
                anchored[wid] = {
                    "wid": wid,
                    "anchor_paragraph_index": -1,
                    "anchor_paragraph_id": None,
                    "anchor_order": 10**9,  # push to end
                    "anchor_text": "",
                }

        ordered_wids = sorted(
            comment_meta.keys(),
            key=lambda w: anchored[w]["anchor_order"],
        )

        # v0.4 rule I: parse commentsExtended.xml for reply chains.
        comment_threads = _build_comment_threads(comments_root, comments_ext_root)

        for idx, wid in enumerate(ordered_wids, start=1):
            meta = comment_meta[wid]
            a = anchored[wid]
            inline_items.append(
                {
                    "feedback_id": f"F{idx:02d}",
                    "source_type": "inline",
                    "source_locator": f"inline-c{wid}",
                    "reviewer": meta["author"],
                    "raw_text": meta["body"],
                    "anchor_text": a["anchor_text"],
                    "anchor_location": (
                        f"para-idx-{a['anchor_paragraph_index']}"
                        if a["anchor_paragraph_index"] >= 0
                        else "unknown"
                    ),
                    "anchor_paragraph_id": a["anchor_paragraph_id"],
                    "anchor_paragraph_index": a["anchor_paragraph_index"],
                    "comment_wid": wid,
                    "date": meta["date"],
                    "comment_thread": comment_threads.get(wid, []),
                }
            )

    dotpoint_items: list[dict[str, Any]] = []
    if dotpoint_text:
        items = parse_dotpoints(dotpoint_text)
        next_idx = len(inline_items) + 1
        for n, raw in enumerate(items, start=1):
            dotpoint_items.append(
                {
                    "feedback_id": f"F{next_idx:02d}",
                    "source_type": "dotpoint",
                    "source_locator": f"dotpoint-{n}",
                    "reviewer": "(dotpoint)",
                    "raw_text": raw,
                    "anchor_text": "",
                    "anchor_location": "",
                    "anchor_paragraph_id": None,
                    "anchor_paragraph_index": -1,
                    "comment_wid": None,
                    "date": "",
                    "comment_thread": [],
                }
            )
            next_idx += 1

    return inline_items + dotpoint_items


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("doc", type=Path, help="Path to .docx file")
    ap.add_argument(
        "--dotpoints",
        type=str,
        default=None,
        help="Path to a free-text dotpoint dump, or '-' for stdin",
    )
    ap.add_argument("--out", type=Path, default=None, help="Output path (default: stdout)")
    args = ap.parse_args()

    dotpoint_text: str | None = None
    if args.dotpoints == "-":
        dotpoint_text = sys.stdin.read()
    elif args.dotpoints:
        dotpoint_text = Path(args.dotpoints).read_text(encoding="utf-8")

    items = extract(args.doc, dotpoint_text)
    out_str = json.dumps(items, indent=2, ensure_ascii=False)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(out_str + "\n", encoding="utf-8")
        print(f"[extract_feedback] wrote {len(items)} items → {args.out}", file=sys.stderr)
    else:
        print(out_str)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
