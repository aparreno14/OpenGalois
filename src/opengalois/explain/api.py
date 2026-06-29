# ruff: noqa: D102,D103
"""Public API for clean OpenGalois explanations."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from .context import ExplainContext, FactView, build_explain_context
from .errors import (
    ExplainInvalidCertificateError,
    ExplainMissingTemplateError,
    MissingTemplate,
)
from .graph import dependency_subgraph, select_target_fact_ids
from .math_render import equation_poly
from .pdf import compile_latex_to_pdf
from .proof_model import (
    DisplayMath,
    Paragraph,
    ProofBlock,
    ProofDocument,
    ProofStatement,
    math,
    par,
)
from .renderers import render_latex, render_markdown
from .templates.registry import TemplateRegistry, get_default_registry

ExplainFormat = Literal["md", "markdown", "tex", "latex"]


def _load_builtin_templates() -> None:
    # Import for registration side effects.
    from .templates import le5_core_1 as _le5_core_1

    _ = _le5_core_1


def explain_certificate_to_document(
    certificate: Mapping[str, Any],
    *,
    target: str | None = None,
    strict: bool = True,
    verify_first: bool = False,
    registry: TemplateRegistry | None = None,
) -> ProofDocument:
    """Build a clean proof document from a certificate.

    The document is non-normative. When ``verify_first`` is true, the certificate
    is checked by the independent verifier before any explanation is produced.
    """
    if verify_first:
        _verify_certificate(certificate)

    _load_builtin_templates()
    ctx = build_explain_context(certificate)
    active_registry = registry or get_default_registry()
    targets = select_target_fact_ids(ctx, target)
    statements: list[ProofStatement] = []

    for target_id in targets:
        goal_fact = ctx.get_fact(target_id)
        subgraph = dependency_subgraph(ctx, target_id)
        if strict:
            active_registry.require_templates(subgraph)
        statement = _statement_for(goal_fact, ctx, active_registry)
        proof = _proof_for(subgraph, ctx, active_registry, strict=strict)
        statements.append(
            ProofStatement(
                fact_id=target_id,
                statement=statement,
                proof=proof,
            )
        )

    return ProofDocument(
        title="OpenGalois explanation",
        introduction=_introduction(ctx),
        statements=tuple(statements),
        metadata={
            "ruleset_id": ctx.ruleset_id,
            "targets": ",".join(targets),
        },
    )


def explain_certificate(
    certificate: Mapping[str, Any],
    *,
    format: ExplainFormat = "markdown",
    target: str | None = None,
    strict: bool = True,
    verify_first: bool = False,
    level: str | None = None,
) -> str:
    """Render a clean explanation in Markdown or LaTeX.

    ``level`` is accepted for compatibility with the earlier CLI patch and is
    currently ignored by the clean renderer.
    """
    _ = level
    document = explain_certificate_to_document(
        certificate,
        target=target,
        strict=strict,
        verify_first=verify_first,
    )
    normalized = _normalize_format(format)
    if normalized == "markdown":
        return render_markdown(document)
    return render_latex(document)


def explain_certificate_to_pdf(
    certificate: Mapping[str, Any],
    output_pdf: str | Path,
    *,
    target: str | None = None,
    strict: bool = True,
    verify_first: bool = False,
) -> Path:
    """Render a certificate explanation and compile it as PDF."""
    document = explain_certificate_to_document(
        certificate,
        target=target,
        strict=strict,
        verify_first=verify_first,
    )
    latex_source = render_latex(document)
    return compile_latex_to_pdf(latex_source, output_pdf)


def render_explanation_from_certificate(
    certificate: Mapping[str, Any],
    fmt: ExplainFormat = "md",
    *,
    target: str | None = None,
    strict: bool = True,
    verify_first: bool = False,
    level: str | None = None,
) -> str:
    """Backward-compatible entry point used by the public API."""
    return explain_certificate(
        certificate,
        format=fmt,
        target=target,
        strict=strict,
        verify_first=verify_first,
        level=level,
    )


def explain(
    certificate: Mapping[str, Any],
    *,
    format: ExplainFormat = "markdown",
    target: str | None = None,
    strict: bool = True,
    verify_first: bool = False,
) -> str:
    """Alias for :func:`explain_certificate`."""
    return explain_certificate(
        certificate,
        format=format,
        target=target,
        strict=strict,
        verify_first=verify_first,
    )


def _verify_certificate(certificate: Mapping[str, Any]) -> None:
    from opengalois.verify import verify_certificate

    result = verify_certificate(certificate)
    verified = getattr(result, "verified", False)
    if not verified:
        raise ExplainInvalidCertificateError(
            "cannot explain invalid certificate: verification failed"
        )


def _statement_for(
    fact: FactView,
    ctx: ExplainContext,
    registry: TemplateRegistry,
) -> tuple[ProofBlock, ...]:
    template = registry.statement(fact.pred)
    if template is None:
        raise ExplainMissingTemplateError(
            [MissingTemplate(rule_id=f"statement:{fact.pred}", fact_id=fact.fact_id)]
        )
    return template(fact, ctx)


def _proof_for(
    facts: tuple[FactView, ...],
    ctx: ExplainContext,
    registry: TemplateRegistry,
    *,
    strict: bool,
) -> tuple[ProofBlock, ...]:
    paragraphs: list[ProofBlock] = []
    for fact in facts:
        template = registry.rule(fact.rule_id)
        if template is None:
            if strict:
                # require_templates already raises a better aggregate error.
                continue
            paragraphs.append(
                par("The certificate proves ", math(_generic_fact_math(fact)), ".")
            )
            continue
        paragraphs.extend(template(fact, ctx))
    return _deduplicate(paragraphs)


def _introduction(ctx: ExplainContext) -> tuple[Paragraph, ...]:
    return (
        par("Let ", math(equation_poly(ctx, "$input", name="f")), "."),
        par("The following explanation is derived from the verified fact graph."),
    )


def _generic_fact_math(fact: FactView) -> str:
    return rf"\operatorname{{{fact.pred}}}"


def _deduplicate(paragraphs: list[ProofBlock]) -> tuple[ProofBlock, ...]:
    seen: set[tuple[tuple[str, str], ...] | tuple[str, str]] = set()
    out: list[ProofBlock] = []
    for paragraph in paragraphs:
        if isinstance(paragraph, DisplayMath):
            # Identical display formulae may occur in different logical places.
            # For instance, Ferrari may certify a root list and a later lift rule
            # may transport the same list back to the original polynomial.  The
            # surrounding sentences are different, so dropping the second display
            # leaves an unfinished paragraph.
            out.append(paragraph)
            continue
        key = _block_key(paragraph)
        if key in seen:
            continue
        seen.add(key)
        out.append(paragraph)
    return tuple(out)


def _block_key(block: ProofBlock) -> tuple[tuple[str, str], ...] | tuple[str, str]:
    if isinstance(block, DisplayMath):
        return ("display", block.value)
    return tuple((part.kind, part.value) for part in block.parts)


def _normalize_format(format: ExplainFormat) -> Literal["markdown", "latex"]:
    value = str(format).lower()
    if value in {"md", "markdown"}:
        return "markdown"
    if value in {"tex", "latex"}:
        return "latex"
    raise ValueError(f"unsupported explanation format: {format!r}")


# Compatibility name used by earlier patches.
def _document_to_json(document: ProofDocument) -> dict[str, Any]:
    return {
        "title": document.title,
        "statements": [
            {
                "fact_id": statement.fact_id,
                "statement": [_block_to_plain(b) for b in statement.statement],
                "proof": [_block_to_plain(p) for p in statement.proof],
            }
            for statement in document.statements
        ],
    }


def _block_to_plain(block: ProofBlock) -> str:
    if isinstance(block, DisplayMath):
        return f"\\[{block.value}\\]"
    chunks: list[str] = []
    for part in block.parts:
        chunks.append(part.value if part.kind == "text" else f"${part.value}$")
    return "".join(chunks)
