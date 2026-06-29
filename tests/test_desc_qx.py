from __future__ import annotations

from fractions import Fraction as F

import pytest

from opengalois.polyops.desc_qx import (
    _degree_desc,
    _derivative_desc,
    _divmod_desc,
    _gcd_desc,
    _mul_desc,
    _mul_scalar_desc,
    _poly_equal_up_to_unit_desc,
    _pow_desc,
    _shift_desc,
    _trim_leading_zeros_desc,
)

"""
Tests for polynomial operations in Q[x]
represented as lists of coefficients in descending degree order.
"""

def test_trim_leading_zeros_desc_canon_zero():
    """Test trimming leading zeros from polynomials.

    Verifies that leading zeros are removed correctly, including edge cases
    like all-zero polynomials and polynomials with trailing zeros.
    """
    assert _trim_leading_zeros_desc([]) == []
    assert _trim_leading_zeros_desc([F(0), F(0)]) == []
    assert _trim_leading_zeros_desc([F(0), F(0), F(3)]) == [F(3)]
    assert _trim_leading_zeros_desc([F(1), F(0), F(0)]) == [F(1), F(0), F(0)]


def test_degree_desc_convention():
    """Test the degree computation of polynomials.

    Verifies that the degree is computed correctly, including edge cases
    like zero polynomials and constant polynomials.
    """
    assert _degree_desc([]) == -1
    assert _degree_desc([F(0)]) == -1
    assert _degree_desc([F(0), F(0)]) == -1
    assert _degree_desc([F(7)]) == 0
    assert _degree_desc([F(2), F(0), F(1)]) == 2  # 2x^2 + 1


def test_derivative_desc_basic():
    """Test the derivative computation of polynomials.

    Verifies that the derivative is computed correctly for various cases,
    including zero, constant, and higher-degree polynomials.
    """
    # d/dx 0 = 0
    assert _derivative_desc([]) == []
    # d/dx c = 0
    assert _derivative_desc([F(5)]) == []
    # d/dx (x^2) = 2x
    assert _derivative_desc([F(1), F(0), F(0)]) == [F(2), F(0)]
    # d/dx (3x^3 + 2x - 1) = 9x^2 + 2
    assert _derivative_desc([F(3), F(0), F(2), F(-1)]) == [F(9), F(0), F(2)]


def test_mul_scalar_desc():
    """Test scalar multiplication of polynomials.

    Verifies that multiplying a polynomial by a scalar produces the correct
    result, including edge cases like zero scalar and zero polynomial.
    """
    assert _mul_scalar_desc([], F(7)) == []
    assert _mul_scalar_desc([F(2), F(0), F(1)], F(3)) == [F(6), F(0), F(3)]
    assert _mul_scalar_desc([F(2), F(0), F(1)], F(0)) == []


def test_mul_desc_basic():
    """Test multiplication of two polynomials.

    Verifies that the product of two polynomials is computed correctly,
    including edge cases like zero polynomials.
    """
    # 0 * p = 0
    assert _mul_desc([], [F(1), F(2)]) == []
    assert _mul_desc([F(1), F(2)], []) == []

    # (x^2 - 1)(x + 1) = x^3 + x^2 - x - 1
    a = [F(1), F(0), F(-1)]
    b = [F(1), F(1)]
    assert _mul_desc(a, b) == [F(1), F(1), F(-1), F(-1)]


def test_pow_desc_basic():
    """Test exponentiation of polynomials.

    Verifies that raising a polynomial to a non-negative integer power
    produces the correct result, including edge cases like zero exponent
    and zero polynomial.
    """
    # p^0 = 1 (even for p=0, by convention in your implementation)
    assert _pow_desc([F(2), F(3)], 0) == [F(1)]
    assert _pow_desc([], 0) == [F(1)]

    # (x+1)^3 = x^3 + 3x^2 + 3x + 1
    p = [F(1), F(1)]
    assert _pow_desc(p, 3) == [F(1), F(3), F(3), F(1)]

    with pytest.raises(ValueError):
        _pow_desc([F(1), F(1)], -1)


def test_divmod_desc_zero_dividend():
    """Test polynomial division with a zero dividend.

    Verifies that dividing zero by a polynomial produces zero quotient
    and zero remainder.
    """
    # 0 / (x+1) => q=0, r=0
    q, r = _divmod_desc([], [F(1), F(1)])
    assert q == []
    assert r == []


def test_divmod_desc_degree_smaller():
    """Test polynomial division when the dividend degree is smaller than the divisor.

    Verifies that the quotient is zero and the remainder is the dividend.
    """
    # x / (x^2+1) => q=0, r=x
    a = [F(1), F(0)]
    b = [F(1), F(0), F(1)]
    q, r = _divmod_desc(a, b)
    assert q == []
    assert r == a


def test_divmod_desc_exact_division():
    """Test exact polynomial division.

    Verifies that the quotient and remainder are computed correctly when
    the division is exact.
    """
    # (x^2 + 2x + 1) / (x+1) = x+1, remainder 0
    a = [F(1), F(2), F(1)]
    b = [F(1), F(1)]
    q, r = _divmod_desc(a, b)
    assert q == [F(1), F(1)]
    assert r == []


def test_divmod_desc_nonexact_division():
    """Test non-exact polynomial division.

    Verifies that the quotient and remainder are computed correctly when
    the division is not exact.
    """
    # x^2 / (x+1) = x-1, remainder 1
    a = [F(1), F(0), F(0)]
    b = [F(1), F(1)]
    q, r = _divmod_desc(a, b)
    assert q == [F(1), F(-1)]
    assert r == [F(1)]


def test_divmod_desc_division_by_zero_raises():
    """Test that division by zero raises an error.

    Verifies that attempting to divide by a zero polynomial raises a
    ZeroDivisionError.
    """
    with pytest.raises(ZeroDivisionError):
        _divmod_desc([F(1), F(2)], [])
    with pytest.raises(ZeroDivisionError):
        _divmod_desc([F(1), F(2)], [F(0), F(0)])


def test_gcd_desc_basic_and_monic():
    """Test computation of the greatest common divisor (GCD) of polynomials.

    Verifies that the GCD is computed correctly and normalized to monic form.
    """
    # gcd(0, p) = monic(p)
    assert _gcd_desc([], [F(2), F(2)]) == [F(1), F(1)]

    # gcd(2x+2, x+1) = x+1 (monic)
    assert _gcd_desc([F(2), F(2)], [F(1), F(1)]) == [F(1), F(1)]

    # gcd(x^2 - 1, x - 1) = x - 1
    a = [F(1), F(0), F(-1)]
    b = [F(1), F(-1)]
    assert _gcd_desc(a, b) == [F(1), F(-1)]


def test_poly_equal_up_to_unit_desc():
    """Test equality of polynomials up to a unit factor.

    Verifies that polynomials are correctly identified as equal or not
    equal up to a unit factor.
    """
    # 2x^2 + 2 is equal up to unit to x^2 + 1
    p = [F(2), F(0), F(2)]
    q = [F(1), F(0), F(1)]
    assert _poly_equal_up_to_unit_desc(p, q) is True
    # Different degrees => False
    assert _poly_equal_up_to_unit_desc([F(1), F(0)], [F(1), F(0), F(0)]) is False
    # Both zero => True
    assert _poly_equal_up_to_unit_desc([], []) is True


def test_shift_desc_basic():
    """Test shifting of polynomials.

    Verifies that shifting a polynomial by a constant produces the correct
    result.
    """
    # 0 shifted is 0
    assert _shift_desc([], F(5)) == []

    # x^2 shifted by 1: (x+1)^2 = x^2 + 2x + 1
    assert _shift_desc([F(1), F(0), F(0)], F(1)) == [F(1), F(2), F(1)]

    # x shifted by 3: x+3
    assert _shift_desc([F(1), F(0)], F(3)) == [F(1), F(3)]

    # (x^2 - 1) shifted by 1: (x+1)^2 - 1 = x^2 + 2x
    assert _shift_desc([F(1), F(0), F(-1)], F(1)) == [F(1), F(2), F(0)]


def test_shift_desc_composition():
    """Test composition of polynomial shifts.

    Verifies that shifting a polynomial by two constants sequentially is
    equivalent to shifting it by their sum.
    """
    # p(x + a + b) == (p(x + a))(x + b)
    p = [F(3), F(0), F(2), F(-1)]  # 3x^3 + 2x - 1
    a = F(2)
    b = F(-5)

    left = _shift_desc(p, a + b)
    right = _shift_desc(_shift_desc(p, a), b)
    assert left == right

def test_divmod_desc_complex_fractions():
    """Test division with complex fractions to ensure arithmetic robustness."""
    # (1/2 x^2 + 1/3) / (1/4 x) 
    # q should be 2x, r should be 1/3
    a = [F(1, 2), F(0), F(1, 3)]
    b = [F(1, 4), F(0)]
    
    q, r = _divmod_desc(a, b)
    
    # q = 2x
    assert q == [F(2), F(0)] 
    # r = 1/3
    assert r == [F(1, 3)]
    
    # Reconstruct: a = b*q + r
    # (1/4 x) * (2x) + 1/3 = 1/2 x^2 + 1/3. Correct.

def test_gcd_desc_fractions():
    """Test GCD with fractional coefficients."""
    # p = 1/2 x^2 - 1/2  = 1/2(x^2 - 1)
    # q = 1/3 x - 1/3    = 1/3(x - 1)
    # GCD should be monic: x - 1
    p = [F(1, 2), F(0), F(-1, 2)]
    q = [F(1, 3), F(-1, 3)]
    
    # The gcd must be normalized to x - 1 (monic)
    assert _gcd_desc(p, q) == [F(1), F(-1)]
    
def test_gcd_desc_negative_leading_coeffs():
    """Test that GCD returns a monic polynomial even with negative inputs."""
    # a = -x + 1
    # b = -2x + 2
    # gcd should be x - 1, NOT -x + 1
    a = [F(-1), F(1)]
    b = [F(-2), F(2)]
    
    g = _gcd_desc(a, b)
    assert g == [F(1), F(-1)]
    assert g[0] == F(1)  # Must be monic
    
def test_operations_with_untrimmed_inputs():
    """Test that functions handle inputs with explicit leading zeros gracefully."""
    # Input: 0x^2 + 2x + 1 (represented as [0, 2, 1])
    p_dirty = [F(0), F(2), F(1)]
    
    # Degree should be 1, not 2
    assert _degree_desc(p_dirty) == 1
    
    # Multiplication should verify trimming
    # (0x^2 + 1) * (1) = 1
    res = _mul_desc([F(0), F(0), F(1)], [F(1)])
    assert res == [F(1)]
    
def test_shift_desc_negative_and_fraction():
    """Test polynomial shift with negative and fractional values."""
    # p(x) = x^2
    # Shift by -1/2: p(x - 1/2) = (x - 1/2)^2 = x^2 - x + 1/4
    p = [F(1), F(0), F(0)]
    t = F(-1, 2)
    
    shifted = _shift_desc(p, t)
    expected = [F(1), F(-1), F(1, 4)]
    
    assert shifted == expected

def test_shift_desc_identity():
    """Test that shifting by 0 leaves the polynomial unchanged."""
    p = [F(1), F(2), F(3)]
    assert _shift_desc(p, F(0)) == p
    
def test_shift_constant_polynomial():
    """Test shifting a constant polynomial."""
    # p(x) = 5, shift by 3: p(x+3) = 5 (unchanged)
    p = [F(5)]
    t = F(3)
    
    shifted = _shift_desc(p, t)
    assert shifted == [F(5)]
    
def test_gcd_coprime():
    """Test GCD of coprime polynomials is 1."""
    # x and x + 1 are coprime
    a = [F(1), F(0)]
    b = [F(1), F(1)]
    
    assert _gcd_desc(a, b) == [F(1)]