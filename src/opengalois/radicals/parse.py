"""Placeholder parser for textual radical expressions.

The current integration bundle focuses on AST construction, local
canonicalization, certificate encoding/decoding, and rendering. A user-facing
text parser can be added later without changing the structural AST API.
"""

from __future__ import annotations

from .ast import Expr

__all__ = ["parse_text"]


def parse_text(text: str) -> Expr:
    """Parse a textual radical expression.

    Args:
        text: Source text to parse.

    Returns:
        Parsed expression.

    Raises:
        NotImplementedError: Always, because the parser is still a placeholder.
    """
    del text
    raise NotImplementedError("radicals.parse.parse_text() is not implemented yet")
