from __future__ import annotations

from fractions import Fraction

from opengalois.algorithms.factorization import (
    _choose_zassenhaus_prime,
    _is_good_prime_for_zassenhaus,
    _prime_stream_up_to,
    _zassenhaus_prime_search_bound,
    factorize_le5,
    factorize_le5_multiplicity,
)
from opengalois.polyops.desc_zx import _degree_desc_z


def _mul_q(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
    ar = list(reversed(a))
    br = list(reversed(b))
    out = [Fraction(0) for _ in range(len(ar) + len(br) - 1)]
    for i, ai in enumerate(ar):
        for j, bj in enumerate(br):
            out[i + j] += ai * bj
    return list(reversed(out))


def _pow_q(f: list[Fraction], e: int) -> list[Fraction]:
    out = [Fraction(1)]
    for _ in range(e):
        out = _mul_q(out, f)
    return out


def _product_from_multiplicity(factors: list[tuple[list[Fraction], int]]) -> list[Fraction]:
    out = [Fraction(1)]
    for factor, mult in factors:
        out = _mul_q(out, _pow_q(factor, mult))
    return out


def test_rational_non_integer_linear_factors() -> None:
    f = [Fraction(1), Fraction(-5, 6), Fraction(1, 6)]
    assert factorize_le5(f) == [
        [Fraction(1), Fraction(-1, 2)],
        [Fraction(1), Fraction(-1, 3)],
    ]


def test_repeated_quadratic_factor() -> None:
    f = [Fraction(1), Fraction(0), Fraction(2), Fraction(0), Fraction(1)]
    assert factorize_le5_multiplicity(f) == [([Fraction(1), Fraction(0), Fraction(1)], 2)]


def test_x5_minus_one() -> None:
    f = [Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(-1)]
    factors = factorize_le5_multiplicity(f)
    assert _product_from_multiplicity(factors) == f
    assert [len(g) - 1 for g, _ in factors] == [1, 4]


def test_prime_search_uses_theoretical_bound() -> None:
    f = [1, 0, 0, 0, 0, -1]
    bound = _zassenhaus_prime_search_bound(f)
    p = _choose_zassenhaus_prime(f)
    assert p <= bound
    assert _is_good_prime_for_zassenhaus(f, p)
    assert list(_prime_stream_up_to(p))[-1] == p


def test_modular_irreducibility_path_degree_is_preserved() -> None:
    f = [1, 0, 1]
    p = _choose_zassenhaus_prime(f)
    assert p <= _zassenhaus_prime_search_bound(f)
    assert _degree_desc_z(f) == 2
