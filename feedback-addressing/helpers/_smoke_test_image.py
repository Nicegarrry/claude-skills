#!/usr/bin/env python3
"""Smoke test for image insertion.

- Generates a tiny 1×1 transparent PNG via stdlib `struct` (no external deps).
- Inserts it after paragraph 0 of a synthetic .docx.
- Validates: word/media/imageN.png exists, [Content_Types] has png Default,
  document.xml has a tracked <w:drawing> with the right rId, the
  surrounding paragraphs are intact.
"""
from __future__ import annotations

import struct
import subprocess
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

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
    <w:p w14:paraId="AAAA0001"><w:r><w:t>Before image.</w:t></w:r></w:p>
    <w:p w14:paraId="AAAA0002"><w:r><w:t>After image.</w:t></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""


def make_tiny_png(out: Path) -> None:
    """Hand-built 1×1 transparent PNG (smallest valid)."""
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(typ: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + typ + data + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))  # 1x1, RGBA, 8 bit
    raw = b"\x00" + b"\x00\x00\x00\x00"  # filter byte + 1 pixel RGBA
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    out.write_bytes(sig + ihdr + idat + iend)


def make_docx(out: Path) -> None:
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CT)
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("word/_rels/document.xml.rels", DOC_RELS)
        zf.writestr("word/document.xml", DOC_XML)


def main() -> int:
    here = Path(__file__).parent
    helper = here / "apply_changes_docx.py"
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        in_doc = tdp / "in.docx"
        out_doc = tdp / "out.docx"
        png = tdp / "tiny.png"
        changes_md = tdp / "changes.md"
        make_docx(in_doc)
        make_tiny_png(png)
        changes_md.write_text(f"""\
feedback_id: IMG01
change_type: insert_image
target_locator: AAAA0001
image_path: {png}
width_emu: 914400
height_emu: 914400
caption_text: Figure 1: Tiny test image.
rationale: smoke test image insertion
""", encoding="utf-8")

        cmd = [sys.executable, str(helper), str(in_doc), str(changes_md), "--out", str(out_doc), "--date", "2026-05-09T00:00:00Z"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print("HELPER FAILED:", r.stdout, r.stderr)
            return 1

        with zipfile.ZipFile(out_doc) as zf:
            names = zf.namelist()
            media = [n for n in names if n.startswith("word/media/")]
            assert media, f"no word/media/ entry; got {names}"
            ct_xml = zf.read("[Content_Types].xml").decode("utf-8")
            doc_xml = zf.read("word/document.xml").decode("utf-8")
            doc_rels = zf.read("word/_rels/document.xml.rels").decode("utf-8")

        # png Default in content-types
        assert 'Extension="png"' in ct_xml, "png content-type Default missing"
        # rels has image relationship
        assert "media/image" in doc_rels and "/image" in doc_rels, f"no image rel in {doc_rels}"
        # extract the rId from the rels and confirm it's referenced in document.xml
        import re
        m = re.search(r'<Relationship[^/]*Type="[^"]*image"[^/]*Id="(rId\d+)"', doc_rels)
        if not m:
            m = re.search(r'<Relationship[^/]*Id="(rId\d+)"[^/]*Type="[^"]*image"', doc_rels)
        assert m, f"could not parse image rId from rels: {doc_rels}"
        rid = m.group(1)
        # The r:embed attribute may be serialised under any prefix; check for
        # the namespaced form by looking for embed="rId..." with the relationships
        # namespace declared somewhere on the same element.
        assert f'embed="{rid}"' in doc_xml, f"document.xml does not reference {rid}: {doc_xml[:500]}"
        # tracked insertion: <w:ins> may serialise under any prefix bound to
        # the wordprocessingml namespace
        assert "ins " in doc_xml or "<w:ins" in doc_xml, "no <w:ins> wrapper for inserted drawing"
        assert "drawing" in doc_xml, "no <w:drawing> in document.xml"
        # original paragraphs still present
        assert "Before image" in doc_xml and "After image" in doc_xml, "surrounding paragraphs lost"
        # caption present
        assert "Figure 1" in doc_xml, "caption text missing"

        print("[smoke:image] PASS — image inserted, content-type registered, rId resolves, captions present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
