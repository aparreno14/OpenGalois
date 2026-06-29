# ruff: noqa: D102,D103
"""Errors raised by the non-normative explanation layer."""

from __future__ import annotations

from dataclasses import dataclass


class ExplainError(Exception):
    """Base class for explain-layer errors."""


class ExplainInvalidCertificateError(ExplainError):
    """Raised when a certificate cannot be explained safely."""


@dataclass(frozen=True)
class MissingTemplate:
    """A missing rule narrative template."""

    rule_id: str
    fact_id: str


class ExplainMissingTemplateError(ExplainError):
    """Raised when strict rendering needs a rule template that is not registered."""

    def __init__(self, missing: list[MissingTemplate]) -> None:
        """Build an error message listing every missing template."""
        self.missing = tuple(missing)
        lines = ["Cannot render a clean explanation: missing narrative templates."]
        for item in self.missing:
            lines.append(f"  - {item.rule_id} ({item.fact_id})")
        super().__init__("\n".join(lines))


class ExplainPdfError(ExplainError):
    """Raised when PDF rendering or LaTeX compilation fails."""
