from __future__ import annotations

from opengalois.algorithms.factorization_fpx import factor_fpx_le5
from opengalois.polyops.asc_fpx import FpPolynomialRing


def _prod(ring: FpPolynomialRing, factors: list[list[int]]) -> list[int]:
    out = ring.one()
    for factor in factors:
        out = ring.mul(out, factor)
    return out


def _expand(factors_with_mult: list[tuple[list[int], int]]) -> list[list[int]]:
    out: list[list[int]] = []
    for factor, multiplicity in factors_with_mult:
        out.extend([factor] * multiplicity)
    return out


def test_split_product_of_linear_factors_without_root_enumeration() -> None:
    ring = FpPolynomialRing(101)
    factors = [[-3, 1], [-17, 1], [-42, 1], [-88, 1]]
    f = ring.monic(_prod(ring, factors))

    actual = factor_fpx_le5(ring, f)

    assert [e for _, e in actual] == [1, 1, 1, 1]
    assert _prod(ring, _expand(actual)) == f
    assert [ring.degree(g) for g, _ in actual] == [1, 1, 1, 1]


def test_split_two_irreducible_quadratics() -> None:
    ring = FpPolynomialRing(5)
    q1 = [2, 0, 1]  # x^2 + 2, irreducible over F_5
    q2 = [2, 1, 1]  # x^2 + x + 2, irreducible over F_5
    f = ring.monic(_prod(ring, [q1, q2]))

    actual = factor_fpx_le5(ring, f)

    assert _prod(ring, _expand(actual)) == f
    assert sorted((g for g, _ in actual), key=lambda h: (ring.degree(h), tuple(h))) == [q1, q2]
    assert [e for _, e in actual] == [1, 1]


def test_irreducible_degree_five_is_kept_whole() -> None:
    ring = FpPolynomialRing(2)
    f = [1, 0, 1, 0, 0, 1]  # x^5 + x^2 + 1, irreducible over F_2

    actual = factor_fpx_le5(ring, f)

    assert actual == [(f, 1)]


def test_large_prime_does_not_enumerate_quadratics() -> None:
    ring = FpPolynomialRing(1_000_003)
    q1 = [1, 0, 1]
    q2 = [1, 3, 1]
    f = ring.monic(_prod(ring, [q1, q2]))

    actual = factor_fpx_le5(ring, f)

    assert _prod(ring, _expand(actual)) == f
    assert [ring.degree(g) for g, _ in actual] == [2, 2]
