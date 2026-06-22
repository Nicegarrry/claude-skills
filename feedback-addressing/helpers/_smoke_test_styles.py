#!/usr/bin/env python3
"""Smoke test for apply_style change_type.

Builds a doc where Heading 1 exists in styles.xml but Heading 2 does NOT.
Applies Heading 1 to paragraph 0 (existing-style path) and Heading 2 to
paragraph 1 (dynamic-add path). Validates:
  - both paragraphs end up with <w:pStyle> set to the correct styleId
  - <w:pPrChange> is recorded with author/date
  - styles.xml gains a Heading2 entry
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""

DOC_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">
  <w:body>
    <w:p w14:paraId="AAAA0001"><w:r><w:t>Section heading goes here.</w:t></w:r></w:p>
    <w:p w14:paraId="AAAA0002"><w:r><w:t>Sub-section heading goes here.</w:t></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Normal" w:default="1">
    <w:name w:val="Normal"/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
  </w:style>
</w:styles>
"""


def make_docx(out: Path) -> None:
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CT)
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("word/_rels/document.xml.rels", DOC_RELS)
        zf.writestr("word/document.xml", DOC_XML)
        zf.writestr("word/styles.xml", STYLES_XML)


CHANGES_MD = """\
feedback_id: ST01
change_type: apply_style
target_locator: AAAA0001
style_name: Heading 1
rationale: existing-style path
---
feedback_id: ST02
change_type: apply_style
target_locator: AAAA0002
style_name: Heading 2
rationale: dynamic-add path
"""


def main() -> int:
    here = Path(__file__).parent
    helper = here / "apply_changes_docx.py"
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        in_doc = tdp / "in.docx"
        out_doc = tdp / "out.docx"
        changes_md = tdp / "changes.md"
        make_docx(in_doc)
        changes_md.write_text(CHANGES_MD, encoding="utf-8")

        cmd = [sys.executable, str(helper), str(in_doc), str(changes_md), "--out", str(out_doc), "--date", "2026-05-09T00:00:00Z"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print("HELPER FAILED:", r.stdout, r.stderr)
            return 1

        with zipfile.ZipFile(out_doc) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")
            styles_xml = zf.read("word/styles.xml").decode("utf-8")

        from lxml import etree
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        tree = etree.fromstring(doc_xml.encode())
        paras = list(tree.iter(f"{{{W}}}p"))
        # Find paras with paraId matching our test paragraphs
        para1 = None
        para2 = None
        for p in paras:
            pid = p.get(f"{{http://schemas.microsoft.com/office/word/2010/wordml}}paraId")
            if pid == "AAAA0001":
                para1 = p
            elif pid == "AAAA0002":
                para2 = p
        assert para1 is not None and para2 is not None, "paragraphs missing"

        ps1 = para1.find(f"{{{W}}}pPr/{{{W}}}pStyle")
        ps2 = para2.find(f"{{{W}}}pPr/{{{W}}}pStyle")
        assert ps1 is not None and ps1.get(f"{{{W}}}val") == "Heading1", f"para1 pStyle wrong: {ps1.get(f'{{{W}}}val') if ps1 is not None else None}"
        assert ps2 is not None and ps2.get(f"{{{W}}}val") == "Heading2", f"para2 pStyle wrong: {ps2.get(f'{{{W}}}val') if ps2 is not None else None}"

        # pPrChange recorded
        ppc1 = para1.find(f"{{{W}}}pPr/{{{W}}}pPrChange")
        ppc2 = para2.find(f"{{{W}}}pPr/{{{W}}}pPrChange")
        assert ppc1 is not None and ppc2 is not None, "pPrChange missing"
        assert ppc1.get(f"{{{W}}}author") == "feedback-addressing", "pPrChange author missing"

        # styles.xml gained Heading2 dynamically
        assert 'w:styleId="Heading2"' in styles_xml, "Heading2 was not added to styles.xml"
        # Existing Heading1 preserved
        assert 'w:styleId="Heading1"' in styles_xml, "Heading1 lost"

        print("[smoke:styles] PASS — Heading 1 (existing) + Heading 2 (dynamic-add) applied; pPrChange recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
