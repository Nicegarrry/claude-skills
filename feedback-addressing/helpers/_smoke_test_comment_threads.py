#!/usr/bin/env python3
"""
Smoke test for v0.4 rule I: comment-reply-chain reading.

Builds a synthetic .docx in memory with:
  - one parent comment (Reviewer A "needs definition")
  - one nested reply (the owner "to do")
… via the same OOXML structure that Word emits (commentRangeStart/End in
document.xml, w:comment in comments.xml, w15:commentEx with paraIdParent
in commentsExtended.xml).

Asserts:
  - extract_feedback returns 2 rows
  - both rows have comment_thread of length 2
  - parent row has [self, reply] roles in order
  - reply row has [parent, self] roles in order
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path

# allow `from extract_feedback import extract`
sys.path.insert(0, str(Path(__file__).parent))
from extract_feedback import extract  # noqa: E402

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
W15_NS = "http://schemas.microsoft.com/office/word/2012/wordml"

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
  <Override PartName="/word/commentsExtended.xml" ContentType="application/vnd.ms-word.commentsExtended+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId10" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
  <Relationship Id="rId11" Type="http://schemas.microsoft.com/office/2011/relationships/commentsExtended" Target="commentsExtended.xml"/>
</Relationships>"""

DOCUMENT_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}" xmlns:w14="{W14_NS}" xmlns:w15="{W15_NS}">
  <w:body>
    <w:p w14:paraId="11111111">
      <w:r><w:t xml:space="preserve">The interconnector has a maximum </w:t></w:r>
      <w:commentRangeStart w:id="100"/>
      <w:commentRangeStart w:id="101"/>
      <w:r><w:t>rating</w:t></w:r>
      <w:commentRangeEnd w:id="100"/>
      <w:commentRangeEnd w:id="101"/>
      <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="100"/></w:r>
      <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="101"/></w:r>
      <w:r><w:t xml:space="preserve"> set by engineering.</w:t></w:r>
    </w:p>
  </w:body>
</w:document>"""

COMMENTS_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}" xmlns:w14="{W14_NS}">
  <w:comment w:id="100" w:author="Reviewer A" w:date="2026-03-31T14:00:00Z" w:initials="RA">
    <w:p w14:paraId="AAAAAA01">
      <w:r><w:t>I would put a footnote here to define rating.</w:t></w:r>
    </w:p>
  </w:comment>
  <w:comment w:id="101" w:author="Document Owner" w:date="2026-05-09T10:00:00Z" w:initials="DO">
    <w:p w14:paraId="BBBBBB02">
      <w:r><w:t>to do</w:t></w:r>
    </w:p>
  </w:comment>
</w:comments>"""

COMMENTS_EXTENDED_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w15:commentsEx xmlns:w15="{W15_NS}">
  <w15:commentEx w15:paraId="AAAAAA01" w15:done="0"/>
  <w15:commentEx w15:paraId="BBBBBB02" w15:paraIdParent="AAAAAA01" w15:done="0"/>
</w15:commentsEx>"""


def build_fixture_docx(out_path: Path) -> None:
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("word/_rels/document.xml.rels", DOC_RELS)
        zf.writestr("word/document.xml", DOCUMENT_XML)
        zf.writestr("word/comments.xml", COMMENTS_XML)
        zf.writestr("word/commentsExtended.xml", COMMENTS_EXTENDED_XML)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        fix = Path(td) / "fixture.docx"
        build_fixture_docx(fix)
        rows = extract(fix)

    print("=== smoke_test_comment_threads ===")
    print(json.dumps(rows, indent=2, ensure_ascii=False))

    assert len(rows) == 2, f"expected 2 rows, got {len(rows)}"

    # Find each by comment_wid
    by_cwid = {r["comment_wid"]: r for r in rows}
    assert "100" in by_cwid and "101" in by_cwid, f"missing cwid 100/101: {list(by_cwid)}"

    parent_row = by_cwid["100"]
    reply_row = by_cwid["101"]

    # Both should have a 2-entry thread
    p_thread = parent_row["comment_thread"]
    r_thread = reply_row["comment_thread"]
    assert len(p_thread) == 2, f"parent thread len={len(p_thread)}: {p_thread}"
    assert len(r_thread) == 2, f"reply thread len={len(r_thread)}: {r_thread}"

    # Parent row's thread: [self (cid=100), reply (cid=101)]
    assert p_thread[0]["comment_id"] == "100" and p_thread[0]["role"] == "self", p_thread[0]
    assert p_thread[1]["comment_id"] == "101" and p_thread[1]["role"] == "reply", p_thread[1]

    # Reply row's thread: [parent (cid=100), self (cid=101)]
    assert r_thread[0]["comment_id"] == "100" and r_thread[0]["role"] == "parent", r_thread[0]
    assert r_thread[1]["comment_id"] == "101" and r_thread[1]["role"] == "self", r_thread[1]

    print("\nALL ASSERTIONS PASSED — comment_thread parsing works end-to-end.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
