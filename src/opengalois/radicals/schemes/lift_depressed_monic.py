from __future__ import annotations

from fractions import Fraction

from opengalois.radicals.ast import Expr, qq, sub


def build(*, roots: list[Expr], shift: Fraction) -> list[Expr]:
    """Lift depressed-monic radical roots back to the original polynomial.

    The normalization rule used by the project is ``g(x) = f_m(x - t)`` after
    monicization. Consequently, if ``y`` is a root of the depressed monic
    polynomial ``g``, then the corresponding root of the original polynomial is
    ``y - t``.

    Args:
        roots: Ordered radical roots for the depressed monic target polynomial.
        shift: Tschirnhaus shift ``t``.

    Returns:
        Ordered list of lifted radical-expression AST payloads.
    """
    shift_expr = qq(shift)
    return [sub(expr, shift_expr) for expr in roots]
