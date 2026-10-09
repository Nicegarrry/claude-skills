#!/usr/bin/env python3
"""Smoke test v0.8 delete_footnote_ref: the run holding footnoteReference N is
wrapped in an author w:del; missing / already-deleted refs are skipped."""
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


BODY = ('<w:p w14:paraId="0000CC01"><w:r><w:t>Claim.</w:t></w:r><w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteReference w:id="3"/></w:r>'
        '<w:r><w:t xml:space="preserve"> More.</w:t></w:r></w:p>'
        f'<w:p w14:paraId="0000CC02"><w:r><w:t>Other.</w:t></w:r><w:del w:id="9" {REV}><w:r><w:footnoteReference w:id="4"/></w:r></w:del></w:p>')
CH = """feedback_id: FN1
change_type: delete_footnote_ref
target_locator: 0000CC01
footnote_id: 3
---
feedback_id: FN2
change_type: delete_footnote_ref
target_locator: 0000CC02
footnote_id: 4
---
feedback_id: FN3
change_type: delete_footnote_ref
target_locator: 0000CC02
footnote_id: 99
"""
a, s, notes, P = run(BODY, CH)
assert a == 1 and s == 2, notes
p1 = P["0000CC01"]
d = p1.find(q("del"))
assert d is not None and d.get(q("author")) == "Owner" and d.find(f"{q('r')}/{q('footnoteReference')}").get(q("id")) == "3"
assert [etree.QName(c).localname for c in p1] == ["r", "del", "r"], "footnote ref not deleted in place"
assert accepted(p1) == "Claim. More."
print("OK delete_footnote_ref smoke test")
