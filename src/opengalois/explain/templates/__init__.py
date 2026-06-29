# ruff: noqa: D102,D103
"""Template registry public surface."""

from __future__ import annotations

from .registry import (
    Template,
    TemplateRegistry,
    get_default_registry,
    rule_template,
    statement_template,
)

__all__ = [
    "Template",
    "TemplateRegistry",
    "get_default_registry",
    "rule_template",
    "statement_template",
]
