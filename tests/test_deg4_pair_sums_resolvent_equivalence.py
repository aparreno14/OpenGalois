from __future__ import annotations

from fractions import Fraction

import pytest

from opengalois.nodes.resolvent import (
    _compute_deg4_cubic_x1plusx2_times_x3plusx4,
    _compute_deg4_cubic_x1x2_plus_x3x4,
)


def _trim_asc(poly: list[Fraction]) -> list[Fraction]:
    while len(poly) > 1 and poly[-1] == 0:
        poly.pop()
    return poly


def _trim_desc(poly: list[Fraction]) -> list[Fraction]:
    while len(poly) > 1 and poly[0] == 0:
        poly.pop(0)
    return poly


def _add_asc(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
    n = max(len(a), len(b))
    out = [Fraction(0)] * n
    for i in range(n):
        if i < len(a):
            out[i] += a[i]
        if i < len(b):
            out[i] += b[i]
    return _trim_asc(out)


def _mul_asc(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            out[i + j] += ai * bj
    return _trim_asc(out)


def _pow_asc(poly: list[Fraction], exp: int) -> list[Fraction]:
    out = [Fraction(1)]
    for _ in range(exp):
        out = _mul_asc(out, poly)
    return out


def _scalar_asc(poly: list[Fraction], scalar: Fraction) -> list[Fraction]:
    return _trim_asc([scalar * c for c in poly])


def _pair_sums_from_pair_products(pair_products_desc: list[Fraction], b: Fraction) -> list[Fraction]:
    """Return -R_products(b-y), since the cubic degree is odd."""
    p = _trim_desc(list(pair_products_desc))
    deg = len(p) - 1
    base = [b, Fraction(-1)]  # b-y, ascending.
    acc = [Fraction(0)]
    for i, coeff in enumerate(p):
        power = deg - i
        acc = _add_asc(acc, _scalar_asc(_pow_asc(base, power), coeff))
    if deg % 2:
        acc = _scalar_asc(acc, Fraction(-1))
    return _trim_desc(list(reversed(acc)))


@pytest.mark.parametrize(
    "quartic",
    [
        [Fraction(1), Fraction(0), Fraction(0), Fraction(-1), Fraction(-1)],
        [Fraction(1), Fraction(3), Fraction(-2), Fraction(5), Fraction(-7)],
        [Fraction(2), Fraction(-6), Fraction(4), Fraction(10), Fraction(-14)],
        [Fraction(3), Fraction(5, 2), Fraction(-7, 3), Fraction(11, 5), Fraction(-13, 7)],
    ],
)
def test_pair_sums_resolvent_is_affine_coordinate_change(quartic: list[Fraction]) -> None:
    monic_b = quartic[2] / quartic[0]
    pair_products = _compute_deg4_cubic_x1x2_plus_x3x4(quartic)
    pair_sums = _compute_deg4_cubic_x1plusx2_times_x3plusx4(quartic)

    assert pair_sums == _pair_sums_from_pair_products(pair_products, monic_b)
