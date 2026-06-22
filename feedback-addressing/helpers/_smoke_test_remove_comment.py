#!/usr/bin/env python3
"""Smoke test for the ``remove_comment`` change_type in apply_changes_docx.

Builds a synthetic .docx with TWO comments — one authored by "Document Owner"
(allowlisted) and one authored by "Other Reviewer" — runs ``remove_comment``
against both, and asserts:

  * The owner's comment is removed from word/document.xml AND word/comments.xml.
  * The "Other Reviewer" comment is preserved AND the helper raised
    ``RemoveCommentAuthorNotAllowed`` (caught at orchestration level and logged
    as escalated).

The allowlist defaults to EMPTY, so the test passes an explicit
``allowlist=["Document Owner"]`` for the allowed case.
"""
from __future__ import annotations

import datetime as dt
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import apply_changes_docx as acd  # noqa: E402

from lxml import etree  # noqa: E402

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def build_synthetic_docx_with_comments(out_path: Path) -> None:
    """Hand-roll the minimal .docx parts needed for two comments."""
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}">
  <w:body>
    <w:p>
      <w:commentRangeStart w:id="0"/>
      <w:r><w:t xml:space="preserve">First paragraph anchor for the owner.</w:t></w:r>
      <w:commentRangeEnd w:id="0"/>
      <w:r><w:rPr/><w:commentReference w:id="0"/></w:r>
    </w:p>
    <w:p>
      <w:commentRangeStart w:id="1"/>
      <w:r><w:t xml:space="preserve">Second paragraph anchor for Other Reviewer.</w:t></w:r>
      <w:commentRangeEnd w:id="1"/>
      <w:r><w:rPr/><w:commentReference w:id="1"/></w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
""".encode()

    comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W}">
  <w:comment w:id="0" w:author="Document Owner" w:date="2026-05-09T10:00:00Z" w:initials="DO">
    <w:p><w:r><w:t>Owner said something.</w:t></w:r></w:p>
  </w:comment>
  <w:comment w:id="1" w:author="Other Reviewer" w:date="2026-05-09T10:00:00Z" w:initials="OR">
    <w:p><w:r><w:t>Other reviewer said something.</w:t></w:r></w:p>
  </w:comment>
</w:comments>
""".encode()

    rels_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

    doc_rels_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
</Relationships>
"""

    content_types_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
</Types>
"""

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types_xml)
        z.writestr("_rels/.rels", rels_xml)
        z.writestr("word/document.xml", document_xml)
        z.writestr("word/comments.xml", comments_xml)
        z.writestr("word/_rels/document.xml.rels", doc_rels_xml)


def main() -> int:
    with tempfile.TemporaryDirectory() as tdir:
        d = Path(tdir)
        doc_path = d / "fixture.docx"
        build_synthetic_docx_with_comments(doc_path)

        pkg = acd.DocPackage(doc_path)
        body = pkg.get_tree(acd.DocPackage.DOC_PART).find(f"{{{W}}}body")
        assert body is not None
        rev = acd.RevisionFactory(author="feedback-addressing", date_iso=dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

        # The allowlist defaults to EMPTY; pass it explicitly for the allowed case.
        owner_allowlist = ["Document Owner"]

        # Allowed remove (owner's comment id=0)
        ok, note = acd._apply_remove_comment(
            body,
            {"feedback_id": "F-T1", "comment_id": "0", "comment_author": "Document Owner"},
            rev,
            pkg,
            allowlist=owner_allowlist,
        )
        assert ok, f"expected owner's comment removal to succeed: {note}"
        print(f"[smoke] allowed-remove: {note}")

        # Disallowed remove (Other Reviewer id=1)
        raised = False
        try:
            acd._apply_remove_comment(
                body,
                {"feedback_id": "F-T2", "comment_id": "1", "comment_author": "Other Reviewer"},
                rev,
                pkg,
                allowlist=owner_allowlist,
            )
        except acd.RemoveCommentAuthorNotAllowed as exc:
            raised = True
            print(f"[smoke] disallowed-remove correctly raised: {exc}")
        assert raised, "expected RemoveCommentAuthorNotAllowed for non-owner author"

        # Even with a forged claim of "Document Owner" against id=1, helper must
        # cross-check actual author and refuse.
        raised2 = False
        try:
            acd._apply_remove_comment(
                body,
                {"feedback_id": "F-T3", "comment_id": "1", "comment_author": "Document Owner"},
                rev,
                pkg,
                allowlist=owner_allowlist,
            )
        except acd.RemoveCommentAuthorNotAllowed as exc:
            raised2 = True
            print(f"[smoke] forged-claim correctly raised: {exc}")
        assert raised2, "expected helper to cross-check actual author and refuse forged claim"

        # Verify state: comments.xml has only id=1 left; body has no refs to id=0.
        cm_root = pkg.get_tree(acd.DocPackage.COMMENTS_PART)
        ids_left = [c.get(f"{{{W}}}id") for c in cm_root.findall(f"{{{W}}}comment")]
        assert ids_left == ["1"], f"expected only id=1 to remain; got {ids_left}"

        body_refs_id0 = [
            el for el in body.iter()
            if el.tag in (f"{{{W}}}commentRangeStart", f"{{{W}}}commentRangeEnd", f"{{{W}}}commentReference")
            and el.get(f"{{{W}}}id") == "0"
        ]
        assert not body_refs_id0, f"body still has id=0 refs: {body_refs_id0}"

        # Confirm id=1 references intact (since removal was rejected).
        body_refs_id1 = [
            el for el in body.iter()
            if el.tag in (f"{{{W}}}commentRangeStart", f"{{{W}}}commentRangeEnd", f"{{{W}}}commentReference")
            and el.get(f"{{{W}}}id") == "1"
        ]
        assert len(body_refs_id1) == 3, f"expected 3 id=1 refs (start/end/ref); got {len(body_refs_id1)}"

        print("[smoke] OK: remove_comment allowlist enforcement working")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
