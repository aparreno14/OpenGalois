"""Polynomial operations for polynomials in Q[x].

represented as lists of coefficients in descending degree order.
"""

from fractions import Fraction
from math import comb


def _leading(coeffs: list[Fraction]) -> Fraction:
    """Retrieves the leading coefficient of a polynomial.

    Args:
        coeffs (list[Fraction]): Polynomial coefficients in descending order.

    Returns:
        Fraction: The non-zero leading coefficient.

    Raises:
        ValueError: If the polynomial evaluates to zero.
    """
    c = _trim_leading_zeros_desc(coeffs)
    if not c:
        raise ValueError("Zero polynomial")
    return c[0]

def _trim_leading_zeros_desc(p: list[Fraction]) -> list[Fraction]:
    """Remove leading zeros from a polynomial represented as a list of coefficients.

    Zero polynomial is represented as an empty list.

    Args:
        p (list[Fraction]): Polynomial coefficients in descending degree order.

    Returns:
        list[Fraction]: Polynomial with leading zeros removed.
    """
    i = 0
    while i < len(p) and p[i] == 0:
        i += 1
    return p[i:]


def _degree_desc(p: list[Fraction]) -> int:
    """Compute the degree of a polynomial.

    Args:
        p (list[Fraction]): Polynomial coefficients in descending degree order.

    Returns:
        int: Degree of the polynomial. -1 for the zero polynomial.
    """
    p = _trim_leading_zeros_desc(p)
    return len(p) - 1


def _derivative_desc(p: list[Fraction]) -> list[Fraction]:
    """Compute the derivative of a polynomial.

    Args:
        p (list[Fraction]): Polynomial coefficients in descending degree order.

    Returns:
        list[Fraction]: Coefficients of the derivative polynomial.
    """
    p = _trim_leading_zeros_desc(p)
    n = _degree_desc(p)
    out: list[Fraction] = []
    for i, a in enumerate(p[:-1]):  # drop constant term
        deg = n - i
        out.append(a * deg)
    return _trim_leading_zeros_desc(out)


def _mul_scalar_desc(p: list[Fraction], c: Fraction) -> list[Fraction]:
    """Multiply a polynomial by a scalar.

    Args:
        p (list[Fraction]): Polynomial coefficients in descending degree order.
        c (Fraction): Scalar to multiply by.

    Returns:
        list[Fraction]: Resulting polynomial after multiplication.
    """
    return _trim_leading_zeros_desc([a * c for a in p])


def _divmod_desc(a: list[Fraction], b: list[Fraction]) -> tuple[list[Fraction], list[Fraction]]:
    """Perform polynomial long division.

    Args:
        a (list[Fraction]): Dividend polynomial coefficients in descending degree order.
        b (list[Fraction]): Divisor polynomial coefficients in descending degree order.

    Returns:
        tuple[list[Fraction], list[Fraction]]: Quotient and remainder polynomials.
    """
    a = _trim_leading_zeros_desc(a)
    b = _trim_leading_zeros_desc(b)
    if _degree_desc(b) < 0:
        raise ZeroDivisionError("polynomial division by zero")

    da, db = _degree_desc(a), _degree_desc(b)
    if da < db:
        return ([], a)

    dq = da - db
    q = [Fraction(0, 1)] * (dq + 1)
    r = a[:]

    while _degree_desc(r) >= db:
        dr = _degree_desc(r)
        lead = r[0] / b[0]
        q[dq - (dr - db)] += lead

        # subtract lead * x^shift * b from r
        sub = _mul_scalar_desc(b, lead) + [Fraction(0, 1)] * (dr - db)
        
        r = [ri - si for ri, si in zip(r, sub, strict=True)]
        r = _trim_leading_zeros_desc(r)

    return (_trim_leading_zeros_desc(q), _trim_leading_zeros_desc(r))


def _gcd_desc(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
    """Compute the greatest common divisor (GCD) of two polynomials.

    Args:
        a (list[Fraction]): First polynomial coefficients in descending degree order.
        b (list[Fraction]): Second polynomial coefficients in descending degree order.

    Returns:
        list[Fraction]: GCD of the two polynomials, normalized to monic form.
    """
    a = _trim_leading_zeros_desc(a)
    b = _trim_leading_zeros_desc(b)
    # Euclidean algorithm
    while _degree_desc(b) >= 0:
        _, r = _divmod_desc(a, b)
        a, b = b, r
    # normalize to monic gcd (unique in Q[x])
    if _degree_desc(a) >= 0:
        a = _mul_scalar_desc(a, Fraction(1, 1) / a[0])
    return a


def _poly_equal_up_to_unit_desc(p: list[Fraction], q: list[Fraction]) -> bool:
    """Check if two polynomials are equal up to a unit factor.

    Args:
        p (list[Fraction]): First polynomial coefficients in descending degree order.
        q (list[Fraction]): Second polynomial coefficients in descending degree order.

    Returns:
        bool: True if the polynomials are equal up to a unit factor, False otherwise.
    """
    p = _trim_leading_zeros_desc(p)
    q = _trim_leading_zeros_desc(q)
    if _degree_desc(p) != _degree_desc(q):
        return False
    if _degree_desc(p) < 0:
        # both zero polynomials, considered equal up to unit
        return True
    # compare after monic normalization
    p_m = _mul_scalar_desc(p, Fraction(1, 1) / p[0])
    q_m = _mul_scalar_desc(q, Fraction(1, 1) / q[0])
    return p_m == q_m

def _mul_desc(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
    """Multiply two polynomials.

    Args:
        a (list[Fraction]): First polynomial coefficients in descending degree order.
        b (list[Fraction]): Second polynomial coefficients in descending degree order.

    Returns:
        list[Fraction]: Coefficients of the product polynomial.
    """
    a = _trim_leading_zeros_desc(a)
    b = _trim_leading_zeros_desc(b)
    if _degree_desc(a) < 0 or _degree_desc(b) < 0:
        return []
    ar = list(reversed(a))
    br = list(reversed(b))
    cr = [Fraction(0) for _ in range(len(ar) + len(br) - 1)]
    for i, ai in enumerate(ar):
        for j, bj in enumerate(br):
            cr[i + j] += ai * bj
    c = list(reversed(cr))
    return _trim_leading_zeros_desc(c)


def _pow_desc(p: list[Fraction], k: int) -> list[Fraction]:
    """Compute the power of a polynomial.

    Args:
        p (list[Fraction]): Polynomial coefficients in descending degree order.
        k (int): Exponent (must be non-negative).

    Returns:
        list[Fraction]: Coefficients of the polynomial raised to the power k.

    Raises:
        ValueError: If the exponent k is negative.
    """
    p = _trim_leading_zeros_desc(p)
    if k < 0:
        raise ValueError("exponent must be >= 0")
    if k == 0:
        return [Fraction(1)]
    out = [Fraction(1)]
    base = p
    e = k
    # fast exponentiation
    while e > 0:
        if e & 1:
            out = _mul_desc(out, base)
        e >>= 1
        if e:
            base = _mul_desc(base, base)
    return out

def _shift_desc(p: list[Fraction], t: Fraction) -> list[Fraction]:
    """Compute the shifted polynomial p(x + t).

    Args:
        p (list[Fraction]): Polynomial coefficients in descending degree order.
        t (Fraction): Shift value.

    Returns:
        list[Fraction]: Coefficients of the shifted polynomial.
    """
    p = _trim_leading_zeros_desc(p)
    n = _degree_desc(p)
    if n < 0:
        return []
    
    # Compute p(x+t) using binomial expansion
    out = [Fraction(0) for _ in range(n + 1)]
    for i_r, coeff in enumerate(p):
        if coeff == 0:
            continue
        i = n - i_r  # degree of the current term
        for j in range(i + 1):
            out[j] += coeff * comb(i, j) * (t ** (i - j))
    return _trim_leading_zeros_desc(list(reversed(out)))
