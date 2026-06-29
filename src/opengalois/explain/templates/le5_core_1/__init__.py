# ruff: noqa: D102,D103
"""Register clean narrative templates for the le5-core ruleset."""

from __future__ import annotations

from . import basic as basic
from . import discriminant as discriminant
from . import galois as galois
from . import radicals as radicals
from . import statements as statements

__all__ = ["basic", "discriminant", "galois", "radicals", "statements"]
