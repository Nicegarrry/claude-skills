#!/usr/bin/env python3
"""
visual_qa.py — render a .docx to PDF + per-page PNGs for visual QA.

WHAT IT DOES
------------
- Wraps `soffice --headless --convert-to pdf` to produce a PDF render of the
  .docx in a target directory.
- Wraps `pdftoppm -r <dpi>` to produce one PNG per page.
- Returns a structured result dict so callers can decide.

GRACEFUL FALLBACK
-----------------
If `soffice` (LibreOffice) is not on PATH, the helper logs a clear note and
returns `{"skipped": true, "reason": "soffice not found"}` with exit code 0.
The visual-QA step is non-fatal — the run continues.

USAGE
-----
    visual_qa.py <doc.docx> --out-dir <09-visual-qa>
        [--dpi 150] [--page-prefix <stem>]

The default output:
    <out-dir>/<stem>.pdf
    <out-dir>/<stem>-page01.png, <stem>-page02.png, ...
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


# Candidate paths for LibreOffice's soffice binary on macOS.
SOFFICE_CANDIDATES = [
    "/opt/homebrew/bin/soffice",
    "/usr/local/bin/soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
]


def find_soffice() -> str | None:
    on_path = shutil.which("soffice")
    if on_path:
        return on_path
    for cand in SOFFICE_CANDIDATES:
        if Path(cand).exists():
            return cand
    return None


def find_pdftoppm() -> str | None:
    on_path = shutil.which("pdftoppm")
    if on_path:
        return on_path
    for cand in ("/opt/homebrew/bin/pdftoppm", "/usr/local/bin/pdftoppm"):
        if Path(cand).exists():
            return cand
    return None


def render_docx_to_pdf(doc_path: Path, out_dir: Path, soffice_bin: str) -> Path | None:
    """Convert a .docx to PDF in out_dir using LibreOffice headless. Returns the
    output PDF path or None on failure."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        soffice_bin,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(doc_path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        print(f"[visual_qa] WARN: soffice convert timed out for {doc_path}", file=sys.stderr)
        return None
    if proc.returncode != 0:
        print(f"[visual_qa] WARN: soffice convert failed: {proc.stderr.strip()}", file=sys.stderr)
        return None
    pdf_path = out_dir / (doc_path.stem + ".pdf")
    if not pdf_path.exists():
        # LibreOffice keeps the original stem; double-check by listing
        produced = list(out_dir.glob(doc_path.stem + "*.pdf"))
        if produced:
            return produced[0]
        return None
    return pdf_path


def render_pdf_to_pngs(pdf_path: Path, out_dir: Path, prefix: str, dpi: int, pdftoppm_bin: str) -> list[Path]:
    """Render each page of pdf_path to a PNG named <prefix>-pageNN.png."""
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f"{prefix}-page"
    cmd = [pdftoppm_bin, "-r", str(dpi), "-png", str(pdf_path), str(base)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        print("[visual_qa] WARN: pdftoppm timed out", file=sys.stderr)
        return []
    if proc.returncode != 0:
        print(f"[visual_qa] WARN: pdftoppm failed: {proc.stderr.strip()}", file=sys.stderr)
        return []
    # pdftoppm names files like base-1.png, base-12.png — convert to zero-padded
    raw = sorted(out_dir.glob(f"{prefix}-page-*.png"))
    out: list[Path] = []
    for f in raw:
        # parse number after final '-'
        try:
            num = int(f.stem.rsplit("-", 1)[-1])
        except ValueError:
            continue
        new_name = out_dir / f"{prefix}-page{num:02d}.png"
        if new_name.exists() and new_name != f:
            new_name.unlink()
        f.rename(new_name)
        out.append(new_name)
    return sorted(out)


def run(doc_path: Path, out_dir: Path, dpi: int = 150, page_prefix: str | None = None) -> dict:
    """High-level visual-QA pipeline. Returns a dict with status + paths."""
    soffice = find_soffice()
    if soffice is None:
        return {"skipped": True, "reason": "soffice not found", "doc": str(doc_path)}
    pdftoppm = find_pdftoppm()
    if pdftoppm is None:
        return {"skipped": True, "reason": "pdftoppm not found", "doc": str(doc_path)}
    if not doc_path.exists():
        return {"skipped": True, "reason": f"doc not found: {doc_path}"}

    pdf_path = render_docx_to_pdf(doc_path, out_dir, soffice)
    if pdf_path is None:
        return {"skipped": True, "reason": "soffice conversion failed"}

    prefix = page_prefix or doc_path.stem
    pngs = render_pdf_to_pngs(pdf_path, out_dir, prefix, dpi, pdftoppm)

    return {
        "skipped": False,
        "doc": str(doc_path),
        "pdf": str(pdf_path),
        "pages": [str(p) for p in pngs],
        "page_count": len(pngs),
        "dpi": dpi,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("doc", type=Path)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--page-prefix", default=None)
    args = ap.parse_args()

    result = run(args.doc, args.out_dir, dpi=args.dpi, page_prefix=args.page_prefix)
    print(json.dumps(result, indent=2))
    return 0  # never fatal


if __name__ == "__main__":
    raise SystemExit(main())
