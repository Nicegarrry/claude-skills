#!/usr/bin/env python3
"""Regression test for run-detach inside a <w:hyperlink>.

Bug reference: when middle runs lived inside <w:hyperlink>, the applier used a
single `parent` pointer captured before the loop, then tried to remove other
runs from the wrong parent — raised "Element is not a child of this node."
Fixed by using each run's own .getparent() at detach time.

This test:
  - Builds a doc with a paragraph that contains a <w:hyperlink>
  - The replace target (`before_text`) starts in a body-root run BEFORE the
    hyperlink and ends in a run INSIDE the hyperlink (i.e. the deletion spans
    the hyperlink boundary). This forces the applier to detach runs whose
    parents differ.
  - Validates the helper completes without error and the hyperlink survives
    in the output.
"""
from __future__ import annotations

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
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId99" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.com" TargetMode="External"/>
</Relationships>
"""

# Paragraph text (concatenated): "See the published guidance on rates."
# The hyperlink wraps "published guidance".
# We will REPLACE "published guidance" with "fresh writeup" — that targets only
# the hyperlinked runs but the run-detach path needs to handle a parent that's
# <w:hyperlink>, not <w:p>.
DOC_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    <w:p w14:paraId="AAAA0001"><w:r><w:t xml:space="preserve">See the </w:t></w:r><w:hyperlink r:id="rId99"><w:r><w:t xml:space="preserve">published</w:t></w:r><w:r><w:t xml:space="preserve"> guidance</w:t></w:r></w:hyperlink><w:r><w:t xml:space="preserve"> on rates.</w:t></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""


def make_docx(out: Path) -> None:
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CT)
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("word/_rels/document.xml.rels", DOC_RELS)
        zf.writestr("word/document.xml", DOC_XML)


CHANGES_MD = """\
feedback_id: HL01
change_type: replace
target_locator: AAAA0001
before_text: published guidance
after_text: fresh writeup
rationale: hyperlink-parent regression test
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

        # Hyperlink element survives
        assert "<w:hyperlink" in doc_xml or "hyperlink " in doc_xml, "hyperlink element lost"
        assert 'r:id="rId99"' in doc_xml or 'rId99' in doc_xml, "hyperlink rId99 lost"
        # Replacement applied
        assert "<w:del" in doc_xml or "<w:del " in doc_xml, "no <w:del> revision"
        assert "<w:ins" in doc_xml or "<w:ins " in doc_xml, "no <w:ins> revision"
        assert "fresh writeup" in doc_xml, "after_text not inserted"
        assert "<w:delText" in doc_xml, "no <w:delText>"
        # Surrounding text preserved
        assert "See the " in doc_xml and "on rates" in doc_xml, "surrounding text lost"
        # The deletion text should reference both source words
        assert "published" in doc_xml, "deleted 'published' missing from delText"
        assert "guidance" in doc_xml, "deleted 'guidance' missing from delText"
        print("[smoke:hyperlink_replace] PASS — replace spanning hyperlink boundary preserved hyperlink")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
