from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from opengalois.explain import pdf as pdf_module
from opengalois.explain.errors import ExplainPdfError
from opengalois.explain.pdf import compile_latex_to_pdf


def test_compile_latex_to_pdf_uses_pdflatex_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_which(name: str) -> str | None:
        if name == "pdflatex":
            return "/usr/bin/pdflatex"
        return None

    def fake_run(
        cmd: list[str],
        *,
        cwd: Path,
        text: bool,
        capture_output: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        _ = text, capture_output, check
        calls.append(cmd)
        (cwd / "opengalois_explanation.pdf").write_bytes(b"%PDF-1.7\n")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(pdf_module.shutil, "which", fake_which)
    monkeypatch.setattr(pdf_module.subprocess, "run", fake_run)

    out_pdf = tmp_path / "proof.pdf"
    result = compile_latex_to_pdf(r"\documentclass{article}", out_pdf)

    assert result == out_pdf
    assert out_pdf.read_bytes() == b"%PDF-1.7\n"
    assert [call[0] for call in calls] == ["pdflatex", "pdflatex"]


def test_compile_latex_to_pdf_requires_latex_engine(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pdf_module.shutil, "which", lambda _name: None)

    with pytest.raises(ExplainPdfError) as exc_info:
        compile_latex_to_pdf(r"\documentclass{article}", tmp_path / "proof.pdf")

    message = str(exc_info.value)
    assert "neither latexmk" in message
    assert "pdflatex was found in PATH" in message
    assert "Windows:" in message
    assert "MiKTeX" in message
    assert "where.exe pdflatex" in message
    assert "Linux / WSL:" in message
    assert "texlive-latex-base" in message
    assert "--format latex" in message


def test_compile_latex_to_pdf_rejects_non_pdf_output(tmp_path: Path) -> None:
    with pytest.raises(ExplainPdfError, match="must end with .pdf"):
        compile_latex_to_pdf(r"\documentclass{article}", tmp_path / "proof.tex")
