# src/opengalois/nodes/kappe_warren.py
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING, Any

from opengalois.codec.rationals import _frac_to_str
from opengalois.engine.context import _resolve_poly_desc_QQ
from opengalois.polyops.desc_qx import _leading, _trim_leading_zeros_desc

if TYPE_CHECKING:
    from opengalois.engine.context import EngineContext


PAIR_PRODUCTS_FAMILY = "deg4.cubic_x1x2_plus_x3x4"
PAIR_SUMS_FAMILY = "deg4.cubic_x1plusx2_times_x3plusx4"


def _normalize_quartic_resolvent_family(family: str | None) -> str:
    """Normalize the internal quartic resolvent family name.

    The node accepts the public computation-family ids used by ResolventNode and
    the corresponding object-id suffixes used in certificates.
    """
    if family is None:
        return PAIR_PRODUCTS_FAMILY

    value = str(family)
    if value in {
        PAIR_PRODUCTS_FAMILY,
        "mpoly.resolvent.deg4.cubic_x1x2_plus_x3x4",
        "pair-products",
        "pair_products",
    }:
        return PAIR_PRODUCTS_FAMILY
    if value in {
        PAIR_SUMS_FAMILY,
        "mpoly.resolvent.deg4.cubic_x1plusx2_times_x3plusx4",
        "pair-sums",
        "pair_sums",
    }:
        return PAIR_SUMS_FAMILY

    raise ValueError(f"Unknown quartic resolvent family: {family!r}")


def _extract_unique_linear_root(ctx: EngineContext, factor_refs: list[str]) -> Fraction:
    """Extract the unique rational root from the unique monic linear factor.

    The returned root is expressed in the coordinate of the selected resolvent
    family.  For the legacy pair-products family it is ``r0``; for the pair-sums
    family it is ``s0``.
    """
    linear_factors: list[list[Fraction]] = []
    for ref in factor_refs:
        coeffs = _trim_leading_zeros_desc(_resolve_poly_desc_QQ(ctx, ref))
        if len(coeffs) == 2:  # degree 1
            linear_factors.append(coeffs)

    if len(linear_factors) != 1:
        raise ValueError(
            "KappeWarrenNode expects the resolvent factorization to contain "
            "exactly one linear factor."
        )

    lin = linear_factors[0]
    if lin[0] != 1:
        raise ValueError("KappeWarrenNode expects the unique linear factor to be monic.")

    # lin = x - root = [1, -root]
    return -lin[1]


@dataclass(frozen=True)
class KappeWarrenNode:
    """Compute the Kappe-Warren auxiliary square tests for quartic C4/D4.

    The node is family-aware.

    For the legacy pair-products resolvent

        r = x1*x2 + x3*x4,

    the linear resolvent root is directly ``r0`` and ``s0=b-r0``.

    For the new pair-sums resolvent

        s = (x1+x2)(x3+x4),

    the linear resolvent root is ``s0`` and ``r0=b-s0``.

    In both coordinates the auxiliary values are computed uniformly as

        w1 = (a^2 - 4*s0) * Δ
        w2 = (r0^2 - 4*d) * Δ

    for the monic quartic x^4 + a*x^3 + b*x^2 + c*x + d.
    """

    w_obj_prefix: str = "rat.kw."

    def run(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        resolvent_ref: str,
        factor_refs: list[str],
        resolvent_family: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Compute Kappe-Warren auxiliary values and emit square/non-square facts."""
        family = _normalize_quartic_resolvent_family(resolvent_family)

        out_map = ctx.cache.setdefault("_kw_out_by_poly", {})
        if not isinstance(out_map, dict):
            raise TypeError("ctx.cache['_kw_out_by_poly'] must be a dict")

        cache_key = (poly_ref, resolvent_ref, family)
        cached = out_map.get(cache_key)
        if isinstance(cached, dict):
            return [], dict(cached)

        f_desc = _trim_leading_zeros_desc(_resolve_poly_desc_QQ(ctx, poly_ref))
        if not f_desc:
            raise ValueError("Zero polynomial")
        if len(f_desc) - 1 != 4:
            raise ValueError("KappeWarrenNode expects a degree-4 polynomial")

        lc = _leading(f_desc)
        if lc == 0:
            raise ValueError("Leading coefficient is zero")

        # Monic quartic: x^4 + a x^3 + b x^2 + c x + d
        fm = [coeff / lc for coeff in f_desc]
        _, a, b, c, d = fm
        _ = c  # not used by the Kappe-Warren criteria

        disc_map = ctx.cache.get("_disc_out_by_poly", {})
        if not isinstance(disc_map, dict) or poly_ref not in disc_map:
            raise ValueError(
                f"Missing DiscriminantNode output for {poly_ref!r}. "
                "Run DiscriminantNode before KappeWarrenNode."
            )
        disc_out = disc_map[poly_ref]
        if not isinstance(disc_out, dict):
            raise TypeError("DiscriminantNode cached output must be a dict")

        disc_value_raw = disc_out.get("disc_value")
        if not isinstance(disc_value_raw, str) or not disc_value_raw:
            raise ValueError("DiscriminantNode output is missing a valid disc_value")
        delta = Fraction(disc_value_raw)

        if not isinstance(factor_refs, list) or not all(
            isinstance(x, str) and x for x in factor_refs
        ):
            raise TypeError("factor_refs must be a non-empty list[str]")

        root0 = _extract_unique_linear_root(ctx, factor_refs)
        if family == PAIR_PRODUCTS_FAMILY:
            r0 = root0
            s0 = b - r0
        elif family == PAIR_SUMS_FAMILY:
            s0 = root0
            r0 = b - s0
        else:  # pragma: no cover - protected by normalization above.
            raise AssertionError(f"Unhandled quartic resolvent family: {family!r}")

        w1 = (a * a - Fraction(4, 1) * s0) * delta
        w2 = (r0 * r0 - Fraction(4, 1) * d) * delta

        w1_id = ctx.objects.new_id(self.w_obj_prefix)
        w2_id = ctx.objects.new_id(self.w_obj_prefix)
        ctx.objects.put_rat(w1_id, w1)
        ctx.objects.put_rat(w2_id, w2)

        facts: list[dict[str, Any]] = []

        # ---- w1 ----
        w1_nodes, w1_out = ctx.registry.square.run(ctx, rat_ref=w1_id)
        facts.extend(w1_nodes)

        w1_decision = str(w1_out.get("decision", ""))
        w1_facts_raw = w1_out.get("facts", {})
        if not isinstance(w1_facts_raw, dict):
            raise TypeError("SquareNode out['facts'] for w1 must be a dict")

        if w1_decision == "square":
            w1_sqrt_ref_raw = w1_out.get("sqrt_ref")
            w1_sqrt_value_raw = w1_out.get("sqrt_value")
            if not isinstance(w1_sqrt_ref_raw, str) or not w1_sqrt_ref_raw:
                raise ValueError("SquareNode output for w1 is missing a valid sqrt_ref")
            if not isinstance(w1_sqrt_value_raw, str) or not w1_sqrt_value_raw:
                raise ValueError("SquareNode output for w1 is missing a valid sqrt_value")

            fid_w1_sqrt_raw = w1_facts_raw.get("sqrt")
            fid_w1_sq_raw = w1_facts_raw.get("square")
            if fid_w1_sqrt_raw is None or fid_w1_sq_raw is None:
                raise ValueError("SquareNode square branch for w1 is missing fact ids")

            fid_w1_sqrt = str(fid_w1_sqrt_raw)
            fid_w1_sq = str(fid_w1_sq_raw)
            if not fid_w1_sqrt or not fid_w1_sq:
                raise ValueError("SquareNode square branch for w1 returned empty fact ids")

            w1_facts: dict[str, str] = {"sqrt": fid_w1_sqrt, "square": fid_w1_sq}
            w1_sqrt_ref = w1_sqrt_ref_raw
            w1_sqrt_value = w1_sqrt_value_raw

        elif w1_decision == "nonsquare":
            fid_w1_ns_raw = w1_facts_raw.get("non_square")
            if fid_w1_ns_raw is None:
                raise ValueError("SquareNode nonsquare branch for w1 is missing fact ids")

            fid_w1_ns = str(fid_w1_ns_raw)
            if not fid_w1_ns:
                raise ValueError("SquareNode nonsquare branch for w1 returned an empty fact id")

            w1_facts = {"non_square": fid_w1_ns}
            w1_sqrt_ref = None
            w1_sqrt_value = None

        else:
            raise ValueError(f"Unexpected square decision for w1: {w1_decision!r}")

        # ---- w2 ----
        w2_nodes, w2_out = ctx.registry.square.run(ctx, rat_ref=w2_id)
        facts.extend(w2_nodes)

        w2_decision = str(w2_out.get("decision", ""))
        w2_facts_raw = w2_out.get("facts", {})
        if not isinstance(w2_facts_raw, dict):
            raise TypeError("SquareNode out['facts'] for w2 must be a dict")

        if w2_decision == "square":
            w2_sqrt_ref_raw = w2_out.get("sqrt_ref")
            w2_sqrt_value_raw = w2_out.get("sqrt_value")
            if not isinstance(w2_sqrt_ref_raw, str) or not w2_sqrt_ref_raw:
                raise ValueError("SquareNode output for w2 is missing a valid sqrt_ref")
            if not isinstance(w2_sqrt_value_raw, str) or not w2_sqrt_value_raw:
                raise ValueError("SquareNode output for w2 is missing a valid sqrt_value")

            fid_w2_sqrt_raw = w2_facts_raw.get("sqrt")
            fid_w2_sq_raw = w2_facts_raw.get("square")
            if fid_w2_sqrt_raw is None or fid_w2_sq_raw is None:
                raise ValueError("SquareNode square branch for w2 is missing fact ids")

            fid_w2_sqrt = str(fid_w2_sqrt_raw)
            fid_w2_sq = str(fid_w2_sq_raw)
            if not fid_w2_sqrt or not fid_w2_sq:
                raise ValueError("SquareNode square branch for w2 returned empty fact ids")

            w2_facts: dict[str, str] = {"sqrt": fid_w2_sqrt, "square": fid_w2_sq}
            w2_sqrt_ref = w2_sqrt_ref_raw
            w2_sqrt_value = w2_sqrt_value_raw

        elif w2_decision == "nonsquare":
            fid_w2_ns_raw = w2_facts_raw.get("non_square")
            if fid_w2_ns_raw is None:
                raise ValueError("SquareNode nonsquare branch for w2 is missing fact ids")

            fid_w2_ns = str(fid_w2_ns_raw)
            if not fid_w2_ns:
                raise ValueError("SquareNode nonsquare branch for w2 returned an empty fact id")

            w2_facts = {"non_square": fid_w2_ns}
            w2_sqrt_ref = None
            w2_sqrt_value = None

        else:
            raise ValueError(f"Unexpected square decision for w2: {w2_decision!r}")

        out = {
            "poly_ref": poly_ref,
            "resolvent_ref": resolvent_ref,
            "resolvent_family": family,
            "root_value": _frac_to_str(root0),
            "r0_value": _frac_to_str(r0),
            "s0_value": _frac_to_str(s0),
            "w1_ref": w1_id,
            "w1_value": _frac_to_str(w1),
            "w1_decision": w1_decision,
            "w1_sqrt_ref": w1_sqrt_ref,
            "w1_sqrt_value": w1_sqrt_value,
            "w1_facts": w1_facts,
            "w2_ref": w2_id,
            "w2_value": _frac_to_str(w2),
            "w2_decision": w2_decision,
            "w2_sqrt_ref": w2_sqrt_ref,
            "w2_sqrt_value": w2_sqrt_value,
            "w2_facts": w2_facts,
        }

        out_map[cache_key] = dict(out)
        return facts, out
