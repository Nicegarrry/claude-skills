#!/usr/bin/env python3
"""Smoke test v0.8 `insert`: appends at the TRUE paragraph end (after a
trailing reviewer w:ins), adds a separating space only when needed."""
import sys, tempfile, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from apply_changes_docx import apply
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
CT = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
RR = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
DR = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
REV = 'w:author="Reviewer" w:date="2026-10-01T00:00:00Z"'


def q(t):
    return f"{{{W}}}{t}"


def accepted(p):
    return "".join(t.text or "" for t in p.iter(q("t")) if not any(a.tag == q("del") for a in t.iterancestors()))


def run(body, changes):
    doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}" xmlns:w14="{W14}"><w:body>'
           + body + '<w:sectPr/></w:body></w:document>')
    with tempfile.TemporaryDirectory() as d:
        d = Path(d); src = d / "in.docx"
        with zipfile.ZipFile(src, "w") as z:
            for n, v in (("[Content_Types].xml", CT), ("_rels/.rels", RR), ("word/_rels/document.xml.rels", DR), ("word/document.xml", doc)):
                z.writestr(n, v)
        (d / "c.md").write_text(changes); out = d / "o.docx"
        a, s, notes = apply(src, d / "c.md", out, "Owner", "2026-10-03T00:00:00Z")
        root = etree.fromstring(zipfile.ZipFile(out).read("word/document.xml"))
    return a, s, notes, {p.get(f"{{{W14}}}paraId"): p for p in root.iter(q("p"))}


BODY = (f'<w:p w14:paraId="0000BB01"><w:r><w:t xml:space="preserve">Body text.</w:t></w:r><w:ins w:id="7" {REV}><w:r><w:t xml:space="preserve"> Reviewer tail.</w:t></w:r></w:ins></w:p>'
        '<w:p w14:paraId="0000BB02"><w:r><w:t xml:space="preserve">Ends with space </w:t></w:r></w:p>'
        '<w:p w14:paraId="0000BB03"><w:r><w:t>No stop</w:t></w:r></w:p>')
CH = """feedback_id: I1
change_type: insert
target_locator: 0000BB01
after_text: Added.
---
feedback_id: I2
change_type: insert
target_locator: 0000BB02
after_text: more.
---
feedback_id: I3
change_type: insert
target_locator: 0000BB03
after_text: .
"""
a, s, notes, P = run(BODY, CH)
assert a == 3 and s == 0, notes
p1 = P["0000BB01"]
last = p1[-1]
assert last.tag == q("ins") and last.get(q("author")) == "Owner", "insert not after the reviewer insertion"
assert accepted(p1) == "Body text. Reviewer tail. Added.", repr(accepted(p1))
assert accepted(P["0000BB02"]) == "Ends with space more.", repr(accepted(P["0000BB02"]))
assert accepted(P["0000BB03"]) == "No stop.", repr(accepted(P["0000BB03"]))
print("OK insert-at-end smoke test")
