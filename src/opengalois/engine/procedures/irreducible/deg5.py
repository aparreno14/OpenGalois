from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction
from math import gcd
from typing import Any

from opengalois.algorithms.dummit_quintic_tables import eval_all
from opengalois.algorithms.factorization import factorize_le5_multiplicity
from opengalois.codec.rationals import _frac_to_str
from opengalois.engine.context import (
    EngineContext,
    _ensure_degree_fact,
    _next_fact_id,
    _resolve_poly_desc_QQ,
)
from opengalois.engine.procedures.irreducible._radical_utils import (
    cache_radical_roots,
    emit_irreducible_to_depressed_fact,
    store_radical_expr_list,
)
from opengalois.engine.procedures.procedure import ProcedureResult
from opengalois.polyops.desc_qx import _trim_leading_zeros_desc
from opengalois.radicals.schemes import (
    deg5_mcclintock_depressed_monic,
    lift_depressed_monic,
)


def _degree_fact_id(ctx: EngineContext, poly_ref: str) -> str:
    degree_map = ctx.cache.get("_degree_fact_by_poly", {})
    if not isinstance(degree_map, dict) or poly_ref not in degree_map:
        raise ValueError(
            f"Missing Degree premise for {poly_ref!r}. "
            "Run ReducibilityNode (or emit Degree) before IrreducibleDeg5Procedure."
        )
    fid = str(degree_map[poly_ref])
    if not fid:
        raise ValueError(f"Empty Degree fact id for {poly_ref!r}.")
    return fid


def _irreducible_fact_id(ctx: EngineContext, poly_ref: str) -> str:
    irr_map = ctx.cache.get("_irreducible_fact_by_poly", {})
    if not isinstance(irr_map, dict) or poly_ref not in irr_map:
        raise ValueError(
            f"Missing IrreducibleQQ premise for {poly_ref!r}. "
            "Run ReducibilityNode before IrreducibleDeg5Procedure."
        )
    fid = str(irr_map[poly_ref])
    if not fid:
        raise ValueError(f"Empty IrreducibleQQ fact id for {poly_ref!r}.")
    return fid


def _resolve_ratqq(ctx: EngineContext, rat_ref: str) -> Fraction:
    obj = ctx.objects.objects.get(rat_ref)
    if not isinstance(obj, dict):
        raise KeyError(f"Unknown RatQQ object ref: {rat_ref!r}")
    if obj.get("kind") != "RatQQ":
        raise ValueError(f"Object {rat_ref!r} is not a RatQQ")
    value = obj.get("value")
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"RatQQ object {rat_ref!r} is missing a canonical string value"
        )
    return Fraction(value)


def _poly_eval_desc(coeffs: list[Fraction], x: Fraction) -> Fraction:
    total = Fraction(0, 1)
    for c in coeffs:
        total = total * x + c
    return total


def _lcm_nonneg(a: int, b: int) -> int:
    if a == 0:
        return abs(b)
    if b == 0:
        return abs(a)
    return abs(a * b) // gcd(a, b)


def _small_primes(limit: int = 1000) -> list[int]:
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[:2] = b"\x00\x00"
    p = 2
    while p * p <= limit:
        if sieve[p]:
            start = p * p
            sieve[start : limit + 1 : p] = b"\x00" * (((limit - start) // p) + 1)
        p += 1
    return [i for i, ok in enumerate(sieve) if ok]


_SMALL_PRIMES = _small_primes(1000)

# Deterministic for n < 2^64.
_MR64_BASES = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)

# Safety cap for CRT branching.
_MAX_CRT_RESIDUES = 4096

# Strategy used internally to locate a rational root of Dummit's sextic
# resolvent.  The public input degree remains <= 5; the "factorization"
# option reuses the same Q[x] factorization backend as ReducibilityNode,
# extended to support the auxiliary degree-6 resolvent.
#
# Accepted values:
#   - "specialized": current CRT/divisor rational-root search.
#   - "factorization": factor over Q[x] and extract a linear factor.
DUMMIT_RESOLVENT_RATIONAL_ROOT_METHOD = "factorization"


def _ctz(n: int) -> int:
    """Number of trailing zero bits in n > 0."""
    return (n & -n).bit_length() - 1


def _is_probable_prime(n: int) -> bool:
    if n < 2:
        return False

    for p in _SMALL_PRIMES:
        if n % p == 0:
            return n == p

    d = n - 1
    s = _ctz(d)
    d >>= s

    bases: tuple[int, ...]

    if n < (1 << 64):
        bases = _MR64_BASES
    else:
        # Strong practical heuristic, but not a universal deterministic proof.
        bases = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)

    for a in bases:
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False

    return True


def _pollard_brent(n: int, rng: random.Random) -> int:
    if n % 2 == 0:
        return 2
    if n % 3 == 0:
        return 3

    while True:
        y = rng.randrange(1, n - 1)
        c = rng.randrange(1, n - 1)
        m = 128

        g = 1
        r = 1
        q = 1
        x = 0
        ys = 0

        while g == 1:
            x = y
            for _ in range(r):
                y = (y * y + c) % n

            k = 0
            while k < r and g == 1:
                ys = y
                for _ in range(min(m, r - k)):
                    y = (y * y + c) % n
                    q = (q * abs(x - y)) % n
                g = gcd(q, n)
                k += m

            r <<= 1

        if g == n:
            while True:
                ys = (ys * ys + c) % n
                g = gcd(abs(x - ys), n)
                if g > 1:
                    break

        if 1 < g < n:
            return g


def _factorint_trial(n: int) -> dict[int, int]:
    """Factor a positive integer using small-prime stripping + Miller-Rabin + Pollard Rho."""
    n = abs(n)
    if n < 2:
        return {}

    fac: dict[int, int] = {}

    for p in _SMALL_PRIMES:
        if p * p > n:
            break
        e = 0
        while n % p == 0:
            n //= p
            e += 1
        if e:
            fac[p] = e

    if n == 1:
        return fac

    rng = random.Random(n)  # deterministic per input value
    stack = [n]

    while stack:
        m = stack.pop()
        if m == 1:
            continue

        if _is_probable_prime(m):
            fac[m] = fac.get(m, 0) + 1
            continue

        d = _pollard_brent(m, rng)
        stack.append(d)
        stack.append(m // d)

    return dict(sorted(fac.items()))


def _divisors_from_factorization(fac: dict[int, int]) -> list[int]:
    """Generate all positive divisors from a prime factorization."""
    divs = [1]
    for p, e in fac.items():
        next_divs: list[int] = []
        pe = 1
        for _ in range(e + 1):
            for d in divs:
                next_divs.append(d * pe)
            pe *= p
        divs = next_divs
    return sorted(divs)


def _int_divisors(n: int) -> list[int]:
    """Return all positive divisors of n."""
    n = abs(n)
    if n == 0:
        return [0]
    return _divisors_from_factorization(_factorint_trial(n))


def _primitive_integer_desc(coeffs: list[Fraction]) -> list[int]:
    """Convert a QQ-polynomial to a primitive integer polynomial."""
    coeffs = _trim_leading_zeros_desc(coeffs)
    if not coeffs or coeffs[0] == 0:
        raise ValueError("Malformed polynomial for rational-root test.")

    den_lcm = 1
    for c in coeffs:
        den_lcm = _lcm_nonneg(den_lcm, c.denominator)

    ints = [int(c * den_lcm) for c in coeffs]

    common = 0
    for n in ints:
        common = gcd(common, abs(n))
    if common > 1:
        ints = [n // common for n in ints]

    return ints


def _find_rational_root_QQ_desc_by_divisors(coeffs: list[Fraction]) -> Fraction | None:
    """Return a rational root of a QQ-polynomial in descending form, if any.

    This is the generic divisor-based rational-root search.
    """
    ints = _primitive_integer_desc(coeffs)

    if ints[-1] == 0:
        return Fraction(0, 1)

    lead = abs(ints[0])
    const = abs(ints[-1])
    int_coeffs = [Fraction(n, 1) for n in ints]

    const_divs = _int_divisors(const)
    lead_divs = _int_divisors(lead)

    for p in const_divs:
        for q in lead_divs:
            if q == 0 or gcd(p, q) != 1:
                continue
            for sign in (-1, 1):
                x = Fraction(sign * p, q)
                if _poly_eval_desc(int_coeffs, x) == 0:
                    return x
    return None


def _find_rational_root_QQ_desc(coeffs: list[Fraction]) -> Fraction | None:
    """Return a rational root using the generic divisor-based search."""
    return _find_rational_root_QQ_desc_by_divisors(coeffs)


def _poly_eval_int_mod_desc(coeffs: list[int], x: int, mod: int) -> int:
    """Evaluate an integer polynomial in descending form modulo ``mod``."""
    value = 0
    for c in coeffs:
        value = (value * x + c) % mod
    return value


def _roots_mod_prime_desc(coeffs: list[int], prime: int) -> list[int]:
    """Return all roots of ``coeffs`` modulo a small prime."""
    return [x for x in range(prime) if _poly_eval_int_mod_desc(coeffs, x, prime) == 0]


def _integer_ceiling_div(a: int, b: int) -> int:
    """Return ceil(a / b) for integers with b > 0."""
    if b <= 0:
        raise ValueError("Denominator must be positive.")
    return -(-a // b)


def _rational_root_bound_desc(ints: list[int]) -> int:
    """Return an integer bound B such that any rational root x satisfies |x| <= B."""
    if not ints or ints[0] == 0:
        raise ValueError("Polynomial must have non-zero leading coefficient.")
    lead = abs(ints[0])
    tail_max = max(abs(c) for c in ints[1:]) if len(ints) > 1 else 0
    return 1 + _integer_ceiling_div(tail_max, lead)


def _crt_pair(a1: int, m1: int, a2: int, m2: int) -> tuple[int, int]:
    """Combine two coprime congruences with the Chinese Remainder Theorem."""
    inv = pow(m1, -1, m2)
    t = ((a2 - a1) * inv) % m2
    mod = m1 * m2
    return (a1 + m1 * t) % mod, mod


def _combine_residue_sets(
    residues: list[int],
    modulus: int,
    allowed: list[int],
    prime: int,
) -> tuple[list[int], int]:
    """Refine a residue set modulo ``modulus`` with allowed classes modulo ``prime``."""
    out: list[int] = []
    seen: set[int] = set()

    for a in residues:
        for b in allowed:
            x, mod = _crt_pair(a, modulus, b, prime)
            if x not in seen:
                seen.add(x)
                out.append(x)

    out.sort()
    return out, mod


def _candidates_from_residue_class(a: int, mod: int, bound: int) -> list[int]:
    """Return all integers n with |n| <= bound and n ≡ a (mod mod)."""
    if mod <= 0:
        raise ValueError("Modulus must be positive.")

    n0 = a
    if n0 > mod // 2:
        n0 -= mod

    k_min = _integer_ceiling_div(-bound - n0, mod)
    k_max = (bound - n0) // mod

    out: list[int] = []
    for k in range(k_min, k_max + 1):
        n = n0 + k * mod
        if -bound <= n <= bound:
            out.append(n)

    return out


def _root_of_linear_factor_desc(coeffs: list[Fraction]) -> Fraction:
    """Return the unique root of a nonzero linear QQ-polynomial."""
    coeffs = _trim_leading_zeros_desc(coeffs)
    if len(coeffs) != 2:
        raise ValueError("Expected a linear polynomial in descending form.")

    a, b = coeffs
    if a == 0:
        raise ValueError("Malformed linear polynomial with zero leading coefficient.")

    return -b / a


def _find_rational_root_QQ_desc_resolvent_6_1plus5(
    coeffs: list[Fraction],
) -> Fraction | None:
    """Find a rational root of a sextic known to be either irreducible or 1+5.

    Strategy:
      1. Convert to a primitive integer model G in Z[x].
      2. Modular screen: if G mod p has no root for some small prime p not
         dividing the leading coefficient, then G has no rational root.
      3. Otherwise, enumerate only denominators q | lc(G).
      4. For each q, reconstruct possible numerators p by CRT from root data
         modulo small primes.
      5. Verify the resulting candidates exactly over Q.

    If CRT branching becomes too large, this function falls back to the generic
    divisor-based rational-root search.
    """
    ints = _primitive_integer_desc(coeffs)

    if len(ints) != 7:
        raise ValueError("Expected a sextic polynomial in descending form.")

    if ints[-1] == 0:
        return Fraction(0, 1)

    lead = abs(ints[0])
    int_coeffs = [Fraction(n, 1) for n in ints]

    # Step 1: modular screen on G itself.
    # If G has a rational root p/q with gcd(p,q)=1 and q | lc(G), then for every
    # prime ell not dividing lc(G), G mod ell must have a root.
    prime_root_data: list[tuple[int, list[int]]] = []
    for ell in _SMALL_PRIMES:
        if lead % ell == 0:
            continue
        roots = _roots_mod_prime_desc(ints, ell)
        if not roots:
            return None
        prime_root_data.append((ell, roots))

    # Use primes with fewer roots first to keep CRT branching small.
    prime_root_data.sort(key=lambda item: (len(item[1]), item[0]))

    x_bound = _rational_root_bound_desc(ints)

    # Only denominators q dividing the leading coefficient are possible.
    for q in _int_divisors(lead):
        if q <= 0:
            continue

        # If x = p/q is a root and |x| <= x_bound, then |p| <= q * x_bound.
        p_bound = q * x_bound

        residues = [0]
        modulus = 1
        reached_large_modulus = False

        for ell, roots_x in prime_root_data:
            # Since ell does not divide lead, ell does not divide q either.
            # If x ≡ r (mod ell), then p ≡ q*r (mod ell).
            allowed_p = sorted({(q * r) % ell for r in roots_x})
            residues, modulus = _combine_residue_sets(residues, modulus, allowed_p, ell)

            if not residues:
                break

            if len(residues) > _MAX_CRT_RESIDUES:
                return _find_rational_root_QQ_desc_by_divisors(coeffs)

            if modulus > 2 * p_bound + 1:
                reached_large_modulus = True
                break

        if not residues:
            continue

        if not reached_large_modulus:
            return _find_rational_root_QQ_desc_by_divisors(coeffs)

        seen_p: set[int] = set()
        for a in residues:
            for p in _candidates_from_residue_class(a, modulus, p_bound):
                if p in seen_p:
                    continue
                seen_p.add(p)

                if gcd(abs(p), q) != 1:
                    continue

                theta = Fraction(p, q)
                if _poly_eval_desc(int_coeffs, theta) == 0:
                    return theta

    return None


def _find_rational_root_QQ_desc_resolvent_6_by_factorization(
    coeffs: list[Fraction],
) -> Fraction | None:
    """Find a rational root of Dummit's sextic via Q[x] factorization.

    This has the same interface as
    ``_find_rational_root_QQ_desc_resolvent_6_1plus5``.  It deliberately
    does not call ReducibilityNode or emit any facts; it only reuses the
    factorization backend that ReducibilityNode uses internally.
    """
    coeffs = _trim_leading_zeros_desc(coeffs)

    if len(coeffs) != 7:
        raise ValueError("Expected a sextic polynomial in descending form.")

    if coeffs[-1] == 0:
        return Fraction(0, 1)

    lead = coeffs[0]
    if lead == 0:
        raise ValueError("Malformed polynomial with zero leading coefficient.")

    # ReducibilityNode factors the monic normalization.  Do the same here,
    # but keep the root check against the original resolvent coefficients.
    monic = [c / lead for c in coeffs]
    factors = factorize_le5_multiplicity(monic)

    linear_roots: list[Fraction] = []
    nonconstant_factor_count = 0

    for factor, multiplicity in factors:
        factor = _trim_leading_zeros_desc(factor)
        if len(factor) <= 1:
            continue

        nonconstant_factor_count += int(multiplicity)

        if len(factor) != 2:
            continue

        theta = _root_of_linear_factor_desc(factor)
        if _poly_eval_desc(coeffs, theta) != 0:
            raise RuntimeError(
                "Factorization backend produced a linear factor whose root "
                "does not annihilate Dummit's sextic resolvent."
            )
        linear_roots.append(theta)

    if linear_roots:
        return min(linear_roots)

    # For this Dummit resolvent branch, reducibility over Q should be equivalent
    # to having a linear factor.  If the backend finds a nontrivial factorization
    # without a linear factor, fail loudly instead of silently taking the
    # irreducible-resolvent branch.
    if nonconstant_factor_count > 1:
        raise RuntimeError(
            "Dummit sextic resolvent factored over Q but no linear factor was found. "
            "This violates the expected irreducible / 1+5 dichotomy."
        )

    return None


def _find_rational_root_QQ_desc_resolvent_6(
    coeffs: list[Fraction],
) -> Fraction | None:
    """Return a rational root of Dummit's sextic according to the configured method."""
    if DUMMIT_RESOLVENT_RATIONAL_ROOT_METHOD == "specialized":
        return _find_rational_root_QQ_desc_resolvent_6_1plus5(coeffs)

    if DUMMIT_RESOLVENT_RATIONAL_ROOT_METHOD == "factorization":
        return _find_rational_root_QQ_desc_resolvent_6_by_factorization(coeffs)

    raise ValueError(
        "Unknown Dummit resolvent rational-root method: "
        f"{DUMMIT_RESOLVENT_RATIONAL_ROOT_METHOD!r}"
    )


def _divide_by_linear_monic_desc(
    coeffs: list[Fraction], theta: Fraction
) -> list[Fraction]:
    """Divide by x-theta exactly, returning the quotient in descending order."""
    coeffs = _trim_leading_zeros_desc(coeffs)
    if len(coeffs) < 2:
        raise ValueError("Cannot divide a constant polynomial by a linear factor.")

    q: list[Fraction] = [coeffs[0]]
    for c in coeffs[1:-1]:
        q.append(c + theta * q[-1])
    remainder = coeffs[-1] + theta * q[-1]
    if remainder != 0:
        raise ValueError("Synthetic division remainder is non-zero.")
    return _trim_leading_zeros_desc(q)


def _extract_depressed_quintic_pqrs(
    ctx: EngineContext,
    poly_ref: str,
) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    coeffs = _trim_leading_zeros_desc(_resolve_poly_desc_QQ(ctx, poly_ref))
    if len(coeffs) != 6:
        raise ValueError(
            "Expected a degree-5 polynomial with 6 descending coefficients."
        )
    if coeffs[0] != 1:
        raise ValueError("Dummit quintic formulas expect a monic quintic.")
    if coeffs[1] != 0:
        raise ValueError("Dummit quintic formulas expect a depressed quintic.")
    return coeffs[2], coeffs[3], coeffs[4], coeffs[5]


def _record_group_fact(
    ctx: EngineContext, *, poly_ref: str, fact_id: str, group_ref: str
) -> None:
    gg_map = ctx.cache.setdefault("_galois_group_fact_by_poly", {})
    if not isinstance(gg_map, dict):
        raise TypeError("ctx.cache['_galois_group_fact_by_poly'] must be a dict")
    group_ref_map = ctx.cache.setdefault("_galois_group_ref_by_poly", {})
    if not isinstance(group_ref_map, dict):
        raise TypeError("ctx.cache['_galois_group_ref_by_poly'] must be a dict")
    gg_map[poly_ref] = fact_id
    group_ref_map[poly_ref] = group_ref


def _record_irreducible_fact(
    ctx: EngineContext, *, poly_ref: str, fact_id: str
) -> None:
    irr_map = ctx.cache.setdefault("_irreducible_fact_by_poly", {})
    if not isinstance(irr_map, dict):
        raise TypeError("ctx.cache['_irreducible_fact_by_poly'] must be a dict")
    irr_map[poly_ref] = fact_id


def _is_monic_depressed_quintic(coeffs: list[Fraction]) -> bool:
    """Return True iff coeffs encode a monic depressed quintic."""
    trimmed = _trim_leading_zeros_desc(coeffs)
    return (
        len(trimmed) == 6
        and trimmed[0] == Fraction(1, 1)
        and trimmed[1] == Fraction(0, 1)
    )


@dataclass(frozen=True)
class IrreducibleDeg5Procedure:
    """Irreducible degree-5 procedure based on Dummit's sextic resolvent.

    Workflow on an irreducible quintic f over Q:
      0) If needed, pass to the depressed monic normalization g and transport
         irreducibility to g.
      1) On the working quintic (either f itself or g), compute the
         discriminant and its square/non-square gate.
      2) Compute Dummit's sextic resolvent for the canonical F20 family.
      3) Rational-root branch on the sextic:
           - no rational root  -> IrreducibleQQ(R) via irreducible.QQ.dummit_resolvent@1,
           - rational root     -> explicit FactorizationMonicQQ(R,[l,Q],1) + Degree(l,1).
      4) Final theorem rule:
           - irreducible resolvent + non-square disc -> S5,
           - irreducible resolvent + square disc     -> A5,
           - reducible resolvent   + non-square disc -> F20,
           - reducible resolvent   + square disc     -> D5/C5 via Dummit q1.
    """

    pred: str = "GaloisGroup"

    disc_square_pred: str = "DiscSquareQQ"
    disc_nonsquare_pred: str = "DiscNonSquareQQ"
    disc_square_rule: str = "disc.square.QQ.lift@1"
    disc_nonsquare_rule: str = "disc.nonsquare.QQ.lift@1"

    resolvent_family: str = "deg5.sextic_dummit_F20"
    irreducible_resolvent_rule: str = "irreducible.QQ.dummit_resolvent@1"
    factorization_rule: str = "factorization.QQ.monic@1"

    rule_s5: str = "galois_group.QQ.deg5.S5@1"
    rule_a5: str = "galois_group.QQ.deg5.A5@1"
    rule_f20: str = "galois_group.QQ.deg5.F20@1"
    rule_d5: str = "galois_group.QQ.deg5.D5@1"
    rule_c5: str = "galois_group.QQ.deg5.C5@1"

    group_s5_id: str = "group.S5"
    group_a5_id: str = "group.A5"
    group_f20_id: str = "group.F20"
    group_d5_id: str = "group.D5"
    group_c5_id: str = "group.C5"

    linear_factor_prefix: str = "poly.dummit.linear."
    cofactor_prefix: str = "poly.dummit.cofactor."
    factor_list_prefix: str = "list.dummit.factors."
    unit_prefix: str = "rat.dummit.unit."
    q1_prefix: str = "poly.dummit.q1."
    q2_prefix: str = "poly.dummit.q2."

    irreducible_to_depressed_rule: str = "irreducible.QQ.to.depressed_monic@1"
    group_lift_rule: str = "galois_group.QQ.lift.depressed_monic@1"

    radical_rule_mcclintock: str = "radical_roots.QQ.deg5.mcclintock.depressed_monic@1"
    radical_rule_lift: str = "radical_roots.QQ.lift.depressed_monic@1"
    radical_pred: str = "RadicalRoots"

    def _ensure_group_ids(self, ctx: EngineContext) -> None:
        ctx.objects.put_groupid(
            self.group_s5_id, system="smallgroup", order=120, index=34, alias="S5"
        )
        ctx.objects.put_groupid(
            self.group_a5_id, system="smallgroup", order=60, index=5, alias="A5"
        )
        ctx.objects.put_groupid(
            self.group_f20_id, system="smallgroup", order=20, index=3, alias="F20"
        )
        ctx.objects.put_groupid(
            self.group_d5_id, system="smallgroup", order=10, index=2, alias="D5"
        )
        ctx.objects.put_groupid(
            self.group_c5_id, system="smallgroup", order=5, index=1, alias="C5"
        )

    def _emit_disc_lift(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        disc_fact_id: str,
        square_out: dict[str, Any],
    ) -> tuple[dict[str, Any], str, str]:
        decision = str(square_out.get("decision", ""))
        facts_map = square_out.get("facts", {})
        if not isinstance(facts_map, dict):
            raise TypeError("SquareNode out['facts'] must be a dict.")

        if decision == "square":
            square_fact_raw = facts_map.get("square")
            if square_fact_raw is None:
                raise ValueError("Missing IsSquareQQ fact id from SquareNode.")
            square_fact_id = str(square_fact_raw)
            fact_id = _next_fact_id(ctx)
            fact = {
                "id": fact_id,
                "claim": {"pred": self.disc_square_pred, "args": [{"ref": poly_ref}]},
                "rule": self.disc_square_rule,
                "premises": [disc_fact_id, square_fact_id],
                "statement": "Lift discriminant squarehood from D to the polynomial.",
            }
            return fact, fact_id, "square"

        if decision == "nonsquare":
            non_square_raw = facts_map.get("non_square")
            if non_square_raw is None:
                raise ValueError("Missing NonSquareQQ fact id from SquareNode.")
            non_square_fact_id = str(non_square_raw)
            fact_id = _next_fact_id(ctx)
            fact = {
                "id": fact_id,
                "claim": {
                    "pred": self.disc_nonsquare_pred,
                    "args": [{"ref": poly_ref}],
                },
                "rule": self.disc_nonsquare_rule,
                "premises": [disc_fact_id, non_square_fact_id],
                "statement": "Lift discriminant non-squarehood from D to the polynomial.",
            }
            return fact, fact_id, "nonsquare"

        raise ValueError(f"Unexpected discriminant squarehood decision: {decision!r}")

    def _analyze_dummit_resolvent(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        degree_fact_id: str,
        irreducible_fact_id: str,
        resolvent_ref: str,
        resolvent_fact_id: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        _ = poly_ref  # kept for symmetry / future branch-specific uses

        r_coeffs = _trim_leading_zeros_desc(_resolve_poly_desc_QQ(ctx, resolvent_ref))
        theta = _find_rational_root_QQ_desc_resolvent_6(r_coeffs)

        if theta is None:
            fact_id = _next_fact_id(ctx)
            fact = {
                "id": fact_id,
                "claim": {"pred": "IrreducibleQQ", "args": [{"ref": resolvent_ref}]},
                "rule": self.irreducible_resolvent_rule,
                "premises": [resolvent_fact_id, degree_fact_id, irreducible_fact_id],
                "statement": "Dummit sextic resolvent is irreducible over Q"
                " by the rational-root test.",
            }

            irr_map = ctx.cache.setdefault("_irreducible_fact_by_poly", {})
            if not isinstance(irr_map, dict):
                raise TypeError("ctx.cache['_irreducible_fact_by_poly'] must be a dict")
            irr_map[resolvent_ref] = fact_id

            return [fact], {
                "decision": "irreducible",
                "theta": None,
                "irreducible_fact_id": fact_id,
            }

        linear_ref = ctx.objects.new_id(self.linear_factor_prefix)
        cofactor_ref = ctx.objects.new_id(self.cofactor_prefix)
        factors_ref = ctx.objects.new_id(self.factor_list_prefix)
        unit_ref = ctx.objects.new_id(self.unit_prefix)

        linear_coeffs = [Fraction(1, 1), -theta]
        cofactor_coeffs = _divide_by_linear_monic_desc(r_coeffs, theta)

        ctx.objects.put_poly(linear_ref, linear_coeffs)
        ctx.objects.put_poly(cofactor_ref, cofactor_coeffs)
        ctx.objects.put_poly_list(factors_ref, [linear_ref, cofactor_ref])
        ctx.objects.put_rat(unit_ref, Fraction(1, 1))

        factorization_fact = {
            "id": _next_fact_id(ctx),
            "claim": {
                "pred": "FactorizationMonicQQ",
                "args": [
                    {"ref": resolvent_ref},
                    {"ref": factors_ref},
                    {"ref": unit_ref},
                ],
            },
            "rule": self.factorization_rule,
            "premises": [],
            "statement": "Explicit factorization of the Dummit sextic resolvent"
            " as linear times quintic.",
        }

        aux_facts: list[dict[str, Any]] = [factorization_fact]
        linear_degree_fact_id, _ = _ensure_degree_fact(
            ctx, poly_ref=linear_ref, into=aux_facts
        )

        return aux_facts, {
            "decision": "linear_times_quintic",
            "theta": theta,
            "linear_ref": linear_ref,
            "cofactor_ref": cofactor_ref,
            "factors_ref": factors_ref,
            "unit_ref": unit_ref,
            "factorization_fact_id": factorization_fact["id"],
            "linear_degree_fact_id": linear_degree_fact_id,
        }

    def _build_dummit_quadratics_branch(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        disc_ref: str,
        sqrt_ref: str,
        theta: Fraction,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Build and certify the two Dummit quadratics for the C5/D5 gate.

        In the square-discriminant solvable branch, Dummit's equation (7)
        gives two rational quadratics

            q1 = x^2 + (T1 + T2*A)x + (T3 + T4*A),
            q2 = x^2 + (T1 - T2*A)x + (T3 - T4*A),

        where A is the chosen square-root witness for the quintic
        discriminant.  The cyclic case requires both quadratics to split over
        QQ; the dihedral case is detected as soon as one of them is not split.
        """
        p_coef, q_coef, r_coef, s_coef = _extract_depressed_quintic_pqrs(ctx, poly_ref)
        d_val = _resolve_ratqq(ctx, disc_ref)
        a_val = _resolve_ratqq(ctx, sqrt_ref)

        vals = eval_all(p=p_coef, q=q_coef, r=r_coef, s=s_coef, theta=theta, D=d_val)
        quadratic_specs = [
            (
                "q1",
                self.q1_prefix,
                vals["T1"] + vals["T2"] * a_val,
                vals["T3"] + vals["T4"] * a_val,
            ),
            (
                "q2",
                self.q2_prefix,
                vals["T1"] - vals["T2"] * a_val,
                vals["T3"] - vals["T4"] * a_val,
            ),
        ]

        nodes: list[dict[str, Any]] = []
        entries: dict[str, dict[str, Any]] = {}

        for name, prefix, b, c in quadratic_specs:
            q_ref = ctx.objects.new_id(prefix)
            ctx.objects.put_poly(q_ref, [Fraction(1, 1), b, c])

            disc_nodes, disc_out = ctx.registry.discriminant.run(ctx, poly_ref=q_ref)
            disc_facts = disc_out.get("facts", {})
            if not isinstance(disc_facts, dict):
                raise TypeError("DiscriminantNode out['facts'] must be a dict.")
            disc_fact_raw = disc_facts.get("discriminant")
            if disc_fact_raw is None:
                raise ValueError(
                    f"Missing Discriminant({name},D) fact id from DiscriminantNode."
                )
            disc_fact_id = str(disc_fact_raw)
            if not disc_fact_id:
                raise ValueError(f"Empty Discriminant({name},D) fact id.")

            disc_ref_raw = disc_out.get("disc_ref")
            if not isinstance(disc_ref_raw, str) or not disc_ref_raw:
                raise ValueError(
                    f"DiscriminantNode output is missing a valid {name} discriminant ref."
                )
            q_disc_ref = disc_ref_raw

            square_nodes, square_out = ctx.registry.square.run(ctx, rat_ref=q_disc_ref)
            square_facts = square_out.get("facts", {})
            if not isinstance(square_facts, dict):
                raise TypeError("SquareNode out['facts'] must be a dict.")

            decision = str(square_out.get("decision", ""))
            if decision == "square":
                gate_raw = square_facts.get("square")
                if gate_raw is None:
                    raise ValueError(f"Missing IsSquareQQ(D_{name}) fact id from SquareNode.")
                gate_fact_id = str(gate_raw)
            elif decision == "nonsquare":
                gate_raw = square_facts.get("non_square")
                if gate_raw is None:
                    raise ValueError(f"Missing NonSquareQQ(D_{name}) fact id from SquareNode.")
                gate_fact_id = str(gate_raw)
            else:
                raise ValueError(
                    f"Unexpected squarehood decision for Dummit {name}: {decision!r}"
                )

            nodes.extend(disc_nodes)
            nodes.extend(square_nodes)
            entries[name] = {
                "name": name,
                "decision": decision,
                "poly_ref": q_ref,
                "disc_ref": q_disc_ref,
                "disc_fact_id": disc_fact_id,
                "gate_fact_id": gate_fact_id,
                "discriminant": disc_out,
                "squarehood": square_out,
            }

        all_square = all(entry["decision"] == "square" for entry in entries.values())
        return nodes, {
            "decision": "all_square" if all_square else "some_nonsquare",
            "q1": entries["q1"],
            "q2": entries["q2"],
            "quadratics": [entries["q1"], entries["q2"]],
        }

    def _maybe_emit_radical_roots(
        self,
        ctx: EngineContext,
        *,
        input_ref: str,
        working_ref: str,
        normalize_fact_id: str | None,
        degree_fact_id: str,
        irreducible_fact_id: str,
        resolvent_ref: str,
        resolvent_fact_id: str,
        factorization_fact_id: str,
        linear_ref: str,
    ) -> list[dict[str, Any]]:
        """Emit degree-5 radical roots from already-certified pipeline artifacts.

        When ``normalize_fact_id`` is ``None``, the current rule contract is not
        available because there is no certified ``DepressedMonicEq`` premise. In
        that case this helper emits nothing and leaves the already-classified
        group pipeline untouched.
        """
        facts: list[dict[str, Any]] = []

        if normalize_fact_id is None:
            return facts

        roots_g = deg5_mcclintock_depressed_monic.build_from_linear_factor(
            coeffs_desc=_resolve_poly_desc_QQ(ctx, working_ref),
            linear_factor_desc=_resolve_poly_desc_QQ(ctx, linear_ref),
        )
        roots_g_ref = store_radical_expr_list(
            ctx,
            exprs=roots_g,
            expr_prefix="rexpr.mcclintock.",
            list_prefix="rlist.mcclintock.",
        )

        roots_g_fact_id = _next_fact_id(ctx)
        roots_g_fact = {
            "id": roots_g_fact_id,
            "claim": {
                "pred": self.radical_pred,
                "args": [{"ref": working_ref}, {"ref": roots_g_ref}],
            },
            "rule": self.radical_rule_mcclintock,
            "premises": [
                degree_fact_id,
                irreducible_fact_id,
                normalize_fact_id,
                resolvent_fact_id,
                factorization_fact_id,
            ],
            "statement": "Canonical McClintock radical roots for the depressed monic quintic.",
        }
        facts.append(roots_g_fact)
        cache_radical_roots(
            ctx,
            poly_ref=working_ref,
            fact_id=roots_g_fact_id,
            roots_ref=roots_g_ref,
        )

        if working_ref == input_ref:
            return facts

        f_poly = _resolve_poly_desc_QQ(ctx, input_ref)
        degree_f = len(f_poly) - 1
        if degree_f != 5:
            raise ValueError(f"Input polynomial has unexpected degree {degree_f!r}.")
        lc = f_poly[0]
        if lc == 0:
            raise ValueError("Input polynomial has zero leading coefficient.")
        f_m = [coeff / lc for coeff in f_poly]
        shift = f_m[1] / Fraction(5, 1)

        lifted_roots = lift_depressed_monic.build(roots=roots_g, shift=shift)
        lifted_roots_ref = store_radical_expr_list(
            ctx,
            exprs=lifted_roots,
            expr_prefix="rexpr.mcclintock.lift.",
            list_prefix="rlist.mcclintock.lift.",
        )

        lifted_fact_id = _next_fact_id(ctx)
        lifted_fact = {
            "id": lifted_fact_id,
            "claim": {
                "pred": self.radical_pred,
                "args": [{"ref": input_ref}, {"ref": lifted_roots_ref}],
            },
            "rule": self.radical_rule_lift,
            "premises": [normalize_fact_id, roots_g_fact_id],
            "statement": "Lift depressed-monic McClintock radical roots "
            "back to the original quintic.",
        }
        facts.append(lifted_fact)
        cache_radical_roots(
            ctx,
            poly_ref=input_ref,
            fact_id=lifted_fact_id,
            roots_ref=lifted_roots_ref,
        )

        return facts

    def run(self, ctx: EngineContext, *, poly_ref: str) -> ProcedureResult:
        """Classify the Galois group of an irreducible degree-5 polynomial over Q.

        The reducibility gate is assumed to have already run on ``poly_ref`` and
        therefore to have emitted ``Degree(poly_ref, 5)`` and
        ``IrreducibleQQ(poly_ref)``. If ``poly_ref`` is not already a monic
        depressed quintic, this procedure first normalizes it and transports
        irreducibility to the normalized polynomial via
        ``irreducible.QQ.to.depressed_monic@1``. The Dummit classification then
        proceeds on that working polynomial. When a normalization step was
        performed, the final local ``GaloisGroup`` fact is lifted back to the
        original polynomial via ``galois_group.QQ.lift.depressed_monic@1``.

        Args:
            ctx: Engine context containing the object store, node registry, and
                the cached prerequisite facts for the polynomial.
            poly_ref: Reference to the irreducible degree-5 polynomial to be
                classified.

        Returns:
            ProcedureResult: A procedure result containing all intermediate and
            final facts emitted by the pipeline, together with an output map
            describing the chosen Galois group and the intermediate branch data
            used to reach that classification.
        """
        input_ref = poly_ref
        input_irreducible_fact_id = _irreducible_fact_id(ctx, input_ref)

        self._ensure_group_ids(ctx)

        prefix_facts: list[dict[str, Any]] = []

        input_coeffs = _trim_leading_zeros_desc(_resolve_poly_desc_QQ(ctx, input_ref))
        if _is_monic_depressed_quintic(input_coeffs):
            working_ref = input_ref
            normalize_fact_id = _next_fact_id(ctx)
            normalize_fact = {
                "id": normalize_fact_id,
                "claim": {
                    "pred": "DepressedMonicEq",
                    "args": [{"ref": input_ref}, {"ref": input_ref}],
                },
                "rule": "normalize.depressed_monic_QQ@1",
                "premises": [_degree_fact_id(ctx, input_ref)],
                "evidence": {
                    "tschirnhaus_shift": _frac_to_str(Fraction(0, 1)),
                    "monic_scale": _frac_to_str(Fraction(1, 1)),
                },
                "statement": "Depressed-monic normalization over Q: monicize then apply "
                "x -> x - t to kill x^(n-1).",
            }
            prefix_facts.append(normalize_fact)
            degree_fact_id = _degree_fact_id(ctx, input_ref)
            degree = 5
            irreducible_fact_id = input_irreducible_fact_id
        else:
            normalize_out_id = ctx.objects.new_id("poly.depressed_monic.")
            normalize_fact, normalize_out = ctx.registry.normalize_deg5.run(
                ctx,
                poly_ref=input_ref,
                out_id=normalize_out_id,
            )
            prefix_facts.append(normalize_fact)
            normalize_fact_id = str(normalize_fact["id"])

            working_ref_raw = normalize_out.get("poly_ref")
            if not isinstance(working_ref_raw, str) or not working_ref_raw:
                raise ValueError(
                    "NormalizeDepressedMonicQQ did not return a valid normalized ref."
                )
            working_ref = working_ref_raw

            degree_fact_id, degree = _ensure_degree_fact(
                ctx, poly_ref=working_ref, into=prefix_facts
            )
            if degree != 5:
                raise ValueError(f"Normalized quintic has unexpected degree {degree!r}.")

            irreducible_fact_id = emit_irreducible_to_depressed_fact(
                ctx,
                source_poly_ref=input_ref,
                depressed_poly_ref=working_ref,
                normalize_fact_id=normalize_fact_id,
                source_irreducible_fact_id=input_irreducible_fact_id,
                into=prefix_facts,
                rule_id=self.irreducible_to_depressed_rule,
            )

        disc_nodes, disc_out = ctx.registry.discriminant.run(ctx, poly_ref=working_ref)
        disc_facts = disc_out.get("facts", {})
        if not isinstance(disc_facts, dict):
            raise TypeError("DiscriminantNode out['facts'] must be a dict.")
        disc_fact_raw = disc_facts.get("discriminant")
        if disc_fact_raw is None:
            raise ValueError("Missing Discriminant(f,D) fact id from DiscriminantNode.")
        disc_fact_id = str(disc_fact_raw)
        if not disc_fact_id:
            raise ValueError("Empty Discriminant(f,D) fact id.")

        disc_ref_raw = disc_out.get("disc_ref")
        if not isinstance(disc_ref_raw, str) or not disc_ref_raw:
            raise ValueError("DiscriminantNode output is missing a valid D ref.")
        disc_ref = disc_ref_raw

        square_nodes, square_out = ctx.registry.square.run(ctx, rat_ref=disc_ref)
        disc_lift_fact, disc_lift_fact_id, disc_squarehood = self._emit_disc_lift(
            ctx,
            poly_ref=working_ref,
            disc_fact_id=disc_fact_id,
            square_out=square_out,
        )

        resolvent_nodes, resolvent_out = ctx.registry.resolvent.run(
            ctx,
            poly_ref=working_ref,
            family=self.resolvent_family,
        )
        resolvent_facts = resolvent_out.get("facts", {})
        if not isinstance(resolvent_facts, dict):
            raise TypeError("ResolventNode out['facts'] must be a dict.")
        resolvent_fact_raw = resolvent_facts.get("resolvent")
        if resolvent_fact_raw is None:
            raise ValueError("Missing ResolventQQ fact id from ResolventNode.")
        resolvent_fact_id = str(resolvent_fact_raw)
        if not resolvent_fact_id:
            raise ValueError("Empty ResolventQQ fact id from ResolventNode.")

        resolvent_ref_raw = resolvent_out.get("resolvent_ref")
        if not isinstance(resolvent_ref_raw, str) or not resolvent_ref_raw:
            raise ValueError("ResolventNode output is missing a valid resolvent ref.")
        resolvent_ref = resolvent_ref_raw

        branch_nodes, branch_out = self._analyze_dummit_resolvent(
            ctx,
            poly_ref=working_ref,
            degree_fact_id=degree_fact_id,
            irreducible_fact_id=irreducible_fact_id,
            resolvent_ref=resolvent_ref,
            resolvent_fact_id=resolvent_fact_id,
        )

        facts: list[dict[str, Any]] = [
            *prefix_facts,
            *disc_nodes,
            *square_nodes,
            disc_lift_fact,
            *resolvent_nodes,
            *branch_nodes,
        ]

        def _finalize_group(
            *,
            group_ref: str,
            group_name: str,
            local_rule_id: str,
            premises: list[str],
            statement: str,
            extra_out: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            local_group_fact_id = _next_fact_id(ctx)
            local_group_fact = {
                "id": local_group_fact_id,
                "claim": {
                    "pred": self.pred,
                    "args": [{"ref": working_ref}, {"ref": group_ref}],
                },
                "rule": local_rule_id,
                "premises": premises,
                "statement": statement,
            }
            facts.append(local_group_fact)
            _record_group_fact(
                ctx,
                poly_ref=working_ref,
                fact_id=local_group_fact_id,
                group_ref=group_ref,
            )

            final_group_fact_id = local_group_fact_id
            if working_ref != input_ref:
                lift_fact_id = _next_fact_id(ctx)
                lift_fact = {
                    "id": lift_fact_id,
                    "claim": {
                        "pred": "GaloisGroup",
                        "args": [{"ref": input_ref}, {"ref": group_ref}],
                    },
                    "rule": self.group_lift_rule,
                    "premises": [normalize_fact_id, local_group_fact_id],
                    "statement": "Transport Galois-group classification from "
                    "the depressed monic normalization.",
                }
                facts.append(lift_fact)
                _record_group_fact(
                    ctx, poly_ref=input_ref, fact_id=lift_fact_id, group_ref=group_ref
                )
                final_group_fact_id = lift_fact_id
            else:
                _record_group_fact(
                    ctx,
                    poly_ref=input_ref,
                    fact_id=local_group_fact_id,
                    group_ref=group_ref,
                )

            out = {
                "decision": "galois_group",
                "group": group_name,
                "group_ref": group_ref,
                "group_fact_id": final_group_fact_id,
                "working_ref": working_ref,
                "normalized": normalize_fact_id is not None,
                "discriminant": disc_out,
                "discriminant_squarehood": square_out,
                "resolvent": resolvent_out,
                "resolvent_branch": branch_out,
            }
            if extra_out:
                out.update(extra_out)
            return out

        if branch_out["decision"] == "irreducible":
            resolvent_irred_fact_id = str(branch_out["irreducible_fact_id"])
            if disc_squarehood == "nonsquare":
                out = _finalize_group(
                    group_ref=self.group_s5_id,
                    group_name="S5",
                    local_rule_id=self.rule_s5,
                    premises=[
                        degree_fact_id,
                        irreducible_fact_id,
                        disc_lift_fact_id,
                        resolvent_fact_id,
                        resolvent_irred_fact_id,
                    ],
                    statement="Irreducible quintic classified via Dummit's sextic resolvent.",
                )
            else:
                out = _finalize_group(
                    group_ref=self.group_a5_id,
                    group_name="A5",
                    local_rule_id=self.rule_a5,
                    premises=[
                        degree_fact_id,
                        irreducible_fact_id,
                        disc_lift_fact_id,
                        resolvent_fact_id,
                        resolvent_irred_fact_id,
                    ],
                    statement="Irreducible quintic classified via Dummit's sextic resolvent.",
                )
            return ProcedureResult(facts=facts, out=out)

        factorization_fact_id = str(branch_out["factorization_fact_id"])
        linear_degree_fact_id = str(branch_out["linear_degree_fact_id"])

        if disc_squarehood == "nonsquare":
            out = _finalize_group(
                group_ref=self.group_f20_id,
                group_name="F20",
                local_rule_id=self.rule_f20,
                premises=[
                    degree_fact_id,
                    irreducible_fact_id,
                    disc_lift_fact_id,
                    resolvent_fact_id,
                    factorization_fact_id,
                    linear_degree_fact_id,
                ],
                statement="Irreducible quintic classified as F20 via "
                "a linear factor in Dummit's sextic resolvent.",
            )
            facts.extend(
                self._maybe_emit_radical_roots(
                    ctx,
                    input_ref=input_ref,
                    working_ref=working_ref,
                    normalize_fact_id=normalize_fact_id,
                    degree_fact_id=degree_fact_id,
                    irreducible_fact_id=irreducible_fact_id,
                    resolvent_ref=resolvent_ref,
                    resolvent_fact_id=resolvent_fact_id,
                    factorization_fact_id=factorization_fact_id,
                    linear_ref=str(branch_out["linear_ref"]),
                )
            )
            return ProcedureResult(facts=facts, out=out)

        sqrt_ref_raw = square_out.get("sqrt_ref")
        sqrt_facts = square_out.get("facts", {})
        if not isinstance(sqrt_facts, dict):
            raise TypeError("SquareNode out['facts'] must be a dict.")
        sqrt_fact_raw = sqrt_facts.get("sqrt")
        if not isinstance(sqrt_ref_raw, str) or not sqrt_ref_raw:
            raise ValueError(
                "Square discriminant branch is missing a sqrt witness ref."
            )
        if sqrt_fact_raw is None:
            raise ValueError("Square discriminant branch is missing a SqrtQQ fact id.")
        sqrt_ref = sqrt_ref_raw
        sqrt_fact_id = str(sqrt_fact_raw)

        theta_raw = branch_out.get("theta")
        if not isinstance(theta_raw, Fraction):
            raise ValueError(
                "Dummit solvable branch is missing the rational root theta."
            )
        q_nodes, q_out = self._build_dummit_quadratics_branch(
            ctx,
            poly_ref=working_ref,
            disc_ref=disc_ref,
            sqrt_ref=sqrt_ref,
            theta=theta_raw,
        )
        facts.extend(q_nodes)

        q1_out = q_out["q1"]
        q2_out = q_out["q2"]
        quadratic_premises = [
            str(q1_out["disc_fact_id"]),
            str(q1_out["gate_fact_id"]),
            str(q2_out["disc_fact_id"]),
            str(q2_out["gate_fact_id"]),
        ]

        if q_out["decision"] == "some_nonsquare":
            out = _finalize_group(
                group_ref=self.group_d5_id,
                group_name="D5",
                local_rule_id=self.rule_d5,
                premises=[
                    degree_fact_id,
                    irreducible_fact_id,
                    disc_fact_id,
                    sqrt_fact_id,
                    resolvent_fact_id,
                    factorization_fact_id,
                    linear_degree_fact_id,
                    *quadratic_premises,
                ],
                statement="Irreducible quintic classified via Dummit's two-quadratic criterion.",
                extra_out={"dummit_quadratics": q_out},
            )
            facts.extend(
                self._maybe_emit_radical_roots(
                    ctx,
                    input_ref=input_ref,
                    working_ref=working_ref,
                    normalize_fact_id=normalize_fact_id,
                    degree_fact_id=degree_fact_id,
                    irreducible_fact_id=irreducible_fact_id,
                    resolvent_ref=resolvent_ref,
                    resolvent_fact_id=resolvent_fact_id,
                    factorization_fact_id=factorization_fact_id,
                    linear_ref=str(branch_out["linear_ref"]),
                )
            )
            return ProcedureResult(facts=facts, out=out)

        out = _finalize_group(
            group_ref=self.group_c5_id,
            group_name="C5",
            local_rule_id=self.rule_c5,
            premises=[
                degree_fact_id,
                irreducible_fact_id,
                disc_fact_id,
                sqrt_fact_id,
                resolvent_fact_id,
                factorization_fact_id,
                linear_degree_fact_id,
                *quadratic_premises,
            ],
            statement="Irreducible quintic classified via Dummit's two-quadratic criterion.",
            extra_out={"dummit_quadratics": q_out},
        )
        facts.extend(
            self._maybe_emit_radical_roots(
                ctx,
                input_ref=input_ref,
                working_ref=working_ref,
                normalize_fact_id=normalize_fact_id,
                degree_fact_id=degree_fact_id,
                irreducible_fact_id=irreducible_fact_id,
                resolvent_ref=resolvent_ref,
                resolvent_fact_id=resolvent_fact_id,
                factorization_fact_id=factorization_fact_id,
                linear_ref=str(branch_out["linear_ref"]),
            )
        )
        return ProcedureResult(facts=facts, out=out)






