#!/usr/bin/env python3
"""List reviewer feedback written INLINE rather than as Word comments: tracked
insertions by other authors, and highlighted runs. Emits JSON rows the planner
classifies (note vs ordinary edit). usage: extract_inline_notes.py doc.docx [--owner "Name"]"""
from __future__ import annotations
import argparse, json, re, sys, zipfile
from lxml import etree
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
q = lambda t, ns=W: f"{{{ns}}}{t}"
NOTE_RX = re.compile(r"\?|\b(source|reference|ref|cite|citation|need|needs|check|confirm|acronym|stand for|unclear|tbc|todo|title|table|figure|activity)\b", re.I)

def ptext(p):
    return "".join(t.text or "" for t in p.iter(q("t")))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("doc"); ap.add_argument("--owner", default="")
    a = ap.parse_args()
    root = etree.fromstring(zipfile.ZipFile(a.doc).read("word/document.xml"))
    body = root.find(q("body")); rows = []; n = 0
    for idx, p in enumerate(body.iter(q("p"))):
        pid = p.get(q("paraId", W14)); full = ptext(p)
        for ins in p.iter(q("ins")):
            au = ins.get(q("author"), "")
            if a.owner and au == a.owner: continue
            txt = "".join(t.text or "" for t in ins.iter(q("t"))).strip()
            if not txt: continue
            n += 1
            rows.append({"note_id": f"N{n:03d}", "kind": "tracked-insertion", "author": au, "text": txt,
                         "likely_note": bool(NOTE_RX.search(txt)) and len(txt) < 400,
                         "paragraph_id": pid, "paragraph_index": idx, "paragraph_text": full[:600]})
        hl = [r for r in p.iter(q("r")) if r.find(f"{q('rPr')}/{q('highlight')}") is not None]
        if hl:
            txt = "".join("".join(t.text or "" for t in r.iter(q("t"))) for r in hl).strip()
            if txt:
                n += 1
                col = hl[0].find(f"{q('rPr')}/{q('highlight')}").get(q("val"))
                rows.append({"note_id": f"N{n:03d}", "kind": "highlight", "author": "", "colour": col, "text": txt[:400],
                             "likely_note": True, "paragraph_id": pid, "paragraph_index": idx, "paragraph_text": full[:600]})
    json.dump(rows, sys.stdout, indent=1, ensure_ascii=False)
    print(f"[extract_inline_notes] {len(rows)} rows, {sum(r['likely_note'] for r in rows)} likely notes", file=sys.stderr)

if __name__ == "__main__":
    main()
