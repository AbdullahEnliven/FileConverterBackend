import os
import shutil
import subprocess
from typing import Dict, Optional

import fitz  # PyMuPDF


_GS_CANDIDATES = ["gs", "gswin64c", "gswin32c"]


def _find_ghostscript() -> Optional[str]:
    for name in _GS_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    return None


def _gs_preset(level: str) -> str:
    """
    Ghostscript quality presets:
    - screen: smallest size, lowest quality
    - ebook: good balance
    - printer: higher quality
    - prepress: best quality, bigger file
    """
    level = (level or "ebook").lower().strip()
    if level not in {"screen", "ebook", "printer", "prepress"}:
        level = "ebook"
    return f"/{level}"


def compress_pdf(input_path: str, output_path: str, level: str = "ebook") -> Dict:
    """
    Compress PDF.
    Returns: { success, output_path, before_bytes, after_bytes, reduction_percent, method, warning? }
    """
    try:
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        before = os.path.getsize(input_path)
        gs = _find_ghostscript()

        # ---- Method 1: Ghostscript (best compression) ----
        if gs:
            preset = _gs_preset(level)

            cmd = [
                gs,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS={preset}",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                "-dDetectDuplicateImages=true",
                "-dCompressFonts=true",
                "-dSubsetFonts=true",
                f"-sOutputFile={output_path}",
                input_path,
            ]

            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if proc.returncode != 0 or not os.path.exists(output_path):
                return {
                    "success": False,
                    "error": (
                        "Ghostscript compression failed.\n"
                        f"STDERR: {proc.stderr.strip()}\n"
                        f"STDOUT: {proc.stdout.strip()}"
                    ),
                }

            after = os.path.getsize(output_path)
            reduction = 0.0 if before == 0 else round(((before - after) / before) * 100, 2)

            return {
                "success": True,
                "output_path": output_path,
                "before_bytes": before,
                "after_bytes": after,
                "reduction_percent": reduction,
                "method": f"ghostscript({preset})",
            }

        # ---- Method 2: PyMuPDF optimization (no external install) ----
        doc = fitz.open(input_path)
        doc.save(
            output_path,
            garbage=4,     # remove unused objects
            deflate=True,  # compress streams
            clean=True,    # clean structure
            linear=True,   # web optimized
        )
        doc.close()

        after = os.path.getsize(output_path)
        reduction = 0.0 if before == 0 else round(((before - after) / before) * 100, 2)

        return {
            "success": True,
            "output_path": output_path,
            "before_bytes": before,
            "after_bytes": after,
            "reduction_percent": reduction,
            "method": "pymupdf(optimize)",
            "warning": (
                "Ghostscript not found. Used PyMuPDF optimization only. "
                "For scanned/image-heavy PDFs, install Ghostscript for much bigger compression."
            ),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}