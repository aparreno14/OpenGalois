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
    get_cached_radical_roots,
    load_radical_expr_list,
    store_radical_expr_list,
)
from opengalois.engine.procedures.procedure import ProcedureResult
from opengalois.polyops.desc_qx import _trim_leading_zeros_desc
from opengalois.radicals.schemes import deg4_ferrari_depressed_monic, lift_depressed_monic


def _find_factorization_fact_id(
    facts: list[dict[str, Any]],
    *,
    poly_ref: str,
) -> str:
    """Find the FactorizationMonicQQ fact id for the given polynomial reference."""
    for fact in facts:
        claim = fact.get("claim", {})
        if claim.get("pred") != "FactorizationMonicQQ":
            continue
        args = claim.get("args")
        if not isinstance(args, list) or len(args) != 3:
            continue
        ref0 = args[0].get("ref") if isinstance(args[0], dict) else None
        if ref0 == poly_ref:
            fid = fact.get("id")
            if isinstance(fid, str) and fid:
                return fid
    raise ValueError(f"Missing FactorizationMonicQQ fact id for {poly_ref!r}.")




def _is_monic_depressed_quartic(coeffs: list[Fraction]) -> bool:
    """Return whether coeffs are exactly a monic depressed quartic."""
    c = _trim_leading_zeros_desc(coeffs)
    return len(c) == 5 and c[0] == 1 and c[1] == 0


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
            "Depressed-monic normalization over Q: the input quartic is already "
            "monic and depressed."
        ),
    }


def _record_galois_group_fact(
    ctx: EngineContext,
    *,
    poly_ref: str,
    fact_id: str,
    group_ref: str,
) -> None:
    """Cache a certified GaloisGroup(poly_ref, group_ref) fact."""
    gg_map = ctx.cache.setdefault("_galois_group_fact_by_poly", {})
    if not isinstance(gg_map, dict):
        raise TypeError("ctx.cache['_galois_group_fact_by_poly'] must be a dict")
    gg_map[poly_ref] = fact_id

    group_ref_map = ctx.cache.setdefault("_galois_group_ref_by_poly", {})
    if not isinstance(group_ref_map, dict):
        raise TypeError("ctx.cache['_galois_group_ref_by_poly'] must be a dict")
    group_ref_map[poly_ref] = group_ref


@dataclass(frozen=True)
class IrreducibleDeg4Procedure:
    """Degree-4 irreducible procedure.

    The degree-4 pipeline first transports the input quartic to its depressed
    monic normalization ``g`` and then uses one single quartic cubic resolvent:

        (x1+x2)(x3+x4).

    This is the same coordinate used by Ferrari's radical formula.  Hence
    classification and radical construction share the same certified
    ``ResolventQQ(R,g,p)`` fact instead of computing one resolvent for
    classification and another for radicals.
    """

    pred: str = "GaloisGroup"

    rule_s4: str = "galois_group.QQ.deg4.S4@2"
    rule_a4: str = "galois_group.QQ.deg4.A4@2"
    rule_v4: str = "galois_group.QQ.deg4.V4@3"
    rule_c4: str = "galois_group.QQ.deg4.C4@2"
    rule_d4_w1: str = "galois_group.QQ.deg4.D4.w1@2"
    rule_d4_w2: str = "galois_group.QQ.deg4.D4.w2@2"
    rule_lift_group: str = "galois_group.QQ.lift.depressed_monic@1"

    radical_rule_ferrari: str = "radical_roots.QQ.deg4.ferrari.depressed_monic@2"
    radical_rule_lift: str = "radical_roots.QQ.lift.depressed_monic@1"
    radical_pred: str = "RadicalRoots"
    irreducible_to_depressed_rule: str = "irreducible.QQ.to.depressed_monic@1"
    resolvent_family_ferrari: str = "deg4.cubic_x1plusx2_times_x3plusx4"

    group_s4_id: str = "group.S4"
    group_a4_id: str = "group.A4"
    group_v4_id: str = "group.V4"
    group_c4_id: str = "group.C4"
    group_d4_id: str = "group.D4"

    disc_square_pred: str = "DiscSquareQQ"
    disc_nonsquare_pred: str = "DiscNonSquareQQ"
    disc_square_rule: str = "disc.square.QQ.lift@1"
    disc_nonsquare_rule: str = "disc.nonsquare.QQ.lift@1"

    def _emit_radical_roots_from_selected_resolvent(
        self,
        ctx: EngineContext,
        *,
        source_poly_ref: str,
        depressed_poly_ref: str,
        normalize_fact_id: str,
        degree_g_fact_id: str,
        irreducible_g_fact_id: str,
        resolvent_ref: str,
        resolvent_fact_id: str,
        resolvent_reducibility_decision: str,
    ) -> list[dict[str, Any]]:
        """Emit quartic radical roots using the already-selected pair-sums resolvent."""
        facts: list[dict[str, Any]] = []

        if resolvent_reducibility_decision == "irreducible":
            resolvent_proc = ctx.registry.irreducible_procedures[3].run(
                ctx,
                poly_ref=resolvent_ref,
            )
        elif resolvent_reducibility_decision == "reducible":
            resolvent_proc = ctx.registry.reducible.run(ctx, poly_ref=resolvent_ref)
        else:
            raise ValueError(
                "Unexpected reducibility decision for Ferrari resolvent: "
                f"{resolvent_reducibility_decision!r}"
            )

        facts.extend(resolvent_proc.facts)

        resolvent_radicals = get_cached_radical_roots(ctx, poly_ref=resolvent_ref)
        roots_R = load_radical_expr_list(ctx, roots_ref=resolvent_radicals.roots_ref)

        g_poly = _resolve_poly_desc_QQ(ctx, depressed_poly_ref)
        if len(g_poly) != 5 or g_poly[0] != 1 or g_poly[1] != 0:
            raise ValueError(
                "Normalized polynomial is not a monic depressed quartic in descending form."
            )
        c_coef = g_poly[2]
        d_coef = g_poly[3]
        e_coef = g_poly[4]

        roots_g = deg4_ferrari_depressed_monic.build(
            c=c_coef,
            d=d_coef,
            e=e_coef,
            resolvent_roots=roots_R,
        )
        roots_g_ref = store_radical_expr_list(
            ctx,
            exprs=roots_g,
            expr_prefix="rexpr.ferrari.",
            list_prefix="rlist.ferrari.",
        )

        roots_g_fact_id = _next_fact_id(ctx)
        roots_g_fact = {
            "id": roots_g_fact_id,
            "claim": {
                "pred": self.radical_pred,
                "args": [{"ref": depressed_poly_ref}, {"ref": roots_g_ref}],
            },
            "rule": self.radical_rule_ferrari,
            "premises": [
                degree_g_fact_id,
                irreducible_g_fact_id,
                normalize_fact_id,
                resolvent_fact_id,
                resolvent_radicals.fact_id,
            ],
            "statement": (
                "Canonical Ferrari radical roots for the depressed monic quartic, "
                "using the same pair-sums resolvent as the Galois classification."
            ),
        }
        facts.append(roots_g_fact)

        cache_radical_roots(
            ctx,
            poly_ref=depressed_poly_ref,
            fact_id=roots_g_fact_id,
            roots_ref=roots_g_ref,
        )

        if source_poly_ref == depressed_poly_ref:
            return facts

        f_poly = _resolve_poly_desc_QQ(ctx, source_poly_ref)
        degree_f = len(f_poly) - 1
        if degree_f != 4:
            raise ValueError(f"Input polynomial has unexpected degree {degree_f!r}.")
        lc = f_poly[0]
        if lc == 0:
            raise ValueError("Input polynomial has zero leading coefficient.")
        f_m = [coeff / lc for coeff in f_poly]
        shift = f_m[1] / Fraction(4, 1)

        lifted_roots = lift_depressed_monic.build(roots=roots_g, shift=shift)
        lifted_roots_ref = store_radical_expr_list(
            ctx,
            exprs=lifted_roots,
            expr_prefix="rexpr.ferrari.lift.",
            list_prefix="rlist.ferrari.lift.",
        )

        lifted_fact_id = _next_fact_id(ctx)
        lifted_fact = {
            "id": lifted_fact_id,
            "claim": {
                "pred": self.radical_pred,
                "args": [{"ref": source_poly_ref}, {"ref": lifted_roots_ref}],
            },
            "rule": self.radical_rule_lift,
            "premises": [normalize_fact_id, roots_g_fact_id],
            "statement": "Lift depressed-monic Ferrari radical roots back to the original quartic.",
        }
        facts.append(lifted_fact)

        cache_radical_roots(
            ctx,
            poly_ref=source_poly_ref,
            fact_id=lifted_fact_id,
            roots_ref=lifted_roots_ref,
        )

        return facts

    def _emit_group_lift_fact(
        self,
        ctx: EngineContext,
        *,
        source_poly_ref: str,
        depressed_poly_ref: str,
        group_ref: str,
        normalize_fact_id: str,
        group_g_fact_id: str,
    ) -> dict[str, Any] | None:
        """Emit GaloisGroup(source_poly_ref,G) unless source and depressed refs coincide."""
        if source_poly_ref == depressed_poly_ref:
            return None

        fact_id = _next_fact_id(ctx)
        fact = {
            "id": fact_id,
            "claim": {
                "pred": self.pred,
                "args": [{"ref": source_poly_ref}, {"ref": group_ref}],
            },
            "rule": self.rule_lift_group,
            "premises": [normalize_fact_id, group_g_fact_id],
            "statement": (
                "Lift the Galois group from the depressed monic normalization back "
                "to the original quartic."
            ),
        }
        _record_galois_group_fact(
            ctx,
            poly_ref=source_poly_ref,
            fact_id=fact_id,
            group_ref=group_ref,
        )
        return fact

    def run(self, ctx: EngineContext, *, poly_ref: str) -> ProcedureResult:
        """Execute the degree-4 irreducible procedure."""
        degree_map = ctx.cache.get("_degree_fact_by_poly", {})
        if not isinstance(degree_map, dict) or poly_ref not in degree_map:
            raise ValueError(
                f"Missing Degree premise for {poly_ref!r}. "
                "Run ReducibilityNode (or emit Degree) before IrreducibleDeg4Procedure."
            )
        degree_fact_id = str(degree_map[poly_ref])
        if not degree_fact_id:
            raise ValueError("Empty Degree fact id for quartic input.")

        irr_map = ctx.cache.get("_irreducible_fact_by_poly", {})
        if not isinstance(irr_map, dict) or poly_ref not in irr_map:
            raise ValueError(
                f"Missing IrreducibleQQ premise for {poly_ref!r}. "
                "Run ReducibilityNode before IrreducibleDeg4Procedure."
            )
        irreducible_fact_id = str(irr_map[poly_ref])
        if not irreducible_fact_id:
            raise ValueError("Empty IrreducibleQQ fact id for quartic input.")

        facts: list[dict[str, Any]] = []

        # First choose the depressed monic working quartic g.  If the input is
        # already monic and depressed, keep the same object reference and emit
        # the identity normalization fact DepressedMonicEq(f,f).
        input_poly = _trim_leading_zeros_desc(_resolve_poly_desc_QQ(ctx, poly_ref))
        if _is_monic_depressed_quartic(input_poly):
            g_ref = poly_ref
            normalize_fact = _depressed_monic_identity_fact(
                ctx,
                poly_ref=poly_ref,
                degree_fact_id=degree_fact_id,
            )
            facts.append(normalize_fact)
            normalize_fact_id = str(normalize_fact["id"])
            normalize_out: dict[str, Any] = {
                "poly_ref": g_ref,
                "already_depressed_monic": True,
            }
            degree_g_fact_id = degree_fact_id
            irreducible_g_fact_id = irreducible_fact_id
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
            if degree_g != 4:
                raise ValueError(f"Normalized quartic has unexpected degree {degree_g!r}.")

            irreducible_g_fact_id = emit_irreducible_to_depressed_fact(
                ctx,
                source_poly_ref=poly_ref,
                depressed_poly_ref=g_ref,
                normalize_fact_id=normalize_fact_id,
                source_irreducible_fact_id=irreducible_fact_id,
                into=facts,
                rule_id=self.irreducible_to_depressed_rule,
            )

        res_nodes, res_out = ctx.registry.resolvent.run(
            ctx,
            poly_ref=g_ref,
            family=self.resolvent_family_ferrari,
        )

        res_facts = res_out.get("facts", {})
        if not isinstance(res_facts, dict):
            raise TypeError("ResolventNode out['facts'] must be a dict")

        resolvent_ref_raw = res_out.get("resolvent_ref")
        if not isinstance(resolvent_ref_raw, str) or not resolvent_ref_raw:
            raise ValueError("ResolventNode output is missing a valid resolvent_ref.")
        resolvent_ref = resolvent_ref_raw

        resolvent_fact_raw = res_facts.get("resolvent")
        if resolvent_fact_raw is None:
            raise ValueError("Missing ResolventQQ fact id from ResolventNode.")
        resolvent_fact_id = str(resolvent_fact_raw)
        if not resolvent_fact_id:
            raise ValueError("Empty ResolventQQ fact id from ResolventNode.")

        red_res_nodes, red_res_out = ctx.registry.reducibility.run(ctx, poly_ref=resolvent_ref)
        res_decision = str(red_res_out.get("decision", ""))

        ctx.objects.put_groupid(
            self.group_s4_id,
            system="smallgroup",
            order=24,
            index=12,
            alias="S4",
        )
        ctx.objects.put_groupid(
            self.group_a4_id,
            system="smallgroup",
            order=12,
            index=3,
            alias="A4",
        )
        ctx.objects.put_groupid(
            self.group_v4_id,
            system="smallgroup",
            order=4,
            index=2,
            alias="V4",
        )
        ctx.objects.put_groupid(
            self.group_c4_id,
            system="smallgroup",
            order=4,
            index=1,
            alias="C4",
        )
        ctx.objects.put_groupid(
            self.group_d4_id,
            system="smallgroup",
            order=8,
            index=3,
            alias="D4",
        )

        facts.extend([*res_nodes, *red_res_nodes])

        factorization_fact_id: str | None = None
        resolvent_factor_refs: list[str] = []
        factor_degree_fact_ids: list[str] = []

        if res_decision == "reducible":
            factorization_fact_id = _find_factorization_fact_id(
                red_res_nodes,
                poly_ref=resolvent_ref,
            )
            factor_refs_raw = red_res_out.get("factor_refs")
            if not isinstance(factor_refs_raw, list) or not all(
                isinstance(x, str) and x for x in factor_refs_raw
            ):
                raise ValueError(
                    "ReducibilityNode output for the resolvent is missing valid factor_refs."
                )
            resolvent_factor_refs = factor_refs_raw

            is_split_resolvent = len(resolvent_factor_refs) == 3
            for factor_ref in resolvent_factor_refs:
                degree_factor_fact_id, degree_factor = _ensure_degree_fact(
                    ctx,
                    poly_ref=factor_ref,
                    into=facts,
                )
                factor_degree_fact_ids.append(degree_factor_fact_id)
                if degree_factor != 1:
                    is_split_resolvent = False

            if is_split_resolvent:
                group_g_fact_id = _next_fact_id(ctx)
                group_g_fact = {
                    "id": group_g_fact_id,
                    "claim": {
                        "pred": self.pred,
                        "args": [{"ref": g_ref}, {"ref": self.group_v4_id}],
                    },
                    "rule": self.rule_v4,
                    "premises": [
                        degree_g_fact_id,
                        irreducible_g_fact_id,
                        resolvent_fact_id,
                        factorization_fact_id,
                        *factor_degree_fact_ids,
                    ],
                    "statement": (
                        "Degree-4 irreducible Galois group classification of the "
                        "depressed monic quartic: the pair-sums cubic resolvent "
                        "splits completely over QQ."
                    ),
                }
                facts.append(group_g_fact)
                _record_galois_group_fact(
                    ctx,
                    poly_ref=g_ref,
                    fact_id=group_g_fact_id,
                    group_ref=self.group_v4_id,
                )

                lift_fact = self._emit_group_lift_fact(
                    ctx,
                    source_poly_ref=poly_ref,
                    depressed_poly_ref=g_ref,
                    group_ref=self.group_v4_id,
                    normalize_fact_id=normalize_fact_id,
                    group_g_fact_id=group_g_fact_id,
                )
                if lift_fact is not None:
                    facts.append(lift_fact)

                facts.extend(
                    self._emit_radical_roots_from_selected_resolvent(
                        ctx,
                        source_poly_ref=poly_ref,
                        depressed_poly_ref=g_ref,
                        normalize_fact_id=normalize_fact_id,
                        degree_g_fact_id=degree_g_fact_id,
                        irreducible_g_fact_id=irreducible_g_fact_id,
                        resolvent_ref=resolvent_ref,
                        resolvent_fact_id=resolvent_fact_id,
                        resolvent_reducibility_decision=res_decision,
                    )
                )

                out = {
                    "decision": "galois_group",
                    "group": "V4",
                    "group_ref": self.group_v4_id,
                    "depressed_poly_ref": g_ref,
                    "depressed_group_fact_id": group_g_fact_id,
                    "normalization": normalize_out,
                    "discriminant": None,
                    "discriminant_squarehood": None,
                    "resolvent": res_out,
                    "resolvent_reducibility": red_res_out,
                }
                return ProcedureResult(facts=facts, out=out)

        disc_nodes, disc_out = ctx.registry.discriminant.run(ctx, poly_ref=g_ref)
        disc_facts = disc_out.get("facts", {})
        if not isinstance(disc_facts, dict):
            raise TypeError("DiscriminantNode out['facts'] must be a dict.")

        disc_fact_raw = disc_facts.get("discriminant")
        if disc_fact_raw is None:
            raise ValueError("Missing Discriminant(g,Δ) fact id from DiscriminantNode.")
        discriminant_fact_id = str(disc_fact_raw)
        if not discriminant_fact_id:
            raise ValueError("Empty Discriminant(g,Δ) fact id from DiscriminantNode.")

        disc_ref_raw = disc_out.get("disc_ref")
        if not isinstance(disc_ref_raw, str) or not disc_ref_raw:
            raise ValueError("DiscriminantNode output is missing a valid disc_ref.")
        disc_ref = disc_ref_raw

        square_nodes, square_out = ctx.registry.square.run(ctx, rat_ref=disc_ref)
        square_decision = str(square_out.get("decision", ""))
        square_facts = square_out.get("facts", {})
        if not isinstance(square_facts, dict):
            raise TypeError("SquareNode out['facts'] must be a dict.")

        if square_decision == "square":
            is_square_raw = square_facts.get("square")
            if is_square_raw is None:
                raise ValueError("Missing IsSquareQQ fact id from SquareNode.")
            is_square_fact_id = str(is_square_raw)
            if not is_square_fact_id:
                raise ValueError("Empty IsSquareQQ fact id from SquareNode.")

            disc_square_fact_id = _next_fact_id(ctx)
            disc_lift_fact = {
                "id": disc_square_fact_id,
                "claim": {"pred": self.disc_square_pred, "args": [{"ref": g_ref}]},
                "rule": self.disc_square_rule,
                "premises": [discriminant_fact_id, is_square_fact_id],
                "statement": "Discriminant of the depressed monic quartic is a square in QQ.",
            }
            disc_decision = "disc_square"
            disc_square_or_nonsquare_fact_id = disc_square_fact_id

        elif square_decision == "nonsquare":
            non_square_raw = square_facts.get("non_square")
            if non_square_raw is None:
                raise ValueError("Missing NonSquareQQ fact id from SquareNode.")
            non_square_fact_id = str(non_square_raw)
            if not non_square_fact_id:
                raise ValueError("Empty NonSquareQQ fact id from SquareNode.")

            disc_nonsquare_fact_id = _next_fact_id(ctx)
            disc_lift_fact = {
                "id": disc_nonsquare_fact_id,
                "claim": {"pred": self.disc_nonsquare_pred, "args": [{"ref": g_ref}]},
                "rule": self.disc_nonsquare_rule,
                "premises": [discriminant_fact_id, non_square_fact_id],
                "statement": (
                    "Discriminant of the depressed monic quartic is not a square in QQ."
                ),
            }
            disc_decision = "disc_nonsquare"
            disc_square_or_nonsquare_fact_id = disc_nonsquare_fact_id

        else:
            raise ValueError(f"Unexpected square decision for discriminant: {square_decision!r}")

        facts.extend([*disc_nodes, *square_nodes, disc_lift_fact])

        if res_decision == "irreducible":
            irr_map_after = ctx.cache.get("_irreducible_fact_by_poly", {})
            if not isinstance(irr_map_after, dict) or resolvent_ref not in irr_map_after:
                raise ValueError(
                    "Missing IrreducibleQQ fact for quartic resolvent after ReducibilityNode."
                )
            resolvent_irred_fact_id = str(irr_map_after[resolvent_ref])
            if not resolvent_irred_fact_id:
                raise ValueError("Empty IrreducibleQQ fact id for quartic resolvent.")

            if disc_decision == "disc_square":
                group_id = self.group_a4_id
                rule_id = self.rule_a4
                group_name = "A4"
            elif disc_decision == "disc_nonsquare":
                group_id = self.group_s4_id
                rule_id = self.rule_s4
                group_name = "S4"
            else:
                raise ValueError(f"Unexpected discriminant decision: {disc_decision!r}")

            premises = [
                degree_g_fact_id,
                irreducible_g_fact_id,
                disc_square_or_nonsquare_fact_id,
                resolvent_fact_id,
                resolvent_irred_fact_id,
            ]

            group_g_fact_id = _next_fact_id(ctx)
            group_g_fact = {
                "id": group_g_fact_id,
                "claim": {"pred": self.pred, "args": [{"ref": g_ref}, {"ref": group_id}]},
                "rule": rule_id,
                "premises": premises,
                "statement": (
                    "Degree-4 irreducible Galois group classification of the "
                    "depressed monic quartic via discriminant and pair-sums cubic resolvent."
                ),
            }
            facts.append(group_g_fact)
            _record_galois_group_fact(
                ctx,
                poly_ref=g_ref,
                fact_id=group_g_fact_id,
                group_ref=group_id,
            )

            lift_fact = self._emit_group_lift_fact(
                ctx,
                source_poly_ref=poly_ref,
                depressed_poly_ref=g_ref,
                group_ref=group_id,
                normalize_fact_id=normalize_fact_id,
                group_g_fact_id=group_g_fact_id,
            )
            if lift_fact is not None:
                facts.append(lift_fact)

            facts.extend(
                self._emit_radical_roots_from_selected_resolvent(
                    ctx,
                    source_poly_ref=poly_ref,
                    depressed_poly_ref=g_ref,
                    normalize_fact_id=normalize_fact_id,
                    degree_g_fact_id=degree_g_fact_id,
                    irreducible_g_fact_id=irreducible_g_fact_id,
                    resolvent_ref=resolvent_ref,
                    resolvent_fact_id=resolvent_fact_id,
                    resolvent_reducibility_decision=res_decision,
                )
            )

            out = {
                "decision": "galois_group",
                "group": group_name,
                "group_ref": group_id,
                "depressed_poly_ref": g_ref,
                "depressed_group_fact_id": group_g_fact_id,
                "normalization": normalize_out,
                "discriminant": disc_out,
                "discriminant_squarehood": square_out,
                "resolvent": res_out,
                "resolvent_reducibility": red_res_out,
            }
            return ProcedureResult(facts=facts, out=out)

        if res_decision != "reducible":
            raise ValueError(f"Unexpected resolvent reducibility decision: {res_decision!r}")

        if factorization_fact_id is None:
            raise ValueError(
                "Missing FactorizationMonicQQ fact id for reducible quartic resolvent."
            )
        if not resolvent_factor_refs:
            raise ValueError(
                "ReducibilityNode output for the resolvent is missing valid factor_refs."
            )

        if disc_decision == "disc_square":
            raise ValueError(
                "Unexpected square-discriminant branch after a non-split reducible resolvent."
            )

        if disc_decision != "disc_nonsquare":
            raise ValueError(f"Unexpected discriminant decision: {disc_decision!r}")

        kw_nodes, kw_out = ctx.registry.kappe_warren.run(
            ctx,
            poly_ref=g_ref,
            resolvent_ref=resolvent_ref,
            factor_refs=resolvent_factor_refs,
            resolvent_family=self.resolvent_family_ferrari,
        )
        facts.extend(kw_nodes)

        w1_decision = str(kw_out.get("w1_decision", ""))
        w2_decision = str(kw_out.get("w2_decision", ""))
        w1_facts = kw_out.get("w1_facts", {})
        w2_facts = kw_out.get("w2_facts", {})

        if not isinstance(w1_facts, dict) or not isinstance(w2_facts, dict):
            raise TypeError("KappeWarrenNode out['w1_facts'] and out['w2_facts'] must be dicts.")

        common_premises = [
            degree_g_fact_id,
            irreducible_g_fact_id,
            discriminant_fact_id,
            disc_square_or_nonsquare_fact_id,
            resolvent_fact_id,
            factorization_fact_id,
        ]

        if w1_decision == "square" and w2_decision == "square":
            w1_square_raw = w1_facts.get("square")
            w2_square_raw = w2_facts.get("square")
            if w1_square_raw is None or w2_square_raw is None:
                raise ValueError("Missing IsSquareQQ fact ids from KappeWarrenNode for C4 branch.")
            w1_square_fact_id = str(w1_square_raw)
            w2_square_fact_id = str(w2_square_raw)
            if not w1_square_fact_id or not w2_square_fact_id:
                raise ValueError("Empty IsSquareQQ fact ids from KappeWarrenNode for C4 branch.")

            group_id = self.group_c4_id
            group_name = "C4"
            rule_id = self.rule_c4
            premises = [*common_premises, w1_square_fact_id, w2_square_fact_id]

        elif w1_decision == "nonsquare":
            w1_nonsquare_raw = w1_facts.get("non_square")
            if w1_nonsquare_raw is None:
                raise ValueError(
                    "Missing NonSquareQQ fact id for first Kappe-Warren auxiliary value."
                )
            w1_nonsquare_fact_id = str(w1_nonsquare_raw)
            if not w1_nonsquare_fact_id:
                raise ValueError(
                    "Empty NonSquareQQ fact id for first Kappe-Warren auxiliary value."
                )

            group_id = self.group_d4_id
            group_name = "D4"
            rule_id = self.rule_d4_w1
            premises = [*common_premises, w1_nonsquare_fact_id]

        elif w2_decision == "nonsquare":
            w2_nonsquare_raw = w2_facts.get("non_square")
            if w2_nonsquare_raw is None:
                raise ValueError(
                    "Missing NonSquareQQ fact id for second Kappe-Warren auxiliary value."
                )
            w2_nonsquare_fact_id = str(w2_nonsquare_raw)
            if not w2_nonsquare_fact_id:
                raise ValueError(
                    "Empty NonSquareQQ fact id for second Kappe-Warren auxiliary value."
                )

            group_id = self.group_d4_id
            group_name = "D4"
            rule_id = self.rule_d4_w2
            premises = [*common_premises, w2_nonsquare_fact_id]

        else:
            raise ValueError(
                f"Unexpected Kappe-Warren decisions: w1={w1_decision!r}, w2={w2_decision!r}"
            )

        group_g_fact_id = _next_fact_id(ctx)
        group_g_fact = {
            "id": group_g_fact_id,
            "claim": {"pred": self.pred, "args": [{"ref": g_ref}, {"ref": group_id}]},
            "rule": rule_id,
            "premises": premises,
            "statement": (
                "Degree-4 irreducible Galois group classification of the depressed "
                "monic quartic via pair-sums resolvent and Kappe-Warren criteria."
            ),
        }
        facts.append(group_g_fact)
        _record_galois_group_fact(
            ctx,
            poly_ref=g_ref,
            fact_id=group_g_fact_id,
            group_ref=group_id,
        )

        lift_fact = self._emit_group_lift_fact(
            ctx,
            source_poly_ref=poly_ref,
            depressed_poly_ref=g_ref,
            group_ref=group_id,
            normalize_fact_id=normalize_fact_id,
            group_g_fact_id=group_g_fact_id,
        )
        if lift_fact is not None:
            facts.append(lift_fact)

        facts.extend(
            self._emit_radical_roots_from_selected_resolvent(
                ctx,
                source_poly_ref=poly_ref,
                depressed_poly_ref=g_ref,
                normalize_fact_id=normalize_fact_id,
                degree_g_fact_id=degree_g_fact_id,
                irreducible_g_fact_id=irreducible_g_fact_id,
                resolvent_ref=resolvent_ref,
                resolvent_fact_id=resolvent_fact_id,
                resolvent_reducibility_decision=res_decision,
            )
        )

        out = {
            "decision": "galois_group",
            "group": group_name,
            "group_ref": group_id,
            "depressed_poly_ref": g_ref,
            "depressed_group_fact_id": group_g_fact_id,
            "normalization": normalize_out,
            "discriminant": disc_out,
            "discriminant_squarehood": square_out,
            "resolvent": res_out,
            "resolvent_reducibility": red_res_out,
            "kappe_warren": kw_out,
        }
        return ProcedureResult(facts=facts, out=out)
