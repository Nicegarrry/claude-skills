#!/usr/bin/env python3
"""Smoke test for footnote insertion.

Builds a synthetic .docx with NO existing footnotes part, inserts 2 footnotes
via apply_changes_docx, and validates:
  - word/footnotes.xml exists and parses
  - the [Content_Types].xml has the footnotes Override
  - word/_rels/document.xml.rels has a footnotes relationship
  - document.xml has 2 <w:footnoteReference> runs wrapped in <w:ins>
  - the original paragraph TEXT is unchanged (only the anchor run was added)
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

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
    <w:p w14:paraId="AAAA0001">
      <w:r><w:t xml:space="preserve">Interconnectors have a maximum rating limit.</w:t></w:r>
    </w:p>
    <w:p w14:paraId="AAAA0002">
      <w:r><w:t xml:space="preserve">Capacity markets reward dispatchable plant.</w:t></w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Normal" w:default="1">
    <w:name w:val="Normal"/>
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
feedback_id: FN01
change_type: footnote
target_locator: AAAA0001
anchor_after_text: rating
footnote_text: The rated capacity is the highest power flow the interconnector can carry continuously.
rationale: footnote test 1
---
feedback_id: FN02
change_type: footnote
target_locator: AAAA0002
footnote_text: SWIS is the South West Interconnected System (Western Australia).
rationale: footnote test 2 (no anchor — appends to paragraph end)
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

        cmd = [
            sys.executable, str(helper), str(in_doc), str(changes_md),
            "--out", str(out_doc), "--date", "2026-05-09T00:00:00Z",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print("HELPER FAILED:", r.stdout, r.stderr)
            return 1

        with zipfile.ZipFile(out_doc) as zf:
            names = zf.namelist()
            assert "word/footnotes.xml" in names, "footnotes.xml missing"
            doc_xml = zf.read("word/document.xml").decode("utf-8")
            footnotes_xml = zf.read("word/footnotes.xml").decode("utf-8")
            ct_xml = zf.read("[Content_Types].xml").decode("utf-8")
            doc_rels = zf.read("word/_rels/document.xml.rels").decode("utf-8")
            styles_xml = zf.read("word/styles.xml").decode("utf-8")

        # 1. content-types override
        assert "word/footnotes.xml" in ct_xml, "[Content_Types] missing footnotes Override"
        # 2. doc rels has footnotes relationship
        assert "footnotes.xml" in doc_rels and "/footnotes" in doc_rels, "doc rels missing footnotes relationship"
        # 3. footnotes.xml has separator + continuationSeparator + 2 real footnotes
        assert 'w:type="separator"' in footnotes_xml, "separator footnote missing"
        assert 'w:type="continuationSeparator"' in footnotes_xml, "continuationSeparator missing"
        # Should have at least 2 footnotes that are NEITHER separator NOR continuationSeparator
        real_fn = re.findall(r'<w:footnote\s+(?![^>]*w:type=)[^>]*w:id="(\d+)"', footnotes_xml)
        # Some attribute orderings put id first — re-check more loosely
        all_ids = re.findall(r'<w:footnote\s+[^>]*w:id="(-?\d+)"', footnotes_xml)
        all_ids_int = sorted(int(x) for x in all_ids)
        non_special = [x for x in all_ids_int if x >= 1]
        assert len(non_special) >= 2, f"expected 2 user footnotes, got ids={all_ids_int}"
        # 4. document.xml has 2 footnoteReference runs wrapped in <w:ins>
        ins_blocks = re.findall(r"<w:ins[^>]*>.*?</w:ins>", doc_xml, flags=re.DOTALL)
        ref_count = sum(1 for b in ins_blocks if "footnoteReference" in b)
        assert ref_count >= 2, f"expected ≥2 tracked footnoteReferences, got {ref_count}"
        # 5. original paragraph text is unchanged (rating + dispatchable plant still present
        # — split runs are OK, but the concatenation must still contain the original strings)
        assert "Interconnectors have a maximum rating" in doc_xml.replace("</w:t><w:t xml:space=\"preserve\">", ""), "para 1 text changed"
        assert "Capacity markets reward dispatchable plant" in doc_xml.replace("</w:t><w:t xml:space=\"preserve\">", ""), "para 2 text changed"
        # 6. styles.xml gained FootnoteReference + FootnoteText
        assert 'w:styleId="FootnoteReference"' in styles_xml, "FootnoteReference style missing"
        assert 'w:styleId="FootnoteText"' in styles_xml, "FootnoteText style missing"

        print("[smoke:footnotes] PASS — 2 real footnotes inserted, references tracked, styles registered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
