"""Polynomial operations for polynomials in Z[x].

Polynomials are represented as lists of integer coefficients in descending
degree order. The zero polynomial is represented by the empty list.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from fractions import Fraction

ZPoly = list[int]


def _trim_leading_zeros_desc_z(poly: ZPoly) -> ZPoly:
    """Return ``poly`` without leading zeroes."""
    i = 0
    while i < len(poly) and poly[i] == 0:
        i += 1
    return poly[i:]


def _degree_desc_z(poly: ZPoly) -> int:
    """Return the degree of ``poly``, or -1 for zero."""
    return len(_trim_leading_zeros_desc_z(poly)) - 1


def _leading_desc_z(poly: ZPoly) -> int:
    """Return the leading coefficient of a nonzero integer polynomial."""
    poly = _trim_leading_zeros_desc_z(poly)
    if not poly:
        raise ValueError("zero polynomial")
    return poly[0]


def _content_z(coeffs: Iterable[int]) -> int:
    """Return the nonnegative gcd of the supplied integers."""
    content = 0
    for coeff in coeffs:
        content = math.gcd(content, abs(coeff))
    return content


def _primitive_part_desc_z(poly: ZPoly) -> ZPoly:
    """Return the primitive associate with positive leading coefficient."""
    poly = _trim_leading_zeros_desc_z(poly)
    if not poly:
        return []

    content = _content_z(poly)
    if content > 1:
        poly = [coeff // content for coeff in poly]
    if poly and poly[0] < 0:
        poly = [-coeff for coeff in poly]
    return poly


def _primitive_integer_poly_from_QQ_desc(coeffs: list[Fraction]) -> ZPoly:
    """Clear denominators and return the primitive integer associate."""
    if not coeffs:
        return []

    den_lcm = 1
    for coeff in coeffs:
        den_lcm = math.lcm(den_lcm, coeff.denominator)

    int_coeffs = [
        int(coeff.numerator * (den_lcm // coeff.denominator))
        for coeff in coeffs
    ]
    return _primitive_part_desc_z(int_coeffs)


def _derivative_desc_z(poly: ZPoly) -> ZPoly:
    """Return the formal derivative of ``poly``."""
    poly = _trim_leading_zeros_desc_z(poly)
    degree = _degree_desc_z(poly)
    if degree <= 0:
        return []
    return _trim_leading_zeros_desc_z(
        [coeff * (degree - i) for i, coeff in enumerate(poly[:-1])]
    )


def _desc_z_to_asc(poly: ZPoly) -> ZPoly:
    """Convert descending integer coefficients to ascending order."""
    return _trim_trailing_zeros_asc_z(list(reversed(_trim_leading_zeros_desc_z(poly))))


def _asc_z_to_desc(poly: ZPoly) -> ZPoly:
    """Convert ascending integer coefficients to descending order."""
    return _trim_leading_zeros_desc_z(list(reversed(_trim_trailing_zeros_asc_z(poly))))


def _trim_trailing_zeros_asc_z(poly: ZPoly) -> ZPoly:
    """Return an ascending polynomial without trailing zeroes."""
    i = len(poly) - 1
    while i >= 0 and poly[i] == 0:
        i -= 1
    return poly[: i + 1]


def _add_asc_z(a: ZPoly, b: ZPoly) -> ZPoly:
    """Return a + b in Z[x], using ascending representation."""
    n = max(len(a), len(b))
    out = [0] * n
    for i in range(n):
        out[i] = (a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0)
    return _trim_trailing_zeros_asc_z(out)


def _mul_asc_z(a: ZPoly, b: ZPoly) -> ZPoly:
    """Return a*b in Z[x], using ascending representation."""
    a = _trim_trailing_zeros_asc_z(a)
    b = _trim_trailing_zeros_asc_z(b)
    if not a or not b:
        return []

    out = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            out[i + j] += ai * bj
    return _trim_trailing_zeros_asc_z(out)


def _scalar_mul_asc_z(poly: ZPoly, scalar: int) -> ZPoly:
    """Return scalar*poly in Z[x], using ascending representation."""
    if scalar == 0 or not poly:
        return []
    return _trim_trailing_zeros_asc_z([scalar * coeff for coeff in poly])


def _mul_desc_z(a: ZPoly, b: ZPoly) -> ZPoly:
    """Return a*b in Z[x], using descending representation."""
    return _asc_z_to_desc(_mul_asc_z(_desc_z_to_asc(a), _desc_z_to_asc(b)))


def _scalar_mul_desc_z(poly: ZPoly, scalar: int) -> ZPoly:
    """Return scalar*poly in Z[x], using descending representation."""
    return _asc_z_to_desc(_scalar_mul_asc_z(_desc_z_to_asc(poly), scalar))


def _prod_desc_z(polys: list[ZPoly]) -> ZPoly:
    """Return the product of the supplied descending integer polynomials."""
    out = [1]
    for poly in polys:
        out = _mul_desc_z(out, poly)
    return out


def _div_exact_desc_z(dividend: ZPoly, divisor: ZPoly) -> ZPoly:
    """Return dividend/divisor in Z[x], requiring exact division."""
    dividend_asc = _desc_z_to_asc(dividend)
    divisor_asc = _desc_z_to_asc(divisor)
    if not divisor_asc:
        raise ZeroDivisionError("polynomial division by zero")
    if not dividend_asc:
        return []
    if len(dividend_asc) < len(divisor_asc):
        raise ValueError("polynomial division is not exact over Z[x]")

    rem = dividend_asc[:]
    quotient = [0] * (len(dividend_asc) - len(divisor_asc) + 1)

    while rem and len(rem) >= len(divisor_asc):
        num = rem[-1]
        den = divisor_asc[-1]
        if den == 0 or num % den != 0:
            raise ValueError("polynomial division is not exact over Z[x]")

        factor = num // den
        shift = len(rem) - len(divisor_asc)
        quotient[shift] = factor
        for i, coeff in enumerate(divisor_asc):
            rem[i + shift] -= factor * coeff
        rem = _trim_trailing_zeros_asc_z(rem)

    if rem:
        raise ValueError("polynomial division is not exact over Z[x]")
    return _asc_z_to_desc(quotient)


def _divides_desc_z(dividend: ZPoly, divisor: ZPoly) -> bool:
    """Return whether ``divisor`` divides ``dividend`` in Z[x]."""
    try:
        _div_exact_desc_z(dividend, divisor)
    except ValueError:
        return False
    return True


def _max_norm_desc_z(poly: ZPoly) -> int:
    """Return the maximum absolute coefficient of a nonzero integer polynomial."""
    poly = _trim_leading_zeros_desc_z(poly)
    if not poly:
        return 0
    return max(abs(coeff) for coeff in poly)


def _center_mod(value: int, modulus: int) -> int:
    """Return the centered representative of ``value`` modulo ``modulus``."""
    value %= modulus
    if 2 * value > modulus:
        value -= modulus
    return value


def _center_asc_z(poly: ZPoly, modulus: int) -> ZPoly:
    """Center all coefficients modulo ``modulus`` in ascending representation."""
    return _trim_trailing_zeros_asc_z([_center_mod(coeff, modulus) for coeff in poly])
