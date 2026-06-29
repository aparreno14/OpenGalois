# src/opengalois/nodes/normalize.py
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING, Any

from opengalois.codec.rationals import _frac_to_str

if TYPE_CHECKING:
    from ..engine.context import EngineContext

from ..engine.context import _next_fact_id, _resolve_poly_desc_QQ
from ..polyops.desc_qx import _leading, _mul_scalar_desc, _shift_desc, _trim_leading_zeros_desc


@dataclass(frozen=True)
class NormalizeDepressedMonicQQ:
    """Node that produces a v3 fact: DepressedMonicEq(f, g) with checkable evidence.

    v3 mapping:
      - claim.pred  = "DepressedMonicEq"
      - rule        = "normalize.depressed_monic_QQ@1"
      - evidence    = {"tschirnhaus_shift": t, "monic_scale": a_n}
      - g stored as a v3 PolyQQ object with id `out_id`
    """
    rule_id: str = "normalize.depressed_monic_QQ@1"
    pred: str = "DepressedMonicEq"
    out_id: str = "poly.depressed_monic"

    def run(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        out_id: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Executes the normalization transformation and returns a v3 FactNode.

        Args:
            ctx: Engine context.
            poly_ref: Reference id of the input polynomial (often "$input").
            out_id: Optional target identifier for the normalized polynomial.
                If omitted, the node default ``self.out_id`` is used.

        Returns:
            (fact_node, out) where:
              - fact_node is a v3 FactNode dict
              - out maps "poly_ref" to the output polynomial reference
        """
        inp_poly: list[Fraction] = _resolve_poly_desc_QQ(ctx, poly_ref)

        f = _trim_leading_zeros_desc(inp_poly)
        a_n = _leading(f)
        n = len(f) - 1

        # f_m = f / a_n
        f_m = _mul_scalar_desc(f, Fraction(1, 1) / a_n)

        # t = coeff(x^{n-1}) / n
        a_nm1 = f_m[1] if len(f_m) >= 2 else Fraction(0, 1)
        t = a_nm1 / n

        # g(x) = f_m(x - t)
        g = _shift_desc(f_m, -t)

        target_out_id = out_id if out_id is not None else self.out_id

        # Store output polynomial as an object
        ctx.objects.put_poly(target_out_id, g)

        # Degree premise must already exist (emitted by ReducibilityNode for the same poly_ref)
        degree_map = ctx.cache.get("_degree_fact_by_poly", {})
        if not isinstance(degree_map, dict) or poly_ref not in degree_map:
            raise ValueError(
                f"Missing Degree premise for {poly_ref!r}. "
                "Run ReducibilityNode (or emit Degree) before normalization."
            )
        degree_fact_id = str(degree_map[poly_ref])

        fact_id = _next_fact_id(ctx)
        fact_node: dict[str, Any] = {
            "id": fact_id,
            "claim": {
                "pred": self.pred,
                "args": [{"ref": poly_ref}, {"ref": target_out_id}],
            },
            "rule": self.rule_id,
            "premises": [degree_fact_id],
            "evidence": {
                "tschirnhaus_shift": _frac_to_str(t),
                "monic_scale": _frac_to_str(a_n),
            },
            "statement": "Depressed-monic normalization over Q:"
            " monicize then apply x -> x - t to kill x^(n-1).",
        }
        return fact_node, {"poly_ref": target_out_id}