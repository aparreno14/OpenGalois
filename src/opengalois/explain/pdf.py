# ruff: noqa: D102,D103
"""PDF compilation support for clean proof explanations."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .errors import ExplainPdfError

_LATEX_FILENAME = "opengalois_explanation.tex"
_PDF_FILENAME = "opengalois_explanation.pdf"
_LOG_FILENAME = "opengalois_explanation.log"


def compile_latex_to_pdf(latex_source: str, output_pdf: str | Path) -> Path:
    """Compile a standalone LaTeX document into a PDF file."""
    out_path = Path(output_pdf)
    if out_path.suffix.lower() != ".pdf":
        raise ExplainPdfError("PDF output path must end with .pdf")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="opengalois-explain-") as tmp_raw:
        tmp_dir = Path(tmp_raw)
        tex_path = tmp_dir / _LATEX_FILENAME
        tex_path.write_text(latex_source, encoding="utf-8")

        if _has_executable("latexmk"):
            _run_latexmk(tmp_dir, tex_path, out_path)
        elif _has_executable("pdflatex"):
            _run_pdflatex(tmp_dir, tex_path, out_path)
        else:
            raise ExplainPdfError(_missing_latex_message())

        produced_pdf = tmp_dir / _PDF_FILENAME
        if not produced_pdf.exists():
            _copy_log_if_present(tmp_dir, out_path)
            raise ExplainPdfError("LaTeX finished but did not produce a PDF file")

        shutil.copyfile(produced_pdf, out_path)
        return out_path


def _missing_latex_message() -> str:
    return "\n".join(
        [
            "PDF output requires a LaTeX compiler, but neither latexmk",
            "nor pdflatex was found in PATH.",
            "",
            "Windows:",
            "  1. Install MiKTeX.",
            "  2. Add the folder containing pdflatex.exe to PATH.",
            "     Typical user install:",
            r"     C:\Users\<user>\AppData\Local\Programs\MiKTeX\miktex\bin\x64",
            "  3. Restart PowerShell, Git Bash, or VS Code.",
            "  4. Check with: where.exe pdflatex",
            "     In Git Bash, check with: which pdflatex",
            "",
            "Linux / WSL:",
            "  1. Install TeX Live. On Debian/Ubuntu:",
            "     sudo apt install texlive-latex-base",
            "     sudo apt install texlive-latex-extra latexmk",
            "  2. Check with: command -v pdflatex",
            "",
            "As an alternative, generate LaTeX without compiling:",
            "  opengalois explain --format latex --out proof.tex CERT.json",
        ]
    )


def _has_executable(name: str) -> bool:
    return shutil.which(name) is not None


def _run_latexmk(tmp_dir: Path, tex_path: Path, output_pdf: Path) -> None:
    cmd = [
        "latexmk",
        "-pdf",
        "-halt-on-error",
        "-interaction=nonstopmode",
        tex_path.name,
    ]
    _run_command(cmd, tmp_dir, output_pdf)


def _run_pdflatex(tmp_dir: Path, tex_path: Path, output_pdf: Path) -> None:
    cmd = [
        "pdflatex",
        "-halt-on-error",
        "-interaction=nonstopmode",
        tex_path.name,
    ]
    _run_command(cmd, tmp_dir, output_pdf)
    _run_command(cmd, tmp_dir, output_pdf)


def _run_command(cmd: list[str], cwd: Path, output_pdf: Path) -> None:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return

    log_path = _copy_log_if_present(cwd, output_pdf)
    if log_path is None:
        log_path = output_pdf.with_suffix(".log")
        log_path.write_text(_combined_process_output(result), encoding="utf-8")

    raise ExplainPdfError(
        "LaTeX compilation failed. "
        f"The log was written to {log_path}."
    )


def _copy_log_if_present(tmp_dir: Path, output_pdf: Path) -> Path | None:
    produced_log = tmp_dir / _LOG_FILENAME
    if not produced_log.exists():
        return None
    out_log = output_pdf.with_suffix(".log")
    shutil.copyfile(produced_log, out_log)
    return out_log


def _combined_process_output(result: subprocess.CompletedProcess[str]) -> str:
    parts = [
        "STDOUT:",
        result.stdout or "",
        "",
        "STDERR:",
        result.stderr or "",
    ]
    return "\n".join(parts)
