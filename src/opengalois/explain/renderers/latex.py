# ruff: noqa: D102,D103
"""LaTeX renderer for clean proof explanations."""

from __future__ import annotations

from ..proof_model import DisplayMath, Inline, Paragraph, ProofBlock, ProofDocument, ProofStatement


def render_latex(document: ProofDocument) -> str:
    """Render a proof document as a standalone LaTeX article."""
    lines: list[str] = [
        r"\documentclass{article}",
        r"\usepackage{amsmath,amssymb,mathtools}",
        r"\usepackage{tikz-cd}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\parskip}{0.55em}",
        r"\begin{document}",
        "",
        rf"\section*{{{_escape_text(document.title)}}}",
        "",
    ]
    for block in document.introduction:
        _append_block(lines, block)
    for index, statement in enumerate(document.statements, start=1):
        _append_statement(lines, index, statement)
    lines.append(r"\end{document}")
    lines.append("")
    return "\n".join(lines)


def _append_statement(
    lines: list[str],
    index: int,
    statement: ProofStatement,
) -> None:
    lines.append(rf"\subsection*{{Statement {index}}}")
    for block in statement.statement:
        _append_block(lines, block)
    lines.append(r"\subsection*{Proof}")
    for block in statement.proof:
        _append_block(lines, block)
    _append_qed(lines)


def _append_qed(lines: list[str]) -> None:
    lines.append(r"\noindent\hfill\(\square\)\par")
    lines.append("")


def _append_block(lines: list[str], block: ProofBlock) -> None:
    if isinstance(block, DisplayMath):
        lines.append(r"\[")
        lines.append(block.value)
        lines.append(r"\]")
        lines.append("")
        return
    lines.append(_render_paragraph(block))
    lines.append("")


def _render_paragraph(paragraph: Paragraph) -> str:
    body = "".join(_render_inline(part) for part in paragraph.parts)
    return rf"\noindent {body}\par"


def _render_inline(part: Inline) -> str:
    if part.kind == "math":
        return rf"\({part.value}\)"
    return _escape_text(part.value)


def _escape_text(value: str) -> str:
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(ch, ch) for ch in value)
