#!/usr/bin/env python3
"""
apply_changes_docx.py — apply tracked-changes edits to a .docx, given a
markdown change list per the feedback-addressing skill (SKILL.md step 9).

WHAT IT DOES
------------
- Reads `<doc.docx>` and a markdown changes file with one block per change in
  the format documented below.
- For each change, locates the target paragraph by `paragraph_id`
  (w14:paraId) or fallback `paragraph_index`, then applies the edit using
  native Word revision markup:
    insert  → wrap new text in <w:ins w:id w:author w:date><w:r><w:t>...</w:t></w:r></w:ins>
    delete  → wrap matched run-text in <w:del>...<w:r><w:delText>...</w:delText></w:r></w:del>
    replace → delete the matched text and insert the new text at the same anchor
    comment-only → no doc edit; logged but not applied
- Edits are applied BOTTOM-UP (reverse paragraph order) so locators don't
  shift mid-pass.
- PRESERVES any pre-existing <w:ins> / <w:del> markup (we only ever ADD new
  revisions; we never touch existing ones).
- Sets author/date to the supplied values (defaults: "feedback-addressing" /
  current ISO timestamp).

WHAT IT DOESN'T DO
------------------
- Does NOT regenerate or restructure paragraphs — only insert/delete/replace
  inside an existing paragraph at a specific anchor substring.
- Does NOT validate the change against the original reviewer comment — that's
  the verification (check) step's job.
- Does NOT modify comments.xml — original reviewer comments stay intact.

CHANGE-BLOCK MARKDOWN FORMAT
----------------------------
Each block separated by a `---` line. Within each block, fenced as `key: value`
with one block per change. `target_locator` accepts either a `paragraph_id`
(w14:paraId hex string) or a `paragraph_index` (0-based int).

    feedback_id: F01
    change_type: replace        # insert | delete | replace | comment-only
    target_locator: 6DF65335    # paraId hex OR an int paragraph index
    before_text: incredibly     # required for delete/replace; empty for insert
    after_text: especially       # required for insert/replace; empty for delete
    rationale: shorter, less hyperbolic per reviewer
    evidence_refs: F01

For a `replace`, the helper deletes the FIRST occurrence of `before_text` in
that paragraph, then inserts `after_text` at that anchor. If `before_text` is
not found, the helper logs a warning and SKIPS the change (does not crash).

USAGE
-----
    apply_changes_docx.py <doc.docx> <changes.md> --out <out.docx>
                          [--author NAME] [--date ISO_TIMESTAMP]
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
NSMAP = {"w": W_NS, "w14": W14_NS, "r": R_NS}


def _q(tag: str, ns: str = W_NS) -> str:
    return f"{{{ns}}}{tag}"


def _warn(msg: str) -> None:
    print(f"[apply_changes_docx] WARN: {msg}", file=sys.stderr)


def _info(msg: str) -> None:
    print(f"[apply_changes_docx] {msg}", file=sys.stderr)


# ----- change-file parser ----------------------------------------------------
def parse_changes(md_text: str) -> list[dict[str, str]]:
    """Parse the change-block markdown into a list of dicts."""
    changes: list[dict[str, str]] = []
    blocks = re.split(r"^\s*---\s*$", md_text, flags=re.MULTILINE)
    for raw in blocks:
        raw = raw.strip()
        if not raw:
            continue
        cur: dict[str, str] = {}
        # support multi-line values via leading whitespace continuations
        last_key: str | None = None
        for line in raw.split("\n"):
            if not line.strip():
                continue
            # ignore markdown fence/heading lines that aren't key: value
            if line.lstrip().startswith("#"):
                continue
            m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$", line)
            if m:
                last_key = m.group(1).strip()
                cur[last_key] = m.group(2)
            elif last_key and (line.startswith(" ") or line.startswith("\t")):
                cur[last_key] = (cur.get(last_key, "") + " " + line.strip()).strip()
        if cur.get("change_type") and cur.get("feedback_id"):
            changes.append(cur)
    return changes


# ----- locator → paragraph element ------------------------------------------
def _build_para_index(body: etree._Element) -> tuple[list[etree._Element], dict[str, int]]:
    """
    Enumerate ALL <w:p> in body in document order, including those nested
    inside tables and other containers. This mirrors `extract_feedback.py`'s
    `body.iter('w:p')` traversal so paragraph indices line up across helpers.
    """
    paras = list(body.iter(_q("p")))
    para_id_map: dict[str, int] = {}
    for i, p in enumerate(paras):
        pid = p.get(_q("paraId", W14_NS))
        if pid:
            para_id_map[pid] = i
    return paras, para_id_map


def _resolve_locator(
    locator: str,
    paras: list[etree._Element],
    para_id_map: dict[str, int],
) -> tuple[int, etree._Element] | None:
    if not locator:
        return None
    locator = locator.strip()
    # try paraId first (hex string)
    if locator in para_id_map:
        idx = para_id_map[locator]
        return idx, paras[idx]
    # try int index
    try:
        idx = int(locator)
        if 0 <= idx < len(paras):
            return idx, paras[idx]
    except ValueError:
        pass
    # try "para-{n}" form
    m = re.match(r"^para-(\d+)$", locator)
    if m:
        idx = int(m.group(1))
        if 0 <= idx < len(paras):
            return idx, paras[idx]
    return None


# ----- paragraph text + run scanner -----------------------------------------
def _para_text(p: etree._Element) -> str:
    """Concatenate all <w:t> text in a paragraph (in document order)."""
    return "".join(t.text or "" for t in p.iter(_q("t")))


def _build_text_run_map(p: etree._Element) -> list[tuple[etree._Element, int, int]]:
    """
    For each <w:t> child of a run, return (t_element, start_offset, end_offset)
    where offsets index into the concatenated paragraph text.
    """
    out: list[tuple[etree._Element, int, int]] = []
    pos = 0
    for t in p.iter(_q("t")):
        txt = t.text or ""
        out.append((t, pos, pos + len(txt)))
        pos += len(txt)
    return out


# ----- run / revision factory ------------------------------------------------
class RevisionFactory:
    def __init__(self, author: str, date_iso: str):
        self.author = author
        self.date = date_iso
        self._next_id = 0

    def _id(self) -> str:
        self._next_id += 1
        # use a high base to avoid colliding with any existing w:id values
        return str(900000 + self._next_id)

    def make_ins(self, text: str, run_props: etree._Element | None = None) -> etree._Element:
        ins = etree.SubElement(etree.Element("dummy"), _q("ins"))
        ins.set(_q("id"), self._id())
        ins.set(_q("author"), self.author)
        ins.set(_q("date"), self.date)
        r = etree.SubElement(ins, _q("r"))
        if run_props is not None:
            r.append(_clone(run_props))
        t = etree.SubElement(r, _q("t"))
        t.text = text
        # preserve leading/trailing whitespace
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        ins.getparent().remove(ins)  # detach from dummy
        return ins

    def make_del(self, text: str, run_props: etree._Element | None = None) -> etree._Element:
        delel = etree.SubElement(etree.Element("dummy"), _q("del"))
        delel.set(_q("id"), self._id())
        delel.set(_q("author"), self.author)
        delel.set(_q("date"), self.date)
        r = etree.SubElement(delel, _q("r"))
        if run_props is not None:
            r.append(_clone(run_props))
        dt_el = etree.SubElement(r, _q("delText"))
        dt_el.text = text
        dt_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        delel.getparent().remove(delel)
        return delel


def _clone(el: etree._Element) -> etree._Element:
    return etree.fromstring(etree.tostring(el))


# =============================================================================
# v0.3 additions: footnotes, image insertion, table insertion, apply_style
# =============================================================================


class DocPackage:
    """In-memory representation of the .docx zip parts we care about.

    apply_changes_docx mutates these XML trees and writes them back at the end
    of the run. Lets footnote/image/table/style edits touch multiple parts in
    one pass without re-opening the zip per-edit.
    """

    DOC_PART = "word/document.xml"
    REL_PART = "word/_rels/document.xml.rels"
    CT_PART = "[Content_Types].xml"
    STYLES_PART = "word/styles.xml"
    FOOTNOTES_PART = "word/footnotes.xml"
    FOOTNOTES_REL_PART = "word/_rels/footnotes.xml.rels"
    COMMENTS_PART = "word/comments.xml"
    COMMENTS_EXTENDED_PART = "word/commentsExtended.xml"
    COMMENTS_IDS_PART = "word/commentsIds.xml"
    COMMENTS_EXTENSIBLE_PART = "word/commentsExtensible.xml"

    def __init__(self, docx_path: Path):
        self.path = docx_path
        self._parts: dict[str, bytes] = {}
        with zipfile.ZipFile(docx_path, "r") as zf:
            for name in zf.namelist():
                self._parts[name] = zf.read(name)
        self._trees: dict[str, etree._Element] = {}
        self._dirty: set[str] = set()
        self._media_to_add: dict[str, bytes] = {}  # part_name -> bytes
        # Track next available rId in the document rels (across additions)
        self._next_rel_id_cache: int | None = None

    def has(self, part: str) -> bool:
        return part in self._parts

    def get_tree(self, part: str) -> etree._Element:
        if part in self._trees:
            return self._trees[part]
        if part not in self._parts:
            raise KeyError(f"part not in package: {part}")
        tree = etree.fromstring(self._parts[part])
        self._trees[part] = tree
        return tree

    def set_tree(self, part: str, root: etree._Element) -> None:
        self._trees[part] = root
        self._dirty.add(part)

    def mark_dirty(self, part: str) -> None:
        self._dirty.add(part)

    def add_part(self, part: str, data: bytes) -> None:
        self._parts[part] = data
        self._dirty.add(part)

    def add_media(self, part: str, data: bytes) -> None:
        self._media_to_add[part] = data
        self._parts[part] = data

    def alloc_rel_id(self) -> str:
        """Allocate a fresh rId in word/_rels/document.xml.rels."""
        rels = self.get_tree(self.REL_PART)
        if self._next_rel_id_cache is None:
            max_id = 0
            for rel in rels.iter(f"{{{PKG_REL_NS}}}Relationship"):
                rid = rel.get("Id", "")
                m = re.match(r"^rId(\d+)$", rid)
                if m:
                    max_id = max(max_id, int(m.group(1)))
            self._next_rel_id_cache = max_id
        self._next_rel_id_cache += 1
        return f"rId{self._next_rel_id_cache}"

    def add_relationship(self, rel_part: str, rel_id: str, rel_type: str, target: str) -> None:
        rels = self.get_tree(rel_part)
        rel = etree.SubElement(rels, f"{{{PKG_REL_NS}}}Relationship")
        rel.set("Id", rel_id)
        rel.set("Type", rel_type)
        rel.set("Target", target)
        self._dirty.add(rel_part)

    def ensure_content_type_default(self, ext: str, content_type: str) -> None:
        ct = self.get_tree(self.CT_PART)
        for default in ct.findall(f"{{{CT_NS}}}Default"):
            if default.get("Extension", "").lower() == ext.lower():
                return
        new = etree.SubElement(ct, f"{{{CT_NS}}}Default")
        new.set("Extension", ext)
        new.set("ContentType", content_type)
        self._dirty.add(self.CT_PART)

    def ensure_content_type_override(self, part_name: str, content_type: str) -> None:
        # part_name should start with "/"
        target = part_name if part_name.startswith("/") else "/" + part_name
        ct = self.get_tree(self.CT_PART)
        for ov in ct.findall(f"{{{CT_NS}}}Override"):
            if ov.get("PartName") == target:
                return
        new = etree.SubElement(ct, f"{{{CT_NS}}}Override")
        new.set("PartName", target)
        new.set("ContentType", content_type)
        self._dirty.add(self.CT_PART)

    def write(self, out_path: Path) -> None:
        # Serialise dirty trees
        for part in list(self._dirty):
            if part in self._trees:
                root = self._trees[part]
                self._parts[part] = etree.tostring(
                    root, xml_declaration=True, encoding="UTF-8", standalone=True
                )
        # Write everything to a fresh zip (preserves files, ditches old ZipInfo
        # but that's fine for our purposes — Word doesn't require zipinfo)
        tmp = out_path.with_suffix(out_path.suffix + ".tmp")
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for name, data in self._parts.items():
                zout.writestr(name, data)
        tmp.replace(out_path)


# ----- footnote support ------------------------------------------------------

FOOTNOTES_BOOTSTRAP_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:footnote w:type="separator" w:id="-1">
    <w:p><w:r><w:separator/></w:r></w:p>
  </w:footnote>
  <w:footnote w:type="continuationSeparator" w:id="0">
    <w:p><w:r><w:continuationSeparator/></w:r></w:p>
  </w:footnote>
</w:footnotes>
"""

FOOTNOTES_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes"
FOOTNOTES_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"


def _ensure_footnotes_part(pkg: DocPackage) -> etree._Element:
    if not pkg.has(DocPackage.FOOTNOTES_PART):
        pkg.add_part(DocPackage.FOOTNOTES_PART, FOOTNOTES_BOOTSTRAP_XML.encode("utf-8"))
        # content-type override
        pkg.ensure_content_type_override("/word/footnotes.xml", FOOTNOTES_CONTENT_TYPE)
        # relationship from document.xml.rels → word/footnotes.xml
        rid = pkg.alloc_rel_id()
        pkg.add_relationship(DocPackage.REL_PART, rid, FOOTNOTES_REL_TYPE, "footnotes.xml")
    return pkg.get_tree(DocPackage.FOOTNOTES_PART)


def _alloc_footnote_id(footnotes_root: etree._Element) -> int:
    max_id = 0
    for fn in footnotes_root.findall(_q("footnote")):
        try:
            v = int(fn.get(_q("id"), "0"))
        except ValueError:
            v = 0
            continue
        if v > max_id:
            max_id = v
    return max_id + 1


def _ensure_footnote_styles(pkg: DocPackage) -> None:
    """Make sure FootnoteReference run-style and FootnoteText paragraph-style
    exist in word/styles.xml. If styles.xml itself is missing, do nothing —
    Word will use defaults.
    """
    if not pkg.has(DocPackage.STYLES_PART):
        return
    styles = pkg.get_tree(DocPackage.STYLES_PART)
    have_ref = False
    have_text = False
    for s in styles.findall(_q("style")):
        sid = s.get(_q("styleId"), "")
        if sid == "FootnoteReference":
            have_ref = True
        elif sid == "FootnoteText":
            have_text = True
    if not have_ref:
        s = etree.SubElement(styles, _q("style"))
        s.set(_q("type"), "character")
        s.set(_q("styleId"), "FootnoteReference")
        n = etree.SubElement(s, _q("name"))
        n.set(_q("val"), "footnote reference")
        rPr = etree.SubElement(s, _q("rPr"))
        va = etree.SubElement(rPr, _q("vertAlign"))
        va.set(_q("val"), "superscript")
        pkg.mark_dirty(DocPackage.STYLES_PART)
    if not have_text:
        s = etree.SubElement(styles, _q("style"))
        s.set(_q("type"), "paragraph")
        s.set(_q("styleId"), "FootnoteText")
        n = etree.SubElement(s, _q("name"))
        n.set(_q("val"), "footnote text")
        pkg.mark_dirty(DocPackage.STYLES_PART)


def _build_footnote_body(footnote_id: int, text: str) -> etree._Element:
    """Return a <w:footnote w:id="N"> with one paragraph containing the
    footnote-ref glyph followed by `text`."""
    fn = etree.Element(_q("footnote"))
    fn.set(_q("id"), str(footnote_id))
    p = etree.SubElement(fn, _q("p"))
    pPr = etree.SubElement(p, _q("pPr"))
    pStyle = etree.SubElement(pPr, _q("pStyle"))
    pStyle.set(_q("val"), "FootnoteText")
    # the reference run (small superscript number that appears next to the
    # footnote text in the footnote area)
    r1 = etree.SubElement(p, _q("r"))
    rPr1 = etree.SubElement(r1, _q("rPr"))
    rStyle1 = etree.SubElement(rPr1, _q("rStyle"))
    rStyle1.set(_q("val"), "FootnoteReference")
    etree.SubElement(r1, _q("footnoteRef"))
    # the body run
    r2 = etree.SubElement(p, _q("r"))
    t = etree.SubElement(r2, _q("t"))
    t.text = " " + text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return fn


def _make_footnote_anchor_run(footnote_id: int) -> etree._Element:
    """Build the in-body run that points to the footnote (the superscript number)."""
    r = etree.Element(_q("r"))
    rPr = etree.SubElement(r, _q("rPr"))
    rStyle = etree.SubElement(rPr, _q("rStyle"))
    rStyle.set(_q("val"), "FootnoteReference")
    ref = etree.SubElement(r, _q("footnoteReference"))
    ref.set(_q("id"), str(footnote_id))
    return r


def _apply_footnote(
    p: etree._Element,
    change: dict[str, str],
    rev: RevisionFactory,
    pkg: DocPackage,
) -> tuple[bool, str]:
    fid = change.get("feedback_id", "?")
    footnote_text = change.get("footnote_text", "").strip()
    if not footnote_text:
        return False, f"{fid}: footnote requires footnote_text"
    anchor_after = change.get("anchor_after_text", "").strip()

    footnotes_root = _ensure_footnotes_part(pkg)
    _ensure_footnote_styles(pkg)
    fn_id = _alloc_footnote_id(footnotes_root)
    footnotes_root.append(_build_footnote_body(fn_id, footnote_text))
    pkg.mark_dirty(DocPackage.FOOTNOTES_PART)

    anchor_run = _make_footnote_anchor_run(fn_id)
    # Wrap the anchor run inside a <w:ins> so the insertion is tracked.
    ins = etree.Element(_q("ins"))
    ins.set(_q("id"), rev._id())
    ins.set(_q("author"), rev.author)
    ins.set(_q("date"), rev.date)
    ins.append(anchor_run)

    if anchor_after:
        # Locate anchor_after in paragraph text, split runs at the END of that
        # match, and insert the <w:ins> immediately after.
        para_text = _para_text(p)
        pos = para_text.find(anchor_after)
        if pos < 0:
            # fallback: end-of-paragraph
            anchor_after = ""
        else:
            end = pos + len(anchor_after)
            trmap = _build_text_run_map(p)
            target_t = None
            local_off = 0
            for t_el, s, e in trmap:
                if s <= end < e:
                    target_t = t_el
                    local_off = end - s
                    break
                if end == e:
                    target_t = t_el
                    local_off = end - s
            if target_t is not None:
                left, right = _split_run_at(target_t, local_off)
                # Insert ins after `left` in left's parent
                left_parent = left.getparent()
                if left_parent is not None:
                    insert_idx = left_parent.index(left) + 1
                    left_parent.insert(insert_idx, ins)
                    return True, f"{fid}: footnote inserted after {anchor_after!r} (id={fn_id})"

    # Default: append to end of paragraph
    last_run_parent = None
    last_run = None
    for child in p:
        if child.tag == _q("r"):
            last_run = child
            last_run_parent = p
    if last_run is not None and last_run_parent is not None:
        last_run.addnext(ins)
    else:
        p.append(ins)
    return True, f"{fid}: footnote appended at paragraph end (id={fn_id})"


# ----- image insertion -------------------------------------------------------

IMAGE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

IMAGE_MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
    "tif": "image/tiff",
}


def _next_image_filename(pkg: DocPackage, ext: str) -> str:
    """Find an unused filename word/media/imageN.ext."""
    n = 1
    while True:
        name = f"word/media/image{n}.{ext}"
        if name not in pkg._parts:
            return name
        n += 1


def _build_drawing(rid: str, width_emu: int, height_emu: int, pic_id: int = 1, name: str = "Picture") -> etree._Element:
    """Construct a <w:drawing> wrapping an <wp:inline>...<a:blip r:embed="rid"/>."""
    # Use Clark notation throughout — lxml expands these properly.
    drawing = etree.Element(_q("drawing"))
    inline = etree.SubElement(drawing, f"{{{WP_NS}}}inline")
    inline.set("distT", "0")
    inline.set("distB", "0")
    inline.set("distL", "0")
    inline.set("distR", "0")
    extent = etree.SubElement(inline, f"{{{WP_NS}}}extent")
    extent.set("cx", str(width_emu))
    extent.set("cy", str(height_emu))
    eee = etree.SubElement(inline, f"{{{WP_NS}}}effectExtent")
    eee.set("l", "0"); eee.set("t", "0"); eee.set("r", "0"); eee.set("b", "0")
    docPr = etree.SubElement(inline, f"{{{WP_NS}}}docPr")
    docPr.set("id", str(pic_id))
    docPr.set("name", name)
    cNvGr = etree.SubElement(inline, f"{{{WP_NS}}}cNvGraphicFramePr")
    locks = etree.SubElement(cNvGr, f"{{{A_NS}}}graphicFrameLocks")
    locks.set("noChangeAspect", "1")
    graphic = etree.SubElement(inline, f"{{{A_NS}}}graphic")
    graphic_data = etree.SubElement(graphic, f"{{{A_NS}}}graphicData")
    graphic_data.set("uri", PIC_NS)
    pic = etree.SubElement(graphic_data, f"{{{PIC_NS}}}pic")
    nvPicPr = etree.SubElement(pic, f"{{{PIC_NS}}}nvPicPr")
    cNvPr = etree.SubElement(nvPicPr, f"{{{PIC_NS}}}cNvPr")
    cNvPr.set("id", "0")
    cNvPr.set("name", name)
    etree.SubElement(nvPicPr, f"{{{PIC_NS}}}cNvPicPr")
    blipFill = etree.SubElement(pic, f"{{{PIC_NS}}}blipFill")
    blip = etree.SubElement(blipFill, f"{{{A_NS}}}blip")
    blip.set(f"{{{R_NS}}}embed", rid)
    stretch = etree.SubElement(blipFill, f"{{{A_NS}}}stretch")
    etree.SubElement(stretch, f"{{{A_NS}}}fillRect")
    spPr = etree.SubElement(pic, f"{{{PIC_NS}}}spPr")
    xfrm = etree.SubElement(spPr, f"{{{A_NS}}}xfrm")
    off = etree.SubElement(xfrm, f"{{{A_NS}}}off")
    off.set("x", "0"); off.set("y", "0")
    ext = etree.SubElement(xfrm, f"{{{A_NS}}}ext")
    ext.set("cx", str(width_emu))
    ext.set("cy", str(height_emu))
    prstGeom = etree.SubElement(spPr, f"{{{A_NS}}}prstGeom")
    prstGeom.set("prst", "rect")
    etree.SubElement(prstGeom, f"{{{A_NS}}}avLst")
    return drawing


def _wrap_in_ins(rev: RevisionFactory, child_run: etree._Element) -> etree._Element:
    ins = etree.Element(_q("ins"))
    ins.set(_q("id"), rev._id())
    ins.set(_q("author"), rev.author)
    ins.set(_q("date"), rev.date)
    ins.append(child_run)
    return ins


def _apply_insert_image(
    p: etree._Element,
    change: dict[str, str],
    rev: RevisionFactory,
    pkg: DocPackage,
    paras: list[etree._Element],
    target_idx: int,
) -> tuple[bool, str]:
    fid = change.get("feedback_id", "?")
    img_path_str = change.get("image_path", "").strip()
    if not img_path_str:
        return False, f"{fid}: insert_image requires image_path"
    img_path = Path(img_path_str)
    if not img_path.exists():
        return False, f"{fid}: insert_image image not found at {img_path_str}"
    try:
        width_emu = int(change.get("width_emu", "5400000"))
    except ValueError:
        width_emu = 5400000
    # Default 4:3 aspect ratio if no height supplied
    try:
        height_emu = int(change.get("height_emu", str(int(width_emu * 0.75))))
    except ValueError:
        height_emu = int(width_emu * 0.75)
    caption = change.get("caption_text", "").strip()

    ext = img_path.suffix.lstrip(".").lower()
    if ext not in IMAGE_MIME:
        return False, f"{fid}: unsupported image extension {ext!r}"

    # Copy image bytes into package
    media_part = _next_image_filename(pkg, ext)
    pkg.add_media(media_part, img_path.read_bytes())
    pkg.ensure_content_type_default(ext, IMAGE_MIME[ext])
    # Add relationship: target relative to word/, so "media/imageN.ext"
    rid = pkg.alloc_rel_id()
    pkg.add_relationship(DocPackage.REL_PART, rid, IMAGE_REL_TYPE, media_part[len("word/"):])

    # Build the new paragraph(s)
    body = paras[target_idx].getparent()
    target_p = paras[target_idx]
    insert_index = body.index(target_p) + 1

    img_p = etree.Element(_q("p"))
    # apply optional style
    style_name = change.get("style_name", "").strip()
    if style_name:
        sid = _resolve_style_id(pkg, style_name)
        if sid:
            img_pPr = etree.SubElement(img_p, _q("pPr"))
            ps = etree.SubElement(img_pPr, _q("pStyle"))
            ps.set(_q("val"), sid)
    img_run = etree.Element(_q("r"))
    img_run.append(_build_drawing(rid, width_emu, height_emu, pic_id=1, name=img_path.stem))
    # Wrap the run in <w:ins>
    img_p.append(_wrap_in_ins(rev, img_run))

    body.insert(insert_index, img_p)

    if caption:
        cap_p = etree.Element(_q("p"))
        cap_pPr = etree.SubElement(cap_p, _q("pPr"))
        # try Caption style if it exists
        caption_sid = _resolve_style_id(pkg, "Caption")
        if caption_sid:
            ps = etree.SubElement(cap_pPr, _q("pStyle"))
            ps.set(_q("val"), caption_sid)
        else:
            # fall back: italic + centered direct formatting
            jc = etree.SubElement(cap_pPr, _q("jc"))
            jc.set(_q("val"), "center")
        cap_run = etree.Element(_q("r"))
        cap_rPr = etree.SubElement(cap_run, _q("rPr"))
        if not caption_sid:
            etree.SubElement(cap_rPr, _q("i"))
        cap_t = etree.SubElement(cap_run, _q("t"))
        cap_t.text = caption
        cap_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        cap_p.append(_wrap_in_ins(rev, cap_run))
        body.insert(insert_index + 1, cap_p)

    return True, f"{fid}: image inserted ({media_part}, rid={rid})"


# ----- table insertion -------------------------------------------------------


def _build_table(headers: list[str], rows: list[list[str]], rev: RevisionFactory, table_style_id: str | None) -> etree._Element:
    tbl = etree.Element(_q("tbl"))
    tblPr = etree.SubElement(tbl, _q("tblPr"))
    if table_style_id:
        ts = etree.SubElement(tblPr, _q("tblStyle"))
        ts.set(_q("val"), table_style_id)
    tblW = etree.SubElement(tblPr, _q("tblW"))
    tblW.set(_q("w"), "0")
    tblW.set(_q("type"), "auto")
    # Always emit minimal borders so a table without TableGrid still renders.
    tblBorders = etree.SubElement(tblPr, _q("tblBorders"))
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = etree.SubElement(tblBorders, _q(side))
        b.set(_q("val"), "single")
        b.set(_q("sz"), "4")
        b.set(_q("space"), "0")
        b.set(_q("color"), "auto")
    # Grid
    n_cols = max(len(headers), max((len(r) for r in rows), default=0)) or 1
    grid = etree.SubElement(tbl, _q("tblGrid"))
    for _ in range(n_cols):
        gc = etree.SubElement(grid, _q("gridCol"))
        gc.set(_q("w"), "2000")

    def _cell(text: str, bold: bool = False) -> etree._Element:
        tc = etree.Element(_q("tc"))
        tcPr = etree.SubElement(tc, _q("tcPr"))
        tcW = etree.SubElement(tcPr, _q("tcW"))
        tcW.set(_q("w"), "2000")
        tcW.set(_q("type"), "dxa")
        cp = etree.SubElement(tc, _q("p"))
        cr = etree.SubElement(cp, _q("r"))
        if bold:
            crPr = etree.SubElement(cr, _q("rPr"))
            etree.SubElement(crPr, _q("b"))
        ct = etree.SubElement(cr, _q("t"))
        ct.text = text
        ct.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return tc

    def _row_with_ins_marker(cells: list[etree._Element]) -> etree._Element:
        tr = etree.Element(_q("tr"))
        trPr = etree.SubElement(tr, _q("trPr"))
        ins_marker = etree.SubElement(trPr, _q("ins"))
        ins_marker.set(_q("id"), rev._id())
        ins_marker.set(_q("author"), rev.author)
        ins_marker.set(_q("date"), rev.date)
        for c in cells:
            tr.append(c)
        return tr

    # Header row
    if headers:
        header_cells = [_cell(h, bold=True) for h in headers]
        # pad to n_cols
        while len(header_cells) < n_cols:
            header_cells.append(_cell(""))
        tbl.append(_row_with_ins_marker(header_cells))
    # Data rows
    for row in rows:
        cells = [_cell(c) for c in row]
        while len(cells) < n_cols:
            cells.append(_cell(""))
        tbl.append(_row_with_ins_marker(cells))
    return tbl


def _apply_insert_table(
    p: etree._Element,
    change: dict[str, str],
    rev: RevisionFactory,
    pkg: DocPackage,
    paras: list[etree._Element],
    target_idx: int,
) -> tuple[bool, str]:
    fid = change.get("feedback_id", "?")
    headers_raw = change.get("headers", "")
    rows_raw = change.get("rows", "")

    # Parse headers/rows. We accept JSON-list-style or pipe-separated.
    import json as _json

    def _parse_list_field(val: str) -> Any:
        v = val.strip()
        if not v:
            return []
        if v.startswith("[") or v.startswith('"'):
            try:
                return _json.loads(v)
            except Exception:
                pass
        # pipe-separated single row
        return [x.strip() for x in v.split("|")]

    try:
        headers = _parse_list_field(headers_raw)
        rows_obj = _parse_list_field(rows_raw)
    except Exception as e:
        return False, f"{fid}: insert_table failed to parse headers/rows: {e}"

    # rows could be list-of-lists or single list (interpret as one row)
    if rows_obj and not isinstance(rows_obj[0], list):
        rows = [rows_obj]
    else:
        rows = rows_obj

    if not headers and not rows:
        return False, f"{fid}: insert_table requires at least headers or rows"

    table_style_id = _resolve_style_id(pkg, "TableGrid") or _resolve_style_id(pkg, "Table Grid")
    tbl = _build_table(headers, rows, rev, table_style_id)
    caption = change.get("caption_text", "").strip()

    body = paras[target_idx].getparent()
    target_p = paras[target_idx]
    insert_index = body.index(target_p) + 1
    body.insert(insert_index, tbl)

    if caption:
        cap_p = etree.Element(_q("p"))
        cap_pPr = etree.SubElement(cap_p, _q("pPr"))
        caption_sid = _resolve_style_id(pkg, "Caption")
        if caption_sid:
            ps = etree.SubElement(cap_pPr, _q("pStyle"))
            ps.set(_q("val"), caption_sid)
        else:
            jc = etree.SubElement(cap_pPr, _q("jc"))
            jc.set(_q("val"), "center")
        cap_run = etree.Element(_q("r"))
        cap_rPr = etree.SubElement(cap_run, _q("rPr"))
        if not caption_sid:
            etree.SubElement(cap_rPr, _q("i"))
        cap_t = etree.SubElement(cap_run, _q("t"))
        cap_t.text = caption
        cap_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        cap_p.append(_wrap_in_ins(rev, cap_run))
        body.insert(insert_index + 1, cap_p)

    return True, f"{fid}: table inserted ({len(headers)} cols × {len(rows)} rows)"


# ----- apply_style -----------------------------------------------------------


def _resolve_style_id(pkg: DocPackage, friendly_name: str) -> str | None:
    """Look up a style by w:name (case-insensitive) and return its w:styleId.

    Returns None if styles.xml is missing or the style isn't found.
    """
    if not pkg.has(DocPackage.STYLES_PART):
        return None
    styles = pkg.get_tree(DocPackage.STYLES_PART)
    target = friendly_name.strip().lower()
    # Exact w:name match first
    for s in styles.findall(_q("style")):
        n = s.find(_q("name"))
        if n is not None:
            v = n.get(_q("val"), "").strip().lower()
            if v == target:
                return s.get(_q("styleId"))
    # styleId match (e.g. user passed "Heading1")
    for s in styles.findall(_q("style")):
        sid = s.get(_q("styleId"), "")
        if sid.lower() == target.replace(" ", "").lower():
            return sid
    return None


def _ensure_style(pkg: DocPackage, friendly_name: str, style_type: str = "paragraph") -> str:
    """Return the styleId for `friendly_name`, creating a minimal shell if absent.

    Heading 1 → Heading1, etc. Headings + Title also get a default basedOn ref.
    """
    sid = _resolve_style_id(pkg, friendly_name)
    if sid:
        return sid
    if not pkg.has(DocPackage.STYLES_PART):
        # No styles.xml — bail and let the change apply with a synthetic id;
        # Word can resolve display from defaults. But the safer path is: skip.
        return friendly_name.replace(" ", "")
    styles = pkg.get_tree(DocPackage.STYLES_PART)
    # Build a styleId by stripping spaces
    new_sid = friendly_name.replace(" ", "")
    s = etree.SubElement(styles, _q("style"))
    s.set(_q("type"), style_type)
    s.set(_q("styleId"), new_sid)
    n = etree.SubElement(s, _q("name"))
    n.set(_q("val"), friendly_name)
    pkg.mark_dirty(DocPackage.STYLES_PART)
    return new_sid


def _apply_style(
    p: etree._Element,
    change: dict[str, str],
    rev: RevisionFactory,
    pkg: DocPackage,
) -> tuple[bool, str]:
    fid = change.get("feedback_id", "?")
    style_name = change.get("style_name", "").strip()
    if not style_name:
        return False, f"{fid}: apply_style requires style_name"
    sid = _ensure_style(pkg, style_name)
    # Capture the prior pPr for pPrChange. If no pPr, prior is empty.
    pPr = p.find(_q("pPr"))
    prior_pPr_clone = _clone(pPr) if pPr is not None else etree.Element(_q("pPr"))
    if pPr is None:
        pPr = etree.Element(_q("pPr"))
        # pPr must be first child of <w:p> per OOXML schema
        p.insert(0, pPr)
    # Replace any existing pStyle
    for existing in pPr.findall(_q("pStyle")):
        pPr.remove(existing)
    pStyle = etree.Element(_q("pStyle"))
    pStyle.set(_q("val"), sid)
    pPr.insert(0, pStyle)
    # Remove any prior pPrChange and add a fresh one
    for existing in pPr.findall(_q("pPrChange")):
        pPr.remove(existing)
    pPrChange = etree.SubElement(pPr, _q("pPrChange"))
    pPrChange.set(_q("id"), rev._id())
    pPrChange.set(_q("author"), rev.author)
    pPrChange.set(_q("date"), rev.date)
    # The prior pPr lives inside pPrChange but must NOT contain another pPrChange
    # to avoid recursion.
    for nested in prior_pPr_clone.findall(_q("pPrChange")):
        prior_pPr_clone.remove(nested)
    pPrChange.append(prior_pPr_clone)
    return True, f"{fid}: applied style {style_name!r} (styleId={sid})"


# ----- remove_comment (v0.3) ------------------------------------------------


W15_NS = "http://schemas.microsoft.com/office/word/2012/wordml"


class RemoveCommentAuthorNotAllowed(Exception):
    """Raised when the helper is asked to remove a comment whose author is not
    in the configured allowlist. Caller should catch and log as ``escalated``."""


def _comment_author_allowlist() -> list[str]:
    """Allowlist of comment authors whose comments may be removed.

    Default: EMPTY — no comment may be removed unless you opt in. Set the env
    var ``FA_REMOVE_COMMENT_AUTHORS`` (comma-separated) to the author name(s)
    you own (typically your own display name as it appears in ``word/comments.xml``).
    Reviewer comments must never be removed, so they should never be listed here.
    """
    import os

    raw = os.environ.get("FA_REMOVE_COMMENT_AUTHORS", "").strip()
    if raw:
        return [s.strip() for s in raw.split(",") if s.strip()]
    return []


def _strip_w15_paraid(elem: etree._Element) -> None:
    """Drop w15:paraId / w15:paraIdParent off a single element if present."""
    for k in (f"{{{W15_NS}}}paraId", f"{{{W15_NS}}}paraIdParent"):
        if k in elem.attrib:
            del elem.attrib[k]


def _remove_comment_from_doc_xml(body: etree._Element, comment_wid: str) -> int:
    """Remove ``<w:commentRangeStart w:id=N>``, ``<w:commentRangeEnd w:id=N>``,
    and any ``<w:r>`` whose only payload is ``<w:commentReference w:id=N/>``
    from the body. Returns the count of elements removed."""
    removed = 0
    # commentRangeStart and commentRangeEnd are direct anchors; commentReference
    # is wrapped in a run and used inside <w:p>/<w:hyperlink>/etc.
    for tag in ("commentRangeStart", "commentRangeEnd"):
        for el in list(body.iter(_q(tag))):
            if el.get(_q("id")) == comment_wid:
                parent = el.getparent()
                if parent is not None:
                    parent.remove(el)
                    removed += 1
    # commentReference: remove the wrapping <w:r> entirely if it ONLY contains
    # the commentReference (typical Word output). If the run holds other
    # children, just strip the commentReference element.
    for ref in list(body.iter(_q("commentReference"))):
        if ref.get(_q("id")) != comment_wid:
            continue
        run = ref.getparent()
        if run is None:
            continue
        # Decide: lone commentReference inside the run? remove the run.
        siblings = [c for c in run if c is not ref and c.tag != _q("rPr")]
        if not siblings:
            run_parent = run.getparent()
            if run_parent is not None:
                run_parent.remove(run)
                removed += 1
        else:
            run.remove(ref)
            removed += 1
    return removed


def _remove_comment_from_comments_xml(pkg: DocPackage, comment_wid: str, expected_author: str | None) -> tuple[bool, str | None]:
    """Remove the <w:comment w:id=N> element from word/comments.xml. Returns
    ``(removed_bool, actual_author)``. If the comment isn't found, returns
    ``(False, None)``."""
    if not pkg.has(DocPackage.COMMENTS_PART):
        return False, None
    comments = pkg.get_tree(DocPackage.COMMENTS_PART)
    target = None
    for c in comments.findall(_q("comment")):
        if c.get(_q("id")) == comment_wid:
            target = c
            break
    if target is None:
        return False, None
    actual_author = target.get(_q("author"), "")
    comments.remove(target)
    pkg.mark_dirty(DocPackage.COMMENTS_PART)
    return True, actual_author


def _scrub_comment_in_aux_part(pkg: DocPackage, part_name: str, comment_wid: str, paraid_keys: set[str] | None = None) -> int:
    """Walk an aux part (commentsExtended / commentsIds / commentsExtensible)
    and remove rows that reference ``comment_wid``. The shape is consistent
    across the three parts: rows live as direct children of the root and are
    keyed by either ``w:id`` or ``w15:paraId``. We strip rows whose ``w:id``
    matches; we cannot reliably correlate paraId without context, so we leave
    those (Word will simply ignore an orphaned paraId row).
    """
    if not pkg.has(part_name):
        return 0
    root = pkg.get_tree(part_name)
    removed = 0
    for child in list(root):
        wid = child.get(_q("id"))
        if wid == comment_wid:
            root.remove(child)
            removed += 1
            continue
        # commentsExtended uses w15:paraIdParent — but without a doc-side
        # paraId mapping, leave alone. Word tolerates orphaned rows.
    if removed:
        pkg.mark_dirty(part_name)
    return removed


def _apply_remove_comment(
    body: etree._Element,
    change: dict[str, str],
    rev: RevisionFactory,
    pkg: DocPackage,
    allowlist: list[str] | None = None,
) -> tuple[bool, str]:
    """Remove a Word comment by id, after verifying the author is allowed.

    Schema:
      change_type: remove_comment
      feedback_id: F01
      comment_id: 0           (the w:id of the comment)
      comment_author: <your own display name>

    Helper-level allowlist enforcement: if ``comment_author`` is not in the
    configured allowlist (default EMPTY; set via env ``FA_REMOVE_COMMENT_AUTHORS``),
    the helper raises ``RemoveCommentAuthorNotAllowed``. The orchestration layer
    should catch and log the change as ``escalated``. Reviewer comments must
    never be removed — only authors you explicitly allowlist (i.e. yourself)."""
    fid = change.get("feedback_id", "?")
    wid = (change.get("comment_id", "") or "").strip()
    author_claim = (change.get("comment_author", "") or "").strip()
    if not wid:
        return False, f"{fid}: remove_comment requires comment_id"
    allow = allowlist if allowlist is not None else _comment_author_allowlist()
    if author_claim and author_claim not in allow:
        raise RemoveCommentAuthorNotAllowed(
            f"{fid}: comment_author={author_claim!r} not in allowlist {allow}"
        )

    # Verify by reading actual author from comments.xml when possible.
    actual_author = None
    if pkg.has(DocPackage.COMMENTS_PART):
        cm = pkg.get_tree(DocPackage.COMMENTS_PART)
        for c in cm.findall(_q("comment")):
            if c.get(_q("id")) == wid:
                actual_author = c.get(_q("author"), "")
                break
    if actual_author is not None and actual_author not in allow:
        raise RemoveCommentAuthorNotAllowed(
            f"{fid}: actual comment author={actual_author!r} not in allowlist {allow}"
        )

    # Belt + braces: also reject if the asserted author doesn't match the
    # actual author when both are known.
    if actual_author is not None and author_claim and actual_author != author_claim:
        raise RemoveCommentAuthorNotAllowed(
            f"{fid}: claimed author={author_claim!r} ≠ actual={actual_author!r}"
        )

    body_removed = _remove_comment_from_doc_xml(body, wid)
    cm_removed, _ = _remove_comment_from_comments_xml(pkg, wid, actual_author or author_claim)
    aux_removed = 0
    aux_removed += _scrub_comment_in_aux_part(pkg, DocPackage.COMMENTS_EXTENDED_PART, wid)
    aux_removed += _scrub_comment_in_aux_part(pkg, DocPackage.COMMENTS_IDS_PART, wid)
    aux_removed += _scrub_comment_in_aux_part(pkg, DocPackage.COMMENTS_EXTENSIBLE_PART, wid)

    if not (body_removed or cm_removed):
        return False, f"{fid}: remove_comment id={wid!r} not found in body or comments.xml"

    return True, (
        f"{fid}: removed comment id={wid} (body refs={body_removed}, comments.xml={cm_removed}, "
        f"aux rows={aux_removed}, author={actual_author or author_claim!r})"
    )


# ----- core edit operation ---------------------------------------------------
def _split_run_at(t_el: etree._Element, local_offset: int) -> tuple[etree._Element, etree._Element | None]:
    """
    Split the parent run of `t_el` so that the first part contains text up to
    `local_offset` (exclusive) and the second part contains the rest. Returns
    (left_run, right_run_or_None). The original run is replaced in its
    parent. local_offset is in characters within t_el.text.
    """
    txt = t_el.text or ""
    if local_offset <= 0:
        # Whole text moves to the right; return (None_left, original)
        # But we need a left_run — return the run with empty text.
        run = t_el.getparent()
        # Create a left run by cloning run and emptying text
        idx = run.getparent().index(run)
        left = _clone(run)
        for tt in left.iter(_q("t")):
            tt.text = ""
        run.getparent().insert(idx, left)
        return left, run
    if local_offset >= len(txt):
        # All text in left; right is empty
        return t_el.getparent(), None

    run = t_el.getparent()
    parent = run.getparent()
    idx = parent.index(run)
    left = _clone(run)
    right = _clone(run)
    # Find corresponding t in clones (same xpath position)
    # Simple approach: assume single <w:t> per run for split. If multi-t,
    # split the matching t in each clone and clear surrounding text in the
    # opposite clone.
    # Locate this t by enumerating
    src_ts = list(run.iter(_q("t")))
    t_idx = src_ts.index(t_el)
    left_ts = list(left.iter(_q("t")))
    right_ts = list(right.iter(_q("t")))
    for j, (lt, rt) in enumerate(zip(left_ts, right_ts)):
        if j < t_idx:
            rt.text = ""
        elif j == t_idx:
            lt.text = txt[:local_offset]
            rt.text = txt[local_offset:]
            lt.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            rt.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        else:
            lt.text = ""
    parent.remove(run)
    parent.insert(idx, right)
    parent.insert(idx, left)
    return left, right


def apply_change(
    p: etree._Element,
    change: dict[str, str],
    rev: RevisionFactory,
    pkg: DocPackage | None = None,
    paras: list[etree._Element] | None = None,
    target_idx: int | None = None,
) -> tuple[bool, str]:
    """
    Apply one change to paragraph element p. Returns (applied?, note).

    `pkg`, `paras`, `target_idx` are required for v0.3 change types
    (footnote, insert_image, insert_table, apply_style). The legacy types
    (insert/delete/replace/comment-only) ignore them.
    """
    ctype = change["change_type"].strip().lower()
    before = change.get("before_text", "").strip()
    after = change.get("after_text", "").strip()
    fid = change.get("feedback_id", "?")

    if ctype == "comment-only":
        return False, f"{fid}: comment-only — no doc edit applied"

    # v0.3 types
    if ctype == "footnote":
        if pkg is None:
            return False, f"{fid}: footnote requires DocPackage context"
        return _apply_footnote(p, change, rev, pkg)
    if ctype == "insert_image":
        if pkg is None or paras is None or target_idx is None:
            return False, f"{fid}: insert_image requires DocPackage + paras + target_idx"
        return _apply_insert_image(p, change, rev, pkg, paras, target_idx)
    if ctype == "insert_table":
        if pkg is None or paras is None or target_idx is None:
            return False, f"{fid}: insert_table requires DocPackage + paras + target_idx"
        return _apply_insert_table(p, change, rev, pkg, paras, target_idx)
    if ctype == "apply_style":
        if pkg is None:
            return False, f"{fid}: apply_style requires DocPackage context"
        return _apply_style(p, change, rev, pkg)
    if ctype == "remove_comment":
        if pkg is None:
            return False, f"{fid}: remove_comment requires DocPackage context"
        # `p` is unused for remove_comment; we walk from <w:body> directly.
        body = p
        while body is not None and body.tag != _q("body"):
            body = body.getparent()
        if body is None:
            return False, f"{fid}: remove_comment could not locate <w:body>"
        return _apply_remove_comment(body, change, rev, pkg)

    if ctype not in ("insert", "delete", "replace"):
        return False, f"{fid}: unknown change_type={ctype!r}"

    if ctype in ("delete", "replace") and not before:
        return False, f"{fid}: change_type={ctype} requires before_text"
    if ctype in ("insert", "replace") and not after:
        return False, f"{fid}: change_type={ctype} requires after_text"

    para_text = _para_text(p)

    if ctype == "insert":
        # Insert at end of paragraph (default). For richer anchoring, we'd
        # accept an `insert_after_text` field; v0.2 keeps it simple.
        # Find last <w:r> direct child to append after; if none, append <w:r>
        last_run = None
        for child in p:
            if child.tag == _q("r"):
                last_run = child
        ins = rev.make_ins(after)
        if last_run is not None:
            last_run.addnext(ins)
        else:
            p.append(ins)
        return True, f"{fid}: inserted {after!r} at paragraph end"

    # delete or replace: locate `before` in para_text
    pos = para_text.find(before)
    if pos < 0:
        # try a relaxed match (collapse whitespace)
        norm = re.sub(r"\s+", " ", para_text)
        nbefore = re.sub(r"\s+", " ", before)
        npos = norm.find(nbefore)
        if npos < 0:
            return False, f"{fid}: before_text not found in paragraph: {before!r}"
        # rebuild original-pos approximately by re-scanning whitespace runs
        # (good enough — we accept the relaxed match start)
        # walk para_text counting matched normalised positions
        i = 0
        running = 0
        while i < len(para_text) and running < npos:
            if para_text[i].isspace():
                # collapse
                while i < len(para_text) and para_text[i].isspace():
                    i += 1
                running += 1
            else:
                i += 1
                running += 1
        pos = i
        # adjust before to actual substring length in original
        # simplest: take a slice of the same normalised length, then expand
        # to next non-whitespace boundary
        end = pos
        running2 = 0
        target_len = len(nbefore)
        while end < len(para_text) and running2 < target_len:
            if para_text[end].isspace():
                while end < len(para_text) and para_text[end].isspace():
                    end += 1
                running2 += 1
            else:
                end += 1
                running2 += 1
        actual_before = para_text[pos:end]
    else:
        actual_before = before

    end = pos + len(actual_before)

    # Now perform the deletion in-tree by walking the run-text map and
    # surgically splitting runs at pos and end.
    # Rebuild the map at each split because element identities change.
    trmap = _build_text_run_map(p)
    # find t containing `pos`
    target_t_left = None
    local_off_left = 0
    for t_el, s, e in trmap:
        if s <= pos < e:
            target_t_left = t_el
            local_off_left = pos - s
            break
        if pos == e:  # at exact boundary: next t is fine
            target_t_left = t_el
            local_off_left = pos - s

    if target_t_left is None:
        return False, f"{fid}: failed to locate run for pos={pos}"

    # Split at pos
    left_run, right_run = _split_run_at(target_t_left, local_off_left)
    # Now split at end. Recompute trmap
    trmap = _build_text_run_map(p)
    target_t_right = None
    local_off_right = 0
    for t_el, s, e in trmap:
        if s <= end < e:
            target_t_right = t_el
            local_off_right = end - s
            break
        if end == e:
            target_t_right = t_el
            local_off_right = end - s

    if target_t_right is None:
        return False, f"{fid}: failed to locate run for end={end}"

    # If the right-cut is at the start of the same t, splitting at offset 0 is fine
    _split_run_at(target_t_right, local_off_right)

    # After both splits, the runs whose text falls in [pos,end) are the
    # "middle" runs. We collect them by walking the paragraph text-map again
    # and selecting runs whose offsets are entirely inside [pos,end).
    trmap = _build_text_run_map(p)
    middle_runs: list[etree._Element] = []
    for t_el, s, e in trmap:
        if s >= pos and e <= end and e > s:
            run = t_el.getparent()
            if run not in middle_runs:
                middle_runs.append(run)

    if not middle_runs:
        return False, f"{fid}: no runs captured in [{pos},{end})"

    # Wrap the middle runs in <w:del> and convert <w:t> to <w:delText>.
    # Each run may have a different parent (e.g. inside <w:hyperlink>) — we
    # use each run's own parent when detaching, and place the <w:del> at the
    # position of the FIRST middle run within ITS parent.
    first_parent = middle_runs[0].getparent()
    insert_idx = first_parent.index(middle_runs[0])

    delel = etree.SubElement(etree.Element("dummy"), _q("del"))
    delel.set(_q("id"), rev._id())
    delel.set(_q("author"), rev.author)
    delel.set(_q("date"), rev.date)

    for run in middle_runs:
        rPr = run.find(_q("rPr"))
        new_run = etree.SubElement(delel, _q("r"))
        if rPr is not None:
            new_run.append(_clone(rPr))
        orig_text = "".join(tt.text or "" for tt in run.iter(_q("t")))
        delText = etree.SubElement(new_run, _q("delText"))
        delText.text = orig_text
        delText.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        # remove the original run from its actual parent
        run_parent = run.getparent()
        if run_parent is not None:
            run_parent.remove(run)

    delel.getparent().remove(delel)  # detach from dummy
    first_parent.insert(insert_idx, delel)

    note = f"{fid}: deleted {actual_before!r}"

    if ctype == "replace":
        # Insert the after_text immediately after the <w:del>
        # Use rPr of the first cloned run if available
        rPr_for_ins = None
        first_r = delel.find(_q("r"))
        if first_r is not None:
            rPr_for_ins = first_r.find(_q("rPr"))
        ins = rev.make_ins(after, rPr_for_ins)
        delel.addnext(ins)
        note = f"{fid}: replaced {actual_before!r} with {after!r}"

    return True, note


# ----- main pipeline ---------------------------------------------------------
def apply(
    doc_path: Path,
    changes_md: Path,
    out_path: Path,
    author: str,
    date_iso: str,
) -> tuple[int, int, list[str]]:
    md_text = changes_md.read_text(encoding="utf-8")
    changes = parse_changes(md_text)
    if not changes:
        _warn("no change blocks parsed from changes file")
        # still produce an output copy
        shutil.copyfile(doc_path, out_path)
        return 0, 0, []

    # Build a DocPackage that holds every part of the .docx in memory.
    # We'll write it back at the end of the run.
    pkg = DocPackage(doc_path)
    tree = pkg.get_tree(DocPackage.DOC_PART)
    body = tree.find(_q("body"))
    if body is None:
        raise SystemExit("document.xml has no <w:body>")
    pkg.mark_dirty(DocPackage.DOC_PART)

    paras, para_id_map = _build_para_index(body)
    rev = RevisionFactory(author=author, date_iso=date_iso)

    # Resolve each change to its paragraph index for bottom-up sequencing.
    # remove_comment doesn't have a paragraph anchor — we use sentinel idx -1
    # and process those AFTER all paragraph-targeted changes (so paragraph
    # indices don't shift mid-pass).
    resolved: list[tuple[int, etree._Element, dict[str, str]]] = []
    notes: list[str] = []
    for ch in changes:
        ctype = (ch.get("change_type", "") or "").strip().lower()
        if ctype == "remove_comment":
            # Use sentinel -1; we'll pass <w:body> as the element so the
            # helper can locate comment refs anywhere in the doc.
            resolved.append((-1, body, ch))
            continue
        loc = ch.get("target_locator", "")
        r = _resolve_locator(loc, paras, para_id_map)
        if r is None:
            note = f"{ch.get('feedback_id','?')}: locator {loc!r} not resolved — skipped"
            notes.append(note)
            _warn(note)
            continue
        idx, p = r
        resolved.append((idx, p, ch))

    # Sort by paragraph index DESCENDING (bottom-up). remove_comment rows have
    # idx=-1 and run last, after all paragraph-anchored edits.
    resolved.sort(key=lambda t: t[0], reverse=True)

    applied_count = 0
    skipped_count = 0
    escalated_count = 0
    for idx, p, ch in resolved:
        try:
            ok, note = apply_change(p, ch, rev, pkg=pkg, paras=paras, target_idx=idx)
        except RemoveCommentAuthorNotAllowed as exc:
            note = f"{ch.get('feedback_id','?')}: ESCALATED remove_comment refused — {exc}"
            notes.append(note)
            escalated_count += 1
            _warn(note)
            continue
        notes.append(note)
        if ok:
            applied_count += 1
            _info(f"applied @para {idx}: {note}")
        else:
            skipped_count += 1
            _info(f"skipped @para {idx}: {note}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pkg.write(out_path)

    return applied_count, skipped_count, notes


def _replace_in_zip(zip_path: Path, target_name: str, new_data: bytes) -> None:
    """Replace one file in a zip archive in-place."""
    tmp_path = zip_path.with_suffix(zip_path.suffix + ".tmp")
    with zipfile.ZipFile(zip_path, "r") as zin, zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == target_name:
                data = new_data
            zout.writestr(item, data)
    tmp_path.replace(zip_path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("doc", type=Path)
    ap.add_argument("changes", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--author", default="feedback-addressing")
    ap.add_argument("--date", default=None, help="ISO timestamp; defaults to now (UTC)")
    args = ap.parse_args()

    date_iso = args.date or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    applied, skipped, notes = apply(args.doc, args.changes, args.out, args.author, date_iso)
    print(f"[apply_changes_docx] applied={applied} skipped={skipped} → {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
