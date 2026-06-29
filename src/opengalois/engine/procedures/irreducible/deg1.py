from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from opengalois.engine.context import EngineContext, _next_fact_id, _resolve_poly_desc_QQ
from opengalois.engine.procedures.procedure import ProcedureResult
from opengalois.radicals.schemes import deg1_trivial


@dataclass(frozen=True)
class IrreducibleDeg1Procedure:
    """Degree-1 procedure.

    The procedure keeps the existing degree-1 Galois-group emission and, in a
    second local step, emits the canonical ``RadicalRoots`` fact using the
    degree-1 trivial scheme.
    """

    rule_id: str = "galois_group.QQ.deg1.trivial@1"
    pred: str = "GaloisGroup"
    group_obj_id: str = "group.trivial"
    radical_roots_rule_id: str = "radical_roots.QQ.deg1.trivial@1"

    def run(self, ctx: EngineContext, *, poly_ref: str) -> ProcedureResult:
        """Run the degree-1 irreducible procedure.

        Args:
            ctx: Engine context.
            poly_ref: Reference to the polynomial object.

        Returns:
            Procedure result containing the degree-1 Galois-group fact and the
            canonical degree-1 ``RadicalRoots`` fact.

        Raises:
            ValueError: If the required degree premise is missing or if the
                polynomial reference does not decode to a linear polynomial.
        """
        ctx.objects.put_groupid(
            self.group_obj_id,
            system="smallgroup",
            order=1,
            index=1,
            alias="Trivial",
        )

        degree_map = ctx.cache.get("_degree_fact_by_poly", {})
        if not isinstance(degree_map, dict) or poly_ref not in degree_map:
            raise ValueError(
                f"Missing Degree premise for {poly_ref!r}. "
                "Emit Degree(poly_ref, 1) before IrreducibleDeg1Procedure."
            )
        degree_fact_id = str(degree_map[poly_ref])
        if not degree_fact_id:
            raise ValueError("Empty Degree fact id for degree-1 input.")

        facts: list[dict[str, Any]] = []

        group_fact = {
            "id": _next_fact_id(ctx),
            "claim": {
                "pred": self.pred,
                "args": [{"ref": poly_ref}, {"ref": self.group_obj_id}],
            },
            "rule": self.rule_id,
            "premises": [degree_fact_id],
            "statement": "Degree-1 polynomial has trivial Galois group.",
        }
        facts.append(group_fact)

        facts.extend(
            self._emit_radical_roots(
                ctx,
                poly_ref=poly_ref,
                degree_fact_id=degree_fact_id,
            )
        )

        out = {
            "decision": "galois_group",
            "group": "Trivial",
            "group_ref": self.group_obj_id,
        }
        return ProcedureResult(facts=facts, out=out)

    def _emit_radical_roots(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        degree_fact_id: str,
    ) -> list[dict[str, Any]]:
        """Emit the canonical degree-1 ``RadicalRoots`` fact.

        Args:
            ctx: Engine context.
            poly_ref: Reference to the linear polynomial.
            degree_fact_id: Verified ``Degree(f,1)`` fact id.

        Returns:
            Single-element list containing the emitted ``RadicalRoots`` fact.

        Raises:
            ValueError: If the polynomial does not decode to a non-degenerate
                linear polynomial.
        """
        coeffs = _resolve_poly_desc_QQ(ctx, poly_ref)
        if len(coeffs) != 2:
            raise ValueError(
                "IrreducibleDeg1Procedure expected a linear polynomial with exactly 2 coefficients"
            )
        a, b = coeffs
        if a == 0:
            raise ValueError("IrreducibleDeg1Procedure requires a non-zero leading coefficient")

        expr_refs: list[str] = []
        for expr in deg1_trivial.build(a=a, b=b):
            expr_obj_id = ctx.objects.new_id("rexpr.deg1.")
            ctx.objects.put_radical_expr(expr_obj_id, expr)
            expr_refs.append(expr_obj_id)

        roots_obj_id = ctx.objects.new_id("rlist.deg1.")
        ctx.objects.put_radical_expr_list(roots_obj_id, expr_refs)

        radical_fact = {
            "id": _next_fact_id(ctx),
            "claim": {
                "pred": "RadicalRoots",
                "args": [{"ref": poly_ref}, {"ref": roots_obj_id}],
            },
            "rule": self.radical_roots_rule_id,
            "premises": [degree_fact_id],
            "statement": "Canonical degree-1 radical root over QQ.",
        }
        return [radical_fact]
