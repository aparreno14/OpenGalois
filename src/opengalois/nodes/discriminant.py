# src/opengalois/nodes/discriminant.py
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING, Any

from opengalois.codec.rationals import _frac_to_str
from opengalois.engine.context import _next_fact_id, _resolve_poly_desc_QQ
from opengalois.polyops.desc_qx import _trim_leading_zeros_desc

if TYPE_CHECKING:
    from opengalois.engine.context import EngineContext


def _det_fraction_matrix(a: list[list[Fraction]]) -> Fraction:
    """Exact determinant over Q using Gaussian elimination (Fractions)."""
    n = len(a)
    if n == 0:
        return Fraction(1)
    if any(len(row) != n for row in a):
        raise ValueError("det: matrix must be square")

    m = [row[:] for row in a]
    det = Fraction(1)
    sign = 1

    for i in range(n):
        piv = None
        for r in range(i, n):
            if m[r][i] != 0:
                piv = r
                break
        if piv is None:
            return Fraction(0)
        if piv != i:
            m[i], m[piv] = m[piv], m[i]
            sign *= -1

        pivot = m[i][i]
        det *= pivot

        for r in range(i + 1, n):
            if m[r][i] == 0:
                continue
            factor = m[r][i] / pivot
            for c in range(i, n):
                m[r][c] -= factor * m[i][c]

    return det * sign


def _poly_derivative_desc(p: list[Fraction]) -> list[Fraction]:
    """Derivative of polynomial in descending-degree order."""
    p = _trim_leading_zeros_desc(p)
    deg = len(p) - 1
    if deg <= 0:
        return [Fraction(0)]
    out: list[Fraction] = []
    for i, a in enumerate(p[:-1]):
        out.append(a * (deg - i))
    return _trim_leading_zeros_desc(out) or [Fraction(0)]


def _resultant_sylvester_desc(f: list[Fraction], g: list[Fraction]) -> Fraction:
    """Res(f,g) via Sylvester determinant (exact over Q)."""
    f = _trim_leading_zeros_desc(f)
    g = _trim_leading_zeros_desc(g)
    mdeg = len(f) - 1
    ndeg = len(g) - 1

    # Convention: resultant with zero polynomial is 0.
    if (mdeg == 0 and f[0] == 0) or (ndeg == 0 and g[0] == 0):
        return Fraction(0)

    size = mdeg + ndeg
    S: list[list[Fraction]] = []

    # ndeg rows: shifted copies of f
    for i in range(ndeg):
        row = [Fraction(0)] * size
        row[i : i + (mdeg + 1)] = f
        S.append(row)

    # mdeg rows: shifted copies of g
    for i in range(mdeg):
        row = [Fraction(0)] * size
        row[i : i + (ndeg + 1)] = g
        S.append(row)

    return _det_fraction_matrix(S)


def _discriminant_QQ_desc(f: list[Fraction]) -> Fraction:
    """Disc(f) = (-1)^(n(n-1)/2) * Res(f,f') / lc(f). Convention: deg=1 -> 1."""
    f = _trim_leading_zeros_desc(f)
    n = len(f) - 1
    if n < 0:
        raise ValueError("discriminant: zero polynomial")
    if n == 0:
        # Not expected.
        return Fraction(0)
    if n == 1:
        return Fraction(1)

    lc = f[0]
    if lc == 0:
        raise ValueError("discriminant: leading coefficient is zero")

    fp = _poly_derivative_desc(f)
    res = _resultant_sylvester_desc(f, fp)
    sgn = -1 if ((n * (n - 1) // 2) % 2) else 1
    return Fraction(sgn) * (res / lc)


@dataclass(frozen=True)
class DiscriminantNode:
    """Compute the exact discriminant Disc(f) over QQ.

    Emits only:
      - Discriminant(f, D)

    Square/non-square classification of D is handled separately by SquareNode.
    Any lifted predicates such as DiscSquareQQ(f) / DiscNonSquareQQ(f) belong
    to higher-level procedures that explicitly compose:

      Discriminant(f, D) + [IsSquareQQ(D) | NonSquareQQ(D)].
    """

    disc_pred: str = "Discriminant"
    disc_rule: str = "disc.QQ.compute@1"

    # Object-id prefix (deterministic by execution order)
    disc_obj_prefix: str = "rat.disc."

    def run(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Execute discriminant computation for a polynomial over QQ.

        Args:
            ctx: Engine context for the procedure.
            poly_ref: Object reference for the polynomial.

        Returns:
            Tuple of (facts, out) where:
                - facts: List containing the generated Discriminant fact node.
                - out: Dictionary with the discriminant reference and value.

        Raises:
            ValueError: If the polynomial has degree < 1.
        """
        # Idempotence: if already computed for this poly_ref, do not re-emit facts.
        out_map = ctx.cache.setdefault("_disc_out_by_poly", {})
        if isinstance(out_map, dict) and poly_ref in out_map:
            return [], dict(out_map[poly_ref])

        pQ = _resolve_poly_desc_QQ(ctx, poly_ref)
        pQ = _trim_leading_zeros_desc(pQ)
        if len(pQ) < 2:
            raise ValueError("DiscriminantNode expects deg(f) >= 1 (non-constant).")

        deg = len(pQ) - 1
        if deg > 5:
            raise ValueError(
                f"DiscriminantNode currently supports deg(f) ≤ 5 for QQ discriminants; "
                f"got deg(f) = {deg}."
            )
        D = _discriminant_QQ_desc(pQ)

        # Store D as RatQQ object
        D_id = ctx.objects.new_id(self.disc_obj_prefix)
        ctx.objects.put_rat(D_id, D)

        facts: list[dict[str, Any]] = []

        # Fact: Discriminant(f,D)
        fid_disc = _next_fact_id(ctx)
        facts.append(
            {
                "id": fid_disc,
                "claim": {"pred": self.disc_pred, "args": [{"ref": poly_ref}, {"ref": D_id}]},
                "rule": self.disc_rule,
                "premises": [],
                "statement": "Discriminant over QQ computed via resultant with the derivative.",
            }
        )

        out = {
            "poly_ref": poly_ref,
            "disc_ref": D_id,
            "disc_value": _frac_to_str(D),
            "facts": {
                "discriminant": fid_disc,
            },
        }

        # Cache out for re-use without duplicating facts
        if isinstance(out_map, dict):
            out_map[poly_ref] = dict(out)
        return facts, out