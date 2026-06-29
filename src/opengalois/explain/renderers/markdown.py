# ruff: noqa: D102,D103
"""Markdown renderer for clean proof explanations."""

from __future__ import annotations

from ..proof_model import DisplayMath, Inline, Paragraph, ProofBlock, ProofDocument, ProofStatement


def render_markdown(document: ProofDocument) -> str:
    """Render a proof document as Markdown."""
    lines: list[str] = [f"# {_escape_text(document.title)}", ""]
    for block in document.introduction:
        _append_block(lines, block)
    for index, statement in enumerate(document.statements, start=1):
        _append_statement(lines, index, statement)
    return "\n".join(lines).rstrip() + "\n"


def _append_statement(
    lines: list[str],
    index: int,
    statement: ProofStatement,
) -> None:
    lines.append(f"## Statement {index}")
    lines.append("")
    for block in statement.statement:
        _append_block(lines, block)
    lines.append("## Proof")
    lines.append("")
    for block in statement.proof:
        _append_block(lines, block)
    _append_qed(lines)


def _append_qed(lines: list[str]) -> None:
    lines.append(r"$\square$")
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
    return "".join(_render_inline(part) for part in paragraph.parts)


def _render_inline(part: Inline) -> str:
    if part.kind == "math":
        return f"${part.value}$"
    return _escape_text(part.value)


def _escape_text(value: str) -> str:
    return value
