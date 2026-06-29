from __future__ import annotations

from fractions import Fraction

from opengalois.algorithms.factorization import factorize_le5, factorize_le5_multiplicity


def _mul_desc(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
    if not a or not b:
        return []
    out = [Fraction(0) for _ in range(len(a) + len(b) - 1)]
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            out[i + j] += ai * bj
    while out and out[0] == 0:
        out.pop(0)
    return out


def _prod_desc(polys: list[list[Fraction]]) -> list[Fraction]:
    out = [Fraction(1)]
    for poly in polys:
        out = _mul_desc(out, poly)
    return out


def _q(values: list[int | Fraction]) -> list[Fraction]:
    return [Fraction(v) for v in values]


def test_rational_noninteger_linear_factors() -> None:
    poly = [Fraction(1), Fraction(-5, 6), Fraction(1, 6)]
    factors = factorize_le5(poly)
    assert factors == [
        [Fraction(1), Fraction(-1, 2)],
        [Fraction(1), Fraction(-1, 3)],
    ]
    assert _prod_desc(factors) == poly


def test_x5_minus_one() -> None:
    poly = _q([1, 0, 0, 0, 0, -1])
    factors = factorize_le5(poly)
    assert factors == [_q([1, -1]), _q([1, 1, 1, 1, 1])]
    assert _prod_desc(factors) == poly


def test_repeated_factors() -> None:
    poly = _prod_desc([
        _q([1, 1]),
        _q([1, 1]),
        _q([1, 0, 1]),
    ])
    factors = factorize_le5(poly)
    assert factors == [_q([1, 1]), _q([1, 1]), _q([1, 0, 1])]
    assert factorize_le5_multiplicity(poly) == [(_q([1, 1]), 2), (_q([1, 0, 1]), 1)]
    assert _prod_desc(factors) == poly


def test_degree_five_mixed_factorization() -> None:
    poly = _prod_desc([
        _q([1, -2]),
        _q([1, 3]),
        _q([1, 0, 1]),
        _q([1, 1]),
    ])
    factors = factorize_le5(poly)
    assert factors == [_q([1, -2]), _q([1, 1]), _q([1, 3]), _q([1, 0, 1])]
    assert _prod_desc(factors) == poly


def test_irreducible_modular_certificate_case() -> None:
    poly = _q([1, 0, 0, 0, 1, 1])
    factors = factorize_le5(poly)
    assert _prod_desc(factors) == poly
    assert all(f[0] == 1 for f in factors)
