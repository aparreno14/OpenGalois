"""Legacy degree-<=5 factorization prototype retained for reference (not used by the library)."""
import math
from fractions import Fraction
from itertools import product

from opengalois.algorithms.intfactor import int_divisors
from opengalois.polyops.desc_qx import _trim_leading_zeros_desc


def _get_positive_divisors(n: int) -> list[int]:
    """Return all positive divisors of |n|."""
    if n == 0:
        return []
    return list(int_divisors(abs(n)))


def _get_signed_divisors(n: int) -> list[int]:
    """Return all positive and negative divisors of |n|, sorted."""
    if n == 0:
        return []
    pos = list(int_divisors(abs(n)))
    return [-d for d in reversed(pos)] + pos


def _to_primitive_integer_poly(coeffs: list[Fraction]) -> list[int]:
    """Converts a polynomial over Q to a primitive polynomial over Z.

    Clears denominators, divides by the greatest common divisor (content),
    and normalizes the sign so that the leading coefficient is strictly positive.

    Args:
        coeffs: A list of fractions representing the polynomial coefficients
            in descending order of degree.

    Returns:
        A list of integers representing the primitive polynomial.
    """
    # 1. Clear denominators (LCM)
    lcm_den = math.lcm(*(c.denominator for c in coeffs))
    int_coeffs = [int(c.numerator * (lcm_den // c.denominator)) for c in coeffs]

    # 2. Divide by the content (GCD)
    gcd_num = math.gcd(*int_coeffs)

    if gcd_num > 1:
        int_coeffs = [c // gcd_num for c in int_coeffs]

    # 3. Normalize sign (lc > 0)
    if int_coeffs and int_coeffs[0] < 0:
        int_coeffs = [-c for c in int_coeffs]

    return int_coeffs


def _evaluate_poly(coeffs: list[int], x: int) -> int:
    """Evaluates a polynomial at a given integer point using Horner's method.

    Args:
        coeffs: A list of integers representing the polynomial coefficients
            in descending order of degree.
        x: The integer value at which to evaluate the polynomial.

    Returns:
        The integer result of the evaluation.
    """
    res = 0
    for c in coeffs:
        res = res * x + c
    return res


def _poly_divides(dividend: list[int], divisor: list[int]) -> bool:
    """Performs polynomial long division over Z[x].

    Args:
        dividend: A list of integers representing the dividend polynomial.
        divisor: A list of integers representing the divisor polynomial.

    Returns:
        True if the divisor divides the dividend with no remainder, False otherwise.
    """
    if not divisor or all(c == 0 for c in divisor):
        raise ZeroDivisionError("Divisor polynomial cannot be zero.")

    rem = list(dividend)
    deg_num = len(rem) - 1
    deg_den = len(divisor) - 1

    while deg_num >= deg_den:
        lc_num = rem[0]
        lc_den = divisor[0]

        # By Gauss's Lemma, if it divides in Q[x], coefficients must be integers in Z[x]
        if lc_num % lc_den != 0:
            return False

        factor = lc_num // lc_den

        for i in range(len(divisor)):
            rem[i] -= factor * divisor[i]

        rem.pop(0)
        deg_num -= 1

    return all(c == 0 for c in rem)


def _poly_div_q(dividend: list[Fraction], divisor: list[Fraction]) -> list[Fraction]:
    """Performs polynomial long division over Q[x] and returns the quotient.

    Assumes the division is exact (i.e., the remainder is mathematically 0).

    Args:
        dividend: A list of fractions representing the dividend polynomial
            in descending order of degree.
        divisor: A list of fractions representing the divisor polynomial
            in descending order of degree.

    Returns:
        A list of fractions representing the quotient polynomial.
    """
    rem = list(dividend)
    quot = []
    deg_num = len(rem) - 1
    deg_den = len(divisor) - 1

    while deg_num >= deg_den:
        lc_num = rem[0]
        lc_den = divisor[0]

        factor = lc_num / lc_den
        quot.append(factor)

        for i in range(len(divisor)):
            rem[i] -= factor * divisor[i]

        rem.pop(0)
        deg_num -= 1

    return quot


def factorize_le5(coeffs_q: list[Fraction]) -> list[list[Fraction]]:
    """Factorizes a monic polynomial of degree <= 5 into its irreducible components over Q[x].

    Requires the input polynomial to be strictly monic (leading coefficient == 1). 
    Ensures all extracted factors are monic polynomials.

    Args:
        coeffs_q: A list of fractions representing the polynomial coefficients
            in descending order of degree. The first element MUST be 1.

    Returns:
        A list of polynomials (each being a list of Fractions), where each
        polynomial is an irreducible monic factor over Q[x].

    Raises:
        ValueError: If the input is constant, empty, or not monic.
    """
    degree = len(coeffs_q) - 1

    if degree == 0:
        raise ValueError("Input must be a non-constant polynomial.")

    if coeffs_q[0] != Fraction(1, 1):
        raise ValueError(f"Input polynomial must be monic. Leading coefficient is {coeffs_q[0]}.")

    # Base case: Degree 1 is irreducible by definition.
    if degree == 1:
        return [coeffs_q]

    g = _to_primitive_integer_poly(coeffs_q)
    c_term = g[-1]
    lc = g[0]

    # --- B0: Trivial root x = 0 ---
    if c_term == 0:
        factor_x = [Fraction(1, 1), Fraction(0, 1)]  # The polynomial 'x'
        quotient = coeffs_q[:-1]  # Dividing by 'x' is equivalent to dropping the constant

        # Recursive step: return 'x' and factorize the remainder
        return [factor_x] + factorize_le5(quotient)

    # --- B1: Rational Root Extraction (Degrees 2, 3, 4, 5) ---
    p_candidates = _get_signed_divisors(c_term)
    q_candidates = _get_positive_divisors(lc)

    for p in p_candidates:
        for q in q_candidates:
            
            if math.gcd(p, q) != 1:
                continue  # Skip non-coprime pairs
            
            # Evaluate g(p/q) = 0 avoiding floats: sum(c_i * p^(n-i) * q^i)
            val = 0
            power_q = 1
            if p == 0:
                raise ValueError("Unexpected zero candidate for p in rational root test.")
            for c in g:
                val = val*p + c*power_q
                power_q *= q

            if val == 0:
                # Rational root r = p/q found. The monic factor is (x - p/q)
                root = Fraction(p, q)
                linear_factor = [Fraction(1, 1), -root]

                # Extract the quotient in Q[x]
                quotient = _poly_div_q(coeffs_q, linear_factor)

                # Recursive step
                return [linear_factor] + factorize_le5(quotient)

    # --- B2: Quadratic Factor Extraction (Degrees 4, 5) ---
    if degree in (4, 5):
        v1 = _evaluate_poly(g, 1)
        vm1 = _evaluate_poly(g, -1)

        d0_list = p_candidates
        d1_list = _get_signed_divisors(v1)
        dm1_list = _get_signed_divisors(vm1)

        for d0, d1, dm1 in product(d0_list, d1_list, dm1_list):
            # Parity optimization
            if (d1 + dm1 - 2 * d0) % 2 != 0:
                continue

            a = (d1 + dm1 - 2 * d0) // 2

            # Positive leading coefficient and Gauss's Lemma constraints
            if a <= 0 or lc % a != 0:
                continue

            c = d0
            b = d1 - a - c

            # Primitive polynomial constraint
            if math.gcd(a, math.gcd(abs(b), abs(c))) != 1:
                continue

            q_poly_z = [a, b, c]

            if _poly_divides(g, q_poly_z):
                # Quadratic factor found. Convert to Q[x] and make it monic.
                a_frac = Fraction(a, 1)
                quad_factor_q = [Fraction(c_z, a_frac) for c_z in q_poly_z]

                # Extract the quotient in Q[x]
                quotient = _poly_div_q(coeffs_q, quad_factor_q)

                # Recursive step
                return [quad_factor_q] + factorize_le5(quotient)

    # Survives all filters; the polynomial is strictly irreducible.
    return [coeffs_q]


def _poly_key(coeffs: list[Fraction]) -> tuple[tuple[int, int], ...]:
    """Build a hashable canonical key for a QQ polynomial (descending coeffs)."""
    coeffs = _trim_leading_zeros_desc(coeffs)
    return tuple((c.numerator, c.denominator) for c in coeffs)


def compress_factor_list(factors: list[list[Fraction]]) -> list[tuple[list[Fraction], int]]:
    """Compress a factor list into (factor, multiplicity) pairs.

    The input factors are expected to be monic polynomials in descending order.
    The output preserves the first-occurrence order deterministically.

    Args:
        factors: List of monic factor polynomials.

    Returns:
        List of (factor, multiplicity) pairs.
    """
    out: list[tuple[list[Fraction], int]] = []
    index: dict[tuple[tuple[int, int], ...], int] = {}

    for f in factors:
        f = _trim_leading_zeros_desc(f)
        k = _poly_key(f)
        if k in index:
            i = index[k]
            out[i] = (out[i][0], out[i][1] + 1)
        else:
            index[k] = len(out)
            out.append((f, 1))

    return out


def factorize_le5_multiplicity(coeffs_q: list[Fraction]) -> list[tuple[list[Fraction], int]]:
    """Same as factorize_le5 but returns multiplicities explicitly."""
    factors = factorize_le5(coeffs_q)
    return compress_factor_list(factors)