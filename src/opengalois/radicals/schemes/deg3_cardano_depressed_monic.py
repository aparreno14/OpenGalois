from __future__ import annotations

from fractions import Fraction

from opengalois.radicals.ast import Expr, add, div, mul, qq, root, sub, zeta

__all__ = ["build", "build_v1", "build_v2"]


def build_v1(*, p: Fraction, q: Fraction) -> list[Expr]:
    """Build the legacy Cardano @1 radical roots for a depressed monic cubic.

    The input cubic is ``x^3 + p x + q``. The output order matches the
    canonical rule ``radical_roots.QQ.deg3.cardano.depressed_monic@1``.

    Args:
        p: Coefficient of ``x`` in the depressed monic cubic.
        q: Constant coefficient in the depressed monic cubic.

    Returns:
        Ordered list of three canonical radical-expression AST payloads.
    """
    delta = q * q / 4 + p * p * p / 27
    minus_q_over_2 = qq(-q / 2)
    sqrt_delta = root(2, qq(delta))

    u = root(3, add(minus_q_over_2, sqrt_delta))
    v = root(3, sub(minus_q_over_2, sqrt_delta))

    omega = zeta(3, 1)
    omega2 = zeta(3, 2)

    return [
        add(u, v),
        add(mul(omega, u), mul(omega2, v)),
        add(mul(omega2, u), mul(omega, v)),
    ]


def build_v2(*, p: Fraction, q: Fraction) -> list[Expr]:
    """Build the Cardano @2 radical roots for a depressed monic cubic.

    This variant avoids introducing an independent ``v``. In the generic
    branch ``p != 0``, the complementary term is reconstructed as
    ``(-p/3) / u``. Since ``u = 0`` implies ``p = 0`` for the fixed Cardano
    choice used here, that division is safe in the generic branch.

    The singular branch ``p = 0`` is handled locally as ``x^3 + q`` and uses
    ``w = root(3, -q)`` directly, avoiding any expression of the form
    ``0 / u`` or ``0 / 0``.

    Args:
        p: Coefficient of ``x`` in the depressed monic cubic.
        q: Constant coefficient in the depressed monic cubic.

    Returns:
        Ordered list of three canonical radical-expression AST payloads.
    """
    omega = zeta(3, 1)
    omega2 = zeta(3, 2)

    if p == 0:
        w = root(3, qq(-q))
        return [
            w,
            mul(omega, w),
            mul(omega2, w),
        ]

    delta = q * q / 4 + p * p * p / 27
    minus_q_over_2 = qq(-q / 2)
    sqrt_delta = root(2, qq(delta))
    u = root(3, add(minus_q_over_2, sqrt_delta))

    alpha_over_u = div(qq(-p / 3), u)
    return [
        add(u, alpha_over_u),
        add(mul(omega, u), mul(omega2, alpha_over_u)),
        add(mul(omega2, u), mul(omega, alpha_over_u)),
    ]


# Backwards-compatible default kept on the legacy @1 shape.
build = build_v1
