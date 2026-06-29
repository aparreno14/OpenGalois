"""Degree-bounded factorization over F_p[x].

The Q[x] Zassenhaus caller chooses good primes, so the modular polynomial is
square-free.  This module therefore implements the square-free finite-field
part only:

    distinct-degree factorization + equal-degree Cantor-Zassenhaus splitting.

The implementation keeps the project representation: ascending coefficient
lists over a prime field.  Factors are returned monic and in deterministic
order.
"""

from __future__ import annotations

import hashlib
from itertools import product

from opengalois.polyops.asc_fpx import FpPoly, FpPolynomialRing

_MAX_CZ_HASH_ATTEMPTS = 512
_EXHAUSTIVE_ALPHA_SPACE_LIMIT = 512


def _divide_exact(ring: FpPolynomialRing, a: FpPoly, b: FpPoly) -> FpPoly:
    """Return a/b in F_p[x], requiring zero remainder."""
    quotient, remainder = ring.divmod(a, b)
    if remainder:
        raise ValueError("polynomial division is not exact in F_p[x]")
    return quotient


def _factor_sort_key(
    ring: FpPolynomialRing,
    factor: FpPoly,
) -> tuple[int, tuple[int, ...]]:
    """Return the deterministic ordering key used for monic factors."""
    factor = ring.from_coeffs(factor)
    return ring.degree(factor), tuple(factor)


def _is_proper_factor(
    ring: FpPolynomialRing,
    d: FpPoly,
    g: FpPoly,
) -> bool:
    """Return whether d is a proper nonconstant factor of g."""
    d = ring.from_coeffs(d)
    g = ring.from_coeffs(g)
    return ring.degree(d) > 0 and not ring.equal(d, g)


# =============================================================================
# Distinct-degree factorization
# =============================================================================


def _ddf_logic_fpx(
    ring: FpPolynomialRing,
    f: FpPoly,
) -> list[tuple[FpPoly, int]]:
    """Return [(g_k, k)] where g_k is the product of degree-k factors.

    This is the OpenGalois adaptation of the user's ``_ddf_logic_fpx``:

        h <- x mod f
        h <- h^p mod f
        g_k <- gcd(h - x, f)

    The input is expected to be monic and square-free.
    """
    f = ring.monic(f)
    if ring.degree(f) <= 0:
        return []

    out: list[tuple[FpPoly, int]] = []
    x_poly = ring.x()
    h = ring.rem(x_poly, f)
    k = 0

    while not ring.is_one(f):
        h = ring.pow_mod(h, ring.p, f)
        k += 1

        g_k = ring.gcd(ring.sub(h, x_poly), f)
        if not ring.is_one(g_k):
            g_k = ring.monic(g_k)
            out.append((g_k, k))
            f = _divide_exact(ring, f, g_k)
            if ring.is_one(f):
                break
            h = ring.rem(h, f)

    return out


def didegr_fact_fpx(
    ring: FpPolynomialRing,
    g: FpPoly,
) -> list[FpPoly]:
    """Return the dense distinct-degree list [h_1, h_2, ...].

    This keeps the shape of the user's original implementation: the entry at
    index r-1 is the product of all irreducible factors of degree r, or 1 if
    there is no such factor.
    """
    pairs = _ddf_logic_fpx(ring, g)
    max_degree = max((degree for _, degree in pairs), default=0)
    dense = [ring.one() for _ in range(max_degree)]
    for product_factor, degree in pairs:
        dense[degree - 1] = product_factor
    return dense


# =============================================================================
# Equal-degree Cantor-Zassenhaus splitting
# =============================================================================


def _Mk_logic_fpx(
    ring: FpPolynomialRing,
    alpha: FpPoly,
    k: int,
    g: FpPoly,
) -> FpPoly:
    """Return the Cantor-Zassenhaus splitting polynomial M_k(alpha).

    This is the same case distinction as in the user's implementation:

    * p = 2: trace alpha + alpha^2 + ... + alpha^(2^(k-1));
    * p odd: alpha^((p^k - 1)/2) - 1.
    """
    if ring.p == 2:
        out = ring.zero()
        alpha_power = ring.rem(alpha, g)
        for j in range(k):
            out = ring.add(out, alpha_power)
            if j < k - 1:
                alpha_power = ring.pow_mod(alpha_power, 2, g)
        return out

    exponent = (ring.p**k - 1) // 2
    return ring.sub(ring.pow_mod(alpha, exponent, g), ring.one())


def _hash_alpha(
    ring: FpPolynomialRing,
    r: int,
    g: FpPoly,
    attempt: int,
) -> FpPoly:
    """Return a deterministic pseudo-random alpha of degree < deg(g)."""
    degree = ring.degree(g)
    if degree <= 0:
        return ring.zero()

    seed = (
        f"opengalois-cz|p={ring.p}|r={r}|g="
        + ",".join(str(c) for c in ring.from_coeffs(g))
        + f"|attempt={attempt}"
    ).encode("ascii")

    coeffs: list[int] = []
    block = 0
    while len(coeffs) < degree:
        digest = hashlib.sha256(seed + block.to_bytes(4, "big")).digest()
        for offset in range(0, len(digest), 8):
            if len(coeffs) >= degree:
                break
            coeffs.append(int.from_bytes(digest[offset : offset + 8], "big") % ring.p)
        block += 1

    return ring.from_coeffs(coeffs)


def _small_alpha_space_size(p: int, degree: int) -> int:
    """Return p**degree, capped beyond the exhaustive-search threshold."""
    size = 1
    for _ in range(degree):
        size *= p
        if size > _EXHAUSTIVE_ALPHA_SPACE_LIMIT:
            break
    return size


def _iter_small_alphas(ring: FpPolynomialRing, degree: int):
    """Yield all alpha of degree < degree when the space is small enough."""
    if degree <= 0:
        return
    if _small_alpha_space_size(ring.p, degree) > _EXHAUSTIVE_ALPHA_SPACE_LIMIT:
        return

    for coeffs in product(range(ring.p), repeat=degree):
        alpha = ring.from_coeffs(list(coeffs))
        if alpha:
            yield alpha


def _cz_split_once(
    ring: FpPolynomialRing,
    r: int,
    g: FpPoly,
) -> FpPoly:
    """Return a proper Cantor-Zassenhaus divisor of g."""
    g = ring.monic(g)
    if ring.degree(g) <= r:
        raise ValueError("equal-degree split requested for an already irreducible block")

    for attempt in range(_MAX_CZ_HASH_ATTEMPTS):
        alpha = _hash_alpha(ring, r, g, attempt)
        if ring.is_zero(alpha):
            continue
        d = ring.gcd(_Mk_logic_fpx(ring, alpha, r, g), g)
        if _is_proper_factor(ring, d, g):
            return ring.monic(d)

    for alpha in _iter_small_alphas(ring, ring.degree(g)) or ():
        d = ring.gcd(_Mk_logic_fpx(ring, alpha, r, g), g)
        if _is_proper_factor(ring, d, g):
            return ring.monic(d)

    raise RuntimeError("Cantor-Zassenhaus failed to split an equal-degree block")


def eqdegr_fact_fpx(
    ring: FpPolynomialRing,
    r: int,
    h: FpPoly,
) -> list[FpPoly]:
    """Factor h into monic irreducibles of degree r.

    The input h is assumed to be square-free and to be a product of irreducible
    factors all of degree r.
    """
    h = ring.monic(h)
    degree = ring.degree(h)
    if degree <= 0:
        return []
    if r <= 0:
        raise ValueError("equal-degree factorization requires r >= 1")
    if degree % r != 0:
        raise ValueError("equal-degree block degree is not divisible by r")

    expected_count = degree // r
    if expected_count == 1:
        return [h]

    factors = [h]
    while len(factors) < expected_count:
        next_factors: list[FpPoly] = []
        for g in factors:
            if ring.degree(g) == r:
                next_factors.append(g)
                continue

            d = _cz_split_once(ring, r, g)
            q = ring.monic(_divide_exact(ring, g, d))
            next_factors.extend([d, q])

        factors = next_factors

    return sorted((ring.monic(g) for g in factors), key=lambda g: _factor_sort_key(ring, g))


# =============================================================================
# Public API
# =============================================================================


def factor_fpx_le5(ring: FpPolynomialRing, f: FpPoly) -> list[tuple[FpPoly, int]]:
    """Factor a square-free degree-bounded polynomial over F_p[x].

    The returned factors are monic, irreducible, and sorted deterministically.
    Multiplicities are always one: in OpenGalois this routine is called after
    the Zassenhaus good-prime test, so ``f mod p`` is square-free.
    """
    f = ring.from_coeffs(f)
    if not f:
        raise ValueError("cannot factor the zero polynomial over F_p[x]")
    if ring.degree(f) <= 0:
        return []
    if ring.degree(f) > 6:
        raise ValueError("only polynomials of degree <= 6 are supported")

    f = ring.monic(f)
    factors: list[tuple[FpPoly, int]] = []

    for product_factor, degree in _ddf_logic_fpx(ring, f):
        for factor in eqdegr_fact_fpx(ring, degree, product_factor):
            factors.append((ring.monic(factor), 1))

    return sorted(
        factors,
        key=lambda item: (_factor_sort_key(ring, item[0]), item[1]),
    )


# Compatibility name used by the prototype backend.
def fact_fpx(ring: FpPolynomialRing, f: FpPoly) -> list[tuple[FpPoly, int]]:
    """Compatibility wrapper for degree-bounded F_p[x] factorization."""
    return factor_fpx_le5(ring, f)



