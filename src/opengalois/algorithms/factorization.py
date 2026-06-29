"""Degree-bounded factorization over Q[x]."""

from __future__ import annotations

import math
from collections.abc import Iterator
from fractions import Fraction
from itertools import combinations
from typing import Any

from opengalois.algorithms.factorization_fpx import factor_fpx_le5
from opengalois.polyops.asc_fpx import FpPoly, FpPolynomialRing
from opengalois.polyops.desc_qx import (
    _degree_desc,
    _derivative_desc,
    _divmod_desc,
    _gcd_desc,
    _leading,
    _trim_leading_zeros_desc,
)
from opengalois.polyops.desc_zx import (
    ZPoly,
    _add_asc_z,
    _asc_z_to_desc,
    _center_asc_z,
    _center_mod,
    _degree_desc_z,
    _desc_z_to_asc,
    _div_exact_desc_z,
    _divides_desc_z,
    _max_norm_desc_z,
    _mul_asc_z,
    _primitive_integer_poly_from_QQ_desc,
    _primitive_part_desc_z,
    _prod_desc_z,
    _scalar_mul_asc_z,
    _scalar_mul_desc_z,
    _trim_leading_zeros_desc_z,
    _trim_trailing_zeros_asc_z,
)


def _z_factor_to_monic_q(factor: ZPoly) -> list[Fraction]:
    """Convert a primitive Z[x] factor to its monic Q[x] representative."""
    factor = _trim_leading_zeros_desc_z(factor)
    if not factor:
        raise ValueError("zero factor")
    return [Fraction(coeff, factor[0]) for coeff in factor]


# =============================================================================
# Square-free decomposition over characteristic zero
# =============================================================================


def _squarefree_decomposition_z(f: list[Fraction]) -> list[tuple[ZPoly, int]]:
    """Return the square-free decomposition of f over Q[x]."""
    if _degree_desc(f) <= 0:
        return []

    derivative = _derivative_desc(f)
    repeated = _gcd_desc(f, derivative)
    squarefree_cofactor, _ = _divmod_desc(f, repeated)

    out: list[tuple[ZPoly, int]] = []
    multiplicity = 1

    while not (_degree_desc(squarefree_cofactor) == 0 and _leading(squarefree_cofactor) == 1):
        common = _gcd_desc(squarefree_cofactor, repeated)
        part, _ = _divmod_desc(squarefree_cofactor, common)
        if _degree_desc(part) > 0:
            out.append((_primitive_integer_poly_from_QQ_desc(part), multiplicity))
        squarefree_cofactor = common
        repeated, _ = _divmod_desc(repeated, common)
        multiplicity += 1

    return out


# =============================================================================
# Theoretical Zassenhaus prime bound and exact prime search
# =============================================================================


_PRIME_SIEVE_INITIAL_LIMIT = 1000
_PRIME_SIEVE_MIN_SEGMENT_SIZE = 65_536


def _small_primes(limit: int = _PRIME_SIEVE_INITIAL_LIMIT) -> list[int]:
    """Return all primes up to ``limit`` using a sieve of Eratosthenes."""
    if limit < 2:
        return []
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[:2] = b"\x00\x00"
    p = 2
    while p * p <= limit:
        if sieve[p]:
            start = p * p
            sieve[start : limit + 1 : p] = b"\x00" * (((limit - start) // p) + 1)
        p += 1
    return [i for i, ok in enumerate(sieve) if ok]


class _IncrementalPrimeSieve:
    """Cache-backed incremental sieve for deterministic prime iteration.

    The Zassenhaus search needs primes in increasing order but normally stops far
    below the theoretical bound. This cache starts with a small fixed sieve and
    extends it by moderate segments only when a caller actually asks for more
    primes. Thus the search keeps the same deterministic semantics as a full
    sieve up to the bound, while avoiding trial division candidate by candidate.
    """

    def __init__(self, initial_limit: int = _PRIME_SIEVE_INITIAL_LIMIT) -> None:
        self._limit = max(1, initial_limit)
        self._primes = _small_primes(self._limit)

    @staticmethod
    def _next_limit(current: int, bound: int) -> int:
        return min(bound, max(current * 2, current + _PRIME_SIEVE_MIN_SEGMENT_SIZE))

    def primes_up_to(self, bound: int) -> Iterator[int]:
        """Yield all cached/generated primes up to ``bound`` in increasing order."""
        if bound < 2:
            return

        index = 0
        while True:
            while index < len(self._primes):
                prime = self._primes[index]
                if prime > bound:
                    return
                index += 1
                yield prime

            if self._limit >= bound:
                return

            self._extend_to(self._next_limit(self._limit, bound))

    def _extend_to(self, new_limit: int) -> None:
        """Extend the sieve cache up to ``new_limit``."""
        if new_limit <= self._limit:
            return

        root = math.isqrt(new_limit)
        if root > self._limit:
            self._extend_to(root)
            if new_limit <= self._limit:
                return

        old_limit = self._limit
        lo = old_limit + 1
        hi = new_limit
        sieve = bytearray(b"\x01") * (hi - lo + 1)

        for prime in self._primes:
            if prime * prime > hi:
                break
            start = max(prime * prime, ((lo + prime - 1) // prime) * prime)
            sieve[start - lo : hi - lo + 1 : prime] = b"\x00" * (
                ((hi - start) // prime) + 1
            )

        self._primes.extend(
            lo + offset
            for offset, is_prime in enumerate(sieve)
            if is_prime and lo + offset >= 2
        )
        self._limit = new_limit


_PRIME_CACHE = _IncrementalPrimeSieve()


def _zassenhaus_prime_search_bound(f: ZPoly) -> int:
    """Return a theoretical prime-search bound for Zassenhaus.

    The bound follows the prime-search stage of Algorithm 15.19 in the
    Zassenhaus/Hensel exposition used by the project. For a primitive polynomial
    f of degree n and infinity norm A, define

        C = (n + 1)^(2n) * A^(2n - 1),
        gamma = ceil(2 log_2 C).

    A good prime is guaranteed below 2*gamma*log(gamma). The implementation
    uses a safe integer upper approximation to gamma, avoiding construction of
    C when coefficients are large. Since this backend is only used in bounded degree,
    this bound grows quasi-linearly in the coefficient bit-size.
    """
    degree = _degree_desc_z(f)
    if degree <= 0:
        return 2

    A = _max_norm_desc_z(f)
    log2_n1_upper = (degree + 1).bit_length()
    log2_a_upper = A.bit_length()
    log2_c_upper = (
        2 * degree * log2_n1_upper
        + (2 * degree - 1) * log2_a_upper
    )
    gamma = max(2, 2 * log2_c_upper)
    return max(2, math.ceil(2 * gamma * math.log(gamma)))


def _prime_stream_up_to(bound: int) -> Iterator[int]:
    """Yield primes up to ``bound`` exactly and lazily."""
    yield from _PRIME_CACHE.primes_up_to(bound)


def _is_good_prime_for_zassenhaus(f_desc: ZPoly, p: int) -> bool:
    """Return whether p is suitable for square-free modular factorization."""
    if f_desc[0] % p == 0:
        return False

    ring = FpPolynomialRing(p)
    f_mod = ring.from_desc_ints(f_desc)
    return ring.is_one(ring.gcd(f_mod, ring.derivative(f_mod)))


def _choose_zassenhaus_prime(f_desc: ZPoly) -> int:
    """Choose a good prime using the theoretical Zassenhaus bound."""
    bound = _zassenhaus_prime_search_bound(f_desc)
    for prime in _prime_stream_up_to(bound):
        if _is_good_prime_for_zassenhaus(f_desc, prime):
            return prime

    raise RuntimeError(
        "no good Zassenhaus prime found up to the theoretical bound "
        f"{bound}. This should not happen."
    )


# =============================================================================
# Modular factorization and Hensel lifting
# =============================================================================


def _fpx_to_desc_z_centered(poly_asc: FpPoly, p: int) -> ZPoly:
    """Convert ascending F_p[x] coefficients to centered descending integers."""
    return _trim_leading_zeros_desc_z([_center_mod(coeff, p) for coeff in reversed(poly_asc)])


def _verify_modular_factorization(
    ring: FpPolynomialRing,
    f_mod: FpPoly,
    factors_asc: list[FpPoly],
    leading_coeff: int,
) -> bool:
    """Check f_mod == lc(f) * product(factors) in F_p[x]."""
    product = ring.one()
    for factor in factors_asc:
        product = ring.mul(product, factor)
    product = ring.scalar_mul(product, leading_coeff % ring.p)
    return ring.equal(product, f_mod)


def _modular_factorization_z(
    f_desc: ZPoly,
    p: int,
) -> tuple[FpPolynomialRing, FpPoly, list[FpPoly], list[ZPoly]]:
    """Factor primitive square-free ``f_desc`` over F_p[x]."""
    if f_desc[0] % p == 0:
        raise ValueError("p divides lc(f)")

    ring = FpPolynomialRing(p)
    f_mod = ring.from_desc_ints(f_desc)

    factors_asc: list[FpPoly] = []
    for factor, multiplicity in factor_fpx_le5(ring, f_mod):
        if ring.degree(factor) <= 0:
            continue
        if multiplicity != 1:
            raise ValueError("p is not good: f mod p is not square-free")
        factors_asc.append(ring.monic(factor))

    factors_asc.sort(key=lambda h: (ring.degree(h), tuple(h)))
    if not _verify_modular_factorization(ring, f_mod, factors_asc, f_desc[0]):
        raise RuntimeError("invalid modular factorization")

    factors_desc = [_fpx_to_desc_z_centered(factor, p) for factor in factors_asc]
    return ring, f_mod, factors_asc, factors_desc


def _hensel_error_mod_p(
    f: ZPoly,
    u: ZPoly,
    v: ZPoly,
    modulus: int,
    p: int,
) -> FpPoly:
    """Return ((f - u*v) // modulus) mod p in ascending representation."""
    product = _mul_asc_z(u, v)
    n = max(len(f), len(product))
    out = [0] * n
    for i in range(n):
        diff = (f[i] if i < len(f) else 0) - (product[i] if i < len(product) else 0)
        if diff % modulus != 0:
            raise RuntimeError("current Hensel factors are not valid modulo M")
        out[i] = (diff // modulus) % p
    return [coeff % p for coeff in _trim_trailing_zeros_asc_z(out)]


def _hensel_lift_pair_asc(
    f: ZPoly,
    u0: ZPoly,
    v0: ZPoly,
    p: int,
    ell: int,
) -> tuple[ZPoly, ZPoly, int]:
    """Lift f == u0*v0 mod p to f == u*v mod p**ell."""
    ring = FpPolynomialRing(p)
    target = p**ell
    modulus = p

    u = _trim_trailing_zeros_asc_z(u0[:])
    v = _trim_trailing_zeros_asc_z(v0[:])

    while modulus < target:
        error = _hensel_error_mod_p(f, u, v, modulus, p)
        u_mod = ring.from_coeffs(u)
        v_mod = ring.from_coeffs(v)

        # Solve a*v + c*u == error mod p. Choose a modulo u, then divide by u.
        inv_v_mod_u = ring.inv_mod(v_mod, u_mod)
        a = ring.rem(ring.mul(error, inv_v_mod_u), u_mod)
        numerator = ring.sub(error, ring.mul(a, v_mod))
        c, remainder = ring.divmod(numerator, u_mod)
        if remainder:
            raise RuntimeError("Hensel correction is not exact modulo p")

        u = _add_asc_z(u, _scalar_mul_asc_z(a, modulus))
        v = _add_asc_z(v, _scalar_mul_asc_z(c, modulus))
        modulus *= p
        

    u = _center_asc_z(u, modulus)
    v = _center_asc_z(v, modulus)
    return u, v, modulus


# =============================================================================
# Zassenhaus recombination for bounded degree
# =============================================================================


def _zassenhaus_factor_bound_z(f: ZPoly) -> int:
    """Return the coefficient bound used for Hensel recombination.

    This is the conservative bound from Algorithm 15.19:

        B = ceil(sqrt(n + 1) * 2^n * ||f||_inf * |lc(f)|).

    The small degree bound makes the extra lifting cost negligible and keeps
    the implementation directly tied to the reference algorithm.
    """
    degree = _degree_desc_z(f)
    if degree <= 0:
        return 1

    m = (1 << degree) * _max_norm_desc_z(f) * abs(f[0])
    radicand = m * m * (degree + 1)
    root = math.isqrt(radicand)
    return root if root * root == radicand else root + 1


def _hensel_precision_from_bound(p: int, bound: int) -> tuple[int, int]:
    """Return (ell, p**ell) such that p**ell > 2*bound."""
    ell = 0
    modulus = 1
    while modulus <= 2 * bound:
        modulus *= p
        ell += 1
    return ell, modulus


def _subset_degree_desc(factors: list[ZPoly], subset: tuple[int, ...]) -> int:
    """Return the total degree of the selected descending factors."""
    return sum(_degree_desc_z(factors[i]) for i in subset)


def _candidate_subsets(factors: list[ZPoly], max_degree: int) -> list[tuple[int, ...]]:
    """Enumerate recombination subsets deterministically."""
    out: list[tuple[int, ...]] = []
    for size in range(1, len(factors)):
        for subset in combinations(range(len(factors)), size):
            degree = _subset_degree_desc(factors, subset)
            if 0 < degree <= max_degree:
                out.append(subset)
    out.sort(key=lambda subset: (_subset_degree_desc(factors, subset), len(subset), subset))
    return out


def _factor_squarefree_primitive_z_le5(f: ZPoly) -> list[ZPoly]:
    """Factor a square-free primitive polynomial in Z[x], degree <= 6."""
    degree = _degree_desc_z(f)
    if degree <= 0:
        return []
    if degree == 1:
        return [f]
    if degree > 6:
        raise ValueError("only polynomials of degree <= 6 are supported")

    p = _choose_zassenhaus_prime(f)
    _, _, _, local_factors = _modular_factorization_z(f, p)

    # Irreducibility modulo a good prime certifies irreducibility over Q.
    if len(local_factors) == 1:
        return [f]

    bound = _zassenhaus_factor_bound_z(f)
    ell, target_modulus = _hensel_precision_from_bound(p, bound)
    f_asc = _desc_z_to_asc(f)
    leading_coeff = f[0]
    max_candidate_degree = degree // 2

    for subset in _candidate_subsets(local_factors, max_candidate_degree):
        selected = [local_factors[i] for i in subset]
        complement = [
            local_factors[i]
            for i in range(len(local_factors))
            if i not in subset
        ]

        u0_desc = _scalar_mul_desc_z(_prod_desc_z(selected), leading_coeff)
        v0_desc = _prod_desc_z(complement)
        lifted_u, lifted_v, modulus = _hensel_lift_pair_asc(
            f_asc,
            _desc_z_to_asc(u0_desc),
            _desc_z_to_asc(v0_desc),
            p,
            ell,
        )
        if modulus != target_modulus:
            raise RuntimeError("unexpected Hensel modulus")

        for lifted in (lifted_u, lifted_v):
            candidate = _primitive_part_desc_z(_asc_z_to_desc(_center_asc_z(lifted, modulus)))
            candidate_degree = _degree_desc_z(candidate)
            if candidate_degree <= 0 or candidate_degree >= degree:
                continue
            if _divides_desc_z(f, candidate):
                quotient = _primitive_part_desc_z(_div_exact_desc_z(f, candidate))
                return (
                    _factor_squarefree_primitive_z_le5(candidate)
                    + _factor_squarefree_primitive_z_le5(quotient)
                )

    # With the bound above and exhaustive subset search, lack of recombination
    # means irreducibility for this degree-bounded Zassenhaus specialization.
    return [f]


# =============================================================================
# Public API
# =============================================================================


def factorize_le5(coeffs_q: list[Fraction]) -> list[list[Fraction]]:
    """Factor a monic polynomial of degree at most six over Q[x].

    The implementation follows a degree-bounded Zassenhaus strategy: primitive
    integer normalization, square-free decomposition, bounded good-prime search,
    modular factorization over F_p[x], Hensel lifting, and exact recombination
    certified by division in Z[x].
    """
    coeffs_q = _trim_leading_zeros_desc([Fraction(coeff) for coeff in coeffs_q])
    degree = _degree_desc(coeffs_q)

    if degree <= 0:
        raise ValueError("Input must be a non-constant polynomial.")
    if degree > 6:
        raise ValueError("Only polynomials of degree <= 6 are supported.")
    if coeffs_q[0] != Fraction(1, 1):
        raise ValueError(
            f"Input polynomial must be monic. Leading coefficient is {coeffs_q[0]}."
        )

    factors_with_mult: list[tuple[ZPoly, int]] = []
    for squarefree_part, multiplicity in _squarefree_decomposition_z(coeffs_q):
        for factor in _factor_squarefree_primitive_z_le5(squarefree_part):
            factors_with_mult.append((factor, multiplicity))

    out: list[list[Fraction]] = []
    for factor, multiplicity in factors_with_mult:
        monic_factor = _z_factor_to_monic_q(factor)
        out.extend([monic_factor] * multiplicity)

    out.sort(key=lambda g: (len(g), tuple((c.numerator, c.denominator) for c in g)))
    return out


def _poly_key(coeffs: list[Fraction]) -> tuple[tuple[int, int], ...]:
    """Build a hashable canonical key for a Q[x] polynomial."""
    coeffs = _trim_leading_zeros_desc(coeffs)
    return tuple((coeff.numerator, coeff.denominator) for coeff in coeffs)


def compress_factor_list(factors: list[list[Fraction]]) -> list[tuple[list[Fraction], int]]:
    """Compress a factor list into (factor, multiplicity) pairs."""
    out: list[tuple[list[Fraction], int]] = []
    index: dict[tuple[tuple[int, int], ...], int] = {}

    for factor in factors:
        factor = _trim_leading_zeros_desc(factor)
        key = _poly_key(factor)
        if key in index:
            i = index[key]
            out[i] = (out[i][0], out[i][1] + 1)
        else:
            index[key] = len(out)
            out.append((factor, 1))

    return out


def factorize_le5_multiplicity(coeffs_q: list[Fraction]) -> list[tuple[list[Fraction], int]]:
    """Return the factorization of a monic degree <= 6 polynomial over Q[x]."""
    return compress_factor_list(factorize_le5(coeffs_q))

def _fpx_to_desc_mod_p_strings(poly_asc: FpPoly, p: int) -> list[str]:
    """Convert ascending F_p[x] coefficients to descending canonical integer strings."""
    asc = _trim_trailing_zeros_asc_z([coeff % p for coeff in poly_asc])
    if not asc:
        return ["0"]
    return [str(coeff % p) for coeff in reversed(asc)]


def _mod_p_factorization_evidence(factors_asc: list[FpPoly], p: int) -> list[list[str]]:
    """Serialize modular factors as descending coefficient lists in {0,...,p-1}."""
    return [_fpx_to_desc_mod_p_strings(factor, p) for factor in factors_asc]


def zassenhaus_irreducibility_trace_le5(coeffs_q: list[Fraction]) -> dict[str, Any] | None:
    """Return compact Zassenhaus trace evidence for an irreducible degree-<=6 polynomial.

    The evidence intentionally records only:
      - the chosen good prime p,
      - the Hensel precision exponent ell used by the deterministic recombination stage,
      - the irreducible factorization of the primitive integer model modulo p.

    Hensel lifts are not serialized, because the current implementation lifts
    recombination pairs during the subset search rather than maintaining one global
    list of lifted factors.
    """
    coeffs_q = _trim_leading_zeros_desc([Fraction(coeff) for coeff in coeffs_q])
    degree = _degree_desc(coeffs_q)

    if degree <= 1:
        return None
    if degree > 6:
        raise ValueError("Only polynomials of degree <= 6 are supported.")

    f_desc = _primitive_integer_poly_from_QQ_desc(coeffs_q)
    f_desc = _trim_leading_zeros_desc_z(f_desc)

    # Only emit this trace when the same Zassenhaus implementation proves
    # irreducibility. Reducible cases should be certified by FactorizationMonicQQ.
    factors_z = _factor_squarefree_primitive_z_le5(f_desc)
    if len(factors_z) != 1 or _trim_leading_zeros_desc_z(factors_z[0]) != f_desc:
        return None

    p = _choose_zassenhaus_prime(f_desc)
    _, _, factors_asc, _ = _modular_factorization_z(f_desc, p)

    if len(factors_asc) == 1:
        ell = 0
    else:
        bound = _zassenhaus_factor_bound_z(f_desc)
        ell, _ = _hensel_precision_from_bound(p, bound)

    return {
        "prime": str(p),
        "ell": int(ell),
        "mod_p_factorization": {
            "factors_desc": _mod_p_factorization_evidence(factors_asc, p),
        },
    }


