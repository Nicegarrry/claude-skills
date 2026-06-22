#!/usr/bin/env python3
"""Smoke test for table insertion.

Inserts a 4-column header + 3 data rows table after paragraph 0 of a synthetic
.docx. Validates the resulting document.xml has a <w:tbl> with 4 rows, each
row carrying a <w:trPr><w:ins/></w:trPr> tracked-insertion marker, and the
header cell contents survive.
"""
from __future__ import annotations

import json
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
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""

DOC_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">
  <w:body>
    <w:p w14:paraId="AAAA0001"><w:r><w:t>Anchor paragraph for table.</w:t></w:r></w:p>
    <w:p w14:paraId="AAAA0002"><w:r><w:t>Following paragraph.</w:t></w:r></w:p>
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


def main() -> int:
    here = Path(__file__).parent
    helper = here / "apply_changes_docx.py"
    headers = ["Lever", "$/tCO2e", "Abatement (Mt)", "Notes"]
    rows = [
        ["Solar PV", "-15", "1.2", "negative-cost"],
        ["Onshore wind", "8", "0.9", "behind grid"],
        ["BESS 4h", "55", "0.4", "MLF risk"],
    ]
    headers_json = json.dumps(headers)
    rows_json = json.dumps(rows)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        in_doc = tdp / "in.docx"
        out_doc = tdp / "out.docx"
        changes_md = tdp / "changes.md"
        make_docx(in_doc)
        changes_md.write_text(f"""\
feedback_id: TBL01
change_type: insert_table
target_locator: AAAA0001
headers: {headers_json}
rows: {rows_json}
caption_text: Table 1: MAC curve summary.
rationale: smoke test table insertion
""", encoding="utf-8")

        cmd = [sys.executable, str(helper), str(in_doc), str(changes_md), "--out", str(out_doc), "--date", "2026-05-09T00:00:00Z"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print("HELPER FAILED:", r.stdout, r.stderr)
            return 1

        with zipfile.ZipFile(out_doc) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")

        # Re-parse to ensure validity and count structure
        from lxml import etree
        tree = etree.fromstring(doc_xml.encode())
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        tbls = tree.findall(f".//{{{W}}}tbl")
        assert len(tbls) == 1, f"expected 1 table, found {len(tbls)}"
        trs = tbls[0].findall(f".//{{{W}}}tr")
        assert len(trs) == 4, f"expected 4 rows (1 header + 3 data), got {len(trs)}"
        # each row has a trPr/ins marker
        for tr in trs:
            ins_marker = tr.find(f"{{{W}}}trPr/{{{W}}}ins")
            assert ins_marker is not None, "row missing trPr>ins tracked-insertion marker"
        # header content survives
        assert "Lever" in doc_xml and "$/tCO2e" in doc_xml, "header cells missing"
        # data content survives
        assert "Solar PV" in doc_xml and "BESS 4h" in doc_xml, "data cells missing"
        # caption present
        assert "Table 1" in doc_xml, "caption missing"
        # surrounding paragraphs intact
        assert "Anchor paragraph" in doc_xml and "Following paragraph" in doc_xml, "surrounding paragraphs lost"

        print(f"[smoke:table] PASS — table inserted ({len(trs)} rows, {len(headers)} cols), tracked-insertion markers present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
