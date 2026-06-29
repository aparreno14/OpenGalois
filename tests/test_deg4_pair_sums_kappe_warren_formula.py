from __future__ import annotations

from fractions import Fraction


def test_pair_sums_kappe_warren_auxiliary_values_match_coordinate_change() -> None:
    a = Fraction(3)
    b = Fraction(7)
    d = Fraction(-5)
    delta = Fraction(11)
    r0 = Fraction(2)
    s0 = b - r0
    w1_pair_products = (a * a - 4 * (b - r0)) * delta
    w2_pair_products = (r0 * r0 - 4 * d) * delta
    w1_pair_sums = (a * a - 4 * s0) * delta
    w2_pair_sums = ((b - s0) * (b - s0) - 4 * d) * delta
    assert w1_pair_sums == w1_pair_products
    assert w2_pair_sums == w2_pair_products
