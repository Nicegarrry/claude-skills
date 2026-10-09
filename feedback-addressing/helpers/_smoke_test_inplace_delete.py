#!/usr/bin/env python3
"""Smoke test v0.8 delete/replace semantics.

  2. runs wrapped in w:del IN PLACE: comment range markers, the comment
     reference run, bookmarks and the hyperlink boundary stay put; replace text
     lands right after the last deleted run.
  3. no double space after a delete (explicit trailing space, or auto).
  5. a cut at offset 0 never creates an empty run.
  6. a delete that empties a paragraph deletes its paragraph mark, unless the
     mark already carries a revision.
  7. replacement runs never inherit reviewer rPrChange/ins/del or highlight.
"""
import sys, tempfile, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from apply_changes_docx import apply
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
RR = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
DR = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.com" TargetMode="External"/></Relationships>'
REV = 'w:author="Reviewer" w:date="2026-10-01T00:00:00Z"'
BODY = [
    # P1 comment-anchored placeholder
    '<w:p w14:paraId="0000AA01"><w:r><w:t xml:space="preserve">Keep </w:t></w:r><w:bookmarkStart w:id="0" w:name="bm"/>'
    '<w:commentRangeStart w:id="5"/><w:r><w:t>[x]</w:t></w:r><w:commentRangeEnd w:id="5"/>'
    '<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="5"/></w:r>'
    '<w:bookmarkEnd w:id="0"/><w:r><w:t xml:space="preserve"> here.</w:t></w:r></w:p>',
    # P2 delete spanning into a hyperlink, auto double-space fix
    '<w:p w14:paraId="0000AA02"><w:r><w:t xml:space="preserve">See the </w:t></w:r><w:proofErr w:type="spellStart"/>'
    '<w:hyperlink r:id="rId9"><w:r><w:t xml:space="preserve">published</w:t></w:r><w:r><w:t xml:space="preserve"> guidance</w:t></w:r></w:hyperlink>'
    '<w:proofErr w:type="spellEnd"/><w:r><w:t xml:space="preserve"> on rates.</w:t></w:r></w:p>',
    # P3 explicit trailing space in before_text
    '<w:p w14:paraId="0000AA03"><w:r><w:t>Alpha beta gamma.</w:t></w:r></w:p>',
    # P4 reviewer insertion at a run boundary (cut at offset 0)
    f'<w:p w14:paraId="0000AA04"><w:r><w:t xml:space="preserve">Hello </w:t></w:r><w:ins w:id="11" {REV}><w:r><w:t>shiny new</w:t></w:r></w:ins>'
    '<w:r><w:t xml:space="preserve"> world.</w:t></w:r></w:p>',
    # P5 emptied paragraph -> mark deleted
    '<w:p w14:paraId="0000AA05"><w:r><w:t>Delete me entirely.</w:t></w:r></w:p>',
    # P6 emptied paragraph whose mark already carries a reviewer insertion -> mark kept
    f'<w:p w14:paraId="0000AA06"><w:pPr><w:rPr><w:ins w:id="12" {REV}/></w:rPr></w:pPr><w:r><w:t>Reviewer line.</w:t></w:r></w:p>',
    # P7 run with reviewer formatting revision + highlight
    f'<w:p w14:paraId="0000AA07"><w:r><w:rPr><w:b/><w:highlight w:val="yellow"/><w:rPrChange w:id="13" {REV}><w:rPr/></w:rPrChange></w:rPr>'
    '<w:t>Old value here.</w:t></w:r></w:p>',
    '<w:p w14:paraId="0000AA08"><w:r><w:t>Last.</w:t></w:r></w:p>',
]
DOC = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}" xmlns:w14="{W14}" xmlns:r="{R}"><w:body>'
       + "".join(BODY) + '<w:sectPr/></w:body></w:document>')
CH = """feedback_id: D1
change_type: replace
target_locator: 0000AA01
before_text: [x]
after_text: value
---
feedback_id: D2
change_type: delete
target_locator: 0000AA02
before_text: the published
---
feedback_id: D3
change_type: delete
target_locator: 0000AA03
before_text: beta
---
feedback_id: D4
change_type: delete
target_locator: 0000AA04
before_text: shiny
---
feedback_id: D5
change_type: delete
target_locator: 0000AA05
before_text: Delete me entirely.
---
feedback_id: D6
change_type: delete
target_locator: 0000AA06
before_text: Reviewer line.
---
feedback_id: D7
change_type: replace
target_locator: 0000AA07
before_text: Old
after_text: New
"""


def q(t):
    return f"{{{W}}}{t}"


def accepted(p):
    return "".join(t.text or "" for t in p.iter(q("t")) if not any(a.tag == q("del") for a in t.iterancestors()))


with tempfile.TemporaryDirectory() as d:
    d = Path(d); src = d / "in.docx"
    with zipfile.ZipFile(src, "w") as z:
        for n, v in (("[Content_Types].xml", CT), ("_rels/.rels", RR), ("word/_rels/document.xml.rels", DR), ("word/document.xml", DOC)):
            z.writestr(n, v)
    (d / "c.md").write_text(CH); out = d / "o.docx"
    a, s, notes = apply(src, d / "c.md", out, "Owner", "2026-10-03T00:00:00Z")
    assert a == 7 and s == 0, notes
    root = etree.fromstring(zipfile.ZipFile(out).read("word/document.xml"))
    P = {p.get(f"{{{W14}}}paraId"): p for p in root.iter(q("p"))}

    # 2. markers in place
    p1 = P["0000AA01"]
    tags = [etree.QName(c).localname for c in p1]
    assert tags == ["r", "bookmarkStart", "commentRangeStart", "del", "ins", "commentRangeEnd", "r", "bookmarkEnd", "r"], tags
    assert p1[3].find(f"{q('r')}/{q('delText')}").text == "[x]"
    assert p1[6].find(q("commentReference")) is not None, "comment reference run moved"
    assert accepted(p1) == "Keep value here.", accepted(p1)
    p2 = P["0000AA02"]
    hl = p2.find(q("hyperlink"))
    assert hl is not None and hl.find(q("del")) is not None, "deletion inside the hyperlink not kept in place"
    assert p2.find(q("del")) is not None and len(p2.findall(q("proofErr"))) == 2
    # 3. no double space
    assert accepted(p2) == "See guidance on rates.", repr(accepted(p2))
    assert accepted(P["0000AA03"]) == "Alpha gamma.", repr(accepted(P["0000AA03"]))
    # 5. no empty runs anywhere
    for r in root.iter(q("r")):
        ts = r.findall(q("t"))
        assert not (ts and all((t.text or "") == "" for t in ts)), "empty run created"
    p4 = P["0000AA04"]
    rins = p4.find(q("ins"))
    assert rins.get(q("author")) == "Reviewer" and rins.find(q("del")) is not None, "delete inside reviewer ins not nested"
    assert accepted(p4) == "Hello new world.", repr(accepted(p4))
    # 6. paragraph mark
    m5 = P["0000AA05"].find(f"{q('pPr')}/{q('rPr')}/{q('del')}")
    assert m5 is not None and m5.get(q("author")) == "Owner", "emptied paragraph mark not deleted"
    m6 = P["0000AA06"].find(f"{q('pPr')}/{q('rPr')}")
    assert m6.find(q("del")) is None and m6.find(q("ins")) is not None, "reviewer-marked paragraph mark touched"
    # 7. clean rPr on replacement
    nrpr = P["0000AA07"].find(f"{q('ins')}/{q('r')}/{q('rPr')}")
    assert nrpr.find(q("b")) is not None, "formatting not cloned"
    assert nrpr.find(q("rPrChange")) is None and nrpr.find(q("highlight")) is None, "reviewer revision / highlight inherited"
    assert accepted(P["0000AA07"]) == "New value here."
    print("OK in-place delete/replace smoke test")
