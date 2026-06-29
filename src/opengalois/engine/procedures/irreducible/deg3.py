from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

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
from opengalois.radicals.schemes import deg3_cardano_depressed_monic, lift_depressed_monic


def _is_monic_depressed_cubic(coeffs: list[Fraction]) -> bool:
    """Return whether coeffs are exactly a monic depressed cubic."""
    c = _trim_leading_zeros_desc(coeffs)
    return len(c) == 4 and c[0] == 1 and c[1] == 0


def _depressed_monic_identity_fact(
    ctx: EngineContext,
    *,
    poly_ref: str,
    degree_fact_id: str,
) -> dict[str, Any]:
    """Emit the identity normalization fact DepressedMonicEq(f,f)."""
    fact_id = _next_fact_id(ctx)
    return {
        "id": fact_id,
        "claim": {
            "pred": "DepressedMonicEq",
            "args": [{"ref": poly_ref}, {"ref": poly_ref}],
        },
        "rule": "normalize.depressed_monic_QQ@1",
        "premises": [degree_fact_id],
        "evidence": {
            "tschirnhaus_shift": _frac_to_str(Fraction(0, 1)),
            "monic_scale": _frac_to_str(Fraction(1, 1)),
        },
        "statement": (
            "Depressed-monic normalization over Q: the input cubic is already "
            "monic and depressed."
        ),
    }


@dataclass(frozen=True)
class IrreducibleDeg3Procedure:
    """Irreducible degree-3 pipeline.

    Steps:
      1) DiscriminantNode: compute Disc(f) and emit Discriminant(f,D).
      2) SquareNode: classify D as square or non-square in QQ.
      3) Emit DiscSquareQQ(f) or DiscNonSquareQQ(f) locally.
      4) Emit GaloisGroup(f, G) using:
           - galois_group.QQ.deg3.C3@1 if DiscSquareQQ(f),
           - galois_group.QQ.deg3.S3@1 if DiscNonSquareQQ(f).
      5) Emit RadicalRoots facts by:
           - reusing f directly when it is already monic and depressed,
           - otherwise normalizing to depressed monic form,
           - building canonical Cardano ASTs for the depressed monic cubic,
           - lifting them back only when a distinct normalization was used.

    Premises required (and enforced):
      - Degree(f,3)
      - IrreducibleQQ(f)
      - DiscSquareQQ(f) or DiscNonSquareQQ(f)
    """

    rule_c3: str = "galois_group.QQ.deg3.C3@1"
    rule_s3: str = "galois_group.QQ.deg3.S3@1"
    pred: str = "GaloisGroup"

    radical_rule_cardano: str = "radical_roots.QQ.deg3.cardano.depressed_monic@2"
    radical_rule_lift: str = "radical_roots.QQ.lift.depressed_monic@1"
    radical_pred: str = "RadicalRoots"
    group_c3_id: str = "group.C3"
    group_s3_id: str = "group.S3"

    disc_square_pred: str = "DiscSquareQQ"
    disc_nonsquare_pred: str = "DiscNonSquareQQ"
    disc_square_rule: str = "disc.square.QQ.lift@1"
    disc_nonsquare_rule: str = "disc.nonsquare.QQ.lift@1"

    def _maybe_emit_radical_roots(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
    ) -> list[dict[str, Any]]:
        """Emit degree-3 radical roots using Cardano and optional depressed-monic lift.

        If the input cubic is already monic and depressed, the method emits the
        identity normalization fact ``DepressedMonicEq(f,f)``, reuses the input
        degree/irreducibility premises, emits Cardano directly on ``f``, and
        does not emit a redundant lift.
        """
        facts: list[dict[str, Any]] = []

        degree_map = ctx.cache.get("_degree_fact_by_poly", {})
        if not isinstance(degree_map, dict) or poly_ref not in degree_map:
            raise ValueError(
                f"Missing Degree premise for {poly_ref!r}. "
                "Run ReducibilityNode (or emit Degree) before IrreducibleDeg3Procedure."
            )
        degree_fact_id = str(degree_map[poly_ref])
        if not degree_fact_id:
            raise ValueError("Empty Degree fact id for cubic input.")

        irr_map = ctx.cache.get("_irreducible_fact_by_poly", {})
        if not isinstance(irr_map, dict) or poly_ref not in irr_map:
            raise ValueError(
                f"Missing IrreducibleQQ premise for {poly_ref!r}. "
                "Run ReducibilityNode before IrreducibleDeg3Procedure."
            )
        irreducible_fact_id = str(irr_map[poly_ref])
        if not irreducible_fact_id:
            raise ValueError("Empty IrreducibleQQ fact id for cubic input.")

        f_poly = _resolve_poly_desc_QQ(ctx, poly_ref)
        if _is_monic_depressed_cubic(f_poly):
            g_ref = poly_ref
            normalize_fact = _depressed_monic_identity_fact(
                ctx,
                poly_ref=poly_ref,
                degree_fact_id=degree_fact_id,
            )
            facts.append(normalize_fact)
            normalize_fact_id = str(normalize_fact["id"])
            degree_g_fact_id = degree_fact_id
            irreducible_g_fact_id = irreducible_fact_id
            needs_lift = False
        else:
            normalize_out_id = ctx.objects.new_id("poly.depressed_monic.")
            normalize_fact, normalize_out = ctx.registry.normalize_deg5.run(
                ctx,
                poly_ref=poly_ref,
                out_id=normalize_out_id,
            )
            facts.append(normalize_fact)
            normalize_fact_id = str(normalize_fact["id"])

            g_ref_raw = normalize_out.get("poly_ref")
            if not isinstance(g_ref_raw, str) or not g_ref_raw:
                raise ValueError("NormalizeDepressedMonicQQ output is missing a valid poly_ref")
            g_ref = g_ref_raw

            degree_g_fact_id, degree_g = _ensure_degree_fact(ctx, poly_ref=g_ref, into=facts)
            if degree_g != 3:
                raise ValueError(f"Normalized cubic has unexpected degree {degree_g!r}.")

            irreducible_g_fact_id = emit_irreducible_to_depressed_fact(
                ctx,
                source_poly_ref=poly_ref,
                depressed_poly_ref=g_ref,
                normalize_fact_id=normalize_fact_id,
                source_irreducible_fact_id=irreducible_fact_id,
                into=facts,
            )
            needs_lift = True

        g_poly = _resolve_poly_desc_QQ(ctx, g_ref)
        if len(g_poly) != 4 or g_poly[0] != 1 or g_poly[1] != 0:
            raise ValueError(
                "Normalized polynomial is not a monic depressed cubic in descending form."
            )
        p_coef = g_poly[2]
        q_coef = g_poly[3]

        roots_g = deg3_cardano_depressed_monic.build_v2(p=p_coef, q=q_coef)
        roots_g_ref = store_radical_expr_list(
            ctx,
            exprs=roots_g,
            expr_prefix="rexpr.cardano.v2.",
            list_prefix="rlist.cardano.v2.",
        )

        roots_g_fact_id = _next_fact_id(ctx)
        roots_g_fact = {
            "id": roots_g_fact_id,
            "claim": {
                "pred": self.radical_pred,
                "args": [{"ref": g_ref}, {"ref": roots_g_ref}],
            },
            "rule": self.radical_rule_cardano,
            "premises": [degree_g_fact_id, irreducible_g_fact_id, normalize_fact_id],
            "statement": "Canonical Cardano-v2 radical roots for the depressed monic cubic.",
        }
        facts.append(roots_g_fact)
        cache_radical_roots(ctx, poly_ref=g_ref, fact_id=roots_g_fact_id, roots_ref=roots_g_ref)

        if not needs_lift:
            return facts

        degree_f = len(f_poly) - 1
        if degree_f != 3:
            raise ValueError(f"Input polynomial has unexpected degree {degree_f!r}.")
        lc = f_poly[0]
        if lc == 0:
            raise ValueError("Input polynomial has zero leading coefficient.")
        f_m = [coeff / lc for coeff in f_poly]
        shift = f_m[1] / Fraction(3, 1)

        lifted_roots = lift_depressed_monic.build(roots=roots_g, shift=shift)
        lifted_roots_ref = store_radical_expr_list(
            ctx,
            exprs=lifted_roots,
            expr_prefix="rexpr.cardano.lift.",
            list_prefix="rlist.cardano.lift.",
        )

        lifted_fact_id = _next_fact_id(ctx)
        lifted_fact = {
            "id": lifted_fact_id,
            "claim": {
                "pred": self.radical_pred,
                "args": [{"ref": poly_ref}, {"ref": lifted_roots_ref}],
            },
            "rule": self.radical_rule_lift,
            "premises": [normalize_fact_id, roots_g_fact_id],
            "statement": "Lift depressed-monic Cardano radical roots back to the original cubic.",
        }
        facts.append(lifted_fact)
        cache_radical_roots(
            ctx,
            poly_ref=poly_ref,
            fact_id=lifted_fact_id,
            roots_ref=lifted_roots_ref,
        )

        return facts

    def run(self, ctx: EngineContext, *, poly_ref: str) -> ProcedureResult:
        """Execute the degree-3 irreducibility procedure.

        Determines the Galois group of a degree-3 irreducible polynomial over QQ
        by computing its discriminant, classifying the discriminant value as square
        or non-square, lifting that result to the polynomial, and applying the
        appropriate classification rule.

        Args:
            ctx: Engine context containing cache, registry, and object store.
            poly_ref: Reference to the polynomial object.

        Returns:
            ProcedureResult containing:
                - facts: List of all emitted facts.
                - out: Dictionary with decision info, group classification,
                  discriminant output, and discriminant squarehood output.

        Raises:
            ValueError: If required premises (Degree, IrreducibleQQ) are missing or
                if discriminant squarehood is unexpected.
            TypeError: If node output format is invalid.
        """
        # Ensure we have Degree and Irreducible premises (emitted by ReducibilityNode).
        degree_map = ctx.cache.get("_degree_fact_by_poly", {})
        if not isinstance(degree_map, dict) or poly_ref not in degree_map:
            raise ValueError(
                f"Missing Degree premise for {poly_ref!r}. "
                "Run ReducibilityNode (or emit Degree) before IrreducibleDeg3Procedure."
            )
        degree_fact_id = str(degree_map[poly_ref])

        irr_map = ctx.cache.get("_irreducible_fact_by_poly", {})
        if not isinstance(irr_map, dict) or poly_ref not in irr_map:
            raise ValueError(
                f"Missing IrreducibleQQ premise for {poly_ref!r}. "
                "Run ReducibilityNode before IrreducibleDeg3Procedure."
            )
        irreducible_fact_id = str(irr_map[poly_ref])

        # Compute exact discriminant.
        disc_nodes, disc_out = ctx.registry.discriminant.run(ctx, poly_ref=poly_ref)
        disc_facts = disc_out.get("facts", {})
        if not isinstance(disc_facts, dict):
            raise TypeError("DiscriminantNode out['facts'] must be a dict")
        disc_fact_raw = disc_facts.get("discriminant")
        if disc_fact_raw is None:
            raise ValueError("Missing Discriminant(f,D) fact id from DiscriminantNode")
        disc_fact_id = str(disc_fact_raw)
        if not disc_fact_id:
            raise ValueError("Empty Discriminant(f,D) fact id from DiscriminantNode")

        disc_ref_raw = disc_out.get("disc_ref")
        if not isinstance(disc_ref_raw, str) or not disc_ref_raw:
            raise ValueError("DiscriminantNode output is missing a valid disc_ref")
        disc_ref = disc_ref_raw

        # Square / non-square classification of the discriminant value.
        square_nodes, square_out = ctx.registry.square.run(ctx, rat_ref=disc_ref)
        square_decision = str(square_out.get("decision", ""))
        square_facts = square_out.get("facts", {})
        if not isinstance(square_facts, dict):
            raise TypeError("SquareNode out['facts'] must be a dict")

        # Ensure group objects exist.
        ctx.objects.put_groupid(self.group_c3_id, system="smallgroup", order=3, index=1, alias="C3")
        ctx.objects.put_groupid(self.group_s3_id, system="smallgroup", order=6, index=2, alias="S3")

        if square_decision == "square":
            is_square_raw = square_facts.get("square")
            if is_square_raw is None:
                raise ValueError("Missing IsSquareQQ fact id from SquareNode")
            is_square_fact_id = str(is_square_raw)
            if not is_square_fact_id:
                raise ValueError("Empty IsSquareQQ fact id from SquareNode")

            disc_square_fact_id = _next_fact_id(ctx)
            disc_lift_fact = {
                "id": disc_square_fact_id,
                "claim": {"pred": self.disc_square_pred, "args": [{"ref": poly_ref}]},
                "rule": self.disc_square_rule,
                "premises": [disc_fact_id, is_square_fact_id],
                "statement": "Discriminant of f is a square in QQ.",
            }

            group_id = self.group_c3_id
            rule_id = self.rule_c3
            premises = [degree_fact_id, irreducible_fact_id, disc_square_fact_id]
            disc_lift_nodes = [disc_lift_fact]
            group_name = "C3"

        elif square_decision == "nonsquare":
            non_square_raw = square_facts.get("non_square")
            if non_square_raw is None:
                raise ValueError("Missing NonSquareQQ fact id from SquareNode")
            non_square_fact_id = str(non_square_raw)
            if not non_square_fact_id:
                raise ValueError("Empty NonSquareQQ fact id from SquareNode")

            disc_nonsquare_fact_id = _next_fact_id(ctx)
            disc_lift_fact = {
                "id": disc_nonsquare_fact_id,
                "claim": {"pred": self.disc_nonsquare_pred, "args": [{"ref": poly_ref}]},
                "rule": self.disc_nonsquare_rule,
                "premises": [disc_fact_id, non_square_fact_id],
                "statement": "Discriminant of f is not a square in QQ.",
            }

            group_id = self.group_s3_id
            rule_id = self.rule_s3
            premises = [degree_fact_id, irreducible_fact_id, disc_nonsquare_fact_id]
            disc_lift_nodes = [disc_lift_fact]
            group_name = "S3"

        else:
            raise ValueError(f"Unexpected square decision for discriminant: {square_decision!r}")

        fact = {
            "id": _next_fact_id(ctx),
            "claim": {"pred": self.pred, "args": [{"ref": poly_ref}, {"ref": group_id}]},
            "rule": rule_id,
            "premises": premises,
            "statement": "Degree-3 irreducible Galois group classification via discriminant.",
        }

        radical_facts = self._maybe_emit_radical_roots(ctx, poly_ref=poly_ref)

        out = {
            "decision": "galois_group",
            "group": group_name,
            "group_ref": group_id,
            "discriminant": disc_out,
            "discriminant_squarehood": square_out,
        }
        return ProcedureResult(
            facts=[*disc_nodes, *square_nodes, *disc_lift_nodes, fact, *radical_facts],
            out=out,
        )





