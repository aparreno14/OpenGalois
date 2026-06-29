from __future__ import annotations

from fractions import Fraction

from opengalois.radicals.ast import Expr, add, div, mul, neg, qq, root, sub

__all__ = ["build"]


def build(*, c: Fraction, d: Fraction, e: Fraction, resolvent_roots: list[Expr]) -> list[Expr]:
    """Build the canonical Ferrari-v2 radical roots for a depressed monic quartic.

    The input quartic is ``t^4 + c*t^2 + d*t + e``. For ``d = 0`` the rule switches
    to the canonical biquadratic branch. For ``d != 0`` it uses the first certified
    resolvent root ``s`` and emits the already-simplified Ferrari expressions.

    Args:
        c: Coefficient of ``t^2``.
        d: Coefficient of ``t``.
        e: Constant coefficient.
        resolvent_roots: Ordered certified roots of the quartic cubic resolvent.

    Returns:
        Ordered list of four canonical radical-expression AST payloads.
    """
    if len(resolvent_roots) != 3:
        raise ValueError("Ferrari scheme expects exactly three cubic resolvent roots")

    two = qq(Fraction(2, 1))
    four = qq(Fraction(4, 1))

    if d == 0:
        disc = sub(mul(qq(c), qq(c)), mul(four, qq(e)))
        sqrt_disc = root(2, disc)
        minus_c = neg(qq(c))
        y_plus = div(add(minus_c, sqrt_disc), two)
        y_minus = div(sub(minus_c, sqrt_disc), two)
        s_plus = root(2, y_plus)
        s_minus = root(2, y_minus)
        return [
            s_plus,
            neg(s_plus),
            s_minus,
            neg(s_minus),
        ]

    s = resolvent_roots[0]
    u = root(2, neg(s))
    two_c = mul(two, qq(c))
    two_d_over_u = div(mul(two, qq(d)), u)
    delta1 = sub(sub(s, two_c), two_d_over_u)
    delta2 = add(sub(s, two_c), two_d_over_u)
    sqrt_delta1 = root(2, delta1)
    sqrt_delta2 = root(2, delta2)

    return [
        div(add(u, sqrt_delta1), two),
        div(sub(u, sqrt_delta1), two),
        div(add(neg(u), sqrt_delta2), two),
        div(sub(neg(u), sqrt_delta2), two),
    ]
