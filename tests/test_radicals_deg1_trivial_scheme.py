from fractions import Fraction

from opengalois.radicals import qq
from opengalois.radicals.schemes import deg1_trivial


def test_build_returns_single_canonical_rational_root() -> None:
    exprs = deg1_trivial.build(a=Fraction(2, 1), b=Fraction(-3, 1))

    assert exprs == [qq(Fraction(3, 2))]
