"""
PowerPoint to Word Conversion Service (Best Practical Fidelity)
Pipeline:
  PPT/PPTX -> PDF (LibreOffice) -> DOCX (pdf2docx via pdf_to_word module)

This preserves layout FAR better than extracting text with python-pptx.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pdf_to_word  # your existing module


def _find_soffice() -> Optional[str]:
    env_path = os.getenv("LIBREOFFICE_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    for name in ("soffice", "soffice.exe", "libreoffice", "libreoffice.exe"):
        found = shutil.which(name)
        if found:
            return found

    candidates: List[str] = []
    if sys.platform.startswith("win"):
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        pfx86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        candidates += [
            rf"{pf}\LibreOffice\program\soffice.exe",
            rf"{pfx86}\LibreOffice\program\soffice.exe",
        ]
    elif sys.platform == "darwin":
        candidates += ["/Applications/LibreOffice.app/Contents/MacOS/soffice"]
    else:
        candidates += ["/usr/bin/soffice", "/usr/local/bin/soffice", "/snap/bin/libreoffice"]

    for c in candidates:
        if Path(c).exists():
            return c
    return None


def ppt_to_word(input_path: str, output_path: str) -> Dict:
    try:
        in_path = Path(input_path).expanduser().resolve()
        out_docx = Path(output_path).expanduser().resolve()

        if not in_path.exists():
            return {"success": False, "error": f"Input file not found: {in_path}"}

        out_dir = out_docx.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        soffice = _find_soffice()
        if not soffice:
            return {
                "success": False,
                "error": "LibreOffice not found. Install it or set LIBREOFFICE_PATH to soffice executable.",
            }

        # Step 1: Convert PPTX -> PDF
        profile_dir = out_dir / ".lo_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

        temp_pdf = out_dir / f"{in_path.stem}__temp.pdf"
        expected_pdf = out_dir / f"{in_path.stem}.pdf"

        cmd = [
            soffice,
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            f"-env:UserInstallation=file:///{profile_dir.as_posix().lstrip('/')}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir),
            str(in_path),
        ]

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return {
                "success": False,
                "error": f"LibreOffice PPT->PDF failed.\nSTDERR: {proc.stderr.strip()}\nSTDOUT: {proc.stdout.strip()}",
            }

        if expected_pdf.exists():
            # rename to temp so we can control pipeline output naming
            if temp_pdf.exists():
                temp_pdf.unlink()
            expected_pdf.replace(temp_pdf)
        else:
            alt = list(out_dir.glob(f"{in_path.stem}*.pdf"))
            if alt:
                if temp_pdf.exists():
                    temp_pdf.unlink()
                alt[0].replace(temp_pdf)
            else:
                return {"success": False, "error": f"PDF not produced in {out_dir} after conversion."}

        # Step 2: Convert PDF -> DOCX using your existing converter
        res = pdf_to_word.pdf_to_word(str(temp_pdf), str(out_docx))

        # Cleanup temp pdf (optional)
        try:
            if temp_pdf.exists():
                temp_pdf.unlink()
        except Exception:
            pass

        if not res.get("success"):
            return {"success": False, "error": f"PDF->Word failed: {res.get('error', 'Unknown error')}"}

        return {"success": True, "output_path": str(out_docx)}

    except Exception as e:
        return {"success": False, "error": str(e)}
