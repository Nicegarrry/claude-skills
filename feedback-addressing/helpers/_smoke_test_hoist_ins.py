#!/usr/bin/env python3
"""Smoke test v0.8 nested-insertion hoist: a replace inside reviewer-inserted
text leaves no author w:ins nested in the reviewer's w:ins; the reviewer's
insertion is split around it and the accepted text reads in order."""
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


BODY = (f'<w:p w14:paraId="0000DD01"><w:r><w:t xml:space="preserve">Intro </w:t></w:r><w:ins w:id="7" {REV}>'
        '<w:r><w:t>the reviewer added this phrase here</w:t></w:r></w:ins><w:r><w:t>.</w:t></w:r></w:p>')
CH = """feedback_id: H1
change_type: replace
target_locator: 0000DD01
before_text: added
after_text: wrote
"""
a, s, notes, P = run(BODY, CH)
assert a == 1, notes
assert any("hoisted 1" in n for n in notes), notes
p = P["0000DD01"]
for ins in p.iter(q("ins")):
    par = ins.getparent()
    assert not (par.tag == q("ins") and ins.get(q("author")) != par.get(q("author"))), "nested insertion left behind"
kids = [(etree.QName(c).localname, c.get(q("author"))) for c in p]
assert kids == [("r", None), ("ins", "Reviewer"), ("ins", "Owner"), ("ins", "Reviewer"), ("r", None)], kids
assert p[1].find(q("del")) is not None, "author deletion should stay nested in the reviewer insertion"
ids = [c.get(q("id")) for c in p.iter(q("ins"))]
assert len(set(ids)) == len(ids), "duplicate revision ids after split"
assert accepted(p) == "Intro the reviewer wrote this phrase here.", repr(accepted(p))
print("OK nested-ins hoist smoke test")
