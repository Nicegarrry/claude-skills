#!/usr/bin/env python3
"""Smoke test v0.7 add_comment on a docx with NO comments part, anchored inside a reviewer's tracked insertion."""
import sys, tempfile, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from apply_changes_docx import apply
from extract_feedback import extract
W="http://schemas.openxmlformats.org/wordprocessingml/2006/main"; W14="http://schemas.microsoft.com/office/word/2010/wordml"
CT='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
RR='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
DR='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
DOC=f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}" xmlns:w14="{W14}"><w:body><w:p w14:paraId="22222222"><w:r><w:t xml:space="preserve">The LCOE of wind fell. </w:t></w:r><w:ins w:id="7" w:author="Reviewer" w:date="2026-10-01T00:00:00Z"><w:r><w:t>(what does this stand for?)</w:t></w:r></w:ins></w:p></w:body></w:document>'
CH="""feedback_id: N001
change_type: replace
target_locator: 22222222
before_text: The LCOE of wind
after_text: The levelised cost of electricity (LCOE) of wind
---
feedback_id: N001
change_type: add_comment
target_locator: 22222222
anchor_text: (what does this stand for?)
comment_text: Spelled out LCOE at first use. Your note can go.
"""
with tempfile.TemporaryDirectory() as d:
    d=Path(d); src=d/"in.docx"
    with zipfile.ZipFile(src,"w") as z:
        for n,v in (("[Content_Types].xml",CT),("_rels/.rels",RR),("word/_rels/document.xml.rels",DR),("word/document.xml",DOC)): z.writestr(n,v)
    (d/"c.md").write_text(CH); out=d/"o.docx"
    a,s,notes=apply(src,d/"c.md",out,"Owner","2026-10-03T00:00:00Z")
    assert a==2, notes
    z=zipfile.ZipFile(out); doc=z.read("word/document.xml").decode()
    assert "comments.xml" in z.read("word/_rels/document.xml.rels").decode()
    assert "/word/comments.xml" in z.read("[Content_Types].xml").decode()
    assert 'w:author="Reviewer"' in doc, "reviewer insertion lost"
    assert doc.count('commentRangeStart') == 1 and doc.count('commentReference') == 1
    rows=extract(out); assert len(rows)==1 and rows[0]["reviewer"]=="Claude", rows
    print("OK add_comment smoke test")
