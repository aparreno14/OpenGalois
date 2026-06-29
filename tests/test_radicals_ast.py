"""Unit tests for ``opengalois.radicals.ast``."""

from __future__ import annotations

from fractions import Fraction

from opengalois.radicals import add, div, mul, neg, pow_int, qq, qq_ref, root, sub, zeta


def test_qq_canonicalizes_fraction() -> None:
    """Rational literals should use canonical reduced strings."""
    assert qq(Fraction(2, 4)) == {"kind": "qq", "value_qq": "1/2"}



def test_add_zero_simplifies() -> None:
    """Adding zero should simplify structurally."""
    assert add(qq(0), qq(3)) == {"kind": "qq", "value_qq": "3"}



def test_double_neg_simplifies() -> None:
    """Double negation should collapse under local canonicalization."""
    assert neg(neg(qq("5/7"))) == {"kind": "qq", "value_qq": "5/7"}



def test_mul_div_pow_simplify_literal_cases() -> None:
    """Literal arithmetic should fold when it is locally safe."""
    assert mul(qq(1), qq("3/5")) == {"kind": "qq", "value_qq": "3/5"}
    assert div(qq("3/5"), qq(1)) == {"kind": "qq", "value_qq": "3/5"}
    assert pow_int(qq(2), 3) == {"kind": "qq", "value_qq": "8"}



def test_sub_from_zero_becomes_neg_literal() -> None:
    """Subtracting from zero should become a literal negation when possible."""
    assert sub(qq(0), qq("2/3")) == {"kind": "qq", "value_qq": "-2/3"}



def test_root_keeps_nontrivial_structure() -> None:
    """Nontrivial roots should preserve their structural node form."""
    assert root(2, qq_ref("rat:delta")) == {
        "kind": "root",
        "n": 2,
        "arg": {"kind": "qq", "ref": "rat:delta"},
    }



def test_zeta_shape() -> None:
    """Roots of unity should preserve their exact shape."""
    assert zeta(3, 1) == {"kind": "zeta", "n": 3, "k": 1}
