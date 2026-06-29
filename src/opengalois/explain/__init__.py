# ruff: noqa: D102,D103
"""Clean non-normative explanation renderer for OpenGalois certificates."""

from __future__ import annotations

from .api import (
    ExplainFormat,
    explain,
    explain_certificate,
    explain_certificate_to_document,
    explain_certificate_to_pdf,
    render_explanation_from_certificate,
)
from .errors import (
    ExplainError,
    ExplainInvalidCertificateError,
    ExplainMissingTemplateError,
    ExplainPdfError,
)

__all__ = [
    "ExplainError",
    "ExplainFormat",
    "ExplainInvalidCertificateError",
    "ExplainMissingTemplateError",
    "ExplainPdfError",
    "explain",
    "explain_certificate",
    "explain_certificate_to_document",
    "explain_certificate_to_pdf",
    "render_explanation_from_certificate",
]
