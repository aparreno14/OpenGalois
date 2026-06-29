"""McClintock helpers for solvable depressed quintics over QQ.

This module currently covers the rational computational spine of the degree-5
McClintock scheme and starts exposing AST builders for the generic branch.

The intended use is:

1. decode a depressed monic quintic
2. extract a rational resolvent root ``theta`` from the certified Dummit sextic
3. compute the rational invariants driving the McClintock flow
4. decide the algebraic branch
5. compute branch-local quantities such as ``lambda``, ``T^2``, ``R1^2``,
   ``R2^2``, etc.

Notation follows the user's notebook and the chapter "Solvable Quintics and How
to Solve Them" (scaled depressed form
``x^5 + 10*C*x^3 + 10*D*x^2 + 5*E*x + f``).  The Dummit resolvent root used here
is denoted ``theta`` and satisfies

    theta = 125*S^2 - 25*C^2 - 15*E

so that ``S^2`` is recovered by

    S^2 = (theta + 25*C^2 + 15*E) / 125.

This file deliberately stays small and flat so that the later full scheme can be
implemented in the same style as the existing degree-3/4 radical schemes.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
from math import isqrt

from opengalois.radicals.ast import Expr, add, mul, pow_int, qq, root, zeta


def _to_fraction(x: Fraction | int | str) -> Fraction:
    """Convert supported scalar inputs to ``Fraction``.

    Args:
        x: Integer, ``Fraction``, or canonical integer/rational string.

    Returns:
        The corresponding ``Fraction``.

    Raises:
        TypeError: If the input type is unsupported.
        ValueError: If a string cannot be parsed as an integer or rational.
    """
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x, 1)
    if isinstance(x, str):
        s = x.strip()
        if "/" in s:
            p, q = s.split("/", 1)
            return Fraction(int(p.strip()), int(q.strip()))
        return Fraction(int(s), 1)
    raise TypeError(f"Unsupported scalar type: {type(x)!r}")


def _is_square_int(n: int) -> bool:
    """Return whether ``n`` is a perfect square integer."""
    if n < 0:
        return False
    r = isqrt(n)
    return r * r == n


def is_square_fraction(q: Fraction) -> bool:
    """Return whether ``q`` is a square in ``QQ``.

    Args:
        q: Rational number.

    Returns:
        ``True`` iff ``q >= 0`` and both numerator and denominator are perfect
        squares.
    """
    q = Fraction(q)
    if q < 0:
        return False
    return _is_square_int(q.numerator) and _is_square_int(q.denominator)


def sqrt_fraction(q: Fraction) -> Fraction:
    """Return the canonical nonnegative rational square root of a square fraction.

    Args:
        q: Rational square.

    Returns:
        The unique nonnegative ``Fraction`` whose square is ``q``.

    Raises:
        ValueError: If ``q`` is not a square in ``QQ``.
    """
    q = Fraction(q)
    if not is_square_fraction(q):
        raise ValueError(f"Not a square in QQ: {q}")
    return Fraction(isqrt(q.numerator), isqrt(q.denominator))


@dataclass(frozen=True)
class DepressedQuintic:
    """Scaled depressed monic quintic ``x^5 + 10Cx^3 + 10Dx^2 + 5Ex + f``."""

    C: Fraction
    D: Fraction
    E: Fraction
    f0: Fraction

    @classmethod
    def from_desc_coeffs(
        cls, coeffs_desc: Iterable[Fraction | int | str]
    ) -> DepressedQuintic:
        """Build from descending coefficients.

        Args:
            coeffs_desc: Six descending coefficients of a quintic.

        Returns:
            The scaled depressed quintic.

        Raises:
            ValueError: If the polynomial is not monic depressed quintic of degree 5.
        """
        coeffs = [_to_fraction(c) for c in coeffs_desc]
        if len(coeffs) != 6:
            raise ValueError("Expected 6 descending coefficients for a quintic.")
        a5, a4, a3, a2, a1, a0 = coeffs
        if a5 != 1:
            raise ValueError("Expected monic quintic.")
        if a4 != 0:
            raise ValueError("Expected depressed quintic with zero x^4 coefficient.")
        C = a3 / 10
        D = a2 / 10
        E = a1 / 5
        return cls(C=C, D=D, E=E, f0=a0)

    def coeffs_desc(self) -> list[Fraction]:
        """Return descending coefficients in standard scaled form."""
        return [Fraction(1), Fraction(0), 10 * self.C, 10 * self.D, 5 * self.E, self.f0]


@dataclass(frozen=True)
class QuinticInvariants:
    """Rational invariants used repeatedly in the McClintock flow."""

    theta: Fraction
    s2: Fraction
    s2_is_square: bool
    S2: Fraction
    S4: Fraction
    S6: Fraction
    G0: Fraction
    G1: Fraction
    G2: Fraction
    G3: Fraction
    L0: Fraction
    L1: Fraction
    t2_if_s0: Fraction | None
    lambda_if_s_nonzero: Fraction | None


@dataclass(frozen=True)
class AffineInS:
    """Represents ``a + b*S`` with rational coefficients."""

    a: Fraction
    b: Fraction


@dataclass(frozen=True)
class AffineInT:
    """Represents ``a + b*T`` with rational coefficients."""

    a: Fraction
    b: Fraction


@dataclass(frozen=True)
class BranchInfo:
    """High-level branch data extracted from the rational invariants."""

    tag: str
    s2: Fraction
    s2_is_square: bool
    t2: Fraction | None
    lam: Fraction | None


@dataclass(frozen=True)
class GeneralR1ZeroR2NonzeroCaseAST:
    """AST data for the generic branch with ``R1 = 0`` and ``R2 != 0``."""

    S: Expr
    T: Expr
    R_sq: Expr
    R: Expr
    u1_5: Expr
    K2: Expr
    K3: Expr
    K4: Expr
    u1: Expr
    u2: Expr
    u3: Expr
    u4: Expr
    roots: list[Expr]


@dataclass(frozen=True)
class GeneralR1ZeroR2ZeroCaseAST:
    """AST data for the generic branch with ``R1 = R2 = 0``."""

    S: Expr
    T: Expr
    u1_5: Expr
    K2: Expr
    K3: Expr
    K4: Expr
    u1: Expr
    u2: Expr
    u3: Expr
    u4: Expr
    roots: list[Expr]


GeneralR1ZeroCaseAST = GeneralR1ZeroR2NonzeroCaseAST | GeneralR1ZeroR2ZeroCaseAST


@dataclass(frozen=True)
class SEqualCZeroTrivialCaseAST:
    """AST data for §9.4.4 branch (A): ``S = C = 0`` with ``D = E = 0``."""

    u1_5: Expr
    K2: Expr
    K3: Expr
    K4: Expr
    u1: Expr
    u2: Expr
    u3: Expr
    u4: Expr
    roots: list[Expr]


@dataclass(frozen=True)
class SEqualCZeroNontrivialCaseAST:
    """AST data for §9.4.4 branch (B): ``S = C = 0`` with ``D != 0`` and ``E != 0``."""

    u1_5: Expr
    K2: Expr
    K3: Expr
    K4: Expr
    u1: Expr
    u2: Expr
    u3: Expr
    u4: Expr
    roots: list[Expr]


SEqualCZeroCaseAST = SEqualCZeroTrivialCaseAST | SEqualCZeroNontrivialCaseAST


@dataclass(frozen=True)
class GeneralCaseAST:
    """AST data for the fully generic branch ``S != 0``, ``S^2 != C^2``, ``R1 != 0``."""

    S: Expr
    T: Expr
    R1_sq: Expr
    R1: Expr
    R2: Expr
    u1_5: Expr
    K2: Expr
    K3: Expr
    K4: Expr
    u1: Expr
    u2: Expr
    u3: Expr
    u4: Expr
    roots: list[Expr]


# ---------------------------------------------------------------------------
# Core rational invariants
# ---------------------------------------------------------------------------


def theta_to_s2(q: DepressedQuintic, theta: Fraction | int | str) -> Fraction:
    """Recover ``S^2`` from the rational Dummit resolvent root ``theta``.

    Uses

        theta = 125*S^2 - 25*C^2 - 15*E.
    """
    th = _to_fraction(theta)
    return (th + 25 * q.C * q.C + 15 * q.E) / 125


def compute_S2(q: DepressedQuintic) -> Fraction:
    """Return the scaled sextic invariant ``S2`` from equation (9.8)."""
    C, E = q.C, q.E
    return -3 * C * C - E


def compute_S4(q: DepressedQuintic) -> Fraction:
    """Return the scaled sextic invariant ``S4`` from equation (9.8)."""
    C, D, E, f0 = q.C, q.D, q.E, q.f0
    return 15 * C**4 + 8 * C * D * D - 2 * C * C * E + 3 * E * E - 2 * D * f0


def compute_S6(q: DepressedQuintic) -> Fraction:
    """Return the scaled sextic invariant ``S6`` from equation (9.8)."""
    C, D, E, f0 = q.C, q.D, q.E, q.f0
    return (
        -25 * C**6
        - 40 * C**3 * D**2
        + 35 * C**4 * E
        - 11 * C**2 * E**2
        - 2 * C**2 * f0 * D
        - 16 * D**4
        + E**3
        - 2 * D * E * f0
        + 28 * C * D**2 * E
        + C * f0**2
    )


def compute_G0(q: DepressedQuintic) -> Fraction:
    """Return ``G0`` from equation (9.19)."""
    C, D, E = q.C, q.D, q.E
    return -(C**3) + C * E - D**2


def compute_G1(q: DepressedQuintic) -> Fraction:
    """Return ``G1`` from equation (9.19)."""
    C, D, E, f0 = q.C, q.D, q.E, q.f0
    return -C * C * D + C * f0 - D * E


def compute_G2(q: DepressedQuintic) -> Fraction:
    """Return ``G2`` from equation (9.19)."""
    C, D, E, f0 = q.C, q.D, q.E, q.f0
    return -C * D * D + C * C * E + D * f0 - E * E


def compute_G3(q: DepressedQuintic) -> Fraction:
    """Return ``G3`` from equation (9.19)."""
    C, D, E, f0 = q.C, q.D, q.E, q.f0
    return 2 * C * D * E - C * C * f0 - D**3


def compute_L0(q: DepressedQuintic) -> Fraction:
    """Return ``L0`` from equation (9.19)."""
    C, D, E, f0 = q.C, q.D, q.E, q.f0
    return (
        -15 * C**4 * E
        + 10 * C**3 * D**2
        - 2 * C**2 * D * f0
        + 14 * C**2 * E**2
        - 22 * C * D**2 * E
        + C * f0**2
        + 9 * D**4
        - 2 * D * E * f0
        + E**3
    )


def compute_L1(q: DepressedQuintic) -> Fraction:
    """Return ``L1`` from equation (9.19)."""
    C, D, E, f0 = q.C, q.D, q.E, q.f0
    return (
        9 * C**4 * f0
        - 20 * C**3 * D * E
        + 10 * C**2 * D**3
        + 8 * C**2 * E * f0
        - 12 * C * D * E**2
        - 2 * C * D**2 * f0
        + 6 * D**3 * E
        + D * f0**2
        - E**2 * f0
    )


def compute_lambda_from_s2(q: DepressedQuintic, s2: Fraction) -> Fraction:
    """Return ``lambda = T/S`` from equation (9.49).

    This formula only applies in the branch ``S != 0``. Since it depends only on
    ``S^2``, it remains rational and sign-free.
    """
    C, D, E, f0 = q.C, q.D, q.E, q.f0
    S2 = compute_S2(q)
    S4 = compute_S4(q)
    S6 = compute_S6(q)
    fiveS_sq = 25 * s2
    fiveS_4 = 625 * s2 * s2
    fiveS_6 = 15625 * s2 * s2 * s2
    nu = (
        (2 * C * D + f0) * fiveS_4
        - (20 * C**3 * D + 22 * C * C * f0 - 36 * C * D * E + 24 * D**3 + 2 * E * f0)
        * fiveS_sq
        + 50 * C**5 * D
        - 59 * C**4 * f0
        + 20 * C**3 * D * E
        + 40 * C**2 * D**3
        + 42 * C**2 * E * f0
        - 48 * C * D**2 * f0
        - 38 * C * D * E**2
        + 44 * D**3 * E
        - D * f0**2
        + E**2 * f0
    )
    den = S6 - S4 * fiveS_sq - 3 * S2 * fiveS_4 - fiveS_6
    if den == 0:
        raise ZeroDivisionError("Lambda denominator vanished in equation (9.49).")
    return nu / den


def compute_t2_when_s0(q: DepressedQuintic) -> Fraction:
    """Return ``T^2`` in the branch ``S = 0`` using equation (9.62)."""
    return -compute_G0(q)


def compute_invariants(
    q: DepressedQuintic, theta: Fraction | int | str
) -> QuinticInvariants:
    """Compute the main rational invariants used by the flowchart."""
    s2 = theta_to_s2(q, theta)
    lam = None if s2 == 0 else compute_lambda_from_s2(q, s2)
    t2 = compute_t2_when_s0(q) if s2 == 0 else None
    return QuinticInvariants(
        theta=_to_fraction(theta),
        s2=s2,
        s2_is_square=is_square_fraction(s2),
        S2=compute_S2(q),
        S4=compute_S4(q),
        S6=compute_S6(q),
        G0=compute_G0(q),
        G1=compute_G1(q),
        G2=compute_G2(q),
        G3=compute_G3(q),
        L0=compute_L0(q),
        L1=compute_L1(q),
        t2_if_s0=t2,
        lambda_if_s_nonzero=lam,
    )


# ---------------------------------------------------------------------------
# Branch selection and local square tests
# ---------------------------------------------------------------------------


def classify_branch(q: DepressedQuintic, inv: QuinticInvariants) -> BranchInfo:
    """Classify the high-level McClintock branch from rational data only.

    Tags used here mirror the notebook flow:

    - ``s_eq_c_eq_0``      : ``S = C = 0``
    - ``s_eq_t_eq_0``      : ``S = T = 0, C != 0``
    - ``s_eq_0_ct_ne_0``   : ``S = 0, C*T != 0``
    - ``s2_eq_c2``         : ``S^2 = C^2 != 0``
    - ``general``          : ``S != 0`` and ``S^2 != C^2``
    """
    s2 = inv.s2
    if s2 == 0:
        if q.C == 0:
            return BranchInfo(
                "s_eq_c_eq_0", s2=s2, s2_is_square=True, t2=None, lam=None
            )
        t2 = inv.t2_if_s0
        if t2 is None:
            raise RuntimeError("Missing T^2 in S=0 branch.")
        if t2 == 0:
            return BranchInfo("s_eq_t_eq_0", s2=s2, s2_is_square=True, t2=t2, lam=None)
        return BranchInfo("s_eq_0_ct_ne_0", s2=s2, s2_is_square=True, t2=t2, lam=None)
    if s2 == q.C * q.C:
        return BranchInfo(
            "s2_eq_c2",
            s2=s2,
            s2_is_square=inv.s2_is_square,
            t2=None,
            lam=inv.lambda_if_s_nonzero,
        )
    return BranchInfo(
        "general",
        s2=s2,
        s2_is_square=inv.s2_is_square,
        t2=None,
        lam=inv.lambda_if_s_nonzero,
    )


def zero_test_affine_in_s(expr: AffineInS, s2: Fraction) -> bool:
    """Test whether ``a + b*S`` is zero.

    This helper implements the user's intended policy:

    - in the generic non-square case, ``a + b*S = 0`` iff ``a = b = 0``;
    - when ``S^2`` is a rational square, use the canonical nonnegative rational
      square root only for this local zero test.

    Args:
        expr: Affine expression ``a + b*S``.
        s2: The rational value of ``S^2``.
    """
    if not is_square_fraction(s2):
        return expr.a == 0 and expr.b == 0
    s = sqrt_fraction(s2)
    return expr.a + expr.b * s == 0 or expr.a - expr.b * s == 0


def zero_test_affine_in_t(expr: AffineInT, t2: Fraction) -> bool:
    """Test whether ``a + b*T`` is zero using the same local policy as for ``S``."""
    if not is_square_fraction(t2):
        return expr.a == 0 and expr.b == 0
    t = sqrt_fraction(t2)
    return expr.a + expr.b * t == 0 or expr.a - expr.b * t == 0


# ---------------------------------------------------------------------------
# Local quantities used in the branches
# ---------------------------------------------------------------------------


def general_r1_sq(q: DepressedQuintic, s2: Fraction, lam: Fraction) -> AffineInS:
    """Return ``R1^2 = a + b*S`` in the generic ``S != 0`` branch.

    Notebook cell 3 / equation (9.35) after substituting ``T = lambda*S``.
    """
    C, D = q.C, q.D
    a = 4 * C**3 - 4 * C * s2 + D**2 + lam**2 * s2
    b = -4 * C**2 + 2 * D * lam + 4 * s2
    return AffineInS(a=a, b=b)


def general_r2_sq(q: DepressedQuintic, s2: Fraction, lam: Fraction) -> AffineInS:
    """Return ``R2^2 = a + b*S`` in the generic ``S != 0`` branch."""
    C, D = q.C, q.D
    a = 4 * C**3 - 4 * C * s2 + D**2 + lam**2 * s2
    b = 4 * C**2 - 2 * D * lam - 4 * s2
    return AffineInS(a=a, b=b)


def general_t_sq(s2: Fraction, lam: Fraction) -> Fraction:
    """Return ``T^2 = lambda^2 * S^2``."""
    return lam * lam * s2


def s0_r1_sq(q: DepressedQuintic, t2: Fraction) -> AffineInT:
    """Return ``R1^2 = a + b*T`` in the branch ``S = 0, C*T != 0``.

    Notebook cell 11 / equation (9.35) specialized at ``S = 0``.
    """
    C, D = q.C, q.D
    a = 4 * C**3 + D**2 + t2
    b = 2 * D
    return AffineInT(a=a, b=b)


def s0_r2_sq(q: DepressedQuintic, t2: Fraction) -> AffineInT:
    """Return ``R2^2 = a + b*T`` in the branch ``S = 0, C*T != 0``."""
    C, D = q.C, q.D
    a = 4 * C**3 + D**2 + t2
    b = -2 * D
    return AffineInT(a=a, b=b)


def s0_r1r2_times_t(q: DepressedQuintic) -> Fraction:
    """Return ``R1*R2*T = C*G1`` from equation (9.62)."""
    return q.C * compute_G1(q)


def s0_r2_expr_over_r1(q: DepressedQuintic, t2: Fraction) -> Fraction:
    """Return the rational coefficient in ``R2 = coeff * R1`` for ``S = 0``.

    This is the notebook quantity

        H = -2*C^3*D + C^2*f - D^3 + D*t2
        R2 = ((A*T - 2*D*t2) / H) * R1

    after using the branch-local notation.  It is useful later in the full AST
    builder but is recorded already here because it belongs to the computational
    spine of the flow.
    """
    C, D, f0 = q.C, q.D, q.f0
    H = -2 * C**3 * D + C * C * f0 - D**3 + D * t2
    if H == 0:
        raise ZeroDivisionError("Degenerate H in S=0 branch.")
    # The full factor still depends on T, so only H is exposed here.  This helper
    # is mainly a reminder and a validated denominator check.
    return H


# ---------------------------------------------------------------------------
# Factorization helper
# ---------------------------------------------------------------------------


def root_from_monic_linear_desc(
    coeffs_desc: Iterable[Fraction | int | str],
) -> Fraction:
    """Extract the root from a monic linear factor ``x - r``.

    Args:
        coeffs_desc: Descending coefficients of the factor.

    Returns:
        The rational root ``r``.

    Raises:
        ValueError: If the factor is not monic linear.
    """
    coeffs = [_to_fraction(c) for c in coeffs_desc]
    if len(coeffs) != 2 or coeffs[0] != 1:
        raise ValueError(
            "Expected monic linear factor with descending coefficients [1, -r]."
        )
    return -coeffs[1]


# ---------------------------------------------------------------------------
# Generic-branch AST helpers
# ---------------------------------------------------------------------------


def _add_terms(terms: list[Expr]) -> Expr:
    """Return the left-associated sum of a nonempty list of terms."""
    if not terms:
        return qq(Fraction(0, 1))
    acc = terms[0]
    for term in terms[1:]:
        acc = add(acc, term)
    return acc


def _basis_1sr_expr(
    *, a: Fraction, b: Fraction, c: Fraction, d: Fraction, S_ast: Expr, R_ast: Expr
) -> Expr:
    """Build ``a + b*S + c*R + d*S*R`` as a canonical radical AST."""
    terms: list[Expr] = []
    if a != 0:
        terms.append(qq(a))
    if b != 0:
        terms.append(mul(qq(b), S_ast))
    if c != 0:
        terms.append(mul(qq(c), R_ast))
    if d != 0:
        terms.append(mul(qq(d), mul(S_ast, R_ast)))
    return _add_terms(terms)


def _general_r2_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return the generic-branch coefficients of ``R2`` in the basis ``{1,S,R,SR}``."""
    C, D, E = q.C, q.D, q.E
    return {
        'a': Fraction(0),
        'b': Fraction(0),
        'c': (
            -4 * C**6
            + 2 * C**4 * D * lam
            + 4 * C**4 * E
            - 4 * C**4 * s2
            - 4 * C**3 * D**2
            + 4 * C**3 * lam**2 * s2
            - 2 * C**2 * D * E * lam
            + 4 * C**2 * D * lam * s2
            - 8 * C**2 * E * s2
            + 20 * C**2 * s2**2
            + 2 * C * D**3 * lam
            + 4 * C * D**2 * s2
            - 2 * C * D * lam**3 * s2
            - 4 * C * lam**2 * s2**2
            + 2 * D * E * lam * s2
            - 6 * D * lam * s2**2
            + 4 * E * s2**2
            - 12 * s2**3
        )
        / (
            -16 * C**6
            + 48 * C**4 * s2
            - 8 * C**3 * D**2
            - 8 * C**3 * lam**2 * s2
            - 16 * C**2 * D * lam * s2
            - 48 * C**2 * s2**2
            + 8 * C * D**2 * s2
            + 8 * C * lam**2 * s2**2
            - D**4
            + 2 * D**2 * lam**2 * s2
            + 16 * D * lam * s2**2
            - lam**4 * s2**2
            + 16 * s2**3
        ),
        'd': (
            -4 * C**7
            + 4 * C**5 * E
            - 4 * C**5 * s2
            - 5 * C**4 * D**2
            + 3 * C**4 * lam**2 * s2
            - 8 * C**3 * E * s2
            + 20 * C**3 * s2**2
            + C**2 * D**2 * E
            + 2 * C**2 * D**2 * s2
            + C**2 * E * lam**2 * s2
            - 6 * C**2 * lam**2 * s2**2
            - C * D**4
            + 4 * C * E * s2**2
            + C * lam**4 * s2**2
            - 12 * C * s2**3
            - D**2 * E * s2
            + 3 * D**2 * s2**2
            - E * lam**2 * s2**2
            + 3 * lam**2 * s2**3
        )
        / (
            -16 * C**6 * s2
            + 48 * C**4 * s2**2
            - 8 * C**3 * D**2 * s2
            - 8 * C**3 * lam**2 * s2**2
            - 16 * C**2 * D * lam * s2**2
            - 48 * C**2 * s2**3
            + 8 * C * D**2 * s2**2
            + 8 * C * lam**2 * s2**3
            - D**4 * s2
            + 2 * D**2 * lam**2 * s2**2
            + 16 * D * lam * s2**3
            - lam**4 * s2**3
            + 16 * s2**4
        ),
    }


def _general_u1_5_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return the generic-branch coefficients of ``u1^5`` in the basis ``{1,S,R,SR}``."""
    C, D, E = q.C, q.D, q.E
    return {
        'a': (
            C**4 * lam
            - C**2 * E * lam
            + 10 * C**2 * lam * s2
            + C * D**2 * lam
            + 2 * C * D * E
            - C * lam**3 * s2
            - D**3
            + D * lam**2 * s2
            - E * lam * s2
            + 5 * lam * s2**2
        )
        / (-4 * C**2 + 4 * s2),
        'b': (
            C**4 * D
            - 4 * C**3 * lam * s2
            - C**2 * D * E
            - 2 * C**2 * D * s2
            + C * D**3
            - C * D * lam**2 * s2
            + 2 * C * E * lam * s2
            - 12 * C * lam * s2**2
            - D**2 * lam * s2
            - D * E * s2
            + D * s2**2
            + lam**3 * s2**2
        )
        / (-4 * C**2 * s2 + 4 * s2**2),
        'c': (
            -16 * C**9
            + 4 * C**7 * D * lam
            + 16 * C**7 * E
            - 10 * C**6 * D**2
            - 10 * C**6 * lam**2 * s2
            - 4 * C**5 * D * E * lam
            - 12 * C**5 * D * lam * s2
            - 48 * C**5 * E * s2
            + 96 * C**5 * s2**2
            + 4 * C**4 * D**3 * lam
            + 10 * C**4 * D**2 * E
            - 2 * C**4 * D**2 * s2
            - 4 * C**4 * D * lam**3 * s2
            + 10 * C**4 * E * lam**2 * s2
            - 34 * C**4 * lam**2 * s2**2
            - 4 * C**3 * D**4
            + 4 * C**3 * D**2 * lam**2 * s2
            + 24 * C**3 * D * E * lam * s2
            - 52 * C**3 * D * lam * s2**2
            + 48 * C**3 * E * s2**2
            - 128 * C**3 * s2**3
            - 4 * C**2 * D**3 * lam * s2
            - 12 * C**2 * D**2 * E * s2
            + 2 * C**2 * D**2 * s2**2
            + 4 * C**2 * D * lam**3 * s2**2
            - 12 * C**2 * E * lam**2 * s2**2
            + 66 * C**2 * lam**2 * s2**3
            + 2 * C * D**4 * E
            + 4 * C * D**4 * s2
            - 4 * C * D**2 * E * lam**2 * s2
            + 12 * C * D**2 * lam**2 * s2**2
            - 20 * C * D * E * lam * s2**2
            + 60 * C * D * lam * s2**3
            + 2 * C * E * lam**4 * s2**2
            - 16 * C * E * s2**3
            - 16 * C * lam**4 * s2**3
            + 48 * C * s2**4
            - D**6
            + 3 * D**4 * lam**2 * s2
            + 16 * D**3 * lam * s2**2
            + 2 * D**2 * E * s2**2
            - 3 * D**2 * lam**4 * s2**2
            + 10 * D**2 * s2**3
            - 16 * D * lam**3 * s2**3
            + 2 * E * lam**2 * s2**3
            + lam**6 * s2**3
            - 22 * lam**2 * s2**4
        )
        / (
            64 * C**8
            - 256 * C**6 * s2
            + 32 * C**5 * D**2
            + 32 * C**5 * lam**2 * s2
            + 64 * C**4 * D * lam * s2
            + 384 * C**4 * s2**2
            - 64 * C**3 * D**2 * s2
            - 64 * C**3 * lam**2 * s2**2
            + 4 * C**2 * D**4
            - 8 * C**2 * D**2 * lam**2 * s2
            - 128 * C**2 * D * lam * s2**2
            + 4 * C**2 * lam**4 * s2**2
            - 256 * C**2 * s2**3
            + 32 * C * D**2 * s2**2
            + 32 * C * lam**2 * s2**3
            - 4 * D**4 * s2
            + 8 * D**2 * lam**2 * s2**2
            + 64 * D * lam * s2**3
            - 4 * lam**4 * s2**3
            + 64 * s2**4
        ),
        'd': (
            8 * C**10
            - 8 * C**8 * E
            + 8 * C**8 * s2
            + 14 * C**7 * D**2
            - 2 * C**7 * lam**2 * s2
            + 4 * C**6 * D * lam * s2
            + 16 * C**6 * E * s2
            - 48 * C**6 * s2**2
            - 6 * C**5 * D**2 * E
            - 26 * C**5 * D**2 * s2
            - 6 * C**5 * E * lam**2 * s2
            + 54 * C**5 * lam**2 * s2**2
            + 7 * C**4 * D**4
            - 2 * C**4 * D**2 * lam**2 * s2
            - 4 * C**4 * D * E * lam * s2
            + 20 * C**4 * D * lam * s2**2
            - 5 * C**4 * lam**4 * s2**2
            + 16 * C**4 * s2**3
            + 4 * C**3 * D**3 * lam * s2
            + 4 * C**3 * D**2 * E * s2
            + 42 * C**3 * D**2 * s2**2
            - 4 * C**3 * D * lam**3 * s2**2
            + 4 * C**3 * E * lam**2 * s2**2
            - 70 * C**3 * lam**2 * s2**3
            - C**2 * D**4 * E
            - 10 * C**2 * D**4 * s2
            + 2 * C**2 * D**2 * E * lam**2 * s2
            - 8 * C**2 * D**2 * lam**2 * s2**2
            - 8 * C**2 * D * E * lam * s2**2
            + 12 * C**2 * D * lam * s2**3
            - C**2 * E * lam**4 * s2**2
            - 16 * C**2 * E * s2**3
            + 18 * C**2 * lam**4 * s2**3
            + 40 * C**2 * s2**4
            + C * D**6
            - 3 * C * D**4 * lam**2 * s2
            - 20 * C * D**3 * lam * s2**2
            + 2 * C * D**2 * E * s2**2
            + 3 * C * D**2 * lam**4 * s2**2
            - 30 * C * D**2 * s2**3
            + 20 * C * D * lam**3 * s2**3
            + 2 * C * E * lam**2 * s2**3
            - C * lam**6 * s2**3
            + 18 * C * lam**2 * s2**4
            - D**4 * E * s2
            + 3 * D**4 * s2**2
            + 2 * D**2 * E * lam**2 * s2**2
            - 6 * D**2 * lam**2 * s2**3
            + 12 * D * E * lam * s2**3
            - 36 * D * lam * s2**4
            - E * lam**4 * s2**3
            + 8 * E * s2**4
            + 3 * lam**4 * s2**4
            - 24 * s2**5
        )
        / (
            64 * C**8 * s2
            - 256 * C**6 * s2**2
            + 32 * C**5 * D**2 * s2
            + 32 * C**5 * lam**2 * s2**2
            + 64 * C**4 * D * lam * s2**2
            + 384 * C**4 * s2**3
            - 64 * C**3 * D**2 * s2**2
            - 64 * C**3 * lam**2 * s2**3
            + 4 * C**2 * D**4 * s2
            - 8 * C**2 * D**2 * lam**2 * s2**2
            - 128 * C**2 * D * lam * s2**3
            + 4 * C**2 * lam**4 * s2**3
            - 256 * C**2 * s2**4
            + 32 * C * D**2 * s2**3
            + 32 * C * lam**2 * s2**4
            - 4 * D**4 * s2**2
            + 8 * D**2 * lam**2 * s2**3
            + 64 * D * lam * s2**4
            - 4 * lam**4 * s2**4
            + 64 * s2**5
        ),
    }


def _general_K2_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return the generic-branch coefficients of ``K2 = u2 / u1^2``."""
    C, D = q.C, q.D
    return {
        'a': (-(C**2) * D - 2 * C * lam * s2 - D * s2)
        / (2 * C**4 - 4 * C**2 * s2 + 2 * s2**2),
        'b': (-(C**2) * lam - 2 * C * D - lam * s2)
        / (2 * C**4 - 4 * C**2 * s2 + 2 * s2**2),
        'c': (-(C**2) - s2) / (2 * C**4 - 4 * C**2 * s2 + 2 * s2**2),
        'd': -C / (C**4 - 2 * C**2 * s2 + s2**2),
    }


def _general_K3_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return the generic-branch coefficients of ``K3 = u3 / u1^3``."""
    C, D, E = q.C, q.D, q.E
    return {
        'a': (
            -2 * C**5
            + 2 * C**3 * E
            - 4 * C**3 * s2
            - 3 * C**2 * D**2
            + 3 * C**2 * lam**2 * s2
            - 2 * C * E * s2
            + 6 * C * s2**2
            - D**2 * s2
            + lam**2 * s2**2
        )
        / (-4 * C**6 + 12 * C**4 * s2 - 12 * C**2 * s2**2 + 4 * s2**3),
        'b': (
            -(C**6)
            + C**4 * E
            - 3 * C**4 * s2
            - C**3 * D**2
            + C**3 * lam**2 * s2
            + C**2 * s2**2
            - 3 * C * D**2 * s2
            + 3 * C * lam**2 * s2**2
            - E * s2**2
            + 3 * s2**3
        )
        / (-4 * C**6 * s2 + 12 * C**4 * s2**2 - 12 * C**2 * s2**3 + 4 * s2**4),
        'c': (
            4 * C**9 * lam
            + 28 * C**8 * D
            - 4 * C**7 * E * lam
            - 16 * C**7 * lam * s2
            + 3 * C**6 * D**2 * lam
            - 12 * C**6 * D * E
            - 16 * C**6 * D * s2
            - 3 * C**6 * lam**3 * s2
            + 22 * C**5 * D**3
            - 6 * C**5 * D * lam**2 * s2
            - 4 * C**5 * E * lam * s2
            + 88 * C**5 * lam * s2**2
            + C**4 * D**2 * E * lam
            + 5 * C**4 * D**2 * lam * s2
            + 20 * C**4 * D * E * s2
            - 56 * C**4 * D * s2**2
            - C**4 * E * lam**3 * s2
            - 21 * C**4 * lam**3 * s2**2
            - C**3 * D**4 * lam
            - 2 * C**3 * D**3 * E
            - 4 * C**3 * D**3 * s2
            + 2 * C**3 * D**2 * lam**3 * s2
            + 2 * C**3 * D * E * lam**2 * s2
            - 28 * C**3 * D * lam**2 * s2**2
            + 20 * C**3 * E * lam * s2**2
            - C**3 * lam**5 * s2**2
            - 144 * C**3 * lam * s2**3
            + 3 * C**2 * D**5
            - 6 * C**2 * D**3 * lam**2 * s2
            + 5 * C**2 * D**2 * lam * s2**2
            - 4 * C**2 * D * E * s2**2
            + 3 * C**2 * D * lam**4 * s2**2
            + 48 * C**2 * D * s2**3
            + 27 * C**2 * lam**3 * s2**3
            - 3 * C * D**4 * lam * s2
            + 2 * C * D**3 * E * s2
            - 18 * C * D**3 * s2**2
            + 6 * C * D**2 * lam**3 * s2**2
            - 2 * C * D * E * lam**2 * s2**2
            + 34 * C * D * lam**2 * s2**3
            - 12 * C * E * lam * s2**3
            - 3 * C * lam**5 * s2**3
            + 68 * C * lam * s2**4
            + D**5 * s2
            - 2 * D**3 * lam**2 * s2**2
            - D**2 * E * lam * s2**2
            - 13 * D**2 * lam * s2**3
            - 4 * D * E * s2**3
            + D * lam**4 * s2**3
            - 4 * D * s2**4
            + E * lam**3 * s2**3
            - 3 * lam**3 * s2**4
        )
        / (
            64 * C**12
            - 384 * C**10 * s2
            + 32 * C**9 * D**2
            + 32 * C**9 * lam**2 * s2
            + 64 * C**8 * D * lam * s2
            + 960 * C**8 * s2**2
            - 128 * C**7 * D**2 * s2
            - 128 * C**7 * lam**2 * s2**2
            + 4 * C**6 * D**4
            - 8 * C**6 * D**2 * lam**2 * s2
            - 256 * C**6 * D * lam * s2**2
            + 4 * C**6 * lam**4 * s2**2
            - 1280 * C**6 * s2**3
            + 192 * C**5 * D**2 * s2**2
            + 192 * C**5 * lam**2 * s2**3
            - 12 * C**4 * D**4 * s2
            + 24 * C**4 * D**2 * lam**2 * s2**2
            + 384 * C**4 * D * lam * s2**3
            - 12 * C**4 * lam**4 * s2**3
            + 960 * C**4 * s2**4
            - 128 * C**3 * D**2 * s2**3
            - 128 * C**3 * lam**2 * s2**4
            + 12 * C**2 * D**4 * s2**2
            - 24 * C**2 * D**2 * lam**2 * s2**3
            - 256 * C**2 * D * lam * s2**4
            + 12 * C**2 * lam**4 * s2**4
            - 384 * C**2 * s2**5
            + 32 * C * D**2 * s2**4
            + 32 * C * lam**2 * s2**5
            - 4 * D**4 * s2**3
            + 8 * D**2 * lam**2 * s2**4
            + 64 * D * lam * s2**5
            - 4 * lam**4 * s2**5
            + 64 * s2**6
        ),
        'd': (
            4 * C**9 * D
            - 4 * C**8 * lam * s2
            - 4 * C**7 * D * E
            + 48 * C**7 * D * s2
            + 5 * C**6 * D**3
            - 5 * C**6 * D * lam**2 * s2
            - 12 * C**6 * E * lam * s2
            + 48 * C**6 * lam * s2**2
            + 2 * C**5 * D**2 * lam * s2
            - 4 * C**5 * D * E * s2
            - 104 * C**5 * D * s2**2
            - 18 * C**5 * lam**3 * s2**2
            - C**4 * D**3 * E
            + 27 * C**4 * D**3 * s2
            + C**4 * D * E * lam**2 * s2
            - 11 * C**4 * D * lam**2 * s2**2
            + 20 * C**4 * E * lam * s2**2
            - 56 * C**4 * lam * s2**3
            + C**3 * D**5
            - 2 * C**3 * D**3 * lam**2 * s2
            + 2 * C**3 * D**2 * E * lam * s2
            + 20 * C**3 * D**2 * lam * s2**2
            + 20 * C**3 * D * E * s2**2
            + C**3 * D * lam**4 * s2**2
            + 48 * C**3 * D * s2**3
            - 2 * C**3 * E * lam**3 * s2**2
            + 12 * C**3 * lam**3 * s2**3
            - 3 * C**2 * D**4 * lam * s2
            - 29 * C**2 * D**3 * s2**2
            + 6 * C**2 * D**2 * lam**3 * s2**2
            - 3 * C**2 * D * lam**2 * s2**3
            - 4 * C**2 * E * lam * s2**3
            - 3 * C**2 * lam**5 * s2**3
            - 16 * C**2 * lam * s2**4
            + 3 * C * D**5 * s2
            - 6 * C * D**3 * lam**2 * s2**2
            - 2 * C * D**2 * E * lam * s2**2
            - 22 * C * D**2 * lam * s2**3
            - 12 * C * D * E * s2**3
            + 3 * C * D * lam**4 * s2**3
            + 4 * C * D * s2**4
            + 2 * C * E * lam**3 * s2**3
            + 6 * C * lam**3 * s2**4
            - D**4 * lam * s2**2
            + D**3 * E * s2**2
            - 3 * D**3 * s2**3
            + 2 * D**2 * lam**3 * s2**3
            - D * E * lam**2 * s2**3
            + 19 * D * lam**2 * s2**4
            - 4 * E * lam * s2**4
            - lam**5 * s2**4
            + 28 * lam * s2**5
        )
        / (
            64 * C**12 * s2
            - 384 * C**10 * s2**2
            + 32 * C**9 * D**2 * s2
            + 32 * C**9 * lam**2 * s2**2
            + 64 * C**8 * D * lam * s2**2
            + 960 * C**8 * s2**3
            - 128 * C**7 * D**2 * s2**2
            - 128 * C**7 * lam**2 * s2**3
            + 4 * C**6 * D**4 * s2
            - 8 * C**6 * D**2 * lam**2 * s2**2
            - 256 * C**6 * D * lam * s2**3
            + 4 * C**6 * lam**4 * s2**3
            - 1280 * C**6 * s2**4
            + 192 * C**5 * D**2 * s2**3
            + 192 * C**5 * lam**2 * s2**4
            - 12 * C**4 * D**4 * s2**2
            + 24 * C**4 * D**2 * lam**2 * s2**3
            + 384 * C**4 * D * lam * s2**4
            - 12 * C**4 * lam**4 * s2**4
            + 960 * C**4 * s2**5
            - 128 * C**3 * D**2 * s2**4
            - 128 * C**3 * lam**2 * s2**5
            + 12 * C**2 * D**4 * s2**3
            - 24 * C**2 * D**2 * lam**2 * s2**4
            - 256 * C**2 * D * lam * s2**5
            + 12 * C**2 * lam**4 * s2**5
            - 384 * C**2 * s2**6
            + 32 * C * D**2 * s2**5
            + 32 * C * lam**2 * s2**6
            - 4 * D**4 * s2**4
            + 8 * D**2 * lam**2 * s2**5
            + 64 * D * lam * s2**6
            - 4 * lam**4 * s2**6
            + 64 * s2**7
        ),
    }


def _general_K4_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return the generic-branch coefficients of ``K4 = u4 / u1^4``."""
    C, D, E = q.C, q.D, q.E
    return {
        'a': (
            -(C**6) * lam
            - 4 * C**5 * D
            + C**4 * E * lam
            - C**4 * lam * s2
            - C**3 * D**2 * lam
            + 2 * C**3 * D * E
            + C**3 * lam**3 * s2
            - 3 * C**2 * D**3
            + 3 * C**2 * D * lam**2 * s2
            - 3 * C**2 * lam * s2**2
            - 3 * C * D**2 * lam * s2
            - 2 * C * D * E * s2
            + 4 * C * D * s2**2
            + 3 * C * lam**3 * s2**2
            - D**3 * s2
            + D * lam**2 * s2**2
            - E * lam * s2**2
            + 5 * lam * s2**3
        )
        / (
            4 * C**8
            - 16 * C**6 * s2
            + 24 * C**4 * s2**2
            - 16 * C**2 * s2**3
            + 4 * s2**4
        ),
        'b': (
            -(C**6) * D
            + C**4 * D * E
            - 5 * C**4 * D * s2
            - C**3 * D**3
            + C**3 * D * lam**2 * s2
            + 2 * C**3 * E * lam * s2
            - 8 * C**3 * lam * s2**2
            - 3 * C**2 * D**2 * lam * s2
            + 5 * C**2 * D * s2**2
            + 3 * C**2 * lam**3 * s2**2
            - 3 * C * D**3 * s2
            + 3 * C * D * lam**2 * s2**2
            - 2 * C * E * lam * s2**2
            + 8 * C * lam * s2**3
            - D**2 * lam * s2**2
            - D * E * s2**2
            + D * s2**3
            + lam**3 * s2**3
        )
        / (
            4 * C**8 * s2
            - 16 * C**6 * s2**2
            + 24 * C**4 * s2**3
            - 16 * C**2 * s2**4
            + 4 * s2**5
        ),
        'c': (
            16 * C**11
            + 4 * C**9 * D * lam
            - 16 * C**9 * E
            - 16 * C**9 * s2
            + 46 * C**8 * D**2
            - 18 * C**8 * lam**2 * s2
            - 4 * C**7 * D * E * lam
            + 32 * C**7 * D * lam * s2
            + 64 * C**7 * E * s2
            - 96 * C**7 * s2**2
            + 4 * C**6 * D**3 * lam
            - 14 * C**6 * D**2 * E
            - 64 * C**6 * D**2 * s2
            - 4 * C**6 * D * lam**3 * s2
            - 14 * C**6 * E * lam**2 * s2
            + 96 * C**6 * lam**2 * s2**2
            + 24 * C**5 * D**4
            - 4 * C**5 * D**2 * lam**2 * s2
            - 20 * C**5 * D * E * lam * s2
            + 8 * C**5 * D * lam * s2**2
            - 96 * C**5 * E * s2**2
            - 20 * C**5 * lam**4 * s2**2
            + 224 * C**5 * s2**3
            + 40 * C**4 * D**3 * lam * s2
            + 26 * C**4 * D**2 * E * s2
            - 20 * C**4 * D**2 * s2**2
            - 40 * C**4 * D * lam**3 * s2**2
            + 26 * C**4 * E * lam**2 * s2**2
            - 116 * C**4 * lam**2 * s2**3
            - 2 * C**3 * D**4 * E
            - 8 * C**3 * D**4 * s2
            + 4 * C**3 * D**2 * E * lam**2 * s2
            - 8 * C**3 * D**2 * lam**2 * s2**2
            + 52 * C**3 * D * E * lam * s2**2
            - 128 * C**3 * D * lam * s2**3
            - 2 * C**3 * E * lam**4 * s2**2
            + 64 * C**3 * E * s2**3
            + 16 * C**3 * lam**4 * s2**3
            - 176 * C**3 * s2**4
            + 3 * C**2 * D**6
            - 9 * C**2 * D**4 * lam**2 * s2
            - 28 * C**2 * D**3 * lam * s2**2
            - 10 * C**2 * D**2 * E * s2**2
            + 9 * C**2 * D**2 * lam**4 * s2**2
            + 48 * C**2 * D**2 * s2**3
            + 28 * C**2 * D * lam**3 * s2**3
            - 10 * C**2 * E * lam**2 * s2**3
            - 3 * C**2 * lam**6 * s2**3
            + 16 * C**2 * lam**2 * s2**4
            + 2 * C * D**4 * E * s2
            - 16 * C * D**4 * s2**2
            - 4 * C * D**2 * E * lam**2 * s2**2
            + 12 * C * D**2 * lam**2 * s2**3
            - 28 * C * D * E * lam * s2**3
            + 84 * C * D * lam * s2**4
            + 2 * C * E * lam**4 * s2**3
            - 16 * C * E * s2**4
            + 4 * C * lam**4 * s2**4
            + 48 * C * s2**5
            + D**6 * s2
            - 3 * D**4 * lam**2 * s2**2
            - 16 * D**3 * lam * s2**3
            - 2 * D**2 * E * s2**3
            + 3 * D**2 * lam**4 * s2**3
            - 10 * D**2 * s2**4
            + 16 * D * lam**3 * s2**4
            - 2 * E * lam**2 * s2**4
            - lam**6 * s2**4
            + 22 * lam**2 * s2**5
        )
        / (
            -64 * C**14
            + 448 * C**12 * s2
            - 32 * C**11 * D**2
            - 32 * C**11 * lam**2 * s2
            - 64 * C**10 * D * lam * s2
            - 1344 * C**10 * s2**2
            + 160 * C**9 * D**2 * s2
            + 160 * C**9 * lam**2 * s2**2
            - 4 * C**8 * D**4
            + 8 * C**8 * D**2 * lam**2 * s2
            + 320 * C**8 * D * lam * s2**2
            - 4 * C**8 * lam**4 * s2**2
            + 2240 * C**8 * s2**3
            - 320 * C**7 * D**2 * s2**2
            - 320 * C**7 * lam**2 * s2**3
            + 16 * C**6 * D**4 * s2
            - 32 * C**6 * D**2 * lam**2 * s2**2
            - 640 * C**6 * D * lam * s2**3
            + 16 * C**6 * lam**4 * s2**3
            - 2240 * C**6 * s2**4
            + 320 * C**5 * D**2 * s2**3
            + 320 * C**5 * lam**2 * s2**4
            - 24 * C**4 * D**4 * s2**2
            + 48 * C**4 * D**2 * lam**2 * s2**3
            + 640 * C**4 * D * lam * s2**4
            - 24 * C**4 * lam**4 * s2**4
            + 1344 * C**4 * s2**5
            - 160 * C**3 * D**2 * s2**4
            - 160 * C**3 * lam**2 * s2**5
            + 16 * C**2 * D**4 * s2**3
            - 32 * C**2 * D**2 * lam**2 * s2**4
            - 320 * C**2 * D * lam * s2**5
            + 16 * C**2 * lam**4 * s2**5
            - 448 * C**2 * s2**6
            + 32 * C * D**2 * s2**5
            + 32 * C * lam**2 * s2**6
            - 4 * D**4 * s2**4
            + 8 * D**2 * lam**2 * s2**5
            + 64 * D * lam * s2**6
            - 4 * lam**4 * s2**6
            + 64 * s2**7
        ),
        'd': (
            8 * C**12
            - 8 * C**10 * E
            + 14 * C**9 * D**2
            - 2 * C**9 * lam**2 * s2
            + 20 * C**8 * D * lam * s2
            + 24 * C**8 * E * s2
            - 56 * C**8 * s2**2
            - 6 * C**7 * D**2 * E
            + 32 * C**7 * D**2 * s2
            - 6 * C**7 * E * lam**2 * s2
            + 7 * C**6 * D**4
            - 2 * C**6 * D**2 * lam**2 * s2
            - 20 * C**6 * D * E * lam * s2
            + 32 * C**6 * D * lam * s2**2
            - 16 * C**6 * E * s2**2
            - 5 * C**6 * lam**4 * s2**2
            + 64 * C**6 * s2**3
            + 20 * C**5 * D**3 * lam * s2
            + 2 * C**5 * D**2 * E * s2
            - 116 * C**5 * D**2 * s2**2
            - 20 * C**5 * D * lam**3 * s2**2
            + 2 * C**5 * E * lam**2 * s2**2
            + 76 * C**5 * lam**2 * s2**3
            - C**4 * D**4 * E
            + 23 * C**4 * D**4 * s2
            + 2 * C**4 * D**2 * E * lam**2 * s2
            - 6 * C**4 * D**2 * lam**2 * s2**2
            + 28 * C**4 * D * E * lam * s2**2
            - 88 * C**4 * D * lam * s2**3
            - C**4 * E * lam**4 * s2**2
            - 16 * C**4 * E * s2**3
            - 17 * C**4 * lam**4 * s2**3
            + 24 * C**4 * s2**4
            + C**3 * D**6
            - 3 * C**3 * D**4 * lam**2 * s2
            + 24 * C**3 * D**3 * lam * s2**2
            + 14 * C**3 * D**2 * E * s2**2
            + 3 * C**3 * D**2 * lam**4 * s2**2
            + 80 * C**3 * D**2 * s2**3
            - 24 * C**3 * D * lam**3 * s2**3
            + 14 * C**3 * E * lam**2 * s2**3
            - C**3 * lam**6 * s2**3
            - 144 * C**3 * lam**2 * s2**4
            - 27 * C**2 * D**4 * s2**2
            + 2 * C**2 * D**2 * lam**2 * s2**3
            + 4 * C**2 * D * E * lam * s2**3
            + 24 * C**2 * E * s2**4
            + 25 * C**2 * lam**4 * s2**4
            - 64 * C**2 * s2**5
            + 3 * C * D**6 * s2
            - 9 * C * D**4 * lam**2 * s2**2
            - 44 * C * D**3 * lam * s2**3
            - 10 * C * D**2 * E * s2**3
            + 9 * C * D**2 * lam**4 * s2**3
            - 10 * C * D**2 * s2**4
            + 44 * C * D * lam**3 * s2**4
            - 10 * C * E * lam**2 * s2**4
            - 3 * C * lam**6 * s2**4
            + 70 * C * lam**2 * s2**5
            + D**4 * E * s2**2
            - 3 * D**4 * s2**3
            - 2 * D**2 * E * lam**2 * s2**3
            + 6 * D**2 * lam**2 * s2**4
            - 12 * D * E * lam * s2**4
            + 36 * D * lam * s2**5
            + E * lam**4 * s2**4
            - 8 * E * s2**5
            - 3 * lam**4 * s2**5
            + 24 * s2**6
        )
        / (
            -64 * C**14 * s2
            + 448 * C**12 * s2**2
            - 32 * C**11 * D**2 * s2
            - 32 * C**11 * lam**2 * s2**2
            - 64 * C**10 * D * lam * s2**2
            - 1344 * C**10 * s2**3
            + 160 * C**9 * D**2 * s2**2
            + 160 * C**9 * lam**2 * s2**3
            - 4 * C**8 * D**4 * s2
            + 8 * C**8 * D**2 * lam**2 * s2**2
            + 320 * C**8 * D * lam * s2**3
            - 4 * C**8 * lam**4 * s2**3
            + 2240 * C**8 * s2**4
            - 320 * C**7 * D**2 * s2**3
            - 320 * C**7 * lam**2 * s2**4
            + 16 * C**6 * D**4 * s2**2
            - 32 * C**6 * D**2 * lam**2 * s2**3
            - 640 * C**6 * D * lam * s2**4
            + 16 * C**6 * lam**4 * s2**4
            - 2240 * C**6 * s2**5
            + 320 * C**5 * D**2 * s2**4
            + 320 * C**5 * lam**2 * s2**5
            - 24 * C**4 * D**4 * s2**3
            + 48 * C**4 * D**2 * lam**2 * s2**4
            + 640 * C**4 * D * lam * s2**5
            - 24 * C**4 * lam**4 * s2**5
            + 1344 * C**4 * s2**6
            - 160 * C**3 * D**2 * s2**5
            - 160 * C**3 * lam**2 * s2**6
            + 16 * C**2 * D**4 * s2**4
            - 32 * C**2 * D**2 * lam**2 * s2**5
            - 320 * C**2 * D * lam * s2**6
            + 16 * C**2 * lam**4 * s2**6
            - 448 * C**2 * s2**7
            + 32 * C * D**2 * s2**6
            + 32 * C * lam**2 * s2**7
            - 4 * D**4 * s2**5
            + 8 * D**2 * lam**2 * s2**6
            + 64 * D * lam * s2**7
            - 4 * lam**4 * s2**7
            + 64 * s2**8
        ),
    }


def _basis_1r_expr(*, a: Fraction, b: Fraction, R_ast: Expr) -> Expr:
    """Build ``a + b*R`` as a canonical radical AST."""
    terms: list[Expr] = []
    if a != 0:
        terms.append(qq(a))
    if b != 0:
        terms.append(mul(qq(b), R_ast))
    return _add_terms(terms)


def _basis_1s_expr(*, a: Fraction, b: Fraction, S_ast: Expr) -> Expr:
    """Build ``a + b*S`` as a canonical radical AST."""
    terms: list[Expr] = []
    if a != 0:
        terms.append(qq(a))
    if b != 0:
        terms.append(mul(qq(b), S_ast))
    return _add_terms(terms)


def _general_r1_zero_branch_a_S(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> Fraction:
    """Return the rational ``S`` in the subcase ``R1 = 0``, ``R2 != 0``."""
    C, D = q.C, q.D
    den = 2 * (-2 * C**2 + D * lam + 2 * s2)
    if den == 0:
        raise ZeroDivisionError("Vanishing B1 in general R1=0, R2!=0 branch.")
    num = -4 * C**3 + 4 * C * s2 - D**2 - lam**2 * s2
    return num / den


def _general_r1_zero_branch_a_r_sq(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> Fraction:
    """Return ``R^2`` in the subcase ``R1 = 0``, ``R2 != 0`` with ``R := R2``."""
    C, D = q.C, q.D
    return -2 * (-4 * C**3 + 4 * C * s2 - D**2 - lam**2 * s2)


def _general_r1_zero_a_u1_5_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return branch-A coefficients of ``u1^5`` in the basis ``{1,R}``."""
    C, D = q.C, q.D
    return {
        'a': -((2 * C * D * lam + D**2 + lam**2 * s2) ** 2)
        * (
            -4 * C**3 * lam
            + 4 * C**2 * D
            + 4 * C * lam * s2
            - 3 * D**2 * lam
            - 4 * D * s2
            - lam**3 * s2
        )
        / (
            8
            * (-2 * C**2 + D * lam + 2 * s2) ** 2
            * (-8 * C**3 + 2 * C * D * lam + 8 * C * s2 - D**2 - lam**2 * s2)
        ),
        'b': -((2 * C * D * lam + D**2 + lam**2 * s2) ** 2)
        / (
            4
            * (-2 * C**2 + D * lam + 2 * s2)
            * (-8 * C**3 + 2 * C * D * lam + 8 * C * s2 - D**2 - lam**2 * s2)
        ),
    }


def _general_r1_zero_a_K2_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return branch-A coefficients of ``K2`` in the basis ``{1,R}``."""
    C, D = q.C, q.D
    return {
        'a': -(-2 * C**2 + D * lam + 2 * s2)
        * (
            -4 * C**3 * lam
            - 4 * C**2 * D
            + 4 * C * lam * s2
            + D**2 * lam
            + 4 * D * s2
            - lam**3 * s2
        )
        / (2 * C * D * lam + D**2 + lam**2 * s2) ** 2,
        'b': Fraction(0, 1),
    }


def _general_r1_zero_a_K3_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return branch-A coefficients of ``K3`` in the basis ``{1,R}``."""
    C, D = q.C, q.D
    return {
        'a': -((-2 * C**2 + D * lam + 2 * s2) ** 2)
        * (
            -4 * C**3 * lam
            - 4 * C**2 * D
            + 4 * C * lam * s2
            + D**2 * lam
            + 4 * D * s2
            - lam**3 * s2
        )
        * (
            -4 * C**3 * lam
            + 4 * C**2 * D
            + 4 * C * lam * s2
            - 3 * D**2 * lam
            - 4 * D * s2
            - lam**3 * s2
        )
        / (
            (2 * C * D * lam + D**2 + lam**2 * s2) ** 3
            * (-8 * C**3 + 2 * C * D * lam + 8 * C * s2 - D**2 - lam**2 * s2)
        ),
        'b': 2
        * (-2 * C**2 + D * lam + 2 * s2) ** 3
        * (
            -4 * C**3 * lam
            - 4 * C**2 * D
            + 4 * C * lam * s2
            + D**2 * lam
            + 4 * D * s2
            - lam**3 * s2
        )
        / (
            (2 * C * D * lam + D**2 + lam**2 * s2) ** 3
            * (-8 * C**3 + 2 * C * D * lam + 8 * C * s2 - D**2 - lam**2 * s2)
        ),
    }


def _general_r1_zero_a_K4_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return branch-A coefficients of ``K4`` in the basis ``{1,R}``."""
    C, D = q.C, q.D
    return {
        'a': -2
        * (-2 * C**2 + D * lam + 2 * s2) ** 2
        * (
            -4 * C**3 * lam
            + 4 * C**2 * D
            + 4 * C * lam * s2
            - 3 * D**2 * lam
            - 4 * D * s2
            - lam**3 * s2
        )
        / (
            (2 * C * D * lam + D**2 + lam**2 * s2) ** 2
            * (-8 * C**3 + 2 * C * D * lam + 8 * C * s2 - D**2 - lam**2 * s2)
        ),
        'b': 4
        * (-2 * C**2 + D * lam + 2 * s2) ** 3
        / (
            (2 * C * D * lam + D**2 + lam**2 * s2) ** 2
            * (-8 * C**3 + 2 * C * D * lam + 8 * C * s2 - D**2 - lam**2 * s2)
        ),
    }


def _general_r1_zero_b_u1_5_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return branch-B coefficients of ``u1^5`` in the basis ``{1,S}``."""
    C, D = q.C, q.D
    return {
        'a': -(C**3 * D + 3 * C**2 * lam * s2 + 3 * C * D * s2 + lam * s2**2)
        / (2 * (-(C**2) + s2)),
        'b': (C**3 * lam + 3 * C**2 * D + 3 * C * lam * s2 + D * s2)
        / (2 * (-(C**2) + s2)),
    }


def _general_r1_zero_b_K2_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return branch-B coefficients of ``K2`` in the basis ``{1,S}``."""
    C, D = q.C, q.D
    return {
        'a': -(C**2 * D + 2 * C * lam * s2 + D * s2) / (2 * (-(C**2) + s2) ** 2),
        'b': -(C**2 * lam + 2 * C * D + lam * s2) / (2 * (-(C**2) + s2) ** 2),
    }


def _general_r1_zero_b_K3_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return branch-B coefficients of ``K3`` in the basis ``{1,S}``."""
    C, D = q.C, q.D
    return {
        'a': (C**2 + s2) * (-(D**2) + lam**2 * s2) / (4 * (-(C**2) + s2) ** 3),
        'b': C * (-(D**2) + lam**2 * s2) / (2 * (-(C**2) + s2) ** 3),
    }


def _general_r1_zero_b_K4_coeffs(
    q: DepressedQuintic, *, s2: Fraction, lam: Fraction
) -> dict[str, Fraction]:
    """Return branch-B coefficients of ``K4`` in the basis ``{1,S}``."""
    C, D = q.C, q.D
    return {
        'a': -(-C * D + lam * s2) / (2 * (-(C**2) + s2) ** 2),
        'b': -(C * lam - D) / (2 * (-(C**2) + s2) ** 2),
    }


def build_general_r1_zero_case(
    q: DepressedQuintic, inv: QuinticInvariants
) -> GeneralR1ZeroCaseAST:
    """Build the AST data for the subcase ``general`` with ``R1 = 0``.

    This covers both notebook branches:

    - branch A: ``R1 = 0``, ``R2 != 0`` with basis ``{1, R}``, ``R := R2``
    - branch B: ``R1 = R2 = 0`` with basis ``{1, S}``
    """
    branch = classify_branch(q, inv)
    if branch.tag != "general":
        raise ValueError(
            "build_general_r1_zero_case() expects the generic "
            "S != 0, S^2 != C^2 branch."
        )

    s2 = inv.s2
    lam = inv.lambda_if_s_nonzero
    if lam is None:
        raise ValueError("Missing lambda in generic branch.")

    r1_sq_aff = general_r1_sq(q, s2, lam)
    if not zero_test_affine_in_s(r1_sq_aff, s2):
        raise ValueError("build_general_r1_zero_case() requires R1 = 0.")

    C, D = q.C, q.D
    A1 = 4 * C**3 - 4 * C * s2 + D**2 + lam**2 * s2
    B1 = 2 * (-2 * C**2 + D * lam + 2 * s2)

    if B1 != 0:
        # Branch A: R1 = 0, R2 != 0, S is rational.
        S_rat = _general_r1_zero_branch_a_S(q, s2=s2, lam=lam)
        T_rat = lam * S_rat
        R_sq = _general_r1_zero_branch_a_r_sq(q, s2=s2, lam=lam)

        S_ast = qq(S_rat)
        T_ast = qq(T_rat)
        R_sq_ast = qq(R_sq)
        R_ast = root(2, R_sq_ast)

        u1_5_ast = _basis_1r_expr(
            R_ast=R_ast, **_general_r1_zero_a_u1_5_coeffs(q, s2=s2, lam=lam)
        )
        K2_ast = _basis_1r_expr(
            R_ast=R_ast, **_general_r1_zero_a_K2_coeffs(q, s2=s2, lam=lam)
        )
        K3_ast = _basis_1r_expr(
            R_ast=R_ast, **_general_r1_zero_a_K3_coeffs(q, s2=s2, lam=lam)
        )
        K4_ast = _basis_1r_expr(
            R_ast=R_ast, **_general_r1_zero_a_K4_coeffs(q, s2=s2, lam=lam)
        )

        u1_ast = root(5, u1_5_ast)
        u2_ast = mul(K2_ast, pow_int(u1_ast, 2))
        u3_ast = mul(K3_ast, pow_int(u1_ast, 3))
        u4_ast = mul(K4_ast, pow_int(u1_ast, 4))
        roots = _emit_quintic_roots_from_u(u1=u1_ast, u2=u2_ast, u3=u3_ast, u4=u4_ast)

        return GeneralR1ZeroR2NonzeroCaseAST(
            S=S_ast,
            T=T_ast,
            R_sq=R_sq_ast,
            R=R_ast,
            u1_5=u1_5_ast,
            K2=K2_ast,
            K3=K3_ast,
            K4=K4_ast,
            u1=u1_ast,
            u2=u2_ast,
            u3=u3_ast,
            u4=u4_ast,
            roots=roots,
        )

    # Branch B: A1 = B1 = 0, basis {1,S}.
    if A1 != 0:
        raise ValueError("R1=0 with B1=0 forces A1=0 in the notebook branch structure.")

    S_ast = root(2, qq(s2))
    T_ast = mul(qq(lam), S_ast)

    u1_5_ast = _basis_1s_expr(
        S_ast=S_ast, **_general_r1_zero_b_u1_5_coeffs(q, s2=s2, lam=lam)
    )
    K2_ast = _basis_1s_expr(
        S_ast=S_ast, **_general_r1_zero_b_K2_coeffs(q, s2=s2, lam=lam)
    )
    K3_ast = _basis_1s_expr(
        S_ast=S_ast, **_general_r1_zero_b_K3_coeffs(q, s2=s2, lam=lam)
    )
    K4_ast = _basis_1s_expr(
        S_ast=S_ast, **_general_r1_zero_b_K4_coeffs(q, s2=s2, lam=lam)
    )

    u1_ast = root(5, u1_5_ast)
    u2_ast = mul(K2_ast, pow_int(u1_ast, 2))
    u3_ast = mul(K3_ast, pow_int(u1_ast, 3))
    u4_ast = mul(K4_ast, pow_int(u1_ast, 4))
    roots = _emit_quintic_roots_from_u(u1=u1_ast, u2=u2_ast, u3=u3_ast, u4=u4_ast)

    return GeneralR1ZeroR2ZeroCaseAST(
        S=S_ast,
        T=T_ast,
        u1_5=u1_5_ast,
        K2=K2_ast,
        K3=K3_ast,
        K4=K4_ast,
        u1=u1_ast,
        u2=u2_ast,
        u3=u3_ast,
        u4=u4_ast,
        roots=roots,
    )


def _emit_quintic_roots_from_u(*, u1: Expr, u2: Expr, u3: Expr, u4: Expr) -> list[Expr]:
    """Emit the canonical ordered quintic roots from ``u1``, ``u2``, ``u3``, ``u4``."""
    z1 = zeta(5, 1)
    z2 = zeta(5, 2)
    z3 = zeta(5, 3)
    z4 = zeta(5, 4)

    x1 = _add_terms([u1, u2, u3, u4])
    x2 = _add_terms([mul(z1, u1), mul(z2, u2), mul(z3, u3), mul(z4, u4)])
    x3 = _add_terms([mul(z2, u1), mul(z4, u2), mul(z1, u3), mul(z3, u4)])
    x4 = _add_terms([mul(z3, u1), mul(z1, u2), mul(z4, u3), mul(z2, u4)])
    x5 = _add_terms([mul(z4, u1), mul(z3, u2), mul(z2, u3), mul(z1, u4)])
    return [x1, x2, x3, x4, x5]


def build_general_case(q: DepressedQuintic, inv: QuinticInvariants) -> GeneralCaseAST:
    """Build the AST data for the fully generic McClintock branch.

    This covers exactly the branch

    - ``S != 0``
    - ``S^2 != C^2``
    - ``R1 != 0``

    using the coefficient dictionaries already derived in the notebook for the
    basis ``{1, S, R, S*R}``, where ``R := R1``.
    """
    branch = classify_branch(q, inv)
    if branch.tag != "general":
        raise ValueError(
            "build_general_case() expects the generic S != 0, S^2 != C^2 branch."
        )

    s2 = inv.s2
    lam = inv.lambda_if_s_nonzero
    if lam is None:
        raise ValueError("Missing lambda in generic branch.")

    r1_sq_aff = general_r1_sq(q, s2, lam)
    if zero_test_affine_in_s(r1_sq_aff, s2):
        raise ValueError("The fully generic branch requires R1 != 0.")

    S_ast = root(2, qq(s2))
    T_ast = mul(qq(lam), S_ast)
    R1_sq_ast = _basis_1sr_expr(
        a=r1_sq_aff.a,
        b=r1_sq_aff.b,
        c=Fraction(0, 1),
        d=Fraction(0, 1),
        S_ast=S_ast,
        R_ast=qq(Fraction(0, 1)),
    )
    R1_ast = root(2, R1_sq_ast)

    r2_coeffs = _general_r2_coeffs(q, s2=s2, lam=lam)
    u1_5_coeffs = _general_u1_5_coeffs(q, s2=s2, lam=lam)
    k2_coeffs = _general_K2_coeffs(q, s2=s2, lam=lam)
    k3_coeffs = _general_K3_coeffs(q, s2=s2, lam=lam)
    k4_coeffs = _general_K4_coeffs(q, s2=s2, lam=lam)

    R2_ast = _basis_1sr_expr(S_ast=S_ast, R_ast=R1_ast, **r2_coeffs)
    u1_5_ast = _basis_1sr_expr(S_ast=S_ast, R_ast=R1_ast, **u1_5_coeffs)
    K2_ast = _basis_1sr_expr(S_ast=S_ast, R_ast=R1_ast, **k2_coeffs)
    K3_ast = _basis_1sr_expr(S_ast=S_ast, R_ast=R1_ast, **k3_coeffs)
    K4_ast = _basis_1sr_expr(S_ast=S_ast, R_ast=R1_ast, **k4_coeffs)

    u1_ast = root(5, u1_5_ast)
    u2_ast = mul(K2_ast, pow_int(u1_ast, 2))
    u3_ast = mul(K3_ast, pow_int(u1_ast, 3))
    u4_ast = mul(K4_ast, pow_int(u1_ast, 4))
    roots = _emit_quintic_roots_from_u(u1=u1_ast, u2=u2_ast, u3=u3_ast, u4=u4_ast)

    return GeneralCaseAST(
        S=S_ast,
        T=T_ast,
        R1_sq=R1_sq_ast,
        R1=R1_ast,
        R2=R2_ast,
        u1_5=u1_5_ast,
        K2=K2_ast,
        K3=K3_ast,
        K4=K4_ast,
        u1=u1_ast,
        u2=u2_ast,
        u3=u3_ast,
        u4=u4_ast,
        roots=roots,
    )


@dataclass(frozen=True)
class SZeroR1NonzeroCaseAST:
    """AST data for the branch ``S = 0``, ``C*T != 0``, ``R1 != 0``."""

    T: Expr
    R1_sq: Expr
    R1: Expr
    R2: Expr
    u1_5: Expr
    K2: Expr
    K3: Expr
    K4: Expr
    u1: Expr
    u2: Expr
    u3: Expr
    u4: Expr
    roots: list[Expr]


def _basis_1t_expr(*, a: Fraction, b: Fraction, T_ast: Expr) -> Expr:
    """Build ``a + b*T`` as a canonical radical AST."""
    terms: list[Expr] = []
    if a != 0:
        terms.append(qq(a))
    if b != 0:
        terms.append(mul(qq(b), T_ast))
    return _add_terms(terms)


def _basis_1tr_expr(
    *, a: Fraction, b: Fraction, c: Fraction, d: Fraction, T_ast: Expr, R_ast: Expr
) -> Expr:
    """Build ``a + b*T + c*R + d*T*R`` as a canonical radical AST."""
    terms: list[Expr] = []
    if a != 0:
        terms.append(qq(a))
    if b != 0:
        terms.append(mul(qq(b), T_ast))
    if c != 0:
        terms.append(mul(qq(c), R_ast))
    if d != 0:
        terms.append(mul(qq(d), mul(T_ast, R_ast)))
    return _add_terms(terms)


def _s0_r1_nonzero_r2_coeffs(
    q: DepressedQuintic, *, t2: Fraction
) -> dict[str, Fraction]:
    """Return the coefficients of ``R2`` in the basis ``{1,T,R,TR}``."""
    C, D, f0 = q.C, q.D, q.f0
    A = t2 + D * D + 4 * C**3
    H = C * C * f0 - 2 * C**3 * D - D**3 + D * t2
    if H == 0:
        raise ZeroDivisionError("Degenerate H in S=0, R1!=0 branch.")
    return {
        "a": Fraction(0, 1),
        "b": Fraction(0, 1),
        "c": Fraction(-2) * D * t2 / H,
        "d": A / H,
    }


def _s0_r1_nonzero_u1_5_coeffs(
    q: DepressedQuintic, *, t2: Fraction
) -> dict[str, Fraction]:
    """Return the coefficients of ``u1^5`` in the basis ``{1,T,R,TR}``."""
    C, D, f0 = q.C, q.D, q.f0
    den = -8 * C**5 * D + 4 * C**4 * f0 - 4 * C**2 * D**3 + 4 * C**2 * D * t2
    den_b = -8 * C**3 * D + 4 * C**2 * f0 - 4 * D**3 + 4 * D * t2
    return {
        "a": (
            4 * C**6 * D**2
            - 16 * C**6 * t2
            - 2 * C**5 * D * f0
            + 4 * C**3 * D**4
            - 12 * C**3 * D**2 * t2
            - 8 * C**3 * t2**2
            - C**2 * D**3 * f0
            + C**2 * D * f0 * t2
            + D**6
            - 3 * D**4 * t2
            + 3 * D**2 * t2**2
            - t2**3
        )
        / den,
        "b": (
            -20 * C**4 * D
            + 2 * C**3 * f0
            - 8 * C * D**3
            - 8 * C * D * t2
            - D**2 * f0
            + f0 * t2
        )
        / den_b,
        "c": (
            -2 * C**3 * D**3
            + 6 * C**3 * D * t2
            + C**2 * D**2 * f0
            - C**2 * f0 * t2
            - D**5
            + 2 * D**3 * t2
            - D * t2**2
        )
        / den,
        "d": (8 * C**6 + 6 * C**3 * D**2 + 6 * C**3 * t2 + D**4 - 2 * D**2 * t2 + t2**2)
        / den,
    }


def _s0_r1_nonzero_K2_coeffs(
    q: DepressedQuintic, *, t2: Fraction
) -> dict[str, Fraction]:
    """Return the coefficients of ``K2 = u2 / u1^2`` in the basis ``{1,T,R,TR}``."""
    C, D = q.C, q.D
    den = 2 * C * C
    return {
        "a": -D / den,
        "b": Fraction(-1, 1) / den,
        "c": Fraction(-1, 1) / den,
        "d": Fraction(0, 1),
    }


def _s0_r1_nonzero_K3_coeffs(
    q: DepressedQuintic, *, t2: Fraction
) -> dict[str, Fraction]:
    """Return the coefficients of ``K3 = u3 / u1^3`` in the basis ``{1,T,R,TR}``."""
    C, D, f0 = q.C, q.D, q.f0
    den = -8 * C**7 * D + 4 * C**6 * f0 - 4 * C**4 * D**3 + 4 * C**4 * D * t2
    return {
        "a": (D**2 - t2) / (4 * C**4),
        "b": (
            16 * C**6 + 8 * C**3 * D**2 + 8 * C**3 * t2 + D**4 - 2 * D**2 * t2 + t2**2
        )
        / den,
        "c": (-2 * C**3 * D**2 + 4 * C**3 * t2 + C**2 * D * f0 - D**4 + t2**2) / den,
        "d": (6 * C**3 * D - C**2 * f0 + 2 * D**3 - 2 * D * t2) / den,
    }


def _s0_r1_nonzero_K4_coeffs(
    q: DepressedQuintic, *, t2: Fraction
) -> dict[str, Fraction]:
    """Return the coefficients of ``K4 = u4 / u1^4`` in the basis ``{1,T,R,TR}``."""
    C, D, f0 = q.C, q.D, q.f0
    den = -8 * C**9 * D + 4 * C**8 * f0 - 4 * C**6 * D**3 + 4 * C**6 * D * t2
    den_b = -8 * C**7 * D + 4 * C**6 * f0 - 4 * C**4 * D**3 + 4 * C**4 * D * t2
    return {
        "a": (
            4 * C**6 * D**2
            - 16 * C**6 * t2
            - 2 * C**5 * D * f0
            + 4 * C**3 * D**4
            - 12 * C**3 * D**2 * t2
            - 8 * C**3 * t2**2
            - C**2 * D**3 * f0
            + C**2 * D * f0 * t2
            + D**6
            - 3 * D**4 * t2
            + 3 * D**2 * t2**2
            - t2**3
        )
        / den,
        "b": (
            -20 * C**4 * D
            + 2 * C**3 * f0
            - 8 * C * D**3
            - 8 * C * D * t2
            - D**2 * f0
            + f0 * t2
        )
        / den_b,
        "c": (
            2 * C**3 * D**3
            - 6 * C**3 * D * t2
            - C**2 * D**2 * f0
            + C**2 * f0 * t2
            + D**5
            - 2 * D**3 * t2
            + D * t2**2
        )
        / den,
        "d": (
            -8 * C**6 - 6 * C**3 * D**2 - 6 * C**3 * t2 - D**4 + 2 * D**2 * t2 - t2**2
        )
        / den,
    }


def build_s_eq_0_r1_nonzero_case(
    q: DepressedQuintic, inv: QuinticInvariants
) -> SZeroR1NonzeroCaseAST:
    """Build the AST data for McClintock §9.4.2 with ``S = 0``, ``C*T != 0``, ``R1 != 0``."""
    branch = classify_branch(q, inv)
    if branch.tag != "s_eq_0_ct_ne_0":
        raise ValueError(
            "build_s_eq_0_r1_nonzero_case() expects the S = 0, C*T != 0 branch."
        )

    t2 = inv.t2_if_s0
    if t2 is None or t2 == 0:
        raise ValueError("Missing nonzero T^2 in S = 0 branch.")
    if q.C == 0:
        raise ValueError("build_s_eq_0_r1_nonzero_case() requires C != 0.")

    r1_sq = s0_r1_sq(q, t2)

    T_ast = root(2, qq(t2))
    R1_sq_ast = _basis_1t_expr(a=r1_sq.a, b=r1_sq.b, T_ast=T_ast)
    R1_ast = root(2, R1_sq_ast)

    r2_coeffs = _s0_r1_nonzero_r2_coeffs(q, t2=t2)
    u1_5_coeffs = _s0_r1_nonzero_u1_5_coeffs(q, t2=t2)
    k2_coeffs = _s0_r1_nonzero_K2_coeffs(q, t2=t2)
    k3_coeffs = _s0_r1_nonzero_K3_coeffs(q, t2=t2)
    k4_coeffs = _s0_r1_nonzero_K4_coeffs(q, t2=t2)

    R2_ast = _basis_1tr_expr(T_ast=T_ast, R_ast=R1_ast, **r2_coeffs)
    u1_5_ast = _basis_1tr_expr(T_ast=T_ast, R_ast=R1_ast, **u1_5_coeffs)
    K2_ast = _basis_1tr_expr(T_ast=T_ast, R_ast=R1_ast, **k2_coeffs)
    K3_ast = _basis_1tr_expr(T_ast=T_ast, R_ast=R1_ast, **k3_coeffs)
    K4_ast = _basis_1tr_expr(T_ast=T_ast, R_ast=R1_ast, **k4_coeffs)

    u1_ast = root(5, u1_5_ast)
    u2_ast = mul(K2_ast, pow_int(u1_ast, 2))
    u3_ast = mul(K3_ast, pow_int(u1_ast, 3))
    u4_ast = mul(K4_ast, pow_int(u1_ast, 4))
    roots = _emit_quintic_roots_from_u(u1=u1_ast, u2=u2_ast, u3=u3_ast, u4=u4_ast)

    return SZeroR1NonzeroCaseAST(
        T=T_ast,
        R1_sq=R1_sq_ast,
        R1=R1_ast,
        R2=R2_ast,
        u1_5=u1_5_ast,
        K2=K2_ast,
        K3=K3_ast,
        K4=K4_ast,
        u1=u1_ast,
        u2=u2_ast,
        u3=u3_ast,
        u4=u4_ast,
        roots=roots,
    )


@dataclass(frozen=True)
class SEqualCGenericCaseAST:
    """AST data for the branch ``S = C != 0`` with ``u4 = 0`` and ``u1 != 0``."""

    S: Expr
    T: Expr
    xi: Expr
    eta: Expr
    u1_5: Expr
    K2: Expr
    K3: Expr
    K4: Expr
    u1: Expr
    u2: Expr
    u3: Expr
    u4: Expr
    roots: list[Expr]


@dataclass(frozen=True)
class SEqualCDeMoivreCaseAST:
    """AST data for the De Moivre subcase inside ``S = C``."""

    S: Expr
    T: Expr
    u_5: Expr
    u: Expr
    roots: list[Expr]


SEqualCCaseAST = SEqualCGenericCaseAST | SEqualCDeMoivreCaseAST


def build_s_eq_c_case(q: DepressedQuintic, inv: QuinticInvariants) -> SEqualCCaseAST:
    """Build the AST data for the notebook branch ``S = C``.

    This implements the formulas from the notebook cell for McClintock §9.4.1:

    - ordinary subcase: ``u4 = 0`` and ``u1 != 0``
    - De Moivre subcase: ``u1 = u4 = 0``

    The branch is interpreted literally as ``S = C`` (not merely ``S^2 = C^2``).
    """
    branch = classify_branch(q, inv)
    if branch.tag != "s2_eq_c2":
        raise ValueError("build_s_eq_c_case() expects the S^2 = C^2 branch.")
    if q.C == 0:
        raise ValueError("build_s_eq_c_case() requires C != 0.")
    if inv.s2 != q.C * q.C:
        raise ValueError("build_s_eq_c_case() requires S^2 = C^2.")

    lam = inv.lambda_if_s_nonzero
    if lam is None:
        raise ValueError("Missing lambda in S = C branch.")

    C = q.C
    D = q.D
    E = q.E
    f0 = q.f0

    # We work with the explicit notebook choice S = C.
    S_ast = qq(C)
    T_ast = qq(C * lam)

    # De Moivre subcase:
    #   D = 0, E = 4 C^2, T = 0
    # and x_k = u*omega^k - 2C/(u*omega^k), where u^5 is a root of
    # z^2 + f z - 32 C^5 = 0.
    if D == 0 and lam == 0 and E == 4 * C * C:
        rad_ast = root(2, add(qq(f0 * f0 / 4), qq(32 * C**5)))
        u_5_ast = add(qq(-f0 / 2), rad_ast)
        u_ast = root(5, u_5_ast)

        roots: list[Expr] = []
        z0 = qq(Fraction(1, 1))
        z1 = zeta(5, 1)
        z2 = zeta(5, 2)
        z3 = zeta(5, 3)
        z4 = zeta(5, 4)
        for zk in [z0, z1, z2, z3, z4]:
            term1 = mul(u_ast, zk)
            term2 = mul(qq(-2 * C), pow_int(mul(u_ast, zk), -1))
            roots.append(add(term1, term2))

        return SEqualCDeMoivreCaseAST(
            S=S_ast,
            T=T_ast,
            u_5=u_5_ast,
            u=u_ast,
            roots=roots,
        )

    xi_ast = qq(C * lam - D)
    eta_ast = qq(C * lam + D)

    u1_5_ast = qq((C * lam - D) * (C * lam + D) ** 2 / (4 * C * C))
    K2_ast = qq(Fraction(2) * C / (C * lam + D))
    K3_ast = qq(Fraction(-4) * C * C / ((C * lam - D) * (C * lam + D)))
    K4_ast = qq(Fraction(0, 1))

    u1_ast = root(5, u1_5_ast)
    u2_ast = mul(K2_ast, pow_int(u1_ast, 2))
    u3_ast = mul(K3_ast, pow_int(u1_ast, 3))
    u4_ast = qq(Fraction(0, 1))
    roots = _emit_quintic_roots_from_u(u1=u1_ast, u2=u2_ast, u3=u3_ast, u4=u4_ast)

    return SEqualCGenericCaseAST(
        S=S_ast,
        T=T_ast,
        xi=xi_ast,
        eta=eta_ast,
        u1_5=u1_5_ast,
        K2=K2_ast,
        K3=K3_ast,
        K4=K4_ast,
        u1=u1_ast,
        u2=u2_ast,
        u3=u3_ast,
        u4=u4_ast,
        roots=roots,
    )


@dataclass(frozen=True)
class SZeroR1ZeroR2NonzeroCaseAST:
    """AST data for the branch ``S = 0``, ``C*T != 0``, ``R1 = 0``, ``R2 != 0``."""

    T: Expr
    R1_sq: Expr
    R1: Expr
    R2_sq: Expr
    R2: Expr
    u1_5: Expr
    K2: Expr
    K3: Expr
    K4: Expr
    u1: Expr
    u2: Expr
    u3: Expr
    u4: Expr
    roots: list[Expr]


@dataclass(frozen=True)
class SZeroR1ZeroR2ZeroCaseAST:
    """AST data for the branch ``S = 0``, ``C*T != 0``, ``R1 = R2 = 0``."""

    T_sq: Expr
    T: Expr
    R1_sq: Expr
    R1: Expr
    R2_sq: Expr
    R2: Expr
    u1_5: Expr
    K2: Expr
    K3: Expr
    K4: Expr
    u1: Expr
    u2: Expr
    u3: Expr
    u4: Expr
    roots: list[Expr]


SZeroR1ZeroCaseAST = SZeroR1ZeroR2NonzeroCaseAST | SZeroR1ZeroR2ZeroCaseAST


def _s0_r1_zero_branch_a_t(q: DepressedQuintic, *, t2: Fraction) -> Fraction:
    """Return the rational ``T`` in the subcase ``S = 0``, ``R1 = 0``, ``R2 != 0``."""
    C, D = q.C, q.D
    if D == 0:
        raise ZeroDivisionError("Vanishing D in S=0, R1=0, R2!=0 branch.")
    return -(4 * C**3 + D**2 + t2) / (2 * D)


def _s0_r1_zero_branch_a_r_sq(q: DepressedQuintic, *, t2: Fraction) -> Fraction:
    """Return ``R^2`` with ``R := R2`` in the subcase ``S = 0``, ``R1 = 0``, ``R2 != 0``."""
    C, D = q.C, q.D
    return 2 * (4 * C**3 + D**2 + t2)


def _s0_r1_zero_a_u1_5_coeffs(
    q: DepressedQuintic, *, t2: Fraction
) -> dict[str, Fraction]:
    """Return branch-A coefficients of ``u1^5`` in the basis ``{1,R}``."""
    C, D = q.C, q.D
    return {
        "a": C * (4 * C**3 + 3 * D**2 + t2) / (4 * D),
        "b": -C / 2,
    }


def _s0_r1_zero_a_K2_coeffs(
    q: DepressedQuintic, *, t2: Fraction
) -> dict[str, Fraction]:
    """Return branch-A coefficients of ``K2`` in the basis ``{1,R}``."""
    C, D = q.C, q.D
    return {
        "a": (4 * C**3 - D**2 + t2) / (4 * C**2 * D),
        "b": Fraction(0, 1),
    }


def _s0_r1_zero_a_K3_coeffs(
    q: DepressedQuintic, *, t2: Fraction
) -> dict[str, Fraction]:
    """Return branch-A coefficients of ``K3`` in the basis ``{1,R}``."""
    C, D = q.C, q.D
    return {
        "a": -(4 * C**3 - D**2 + t2) * (4 * C**3 + 3 * D**2 + t2) / (16 * C**4 * D**2),
        "b": -(4 * C**3 - D**2 + t2) / (8 * C**4 * D),
    }


def _s0_r1_zero_b_u1_5_coeffs(q: DepressedQuintic) -> dict[str, Fraction]:
    """Return branch-B coefficients of ``u1^5`` in the basis ``{1,T}``."""
    C = q.C
    return {"a": Fraction(0, 1), "b": -C / 2}


def _s0_r1_zero_b_K2_coeffs(q: DepressedQuintic) -> dict[str, Fraction]:
    """Return branch-B coefficients of ``K2`` in the basis ``{1,T}``."""
    C = q.C
    return {"a": Fraction(0, 1), "b": Fraction(-1, 1) / (2 * C**2)}


def _s0_r1_zero_b_K3_coeffs(q: DepressedQuintic) -> dict[str, Fraction]:
    """Return branch-B coefficients of ``K3`` in the basis ``{1,T}``."""
    C = q.C
    return {"a": Fraction(1, 1) / C, "b": Fraction(0, 1)}


def build_s_eq_0_r1_zero_case(
    q: DepressedQuintic, inv: QuinticInvariants
) -> SZeroR1ZeroCaseAST:
    """Build the AST data for McClintock §9.4.2 with ``S = 0``, ``C*T != 0``, ``R1 = 0``."""
    branch = classify_branch(q, inv)
    if branch.tag != "s_eq_0_ct_ne_0":
        raise ValueError(
            "build_s_eq_0_r1_zero_case() expects the S = 0, C*T != 0 branch."
        )

    t2 = inv.t2_if_s0
    if t2 is None or t2 == 0:
        raise ValueError("Missing nonzero T^2 in S = 0 branch.")
    if q.C == 0:
        raise ValueError("build_s_eq_0_r1_zero_case() requires C != 0.")

    r1_sq = s0_r1_sq(q, t2)
    if not zero_test_affine_in_t(r1_sq, t2):
        raise ValueError("build_s_eq_0_r1_zero_case() requires R1 = 0.")

    #r2_sq = s0_r2_sq(q, t2)

    # Branch (A): R2 != 0. Then T is rational and we work in the basis {1, R}
    # with R := R2.
    #if not zero_test_affine_in_t(r2_sq, t2):
    T_rat = _s0_r1_zero_branch_a_t(q, t2=t2)
    R_sq_rat = _s0_r1_zero_branch_a_r_sq(q, t2=t2)

    T_ast = qq(T_rat)
    R1_sq_ast = qq(Fraction(0, 1))
    R1_ast = qq(Fraction(0, 1))
    R2_sq_ast = qq(R_sq_rat)
    R2_ast = root(2, R2_sq_ast)

    u1_5_coeffs = _s0_r1_zero_a_u1_5_coeffs(q, t2=t2)
    k2_coeffs = _s0_r1_zero_a_K2_coeffs(q, t2=t2)
    k3_coeffs = _s0_r1_zero_a_K3_coeffs(q, t2=t2)

    u1_5_ast = _basis_1r_expr(R_ast=R2_ast, **u1_5_coeffs)
    K2_ast = _basis_1r_expr(R_ast=R2_ast, **k2_coeffs)
    K3_ast = _basis_1r_expr(R_ast=R2_ast, **k3_coeffs)
    K4_ast = mul(K2_ast, K3_ast)

    u1_ast = root(5, u1_5_ast)
    u2_ast = mul(K2_ast, pow_int(u1_ast, 2))
    u3_ast = mul(K3_ast, pow_int(u1_ast, 3))
    u4_ast = mul(K4_ast, pow_int(u1_ast, 4))
    roots = _emit_quintic_roots_from_u(u1=u1_ast, u2=u2_ast, u3=u3_ast, u4=u4_ast)

    return SZeroR1ZeroR2NonzeroCaseAST(
        T=T_ast,
        R1_sq=R1_sq_ast,
        R1=R1_ast,
        R2_sq=R2_sq_ast,
        R2=R2_ast,
        u1_5=u1_5_ast,
        K2=K2_ast,
        K3=K3_ast,
        K4=K4_ast,
        u1=u1_ast,
        u2=u2_ast,
        u3=u3_ast,
        u4=u4_ast,
        roots=roots,
    )
        
    raise NotImplementedError("Branch (B) with R1 = R2 = 0 is not possible.") 


@dataclass(frozen=True)
class SEqualTZeroCaseAST:
    """AST data for the branch ``S = T = 0``, ``C != 0`` (chapter §9.4.3)."""

    R_sq: Expr
    R: Expr
    u1_5: Expr
    K2: Expr
    K3: Expr
    K4: Expr
    u1: Expr
    u2: Expr
    u3: Expr
    u4: Expr
    roots: list[Expr]


def build_s_eq_t_eq_0_case(
    q: DepressedQuintic, inv: QuinticInvariants
) -> SEqualTZeroCaseAST:
    """Build the AST data for chapter §9.4.3: ``S = T = 0``, ``C != 0``.

    We follow the book's canonical choice ``R1 = R2`` with

        R1^2 = R2^2 = 4*C^3 + D^2

    and then compute ``u1, u2, u3, u4`` exactly as in the general case using
    equations (9.37) and (9.39), specialized at ``S = T = 0``.  In this branch
    we have

        alpha = -C, beta = C, xi = -D, eta = D,
        a1 = a2 = (-D + R)/2,
        a3 = a4 = (-D - R)/2,

    where ``R := R1 = R2``.
    """
    branch = classify_branch(q, inv)
    if branch.tag != "s_eq_t_eq_0":
        raise ValueError(
            "build_s_eq_t_eq_0_case() expects the branch S = T = 0, C != 0."
        )

    C, D = q.C, q.D
    if C == 0:
        raise ValueError("The branch S = T = 0 requires C != 0.")
    t2 = branch.t2
    if t2 != 0:
        raise ValueError("The branch S = T = 0 requires T^2 = 0.")

    r_sq = 4 * C**3 + D**2
    R_sq_ast = qq(r_sq)
    R_ast = root(2, R_sq_ast)

    half = Fraction(1, 2)
    a1_ast = mul(qq(half), add(qq(-D), R_ast))
    a3_ast = mul(qq(half), add(qq(-D), mul(qq(Fraction(-1, 1)), R_ast)))

    c_sq = C * C
    c_four = c_sq * c_sq
    c_six = c_four * c_sq

    # u1^5 = a1^3 / C^2
    u1_5_ast = mul(qq(Fraction(1, c_sq)), pow_int(a1_ast, 3))

    # u2 = (a4 / C^2) * u1^2, with a4 = a3.
    K2_ast = mul(qq(Fraction(1, c_sq)), a3_ast)

    # u3 = (a3^2 / C^4) * u1^3.
    K3_ast = mul(qq(Fraction(1, c_four)), pow_int(a3_ast, 2))

    # u4 = (a3^3 / C^6) * u1^4.
    K4_ast = mul(qq(Fraction(1, c_six)), pow_int(a3_ast, 3))

    u1_ast = root(5, u1_5_ast)
    u2_ast = mul(K2_ast, pow_int(u1_ast, 2))
    u3_ast = mul(K3_ast, pow_int(u1_ast, 3))
    u4_ast = mul(K4_ast, pow_int(u1_ast, 4))
    roots = _emit_quintic_roots_from_u(u1=u1_ast, u2=u2_ast, u3=u3_ast, u4=u4_ast)

    return SEqualTZeroCaseAST(
        R_sq=R_sq_ast,
        R=R_ast,
        u1_5=u1_5_ast,
        K2=K2_ast,
        K3=K3_ast,
        K4=K4_ast,
        u1=u1_ast,
        u2=u2_ast,
        u3=u3_ast,
        u4=u4_ast,
        roots=roots,
    )


def build_s_eq_c_eq_0_case(
    q: DepressedQuintic, inv: QuinticInvariants
) -> SEqualCZeroCaseAST:
    """Build the AST payload for §9.4.4: ``S = C = 0``.

    This branch splits as follows, exactly as in the notebook and chapter 9:

    - branch (A): ``D = E = 0``. Then ``q(x) = x^5 + f`` and we take
      ``u1^5 = -f`` with ``u2 = u3 = u4 = 0``.
    - branch (B): ``D != 0`` and ``E != 0``. We choose ``u2 = u4 = 0`` and use

          u1^5 = 8 D^3 / E,
          K2 = 0,
          K3 = -E / (4 D^2),
          K4 = 0.

    The degenerate mixed cases ``(D = 0, E != 0)`` and ``(D != 0, E = 0)`` are
    impossible in this branch for a separable solvable quintic; if they occur we
    treat them as an inconsistent input/branch classification.
    """
    branch = classify_branch(q, inv)
    if branch.tag != "s_eq_c_eq_0":
        raise ValueError("build_s_eq_c_eq_0_case() expects the branch S = C = 0.")

    D, E, f0 = q.D, q.E, q.f0

    if D == 0 and E == 0:
        u1_5_ast = qq(-f0)
        K2_ast = qq(0)
        K3_ast = qq(0)
        K4_ast = qq(0)

        u1_ast = root(5, u1_5_ast)
        u2_ast = qq(0)
        u3_ast = qq(0)
        u4_ast = qq(0)
        roots = _emit_quintic_roots_from_u(u1=u1_ast, u2=u2_ast, u3=u3_ast, u4=u4_ast)

        return SEqualCZeroTrivialCaseAST(
            u1_5=u1_5_ast,
            K2=K2_ast,
            K3=K3_ast,
            K4=K4_ast,
            u1=u1_ast,
            u2=u2_ast,
            u3=u3_ast,
            u4=u4_ast,
            roots=roots,
        )

    if D == 0 or E == 0:
        raise ValueError(
            "Impossible §9.4.4 mixed case: for S = C = 0 one must have either "
            "(D = E = 0) or (D != 0 and E != 0)."
        )

    u1_5_ast = qq(Fraction(8 * D**3, E))
    K2_ast = qq(0)
    K3_ast = qq(Fraction(-E, 4 * D**2))
    K4_ast = qq(0)

    u1_ast = root(5, u1_5_ast)
    u2_ast = qq(0)
    u3_ast = mul(K3_ast, pow_int(u1_ast, 3))
    u4_ast = qq(0)
    roots = _emit_quintic_roots_from_u(u1=u1_ast, u2=u2_ast, u3=u3_ast, u4=u4_ast)

    return SEqualCZeroNontrivialCaseAST(
        u1_5=u1_5_ast,
        K2=K2_ast,
        K3=K3_ast,
        K4=K4_ast,
        u1=u1_ast,
        u2=u2_ast,
        u3=u3_ast,
        u4=u4_ast,
        roots=roots,
    )


def build_from_quintic(q: DepressedQuintic, theta: Fraction | int | str) -> list[Expr]:
    """Return the canonical ordered radical roots for a solvable depressed quintic.

    This is the unified public dispatcher for the McClintock scheme currently
    implemented in this module.  It performs the rational control-flow steps
    (invariant computation, branch classification, and local zero-tests for the
    delicate square-root branches) and then delegates to the corresponding
    branch-local AST builder.

    Args:
        q: Depressed monic quintic in scaled form.
        theta: Rational initial datum extracted from the unique monic linear
            factor of the certified Dummit resolvent.

    Returns:
        The canonical ordered list ``[x1, x2, x3, x4, x5]`` as radical ASTs.
    """
    inv = compute_invariants(q, theta)
    branch = classify_branch(q, inv)

    if branch.tag == "general":
        lam = inv.lambda_if_s_nonzero
        if lam is None:
            raise ValueError("Inconsistent branch: missing lambda in S != 0 case.")
        r1_sq_aff_s = general_r1_sq(q, inv.s2, lam)
        if zero_test_affine_in_s(r1_sq_aff_s, inv.s2):
            return build_general_r1_zero_case(q, inv).roots
        return build_general_case(q, inv).roots

    if branch.tag == "s2_eq_c2":
        return build_s_eq_c_case(q, inv).roots

    if branch.tag == "s_eq_0_ct_ne_0":
        t2 = inv.t2_if_s0
        if t2 is None or t2 == 0:
            raise ValueError("Inconsistent branch: missing nonzero T^2 in S = 0 case.")
        r1_sq_aff_t = s0_r1_sq(q, t2)
        if zero_test_affine_in_t(r1_sq_aff_t, t2):
            return build_s_eq_0_r1_zero_case(q, inv).roots
        return build_s_eq_0_r1_nonzero_case(q, inv).roots

    if branch.tag == "s_eq_t_eq_0":
        return build_s_eq_t_eq_0_case(q, inv).roots

    if branch.tag == "s_eq_c_eq_0":
        return build_s_eq_c_eq_0_case(q, inv).roots

    raise ValueError(f"Unsupported McClintock branch: {branch.tag}")


def build(
    *, coeffs_desc: Iterable[Fraction | int | str], theta: Fraction | int | str
) -> list[Expr]:
    """Convenience wrapper around :func:`build_from_quintic`.

    Args:
        coeffs_desc: Descending coefficients of a monic depressed quintic.
        theta: Rational initial datum of the McClintock flow.

    Returns:
        The canonical ordered radical roots.
    """
    q = DepressedQuintic.from_desc_coeffs(coeffs_desc)
    return build_from_quintic(q, theta)


def build_from_linear_factor(
    *,
    coeffs_desc: Iterable[Fraction | int | str],
    linear_factor_desc: Iterable[Fraction | int | str],
) -> list[Expr]:
    """Convenience wrapper using a monic linear factor ``x - theta``.

    This is the natural entry point for the rule checker / engine path, where
    the initial datum is extracted from the unique monic linear factor of the
    certified resolvent factorization.
    """
    theta = root_from_monic_linear_desc(linear_factor_desc)
    return build(coeffs_desc=coeffs_desc, theta=theta)


__all__ = [
    "GeneralCaseAST",
    "SZeroR1NonzeroCaseAST",
    "SEqualCGenericCaseAST",
    "SEqualCDeMoivreCaseAST",
    "SEqualCCaseAST",
    "build_s_eq_c_case",
    "GeneralR1ZeroR2NonzeroCaseAST",
    "GeneralR1ZeroR2ZeroCaseAST",
    "GeneralR1ZeroCaseAST",
    "build_general_case",
    "build_general_r1_zero_case",
    "build_s_eq_0_r1_nonzero_case",
    "SZeroR1ZeroR2NonzeroCaseAST",
    "SZeroR1ZeroR2ZeroCaseAST",
    "SZeroR1ZeroCaseAST",
    "build_s_eq_0_r1_zero_case",
    "SEqualTZeroCaseAST",
    "build_s_eq_t_eq_0_case",
    "SEqualCZeroTrivialCaseAST",
    "SEqualCZeroNontrivialCaseAST",
    "SEqualCZeroCaseAST",
    "build_s_eq_c_eq_0_case",
    "build_from_quintic",
    "build",
    "build_from_linear_factor",
    "AffineInS",
    "AffineInT",
    "BranchInfo",
    "DepressedQuintic",
    "QuinticInvariants",
    "classify_branch",
    "compute_G0",
    "compute_G1",
    "compute_G2",
    "compute_G3",
    "compute_L0",
    "compute_L1",
    "compute_S2",
    "compute_S4",
    "compute_S6",
    "compute_invariants",
    "compute_lambda_from_s2",
    "compute_t2_when_s0",
    "general_r1_sq",
    "general_r2_sq",
    "general_t_sq",
    "is_square_fraction",
    "root_from_monic_linear_desc",
    "s0_r1_sq",
    "s0_r1r2_times_t",
    "s0_r2_expr_over_r1",
    "s0_r2_sq",
    "sqrt_fraction",
    "theta_to_s2",
    "zero_test_affine_in_s",
    "zero_test_affine_in_t",
]
