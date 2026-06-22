#!/usr/bin/env python3
"""Smoke test apply_changes_docx.py with a tiny synthetic .docx.

Builds an in-memory minimal .docx with two paragraphs, runs the helper to
delete one word from para 0 and replace another in para 1, and asserts the
revision markup is present and original content untouched.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOC_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">
  <w:body>
    <w:p w14:paraId="AAAA0001">
      <w:r><w:t xml:space="preserve">The quick brown fox jumps over the lazy dog.</w:t></w:r>
    </w:p>
    <w:p w14:paraId="AAAA0002">
      <w:r><w:t xml:space="preserve">Hello world, this is a test paragraph.</w:t></w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""


def make_synthetic_docx(out: Path) -> None:
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", RELS)
        zf.writestr("word/document.xml", DOC_XML)


CHANGES_MD = """\
feedback_id: F01
change_type: delete
target_locator: AAAA0001
before_text: brown
after_text:
rationale: smoke test delete
---
feedback_id: F02
change_type: replace
target_locator: AAAA0002
before_text: world
after_text: universe
rationale: smoke test replace
"""


def main() -> int:
    here = Path(__file__).parent
    helper = here / "apply_changes_docx.py"
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        in_doc = tdp / "in.docx"
        out_doc = tdp / "out.docx"
        changes_md = tdp / "changes.md"
        make_synthetic_docx(in_doc)
        changes_md.write_text(CHANGES_MD, encoding="utf-8")

        cmd = [sys.executable, str(helper), str(in_doc), str(changes_md), "--out", str(out_doc), "--date", "2026-05-09T00:00:00Z"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(r.stderr)
        if r.returncode != 0:
            print("HELPER FAILED:", r.stdout, r.stderr)
            return 1

        with zipfile.ZipFile(out_doc) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")

        # Assertions
        assert "<w:del " in doc_xml, "no <w:del> revision found"
        assert "<w:ins " in doc_xml, "no <w:ins> revision found"
        assert "<w:delText" in doc_xml and "brown" in doc_xml, "deleted text missing from delText"
        assert "universe" in doc_xml, "inserted text 'universe' missing"
        # original surrounding text preserved
        assert "The quick" in doc_xml and "fox jumps" in doc_xml, "original para 1 text mangled"
        assert "Hello" in doc_xml and "is a test paragraph" in doc_xml, "original para 2 text mangled"
        # author/date attribute set
        assert 'w:author="feedback-addressing"' in doc_xml, "author attr missing"
        print("[smoke] PASS — apply_changes_docx wrote revisions correctly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
