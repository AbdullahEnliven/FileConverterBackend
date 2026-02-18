"""
Excel to PDF Conversion Service (High Fidelity)
Uses LibreOffice headless export for best layout preservation.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


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


def excel_to_pdf(input_path: str, output_path: str) -> Dict:
    try:
        in_path = Path(input_path).expanduser().resolve()
        out_path = Path(output_path).expanduser().resolve()

        if not in_path.exists():
            return {"success": False, "error": f"Input file not found: {in_path}"}

        out_dir = out_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        soffice = _find_soffice()
        if not soffice:
            return {
                "success": False,
                "error": "LibreOffice not found. Install it or set LIBREOFFICE_PATH to soffice executable.",
            }

        profile_dir = out_dir / ".lo_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

        expected = out_dir / f"{in_path.stem}.pdf"

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
                "error": f"LibreOffice conversion failed.\nSTDERR: {proc.stderr.strip()}\nSTDOUT: {proc.stdout.strip()}",
            }

        if not expected.exists():
            alt = list(out_dir.glob(f"{in_path.stem}*.pdf"))
            if alt:
                expected = alt[0]
            else:
                return {"success": False, "error": f"Output PDF not found in {out_dir} after conversion."}

        if expected.resolve() != out_path:
            if out_path.exists():
                out_path.unlink()
            expected.replace(out_path)

        return {"success": True, "output_path": str(out_path)}

    except Exception as e:
        return {"success": False, "error": str(e)}
