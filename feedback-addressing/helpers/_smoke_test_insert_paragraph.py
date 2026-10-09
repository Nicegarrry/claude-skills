#!/usr/bin/env python3
"""Smoke test v0.8 insert_paragraph (plus the `insert` + `new_paragraph` and
`comment-only` + `new_paragraph_after` aliases).

Checks: tracked paragraph mark + w:ins text by the author; chaining on one
target in sequence / file order; before-inserts; pPr cloned with reviewer
revision marks stripped; style reset; italic_text; fresh unique paraIds."""
import sys, tempfile, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from apply_changes_docx import apply
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
CT = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'
RR = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
DR = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'
STY = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/></w:style><w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/></w:style></w:styles>'
REV = 'w:author="Reviewer" w:date="2026-10-01T00:00:00Z"'
DOC = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}" xmlns:w14="{W14}"><w:body>'
       f'<w:p w14:paraId="0AAA0001"><w:r><w:t>Intro.</w:t></w:r></w:p>'
       f'<w:p w14:paraId="11111111"><w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="4"/></w:numPr>'
       f'<w:rPr><w:ins w:id="1" {REV}/><w:b/></w:rPr><w:pPrChange w:id="2" {REV}><w:pPr/></w:pPrChange></w:pPr>'
       f'<w:r><w:rPr><w:b/><w:rPrChange w:id="3" {REV}><w:rPr/></w:rPrChange></w:rPr><w:t>Target.</w:t></w:r></w:p>'
       f'<w:p w14:paraId="0AAA0002"><w:r><w:t>Outro.</w:t></w:r></w:p>'
       f'<w:sectPr/></w:body></w:document>')
CH = """feedback_id: P02
change_type: insert_paragraph
target_locator: 11111111
sequence: 2
after_text: B second
---
feedback_id: P01
change_type: insert_paragraph
target_locator: 11111111
position: after
sequence: 1
after_text: A first
---
feedback_id: P03
change_type: insert
target_locator: 11111111
new_paragraph: after
clone_ppr_from: 11111111
sequence: 3
after_text: C alias insert
---
feedback_id: P04
change_type: comment-only
target_locator: 0AAA0001
new_paragraph_after: 11111111 (end of list)
new_paragraph_text: D alias comment-only with Some Title in it.
italic_text: Some Title
clone_rpr_from: target
---
feedback_id: P05
change_type: insert_paragraph
target_locator: 11111111
position: before
style_name: Heading 1
after_text: H0 heading
---
feedback_id: P06
change_type: insert_paragraph
target_locator: 11111111
position: before
slot_order: 2
after_text: H1 above
"""


def q(t):
    return f"{{{W}}}{t}"


with tempfile.TemporaryDirectory() as d:
    d = Path(d); src = d / "in.docx"
    with zipfile.ZipFile(src, "w") as z:
        for n, v in (("[Content_Types].xml", CT), ("_rels/.rels", RR), ("word/_rels/document.xml.rels", DR),
                     ("word/document.xml", DOC), ("word/styles.xml", STY)):
            z.writestr(n, v)
    (d / "c.md").write_text(CH); out = d / "o.docx"
    a, s, notes = apply(src, d / "c.md", out, "Owner", "2026-10-03T00:00:00Z")
    assert a == 6 and s == 0, notes
    root = etree.fromstring(zipfile.ZipFile(out).read("word/document.xml"))
    ps = list(root.iter(q("p")))
    texts = ["".join(t.text or "" for t in p.iter(q("t"))) for p in ps]
    assert texts == ["Intro.", "H0 heading", "H1 above", "Target.", "A first", "B second", "C alias insert",
                     "D alias comment-only with Some Title in it.", "Outro."], texts
    pids = [p.get(f"{{{W14}}}paraId") for p in ps]
    assert len(set(pids)) == len(pids) and all(int(x, 16) < 0x80000000 for x in pids), pids
    by = dict(zip(texts, ps))
    for t in texts:
        if t in ("Intro.", "Target.", "Outro."):
            continue
        p = by[t]
        ppr = p.find(q("pPr"))
        assert ppr.find(q("pPrChange")) is None, f"{t}: reviewer pPrChange carried over"
        mark = ppr.find(q("rPr"))
        marks = mark.findall(q("ins"))
        assert len(marks) == 1 and marks[0].get(q("author")) == "Owner", f"{t}: mark not tracked by author"
        assert mark.find(q("rPrChange")) is None
        for r in p.findall(q("r")):
            raise AssertionError(f"{t}: untracked run")
        for ins in p.findall(q("ins")):
            assert ins.get(q("author")) == "Owner"
        for rpr in p.iter(q("rPr")):
            assert rpr.find(q("rPrChange")) is None, f"{t}: reviewer rPrChange inherited"
    assert by["A first"].find(f"{q('pPr')}/{q('numPr')}") is not None, "pPr not cloned from target"
    assert by["A first"].find(f"{q('pPr')}/{q('rPr')}/{q('b')}") is None, "source paragraph-mark rPr carried over"
    h0 = by["H0 heading"].find(q("pPr"))
    assert h0.find(q("pStyle")).get(q("val")) == "Heading1" and h0.find(q("numPr")) is None, "style reset failed"
    druns = by["D alias comment-only with Some Title in it."].findall(f"{q('ins')}/{q('r')}")
    ital = [r for r in druns if r.find(f"{q('rPr')}/{q('i')}") is not None]
    assert len(druns) == 3 and len(ital) == 1 and ital[0].find(q("t")).text == "Some Title", "italic_text failed"
    assert all(r.find(f"{q('rPr')}/{q('b')}") is not None for r in druns), "clone_rpr_from: target failed"
    print("OK insert_paragraph smoke test")
