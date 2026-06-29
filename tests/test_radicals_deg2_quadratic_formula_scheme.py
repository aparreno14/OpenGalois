from __future__ import annotations

from fractions import Fraction

from opengalois.radicals import add, div, qq, root, sub
from opengalois.radicals.schemes import deg2_quadratic_formula


def test_build_returns_canonical_quadratic_formula_roots() -> None:
    exprs = deg2_quadratic_formula.build(a=Fraction(2, 1), b=Fraction(-3, 1), c=Fraction(5, 1))

    expected = [
        div(add(qq(Fraction(3, 1)), root(2, qq(Fraction(-31, 1)))), qq(Fraction(4, 1))),
        div(sub(qq(Fraction(3, 1)), root(2, qq(Fraction(-31, 1)))), qq(Fraction(4, 1))),
    ]
    assert exprs == expected
