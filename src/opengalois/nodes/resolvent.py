# src/opengalois/nodes/resolvent.py
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING, Any

from opengalois.engine.context import _next_fact_id, _resolve_poly_desc_QQ
from opengalois.polyops.desc_qx import _leading, _trim_leading_zeros_desc

if TYPE_CHECKING:
    from opengalois.engine.context import EngineContext



def _ensure_deg4_cubic_family_mpoly(ctx: EngineContext) -> str:
    """Ensure the canonical MPolyQQ object for x1*x2 + x3*x4 exists.

    Returns:
        str: Deterministic object id for the fixed multivariate polynomial.
    """
    obj_id = "mpoly.resolvent.deg4.cubic_x1x2_plus_x3x4"
    ctx.objects.put_mpoly(
        obj_id,
        nvars=4,
        terms=[
            ([1, 1, 0, 0], Fraction(1, 1)),
            ([0, 0, 1, 1], Fraction(1, 1)),
        ],
    )
    return obj_id



def _ensure_deg4_cubic_family_alt_mpoly(ctx: EngineContext) -> str:
    """Ensure the canonical MPolyQQ object for (x1+x2)(x3+x4) exists.

    Returns:
        str: Deterministic object id for the fixed multivariate polynomial.
    """
    obj_id = "mpoly.resolvent.deg4.cubic_x1plusx2_times_x3plusx4"
    ctx.objects.put_mpoly(
        obj_id,
        nvars=4,
        terms=[
            ([1, 0, 1, 0], Fraction(1, 1)),
            ([1, 0, 0, 1], Fraction(1, 1)),
            ([0, 1, 1, 0], Fraction(1, 1)),
            ([0, 1, 0, 1], Fraction(1, 1)),
        ],
    )
    return obj_id



def _ensure_deg5_sextic_dummit_family_mpoly(ctx: EngineContext) -> str:
    """Ensure the canonical MPolyQQ object for Dummit's F20 sextic family exists."""
    obj_id = "mpoly.resolvent.deg5.sextic_dummit_F20"
    ctx.objects.put_mpoly(
        obj_id,
        nvars=5,
        terms=[
            ([2, 1, 0, 0, 1], Fraction(1, 1)),
            ([2, 0, 1, 1, 0], Fraction(1, 1)),
            ([1, 2, 1, 0, 0], Fraction(1, 1)),
            ([1, 1, 0, 2, 0], Fraction(1, 1)),
            ([1, 0, 2, 0, 1], Fraction(1, 1)),
            ([1, 0, 0, 1, 2], Fraction(1, 1)),
            ([0, 2, 0, 1, 1], Fraction(1, 1)),
            ([0, 1, 2, 1, 0], Fraction(1, 1)),
            ([0, 1, 1, 0, 2], Fraction(1, 1)),
            ([0, 0, 1, 2, 1], Fraction(1, 1)),
        ],
    )
    return obj_id



def _compute_deg4_cubic_x1x2_plus_x3x4(f_desc: list[Fraction]) -> list[Fraction]:
    """Compute the degree-4 cubic resolvent attached to x1*x2 + x3*x4.

    If the associated monic quartic is

        x^4 + a x^3 + b x^2 + c x + d,

    then the resolvent is

        x^3 - b x^2 + (a c - 4 d) x - (a^2 d + c^2 - 4 b d).

    The input polynomial need not be monic; monicization is performed internally.

    Args:
        f_desc: Degree-4 polynomial in descending QQ coefficients.

    Returns:
        list[Fraction]: Descending QQ coefficients of the cubic resolvent.

    Raises:
        ValueError: If the input is zero or not degree 4.
    """
    f = _trim_leading_zeros_desc(f_desc)
    if not f:
        raise ValueError("Zero polynomial")
    if len(f) - 1 != 4:
        raise ValueError("Expected a degree-4 polynomial")

    lc = _leading(f)
    if lc == 0:
        raise ValueError("Leading coefficient is zero")

    fm = [c / lc for c in f]
    _, a, b, c, d = fm

    return [
        Fraction(1, 1),
        -b,
        a * c - Fraction(4, 1) * d,
        -(a * a * d + c * c - Fraction(4, 1) * b * d),
    ]



def _compute_deg4_cubic_x1plusx2_times_x3plusx4(f_desc: list[Fraction]) -> list[Fraction]:
    """Compute the quartic cubic resolvent attached to (x1+x2)(x3+x4).

    If the associated monic quartic is

        x^4 + a x^3 + b x^2 + c x + d,

    then the resolvent is

        x^3 - 2*b*x^2 + (b^2 + a*c - 4*d)*x + (a^2*d - a*b*c + c^2).

    The input polynomial need not be monic; monicization is performed internally.

    Args:
        f_desc: Degree-4 polynomial in descending QQ coefficients.

    Returns:
        list[Fraction]: Descending QQ coefficients of the cubic resolvent.

    Raises:
        ValueError: If the input is zero or not degree 4.
    """
    f = _trim_leading_zeros_desc(f_desc)
    if not f:
        raise ValueError("Zero polynomial")
    if len(f) - 1 != 4:
        raise ValueError("Expected a degree-4 polynomial")

    lc = _leading(f)
    if lc == 0:
        raise ValueError("Leading coefficient is zero")

    fm = [c / lc for c in f]
    _, a, b, c, d = fm

    return [
        Fraction(1, 1),
        -Fraction(2, 1) * b,
        b * b + a * c - Fraction(4, 1) * d,
        a * a * d - a * b * c + c * c,
    ]



def _compute_deg5_sextic_dummit_F20(g_desc: list[Fraction]) -> list[Fraction]:
    """Compute Dummit's sextic resolvent for a depressed monic quintic.

    The input must have shape
        x^5 + p x^3 + q x^2 + r x + s.
    """
    g = _trim_leading_zeros_desc(g_desc)
    if not g:
        raise ValueError("Zero polynomial")
    if len(g) != 6:
        raise ValueError("Expected a degree-5 polynomial")
    if g[0] != Fraction(1, 1):
        raise ValueError("Dummit sextic resolvent expects a monic quintic")
    if g[1] != 0:
        raise ValueError("Dummit sextic resolvent expects a depressed quintic")

    _, _, p, q, r, s = g
    return _trim_leading_zeros_desc(
        [
            Fraction(1, 1),
            8 * r,
            2 * p * q * q - 6 * p * p * r + 40 * r * r - 50 * q * s,
            (
                -2 * q**4
                + 21 * p * q * q * r
                - 40 * p * p * r * r
                + 160 * r**3
                - 15 * p * p * q * s
                - 400 * q * r * s
                + 125 * p * s * s
            ),
            (
                p * p * q**4
                - 6 * p**3 * q * q * r
                - 8 * q**4 * r
                + 9 * p**4 * r * r
                + 76 * p * q * q * r * r
                - 136 * p * p * r**3
                + 400 * r**4
                - 50 * p * q**3 * s
                + 90 * p * p * q * r * s
                - 1400 * q * r * r * s
                + 625 * q * q * s * s
                + 500 * p * r * s * s
            ),
            (
                -2 * p * q**6
                + 19 * p * p * q**4 * r
                - 51 * p**3 * q * q * r * r
                + 3 * q**4 * r * r
                + 32 * p**4 * r**3
                + 76 * p * q * q * r**3
                - 256 * p * p * r**4
                + 512 * r**5
                - 31 * p**3 * q**3 * s
                - 58 * q**5 * s
                + 117 * p**4 * q * r * s
                + 105 * p * q**3 * r * s
                + 260 * p * p * q * r * r * s
                - 2400 * q * r**3 * s
                - 108 * p**5 * s * s
                - 325 * p * p * q * q * s * s
                + 525 * p**3 * r * s * s
                + 2750 * q * q * r * s * s
                - 500 * p * r * r * s * s
                + 625 * p * q * s**3
                - 3125 * s**4
            ),
            (
                q**8
                - 13 * p * q**6 * r
                + p**5 * q * q * r * r
                + 65 * p * p * q**4 * r * r
                - 4 * p**6 * r**3
                - 128 * p**3 * q * q * r**3
                + 17 * q**4 * r**3
                + 48 * p**4 * r**4
                - 16 * p * q * q * r**4
                - 192 * p * p * r**5
                + 256 * r**6
                - 4 * p**5 * q**3 * s
                - 12 * p * p * q**5 * s
                + 18 * p**6 * q * r * s
                + 12 * p**3 * q**3 * r * s
                - 124 * q**5 * r * s
                + 196 * p**4 * q * r * r * s
                + 590 * p * q**3 * r * r * s
                - 160 * p * p * q * r**3 * s
                - 1600 * q * r**4 * s
                - 27 * p**7 * s * s
                - 150 * p**4 * q * q * s * s
                - 125 * p * q**4 * s * s
                - 99 * p**5 * r * s * s
                - 725 * p * p * q * q * r * s * s
                + 1200 * p**3 * r * r * s * s
                + 3250 * q * q * r * r * s * s
                - 2000 * p * r**3 * s * s
                - 1250 * p * q * r * s**3
                + 3125 * p * p * s**4
                - 9375 * r * s**4
            ),
        ]
    )


@dataclass(frozen=True)
class ResolventNode:
    """Engine node for supported fixed resolvent families.

    Supported families:
      - degree 4 -> cubic resolvent for x1*x2 + x3*x4
      - degree 4 -> cubic resolvent for (x1+x2)(x3+x4)
      - degree 5 -> Dummit's sextic resolvent for the F20 family
    """

    pred: str = "ResolventQQ"

    rule_deg4: str = "resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1"
    rule_deg4_alt: str = "resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1"
    rule_deg5: str = "resolvent.QQ.compute.deg5.sextic_dummit_F20@1"

    out_prefix: str = "poly.resolvent."
    family_deg4: str = "deg4.cubic_x1x2_plus_x3x4"
    family_deg4_alt: str = "deg4.cubic_x1plusx2_times_x3plusx4"
    family_deg5: str = "deg5.sextic_dummit_F20"

    def run(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        family: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Compute a supported fixed resolvent family for ``poly_ref``.

        Args:
            ctx: Engine context.
            poly_ref: Polynomial reference id.
            family: Optional explicit resolvent family to compute. If None, the family
                is chosen by degree using the historical defaults.

        Returns:
            tuple[list[dict[str, Any]], dict[str, Any]]:
                - facts emitted by this node
                - non-normative output metadata
        """
        f_desc = _trim_leading_zeros_desc(_resolve_poly_desc_QQ(ctx, poly_ref))
        if not f_desc:
            raise ValueError("Zero polynomial")
        deg = len(f_desc) - 1

        if family is None:
            if deg == 4:
                family_name = self.family_deg4
            elif deg == 5:
                family_name = self.family_deg5
            else:
                raise NotImplementedError(
                    f"ResolventNode has no default resolvent family for degree {deg}."
                )
        else:
            family_name = family

        out_map = ctx.cache.setdefault("_resolvent_out_by_poly", {})
        if not isinstance(out_map, dict):
            raise TypeError("ctx.cache['_resolvent_out_by_poly'] must be a dict")

        cache_key = (poly_ref, family_name)
        cached = out_map.get(cache_key)
        if isinstance(cached, dict):
            return [], dict(cached)

        degree_map = ctx.cache.get("_degree_fact_by_poly", {})
        if not isinstance(degree_map, dict) or poly_ref not in degree_map:
            raise ValueError(
                f"Missing Degree premise for {poly_ref!r}. "
                "Run ReducibilityNode (or emit Degree) before computing resolvents."
            )
        degree_fact_id = str(degree_map[poly_ref])
        if not degree_fact_id:
            raise ValueError("Empty Degree fact id")

        if family_name == self.family_deg4:
            if deg != 4:
                raise ValueError("Requested quartic resolvent family for a non-quartic polynomial.")
            p_ref = _ensure_deg4_cubic_family_mpoly(ctx)
            r_coeffs = _compute_deg4_cubic_x1x2_plus_x3x4(f_desc)
            rule_id = self.rule_deg4
            statement = "Degree-4 cubic resolvent over QQ for the family x1*x2 + x3*x4."
        elif family_name == self.family_deg4_alt:
            if deg != 4:
                raise ValueError("Requested Ferrari quartic resolvent "
                                 "family for a non-quartic polynomial.")
            p_ref = _ensure_deg4_cubic_family_alt_mpoly(ctx)
            r_coeffs = _compute_deg4_cubic_x1plusx2_times_x3plusx4(f_desc)
            rule_id = self.rule_deg4_alt
            statement = (
                "Degree-4 cubic resolvent over QQ for the family (x1+x2)(x3+x4)."
            )
        elif family_name == self.family_deg5:
            if deg != 5:
                raise ValueError("Requested Dummit sextic family for a non-quintic polynomial.")
            p_ref = _ensure_deg5_sextic_dummit_family_mpoly(ctx)
            r_coeffs = _compute_deg5_sextic_dummit_F20(f_desc)
            rule_id = self.rule_deg5
            statement = "Degree-5 sextic Dummit resolvent over QQ for the canonical F20 family."
        else:
            raise NotImplementedError(f"Unsupported resolvent family: {family_name!r}")

        r_ref = ctx.objects.new_id(self.out_prefix)
        ctx.objects.put_poly(r_ref, r_coeffs)

        fid = _next_fact_id(ctx)
        fact = {
            "id": fid,
            "claim": {
                "pred": self.pred,
                "args": [{"ref": r_ref}, {"ref": poly_ref}, {"ref": p_ref}],
            },
            "rule": rule_id,
            "premises": [degree_fact_id],
            "statement": statement,
        }

        out = {
            "poly_ref": poly_ref,
            "family": family_name,
            "p_ref": p_ref,
            "resolvent_ref": r_ref,
            "facts": {"resolvent": fid},
        }
        out_map[cache_key] = dict(out)
        return [fact], out
