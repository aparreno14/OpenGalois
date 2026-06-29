"""Canonical degree-2 quadratic-formula scheme.

This module implements the exact AST scheme fixed by
``radical_roots.QQ.deg2.quadratic_formula@1``.

For a quadratic polynomial

    f(x) = a*x^2 + b*x + c,  a != 0,

let ``Δ = b^2 - 4*a*c``. The canonical ordered radical-root list is

    [ (-b + sqrt(Δ)) / (2*a), (-b - sqrt(Δ)) / (2*a) ].
"""

from __future__ import annotations

from fractions import Fraction

from opengalois.radicals.ast import Expr, add, div, qq, root, sub

__all__ = ["build"]


def build(*, a: Fraction, b: Fraction, c: Fraction) -> list[Expr]:
    """Build the canonical degree-2 radical-root list.

    Args:
        a: Leading coefficient of the quadratic polynomial.
        b: Linear coefficient of the quadratic polynomial.
        c: Constant coefficient of the quadratic polynomial.

    Returns:
        The ordered list prescribed by the quadratic-formula rule.

    Raises:
        ValueError: If ``a`` is zero.
    """
    if a == 0:
        raise ValueError("deg2_quadratic_formula.build() requires a non-zero leading coefficient")

    delta = b * b - Fraction(4, 1) * a * c
    minus_b = qq(-b)
    sqrt_delta = root(2, qq(delta))
    denominator = qq(Fraction(2, 1) * a)
    return [
        div(add(minus_b, sqrt_delta), denominator),
        div(sub(minus_b, sqrt_delta), denominator),
    ]
