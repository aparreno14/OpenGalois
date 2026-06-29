from __future__ import annotations

from fractions import Fraction

import pytest

from opengalois.api import _parse_coeffs_le5, _to_fraction


def test_to_fraction_accepts_integer_string() -> None:
    assert _to_fraction("3") == Fraction(3, 1)


def test_to_fraction_accepts_negative_rational_string() -> None:
    assert _to_fraction("-1/2") == Fraction(-1, 2)


def test_to_fraction_accepts_rational_with_spaces() -> None:
    assert _to_fraction("  -1 / 2  ") == Fraction(-1, 2)


def test_to_fraction_accepts_fraction_instance() -> None:
    assert _to_fraction(Fraction(7, 5)) == Fraction(7, 5)


def test_to_fraction_rejects_zero_denominator() -> None:
    with pytest.raises(ValueError, match="zero denominator"):
        _to_fraction("1/0")


def test_to_fraction_rejects_invalid_rational() -> None:
    with pytest.raises(ValueError, match="invalid rational coefficient"):
        _to_fraction("1/2/3")


def test_to_fraction_rejects_empty_string() -> None:
    with pytest.raises(ValueError, match="empty coefficient"):
        _to_fraction("   ")


def test_to_fraction_rejects_invalid_integer() -> None:
    with pytest.raises(ValueError, match="invalid integer coefficient"):
        _to_fraction("abc")


def test_parse_coeffs_le5_accepts_valid_descending_input() -> None:
    out = _parse_coeffs_le5(["1", "0", "0", "0", "-1", "-1/2"])
    assert out == [
        Fraction(1, 1),
        Fraction(0, 1),
        Fraction(0, 1),
        Fraction(0, 1),
        Fraction(-1, 1),
        Fraction(-1, 2),
    ]


def test_parse_coeffs_le5_rejects_too_few_coeffs() -> None:
    with pytest.raises(ValueError, match="2..6 coefficients"):
        _parse_coeffs_le5(["1"])


def test_parse_coeffs_le5_rejects_too_many_coeffs() -> None:
    with pytest.raises(ValueError, match="2..6 coefficients"):
        _parse_coeffs_le5(["1", "0", "0", "0", "0", "0", "1"])


def test_parse_coeffs_le5_rejects_zero_leading_coefficient() -> None:
    with pytest.raises(ValueError, match="Leading coefficient"):
        _parse_coeffs_le5(["0", "1", "-1"])