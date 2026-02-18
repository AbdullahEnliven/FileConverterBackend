"""
PowerPoint to PDF Conversion Service (High Fidelity)
Converts PPT/PPTX to PDF while preserving layout, images, fonts, etc.
Uses LibreOffice in headless mode.

IMPORTANT:
- This is NOT "changing extension". It renders slides and exports to PDF.
- Requires LibreOffice installed on the machine running this code.

ENV OPTIONS:
- LIBREOFFICE_PATH: full path to soffice executable (recommended on Windows)
  e.g.:
    Windows: C:\\Program Files\\LibreOffice\\program\\soffice.exe
    Linux: /usr/bin/soffice
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


def _find_libreoffice_executable() -> Optional[str]:
    """
    Try to find LibreOffice executable across platforms.
    Returns the path to 'soffice' (or 'soffice.exe') if found, else None.
    """
    # 1) Explicit env var (best)
    env_path = os.getenv("LIBREOFFICE_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists() and p.is_file():
            return str(p)

    # 2) Search in PATH
    for name in ("soffice", "soffice.exe", "libreoffice", "libreoffice.exe"):
        found = shutil.which(name)
        if found:
            return found

    # 3) Common install locations
    candidates: List[str] = []

    if sys.platform.startswith("win"):
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        candidates += [
            rf"{program_files}\LibreOffice\program\soffice.exe",
            rf"{program_files_x86}\LibreOffice\program\soffice.exe",
        ]

    elif sys.platform == "darwin":
        candidates += [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]

    else:
        # Linux common paths
        candidates += [
            "/usr/bin/soffice",
            "/usr/local/bin/soffice",
            "/snap/bin/libreoffice",
            "/usr/bin/libreoffice",
            "/usr/local/bin/libreoffice",
        ]

    for c in candidates:
        p = Path(c)
        if p.exists() and p.is_file():
            return str(p)

    return None


def ppt_to_pdf(input_path: str, output_path: str) -> Dict:
    """
    Convert PowerPoint to PDF using LibreOffice headless export.

    Args:
        input_path: Path to input .ppt or .pptx
        output_path: Path to save output .pdf

    Returns:
        dict: Result info (success, error, output_path, etc.)
    """
    try:
        in_path = Path(input_path).expanduser().resolve()
        out_path = Path(output_path).expanduser().resolve()

        if not in_path.exists():
            return {
                "success": False,
                "error": f"Input file not found: {str(in_path)}",
            }

        out_dir = out_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        soffice = _find_libreoffice_executable()
        if not soffice:
            return {
                "success": False,
                "error": (
                    "LibreOffice executable not found (soffice). "
                    "Install LibreOffice OR set LIBREOFFICE_PATH to the full path of soffice."
                ),
            }

        # LibreOffice creates output with same base name as input in the output directory.
        expected_generated = out_dir / (in_path.stem + ".pdf")

        # Some environments need a dedicated user profile dir to avoid permission issues.
        # We'll create a per-run profile directory inside out_dir/.lo_profile
        profile_dir = out_dir / ".lo_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

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

        # Run conversion
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if proc.returncode != 0:
            return {
                "success": False,
                "error": (
                    "LibreOffice conversion failed.\n"
                    f"Command: {' '.join(cmd)}\n"
                    f"STDOUT: {proc.stdout.strip()}\n"
                    f"STDERR: {proc.stderr.strip()}"
                ),
            }

        if not expected_generated.exists():
            # Sometimes LO outputs slightly different; try to find any PDF in out_dir with same stem
            alt = list(out_dir.glob(f"{in_path.stem}*.pdf"))
            if alt:
                expected_generated = alt[0]
            else:
                return {
                    "success": False,
                    "error": (
                        "Conversion ran but output PDF not found in output directory.\n"
                        f"Expected: {str(expected_generated)}\n"
                        f"STDOUT: {proc.stdout.strip()}\n"
                        f"STDERR: {proc.stderr.strip()}"
                    ),
                }

        # If output_path differs from generated name, rename/move
        if expected_generated.resolve() != out_path:
            if out_path.exists():
                out_path.unlink()
            expected_generated.replace(out_path)

        input_size = in_path.stat().st_size
        output_size = out_path.stat().st_size

        return {
            "success": True,
            "input_size": input_size,
            "output_size": output_size,
            "output_path": str(out_path),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def ppt_to_pdf_batch(input_paths: List[str], output_dir: str) -> List[Dict]:
    """
    Convert multiple PowerPoint files to PDF.

    Args:
        input_paths: list of input ppt/pptx paths
        output_dir: directory to save output pdfs

    Returns:
        list: results for each file
    """
    results = []
    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    for p in input_paths:
        p_path = Path(p).expanduser()
        out_path = out_dir / (p_path.stem + ".pdf")
        res = ppt_to_pdf(str(p_path), str(out_path))
        res["filename"] = p_path.name
        results.append(res)

    return results
