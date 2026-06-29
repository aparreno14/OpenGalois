from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from opengalois.engine.context import EngineContext, _next_fact_id, _resolve_poly_desc_QQ
from opengalois.engine.procedures.procedure import ProcedureResult
from opengalois.radicals.schemes import deg2_quadratic_formula


def _degree_fact_id(ctx: EngineContext, poly_ref: str) -> str:
    """Return the cached ``Degree`` fact id for ``poly_ref``.

    Args:
        ctx: Engine execution context.
        poly_ref: Polynomial object reference.

    Returns:
        Identifier of the verified ``Degree(poly_ref, 2)`` premise.

    Raises:
        ValueError: If the cache does not contain a valid degree fact id.
    """
    degree_map = ctx.cache.get("_degree_fact_by_poly", {})
    if not isinstance(degree_map, dict) or poly_ref not in degree_map:
        raise ValueError(
            f"Missing Degree premise for {poly_ref!r}. "
            "Run ReducibilityNode (or emit Degree) before IrreducibleDeg2Procedure."
        )
    fid = str(degree_map[poly_ref])
    if not fid:
        raise ValueError(f"Empty Degree fact id for {poly_ref!r}.")
    return fid



def _irreducible_fact_id(ctx: EngineContext, poly_ref: str) -> str:
    """Return the cached ``IrreducibleQQ`` fact id for ``poly_ref``.

    Args:
        ctx: Engine execution context.
        poly_ref: Polynomial object reference.

    Returns:
        Identifier of the verified ``IrreducibleQQ(poly_ref)`` premise.

    Raises:
        ValueError: If the cache does not contain a valid irreducibility fact id.
    """
    irr_map = ctx.cache.get("_irreducible_fact_by_poly", {})
    if not isinstance(irr_map, dict) or poly_ref not in irr_map:
        raise ValueError(
            f"Missing IrreducibleQQ premise for {poly_ref!r}. "
            "Run ReducibilityNode before IrreducibleDeg2Procedure."
        )
    fid = str(irr_map[poly_ref])
    if not fid:
        raise ValueError(f"Empty IrreducibleQQ fact id for {poly_ref!r}.")
    return fid


@dataclass(frozen=True)
class IrreducibleDeg2Procedure:
    """Degree-2 irreducible procedure.

    The procedure keeps the existing degree-2 Galois-group emission and, in a
    second local step, emits the canonical ``RadicalRoots`` fact using the
    quadratic formula scheme.
    """

    rule_id: str = "galois_group.QQ.deg2.C2@1"
    pred: str = "GaloisGroup"
    group_obj_id: str = "group.C2"
    radical_roots_rule_id: str = "radical_roots.QQ.deg2.quadratic_formula@1"

    def run(self, ctx: EngineContext, *, poly_ref: str) -> ProcedureResult:
        """Run the degree-2 irreducible procedure.

        Args:
            ctx: Engine context.
            poly_ref: Reference to the polynomial object.

        Returns:
            Procedure result containing the degree-2 Galois-group fact and the
            canonical degree-2 ``RadicalRoots`` fact.

        Raises:
            ValueError: If the required cached premises are missing.
        """
        ctx.objects.put_groupid(
            self.group_obj_id,
            system="smallgroup",
            order=2,
            index=1,
            alias="C2",
        )

        degree_fact = _degree_fact_id(ctx, poly_ref)
        irreducible_fact = _irreducible_fact_id(ctx, poly_ref)

        facts: list[dict[str, Any]] = []
        group_fact = {
            "id": _next_fact_id(ctx),
            "claim": {
                "pred": self.pred,
                "args": [{"ref": poly_ref}, {"ref": self.group_obj_id}],
            },
            "rule": self.rule_id,
            "premises": [degree_fact, irreducible_fact],
            "statement": "Irreducible quadratic over Q has Galois group C2.",
        }
        facts.append(group_fact)
        facts.extend(
            self._emit_radical_roots(
                ctx,
                poly_ref=poly_ref,
                degree_fact_id=degree_fact,
                irreducible_fact_id=irreducible_fact,
            )
        )

        out = {
            "decision": "galois_group",
            "group": "C2",
            "group_ref": self.group_obj_id,
        }
        return ProcedureResult(facts=facts, out=out)

    def _emit_radical_roots(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        degree_fact_id: str,
        irreducible_fact_id: str,
    ) -> list[dict[str, Any]]:
        """Emit the canonical degree-2 ``RadicalRoots`` fact.

        Args:
            ctx: Engine context.
            poly_ref: Reference to the quadratic polynomial.
            degree_fact_id: Verified ``Degree(f,2)`` fact id.
            irreducible_fact_id: Verified ``IrreducibleQQ(f)`` fact id.

        Returns:
            Single-element list containing the emitted ``RadicalRoots`` fact.

        Raises:
            ValueError: If the polynomial does not decode to a non-degenerate
                quadratic polynomial.
        """
        coeffs = _resolve_poly_desc_QQ(ctx, poly_ref)
        if len(coeffs) != 3:
            raise ValueError(
                "IrreducibleDeg2Procedure expected a quadratic polynomial"
                " with exactly 3 coefficients"
            )
        a, b, c = coeffs
        if a == 0:
            raise ValueError("IrreducibleDeg2Procedure requires a non-zero leading coefficient")

        expr_refs: list[str] = []
        for expr in deg2_quadratic_formula.build(a=a, b=b, c=c):
            expr_obj_id = ctx.objects.new_id("rexpr.deg2.")
            ctx.objects.put_radical_expr(expr_obj_id, expr)
            expr_refs.append(expr_obj_id)

        roots_obj_id = ctx.objects.new_id("rlist.deg2.")
        ctx.objects.put_radical_expr_list(roots_obj_id, expr_refs)

        radical_fact = {
            "id": _next_fact_id(ctx),
            "claim": {
                "pred": "RadicalRoots",
                "args": [{"ref": poly_ref}, {"ref": roots_obj_id}],
            },
            "rule": self.radical_roots_rule_id,
            "premises": [degree_fact_id, irreducible_fact_id],
            "statement": "Canonical quadratic-formula radical roots over QQ.",
        }
        return [radical_fact]
