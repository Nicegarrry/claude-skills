#!/usr/bin/env python3
"""Smoke test for v0.6 reply_comment: a threaded reply authored "Claude"
under an existing reviewer comment, alongside a tracked replace."""
from __future__ import annotations
import sys, tempfile, zipfile
from pathlib import Path
from lxml import etree
sys.path.insert(0, str(Path(__file__).parent))
from apply_changes_docx import apply  # noqa: E402
from extract_feedback import extract  # noqa: E402

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
W15 = "http://schemas.microsoft.com/office/word/2012/wordml"
CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
</Types>"""
RR = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>"""
DR = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId10" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/></Relationships>"""
DOC = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}" xmlns:w14="{W14}"><w:body>
<w:p w14:paraId="11111111"><w:commentRangeStart w:id="5"/><w:r><w:t xml:space="preserve">Prices are incredibly volatile.</w:t></w:r><w:commentRangeEnd w:id="5"/><w:r><w:commentReference w:id="5"/></w:r></w:p>
</w:body></w:document>"""
COM = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W}" xmlns:w14="{W14}"><w:comment w:id="5" w:author="Reviewer A" w:date="2026-10-01T00:00:00Z" w:initials="RA"><w:p><w:r><w:t>Too hyperbolic, cite a number?</w:t></w:r></w:p></w:comment></w:comments>"""
CHANGES = """feedback_id: F01
change_type: replace
target_locator: 11111111
before_text: incredibly volatile
after_text: volatile, moving 40% within a year
---
feedback_id: F01
change_type: reply_comment
comment_id: 5
reply_text: Replaced the intensifier with a sourced range.\\nSee tracked change.
"""
with tempfile.TemporaryDirectory() as d:
    d = Path(d); src = d / "in.docx"
    with zipfile.ZipFile(src, "w") as z:
        for n, v in (("[Content_Types].xml", CT), ("_rels/.rels", RR), ("word/_rels/document.xml.rels", DR),
                     ("word/document.xml", DOC), ("word/comments.xml", COM)):
            z.writestr(n, v)
    ch = d / "c.md"; ch.write_text(CHANGES)
    out = d / "out.docx"
    applied, skipped, notes = apply(src, ch, out, "Nick Pinidiya", "2026-10-03T00:00:00Z")
    assert applied == 2, notes
    z = zipfile.ZipFile(out)
    cm = etree.fromstring(z.read("word/comments.xml"))
    cs = cm.findall(f"{{{W}}}comment")
    assert len(cs) == 2 and cs[1].get(f"{{{W}}}author") == "Claude", "reply missing"
    assert len(cs[1].findall(f".//{{{W}}}br")) == 1, "line break expected"
    ex = etree.fromstring(z.read("word/commentsExtended.xml"))
    rows = ex.findall(f"{{{W15}}}commentEx")
    parent_pid = cs[0].findall(f"{{{W}}}p")[-1].get(f"{{{W14}}}paraId")
    child_pid = cs[1].findall(f"{{{W}}}p")[-1].get(f"{{{W14}}}paraId")
    assert any(r.get(f"{{{W15}}}paraId") == child_pid and r.get(f"{{{W15}}}paraIdParent") == parent_pid for r in rows)
    assert "commentsExtended" in z.read("word/_rels/document.xml.rels").decode()
    assert "commentsExtended" in z.read("[Content_Types].xml").decode()
    doc = z.read("word/document.xml").decode()
    assert doc.count('w:id="6"') == 3, "reply anchors (start, end, reference) missing"
    assert 'w:author="Nick Pinidiya"' in doc and "<w:ins" in doc and "<w:del" in doc
    rows = extract(out)
    assert any(r.get("comment_thread") and len(r["comment_thread"]) == 2 for r in rows), "extractor did not see the thread"
    print("OK reply_comment smoke test")
