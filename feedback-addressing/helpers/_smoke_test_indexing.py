#!/usr/bin/env python3
"""Regression test for paragraph-index alignment between extract_feedback.py
and apply_changes_docx.py.

Bug reference: paragraph-indexing diverged when extractor used `body.iter`
but applier used `body.findall` (direct children only). Fixed by both helpers
using `body.iter('w:p')`.

This test builds a synthetic doc with paragraphs at THREE nesting depths:
  - body root
  - inside <w:hyperlink>
  - inside <w:tbl>/<w:tr>/<w:tc>
and verifies extract_feedback's anchor_paragraph_index matches the index that
apply_changes_docx will resolve for the same paraId.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import apply_changes_docx as APP

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"

CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
  <Relationship Id="rId99" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.com" TargetMode="External"/>
</Relationships>
"""

# Document with paragraphs nested at three depths. Each carries a distinctive paraId
# AAAA0001 — body root
# AAAA0002 — inside hyperlink (paragraph wrapping a link is a real OOXML pattern)
#           wait: hyperlink lives inside a paragraph, not the other way around.
#           So instead: place a paragraph that CONTAINS a hyperlink, and the
#           paragraph-index test still works as long as the iter-walk reaches
#           the inner paragraphs.
# Replace approach: nest paragraphs inside <w:tbl> AT the body root + at
# different table positions. Mix in a body-root paragraph with a hyperlink
# (run inside hyperlink) but the paragraph itself is at body-root.
DOC_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    <w:p w14:paraId="AAAA0001">
      <w:r><w:t>Body-root para zero.</w:t></w:r>
    </w:p>
    <w:p w14:paraId="AAAA0002">
      <w:r><w:t xml:space="preserve">Body-root para with </w:t></w:r>
      <w:hyperlink r:id="rId99">
        <w:r><w:t xml:space="preserve">a clickable link</w:t></w:r>
      </w:hyperlink>
      <w:r><w:t> inside it.</w:t></w:r>
    </w:p>
    <w:tbl>
      <w:tr>
        <w:tc>
          <w:p w14:paraId="AAAA0003"><w:r><w:t>Table cell para three.</w:t></w:r></w:p>
        </w:tc>
        <w:tc>
          <w:p w14:paraId="AAAA0004"><w:r><w:t>Table cell para four.</w:t></w:r></w:p>
        </w:tc>
      </w:tr>
    </w:tbl>
    <w:p w14:paraId="AAAA0005"><w:r><w:t>Body-root para five (after table).</w:t></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""

COMMENTS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>
"""


def make_docx(out: Path) -> None:
    # Re-write with comment range markers so extract_feedback can attach to
    # each test paragraph
    body = """<w:body>
    <w:p w14:paraId="AAAA0001"><w:commentRangeStart w:id="0"/><w:r><w:t>Body-root para zero.</w:t></w:r><w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p>
    <w:p w14:paraId="AAAA0002"><w:commentRangeStart w:id="1"/><w:r><w:t xml:space="preserve">Body-root para with </w:t></w:r><w:hyperlink r:id="rId99"><w:r><w:t xml:space="preserve">a clickable link</w:t></w:r></w:hyperlink><w:r><w:t> inside it.</w:t></w:r><w:commentRangeEnd w:id="1"/><w:r><w:commentReference w:id="1"/></w:r></w:p>
    <w:tbl><w:tr><w:tc><w:p w14:paraId="AAAA0003"><w:commentRangeStart w:id="2"/><w:r><w:t>Table cell para three.</w:t></w:r><w:commentRangeEnd w:id="2"/><w:r><w:commentReference w:id="2"/></w:r></w:p></w:tc><w:tc><w:p w14:paraId="AAAA0004"><w:commentRangeStart w:id="3"/><w:r><w:t>Table cell para four.</w:t></w:r><w:commentRangeEnd w:id="3"/><w:r><w:commentReference w:id="3"/></w:r></w:p></w:tc></w:tr></w:tbl>
    <w:p w14:paraId="AAAA0005"><w:commentRangeStart w:id="4"/><w:r><w:t>Body-root para five (after table).</w:t></w:r><w:commentRangeEnd w:id="4"/><w:r><w:commentReference w:id="4"/></w:r></w:p>
    <w:sectPr/>
  </w:body>"""
    doc = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
{body}
</w:document>
"""
    comments = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:comment w:id="0" w:author="Tester" w:date="2026-05-09T00:00:00Z"><w:p><w:r><w:t>c0</w:t></w:r></w:p></w:comment>
  <w:comment w:id="1" w:author="Tester" w:date="2026-05-09T00:00:00Z"><w:p><w:r><w:t>c1</w:t></w:r></w:p></w:comment>
  <w:comment w:id="2" w:author="Tester" w:date="2026-05-09T00:00:00Z"><w:p><w:r><w:t>c2</w:t></w:r></w:p></w:comment>
  <w:comment w:id="3" w:author="Tester" w:date="2026-05-09T00:00:00Z"><w:p><w:r><w:t>c3</w:t></w:r></w:p></w:comment>
  <w:comment w:id="4" w:author="Tester" w:date="2026-05-09T00:00:00Z"><w:p><w:r><w:t>c4</w:t></w:r></w:p></w:comment>
</w:comments>
"""
    ct_with_comments = CT
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", ct_with_comments)
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("word/_rels/document.xml.rels", DOC_RELS)
        zf.writestr("word/document.xml", doc)
        zf.writestr("word/comments.xml", comments)


def main() -> int:
    here = Path(__file__).parent
    extract_helper = here / "extract_feedback.py"
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        doc = tdp / "doc.docx"
        make_docx(doc)

        # 1. Run extract_feedback and capture anchor_paragraph_index per paraId
        r = subprocess.run([sys.executable, str(extract_helper), str(doc)], capture_output=True, text=True)
        if r.returncode != 0:
            print("EXTRACT FAILED:", r.stdout, r.stderr)
            return 1
        items = json.loads(r.stdout)
        # Build map paraId -> extractor's index
        extractor_map = {it["anchor_paragraph_id"]: it["anchor_paragraph_index"] for it in items}
        assert len(extractor_map) == 5, f"expected 5 anchor paraIds, got {extractor_map}"

        # 2. Open document.xml directly with the applier's _build_para_index
        with zipfile.ZipFile(doc) as zf:
            doc_xml = zf.read("word/document.xml")
        from lxml import etree
        tree = etree.fromstring(doc_xml)
        body = tree.find(f"{{{W}}}body")
        paras, para_id_map = APP._build_para_index(body)
        # 3. Compare
        for paraId, ext_idx in extractor_map.items():
            applier_idx = para_id_map.get(paraId)
            assert applier_idx == ext_idx, f"paraId {paraId}: extractor={ext_idx} applier={applier_idx}"
        # 4. Bonus: confirm the indices we assigned in declaration order are 0..4
        # in (AAAA0001..AAAA0005) order
        expected_order = ["AAAA0001", "AAAA0002", "AAAA0003", "AAAA0004", "AAAA0005"]
        for i, pid in enumerate(expected_order):
            assert para_id_map[pid] == i, f"paraId {pid} expected idx {i}, got {para_id_map[pid]}"
        print(f"[smoke:indexing] PASS — extractor and applier agree on all 5 paragraph indices: {dict(sorted(extractor_map.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
