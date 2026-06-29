"""Canonical degree-1 radical scheme.

This module implements the exact AST scheme used by
``radical_roots.QQ.deg1.trivial@1``. For a linear polynomial

    f(x) = a*x + b,  a != 0,

the unique canonical ordered radical-root list is

    [ qq((-b)/a) ].
"""

from __future__ import annotations

from fractions import Fraction

from opengalois.radicals.ast import Expr, qq

__all__ = ["build"]


def build(*, a: Fraction, b: Fraction) -> list[Expr]:
    """Build the canonical degree-1 radical-root list.

    Args:
        a: Leading coefficient of the linear polynomial.
        b: Constant coefficient of the linear polynomial.

    Returns:
        The one-element ordered list ``[qq((-b)/a)]``.

    Raises:
        ValueError: If ``a`` is zero.
    """
    if a == 0:
        raise ValueError("deg1_trivial.build() requires a non-zero leading coefficient")
    return [qq((-b) / a)]
