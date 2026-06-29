"""Polynomial operations over F_p[x] in ascending representation."""

from __future__ import annotations

from dataclasses import dataclass

FpPoly = list[int]


def _trim(poly: FpPoly) -> FpPoly:
    """Return a copy of an ascending polynomial without trailing zeroes."""
    i = len(poly) - 1
    while i >= 0 and poly[i] == 0:
        i -= 1
    return poly[: i + 1]


def _is_prime_trial(n: int) -> bool:
    """Return whether ``n`` is prime by exact trial division."""
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


@dataclass(frozen=True)
class PrimeField:
    """Prime field F_p represented by Python integers in [0, p)."""

    p: int

    def __post_init__(self) -> None:
        """Validate the characteristic."""
        if not _is_prime_trial(self.p):
            raise ValueError(f"p={self.p} must be prime")

    def normalize(self, value: int) -> int:
        """Return ``value`` modulo p."""
        return value % self.p

    def inv(self, value: int) -> int:
        """Return the multiplicative inverse of ``value`` in F_p."""
        value %= self.p
        if value == 0:
            raise ZeroDivisionError("zero has no multiplicative inverse")
        return pow(value, -1, self.p)


class FpPolynomialRing:
    """Polynomial arithmetic over F_p.

    A polynomial a_0 + a_1*x + ... + a_n*x^n is represented by the ascending
    coefficient list ``[a_0, a_1, ..., a_n]``. The empty list represents zero.
    """

    def __init__(self, p: int | PrimeField) -> None:
        """Create F_p[x]."""
        self.field = p if isinstance(p, PrimeField) else PrimeField(p)
        self.p = self.field.p

    def zero(self) -> FpPoly:
        """Return the zero polynomial."""
        return []

    def one(self) -> FpPoly:
        """Return the constant polynomial one."""
        return [1]

    def x(self) -> FpPoly:
        """Return the polynomial x."""
        return [0, 1]

    def from_coeffs(self, coeffs: list[int] | tuple[int, ...]) -> FpPoly:
        """Normalize ascending coefficients into F_p[x]."""
        return _trim([coeff % self.p for coeff in coeffs])

    def from_desc_ints(self, coeffs: list[int]) -> FpPoly:
        """Convert descending integer coefficients to F_p[x]."""
        return self.from_coeffs(tuple(reversed(coeffs)))

    def degree(self, poly: FpPoly) -> int:
        """Return the degree of ``poly``, or -1 for zero."""
        return len(_trim(poly)) - 1

    def is_zero(self, poly: FpPoly) -> bool:
        """Return whether ``poly`` is zero."""
        return len(_trim(poly)) == 0

    def is_one(self, poly: FpPoly) -> bool:
        """Return whether ``poly`` is one."""
        return _trim(poly) == [1]

    def equal(self, a: FpPoly, b: FpPoly) -> bool:
        """Return whether ``a`` and ``b`` represent the same polynomial."""
        return self.from_coeffs(a) == self.from_coeffs(b)

    def add(self, a: FpPoly, b: FpPoly) -> FpPoly:
        """Return a + b."""
        n = max(len(a), len(b))
        out = [0] * n
        for i in range(n):
            ai = a[i] if i < len(a) else 0
            bi = b[i] if i < len(b) else 0
            out[i] = (ai + bi) % self.p
        return _trim(out)

    def neg(self, a: FpPoly) -> FpPoly:
        """Return -a."""
        return _trim([(-coeff) % self.p for coeff in a])

    def sub(self, a: FpPoly, b: FpPoly) -> FpPoly:
        """Return a - b."""
        return self.add(a, self.neg(b))

    def scalar_mul(self, a: FpPoly, scalar: int) -> FpPoly:
        """Return scalar*a."""
        scalar %= self.p
        if scalar == 0:
            return []
        return _trim([(scalar * coeff) % self.p for coeff in a])

    def mul(self, a: FpPoly, b: FpPoly) -> FpPoly:
        """Return a*b."""
        a = self.from_coeffs(a)
        b = self.from_coeffs(b)
        if not a or not b:
            return []

        out = [0] * (len(a) + len(b) - 1)
        for i, ai in enumerate(a):
            if ai == 0:
                continue
            for j, bj in enumerate(b):
                out[i + j] = (out[i + j] + ai * bj) % self.p
        return _trim(out)

    def divmod(self, a: FpPoly, b: FpPoly) -> tuple[FpPoly, FpPoly]:
        """Return quotient and remainder of Euclidean division in F_p[x]."""
        a = self.from_coeffs(a)
        b = self.from_coeffs(b)
        if not b:
            raise ZeroDivisionError("polynomial division by zero")
        if not a or len(a) < len(b):
            return [], a

        rem = a[:]
        quotient = [0] * (len(a) - len(b) + 1)
        divisor_degree = len(b) - 1
        inv_lc = pow(b[-1], -1, self.p)

        while rem and len(rem) >= len(b):
            rem_degree = len(rem) - 1
            coeff = (rem[-1] * inv_lc) % self.p
            shift = rem_degree - divisor_degree
            quotient[shift] = coeff
            if coeff:
                for i, bi in enumerate(b):
                    rem[i + shift] = (rem[i + shift] - coeff * bi) % self.p
            rem = _trim(rem)

        return _trim(quotient), rem

    def div(self, a: FpPoly, b: FpPoly) -> FpPoly:
        """Return the Euclidean quotient of a by b."""
        return self.divmod(a, b)[0]

    def rem(self, a: FpPoly, b: FpPoly) -> FpPoly:
        """Return a modulo b."""
        return self.divmod(a, b)[1]

    def gcd_ext(self, a: FpPoly, b: FpPoly) -> tuple[FpPoly, FpPoly, FpPoly]:
        """Return monic g, s, t such that g = s*a + t*b."""
        r0, r1 = self.from_coeffs(a), self.from_coeffs(b)
        s0: FpPoly = [1]
        s1: FpPoly = []
        t0: FpPoly = []
        t1: FpPoly = [1]

        while r1:
            q, r = self.divmod(r0, r1)
            r0, r1 = r1, r
            s0, s1 = s1, self.sub(s0, self.mul(q, s1))
            t0, t1 = t1, self.sub(t0, self.mul(q, t1))

        if r0:
            inv_lc = pow(r0[-1], -1, self.p)
            r0 = self.scalar_mul(r0, inv_lc)
            s0 = self.scalar_mul(s0, inv_lc)
            t0 = self.scalar_mul(t0, inv_lc)

        return r0, s0, t0

    def gcd(self, a: FpPoly, b: FpPoly) -> FpPoly:
        """Return the monic gcd of a and b."""
        return self.gcd_ext(a, b)[0]

    def inv_mod(self, a: FpPoly, modulus: FpPoly) -> FpPoly:
        """Return a^{-1} modulo ``modulus``."""
        g, s, _ = self.gcd_ext(a, modulus)
        if g != [1]:
            raise ValueError("polynomial is not invertible modulo the given modulus")
        return self.rem(s, modulus)

    def pow_mod(self, a: FpPoly, exponent: int, modulus: FpPoly) -> FpPoly:
        """Return a**exponent modulo ``modulus``."""
        if exponent < 0:
            a = self.inv_mod(a, modulus)
            exponent = -exponent

        result = [1]
        base = self.rem(a, modulus)
        while exponent:
            if exponent & 1:
                result = self.rem(self.mul(result, base), modulus)
            exponent >>= 1
            if exponent:
                base = self.rem(self.mul(base, base), modulus)
        return result

    def derivative(self, a: FpPoly) -> FpPoly:
        """Return the formal derivative."""
        a = self.from_coeffs(a)
        if len(a) <= 1:
            return []
        return _trim([(i * coeff) % self.p for i, coeff in enumerate(a[1:], start=1)])

    def monic(self, a: FpPoly) -> FpPoly:
        """Return the monic associate of a nonzero polynomial."""
        a = self.from_coeffs(a)
        if not a:
            raise ValueError("zero polynomial has no monic associate")
        return self.scalar_mul(a, pow(a[-1], -1, self.p))

    def eval(self, a: FpPoly, x: int) -> int:
        """Evaluate ``a`` at ``x`` in F_p."""
        x %= self.p
        value = 0
        for coeff in reversed(a):
            value = (value * x + coeff) % self.p
        return value
