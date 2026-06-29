from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from opengalois.codec.rationals import _frac_to_str
from opengalois.engine.context import EngineContext, _next_fact_id, _resolve_poly_desc_QQ
from opengalois.engine.procedures.procedure import ProcedureResult
from opengalois.polyops.desc_qx import _trim_leading_zeros_desc


def _factorization_items_from_ref(ctx: EngineContext, factors_list_ref: str) -> list[str]:
    """Decode a PolyQQList object into factor-occurrence refs."""
    obj = ctx.objects.objects.get(factors_list_ref)
    if not isinstance(obj, dict):
        raise ValueError(f"Missing PolyQQList object: {factors_list_ref!r}")
    if obj.get("kind") != "PolyQQList":
        raise ValueError(f"Object {factors_list_ref!r} is not a PolyQQList")

    items = obj.get("items")
    if not isinstance(items, list) or not all(isinstance(x, str) and x for x in items):
        raise ValueError(f"Malformed PolyQQList payload for {factors_list_ref!r}")

    return list(items)


def _get_reducibility_out(ctx: EngineContext, *, poly_ref: str) -> dict[str, Any]:
    """Recover the cached ReducibilityNode output for a polynomial."""
    red_out_map = ctx.cache.get("_reducibility_out_by_poly", {})
    if not isinstance(red_out_map, dict):
        raise ValueError("Missing reducibility cache map '_reducibility_out_by_poly'")
    out = red_out_map.get(poly_ref)
    if not isinstance(out, dict):
        raise ValueError(
            f"Missing cached ReducibilityNode output for {poly_ref!r}. "
            "Run ReducibilityNode before ReducibleGaloisGroupProcedure."
        )
    return out


def _distinct_factor_refs(factor_items: list[str]) -> list[str]:
    """Return the order-preserving distinct factor refs from a multiplicity-bearing list."""
    out: list[str] = []
    seen: set[str] = set()
    for ref in factor_items:
        if ref not in seen:
            seen.add(ref)
            out.append(ref)
    return out


def _degree_fact_id(ctx: EngineContext, poly_ref: str) -> str:
    """Return the already-emitted Degree(poly_ref, n) fact id."""
    degree_map = ctx.cache.get("_degree_fact_by_poly", {})
    if not isinstance(degree_map, dict) or poly_ref not in degree_map:
        raise ValueError(
            f"Missing Degree premise for {poly_ref!r}. "
            "Run ReducibilityNode (or emit Degree) before ReducibleGaloisGroupProcedure."
        )
    fid = str(degree_map[poly_ref])
    if not fid:
        raise ValueError(f"Empty Degree fact id for {poly_ref!r}.")
    return fid


def _irreducible_fact_id(ctx: EngineContext, poly_ref: str) -> str:
    """Return the already-emitted IrreducibleQQ(poly_ref) fact id."""
    irr_map = ctx.cache.get("_irreducible_fact_by_poly", {})
    if not isinstance(irr_map, dict) or poly_ref not in irr_map:
        raise ValueError(
            f"Missing IrreducibleQQ premise for {poly_ref!r}. "
            "Run ReducibilityNode before ReducibleGaloisGroupProcedure."
        )
    fid = str(irr_map[poly_ref])
    if not fid:
        raise ValueError(f"Empty IrreducibleQQ fact id for {poly_ref!r}.")
    return fid


def _poly_degree(ctx: EngineContext, poly_ref: str) -> int:
    """Recompute deg(poly_ref) from its canonical QQ representation."""
    p = _trim_leading_zeros_desc(_resolve_poly_desc_QQ(ctx, poly_ref))
    if not p:
        raise ValueError("Zero polynomial is not supported here.")
    return len(p) - 1


def _resolve_ratqq(ctx: EngineContext, rat_ref: str) -> Fraction:
    """Resolve a RatQQ object reference to a Fraction."""
    obj = ctx.objects.objects.get(rat_ref)
    if not isinstance(obj, dict):
        raise KeyError(f"Unknown object ref: {rat_ref!r}")
    if obj.get("kind") != "RatQQ":
        raise ValueError(f"Object {rat_ref!r} is not a RatQQ.")
    value = obj.get("value")
    if not isinstance(value, str) or not value:
        raise ValueError(f"RatQQ object {rat_ref!r} is missing a canonical value.")
    return Fraction(value)


def _extract_group_fact_info(result: ProcedureResult) -> tuple[str, str]:
    """Extract (galois_group_fact_id, group_ref) from a subprocedure result."""
    if not result.facts:
        raise ValueError("Subprocedure returned no facts; cannot extract Galois group fact.")

    for fact in reversed(result.facts):
        claim = fact.get("claim", {})
        if claim.get("pred") != "GaloisGroup":
            continue
        fid = fact.get("id")
        args = claim.get("args")
        if not isinstance(fid, str) or not fid:
            raise ValueError("Subprocedure returned malformed GaloisGroup fact id.")
        if not isinstance(args, list) or len(args) != 2:
            raise ValueError("Subprocedure returned malformed GaloisGroup claim.")
        group_ref = args[1].get("ref") if isinstance(args[1], dict) else None
        if not isinstance(group_ref, str) or not group_ref:
            raise ValueError("Subprocedure returned malformed GaloisGroup group ref.")
        return fid, group_ref

    raise ValueError("Subprocedure returned no GaloisGroup fact.")


def _group_alias(ctx: EngineContext, group_ref: str) -> str:
    """Return a friendly group name from a GroupId object if available."""
    obj = ctx.objects.objects.get(group_ref)
    if isinstance(obj, dict):
        alias = obj.get("alias")
        if isinstance(alias, str) and alias:
            return alias
    return group_ref.split(".", 1)[1] if "." in group_ref else group_ref


def _ensure_subgroup_fact(
    ctx: EngineContext,
    *,
    poly_ref: str,
) -> tuple[list[dict[str, Any]], str, str]:
    """Ensure the irreducible subprocedure for `poly_ref` has been run.

    Returns:
        (new_facts, galois_group_fact_id, group_ref)
    """
    gg_map = ctx.cache.setdefault("_galois_group_fact_by_poly", {})
    if not isinstance(gg_map, dict):
        raise TypeError("ctx.cache['_galois_group_fact_by_poly'] must be a dict")

    group_ref_map = ctx.cache.setdefault("_galois_group_ref_by_poly", {})
    if not isinstance(group_ref_map, dict):
        raise TypeError("ctx.cache['_galois_group_ref_by_poly'] must be a dict")

    if poly_ref in gg_map and poly_ref in group_ref_map:
        fid = str(gg_map[poly_ref])
        gid = str(group_ref_map[poly_ref])
        if fid and gid:
            return [], fid, gid

    deg = _poly_degree(ctx, poly_ref)
    proc = ctx.registry.irreducible_procedures.get(deg)
    if proc is None:
        raise ValueError(f"No irreducible procedure registered for degree {deg}.")

    res = proc.run(ctx, poly_ref=poly_ref)
    fact_id, group_ref = _extract_group_fact_info(res)
    gg_map[poly_ref] = fact_id
    group_ref_map[poly_ref] = group_ref
    return list(res.facts), fact_id, group_ref


def _linear_degree_premises(
    ctx: EngineContext,
    *,
    distinct_refs: list[str],
    nonlinear_refs: list[str],
) -> list[str]:
    """Return Degree(linear_factor,1) premises for all distinct remaining linear factors."""
    nonlinear_set = set(nonlinear_refs)
    return [_degree_fact_id(ctx, ref) for ref in distinct_refs if ref not in nonlinear_set]


@dataclass(frozen=True)
class _FactorRunInfo:
    """Cached local summary of a factor subprocedure run."""

    facts: list[dict[str, Any]]
    group_fact_id: str
    group_ref: str
    radical_fact_id: str | None
    radical_roots_ref: str | None
    discriminant_fact_id: str | None
    discriminant_ref: str | None
    disc_square_fact_id: str | None
    disc_nonsquare_fact_id: str | None
    square_disc_fact_id: str | None
    nonsquare_disc_fact_id: str | None


def _claim_ref_arg(claim: dict[str, Any], index: int) -> str | None:
    """Return ``claim.args[index].ref`` when present and well-formed."""
    args = claim.get("args")
    if not isinstance(args, list) or index >= len(args):
        return None
    arg = args[index]
    if not isinstance(arg, dict):
        return None
    ref = arg.get("ref")
    return ref if isinstance(ref, str) and ref else None


def _collect_factor_run_info(
    ctx: EngineContext,
    *,
    poly_ref: str,
    result: ProcedureResult,
) -> _FactorRunInfo:
    """Collect the reusable facts emitted by a single irreducible subprocedure run."""
    group_fact_id: str | None = None
    group_ref: str | None = None
    radical_fact_id: str | None = None
    radical_roots_ref: str | None = None
    discriminant_fact_id: str | None = None
    discriminant_ref: str | None = None
    disc_square_fact_id: str | None = None
    disc_nonsquare_fact_id: str | None = None
    square_disc_fact_id: str | None = None
    nonsquare_disc_fact_id: str | None = None

    for fact in result.facts:
        claim = fact.get("claim", {})
        if not isinstance(claim, dict):
            continue
        pred = claim.get("pred")
        if not isinstance(pred, str):
            continue
        fid = fact.get("id")
        if not isinstance(fid, str) or not fid:
            continue

        if pred == "GaloisGroup" and _claim_ref_arg(claim, 0) == poly_ref:
            ref = _claim_ref_arg(claim, 1)
            if ref is not None:
                group_fact_id = fid
                group_ref = ref
        elif pred == "RadicalRoots" and _claim_ref_arg(claim, 0) == poly_ref:
            ref = _claim_ref_arg(claim, 1)
            if ref is not None:
                radical_fact_id = fid
                radical_roots_ref = ref
        elif pred == "Discriminant" and _claim_ref_arg(claim, 0) == poly_ref:
            ref = _claim_ref_arg(claim, 1)
            if ref is not None:
                discriminant_fact_id = fid
                discriminant_ref = ref
        elif pred == "DiscSquareQQ" and _claim_ref_arg(claim, 0) == poly_ref:
            disc_square_fact_id = fid
        elif pred == "DiscNonSquareQQ" and _claim_ref_arg(claim, 0) == poly_ref:
            disc_nonsquare_fact_id = fid

    if discriminant_ref is not None:
        for fact in result.facts:
            claim = fact.get("claim", {})
            if not isinstance(claim, dict):
                continue
            pred = claim.get("pred")
            if not isinstance(pred, str):
                continue
            fid = fact.get("id")
            if not isinstance(fid, str) or not fid:
                continue
            if pred == "IsSquareQQ" and _claim_ref_arg(claim, 0) == discriminant_ref:
                square_disc_fact_id = fid
            elif pred == "NonSquareQQ" and _claim_ref_arg(claim, 0) == discriminant_ref:
                nonsquare_disc_fact_id = fid

    if group_fact_id is None or group_ref is None:
        raise ValueError(f"Subprocedure for {poly_ref!r} did not emit GaloisGroup(poly_ref, G).")

    gg_map = ctx.cache.setdefault("_galois_group_fact_by_poly", {})
    if isinstance(gg_map, dict):
        gg_map[poly_ref] = group_fact_id
    group_ref_map = ctx.cache.setdefault("_galois_group_ref_by_poly", {})
    if isinstance(group_ref_map, dict):
        group_ref_map[poly_ref] = group_ref

    if radical_fact_id is not None and radical_roots_ref is not None:
        radical_map = ctx.cache.setdefault("_radical_roots_fact_by_poly", {})
        if isinstance(radical_map, dict):
            radical_map[poly_ref] = radical_fact_id
        radical_ref_map = ctx.cache.setdefault("_radical_roots_ref_by_poly", {})
        if isinstance(radical_ref_map, dict):
            radical_ref_map[poly_ref] = radical_roots_ref

    return _FactorRunInfo(
        facts=list(result.facts),
        group_fact_id=group_fact_id,
        group_ref=group_ref,
        radical_fact_id=radical_fact_id,
        radical_roots_ref=radical_roots_ref,
        discriminant_fact_id=discriminant_fact_id,
        discriminant_ref=discriminant_ref,
        disc_square_fact_id=disc_square_fact_id,
        disc_nonsquare_fact_id=disc_nonsquare_fact_id,
        square_disc_fact_id=square_disc_fact_id,
        nonsquare_disc_fact_id=nonsquare_disc_fact_id,
    )


def _run_factor_subprocedures(
    ctx: EngineContext,
    *,
    distinct_refs: list[str],
) -> tuple[list[dict[str, Any]], dict[str, _FactorRunInfo]]:
    """Run the irreducible subprocedure once for every distinct factor ref."""
    emitted: list[dict[str, Any]] = []
    info: dict[str, _FactorRunInfo] = {}
    for ref in distinct_refs:
        deg = _poly_degree(ctx, ref)
        proc = ctx.registry.irreducible_procedures.get(deg)
        if proc is None:
            raise ValueError(f"No irreducible procedure registered for degree {deg}.")
        result = proc.run(ctx, poly_ref=ref)
        run_info = _collect_factor_run_info(ctx, poly_ref=ref, result=result)
        info[ref] = run_info
        emitted.extend(run_info.facts)
    return emitted, info


def _radical_expr_items_from_ref(ctx: EngineContext, roots_ref: str) -> list[str]:
    """Decode a RadicalExprList object into its ordered item refs."""
    obj = ctx.objects.objects.get(roots_ref)
    if not isinstance(obj, dict):
        raise ValueError(f"Missing RadicalExprList object: {roots_ref!r}")
    if obj.get("kind") != "RadicalExprList":
        raise ValueError(f"Object {roots_ref!r} is not a RadicalExprList")
    items = obj.get("items")
    if not isinstance(items, list) or not all(isinstance(x, str) and x for x in items):
        raise ValueError(f"Malformed RadicalExprList payload for {roots_ref!r}")
    return list(items)


@dataclass(frozen=True)
class ReducibleGaloisGroupProcedure:
    """Classify the Galois group of a reducible polynomial using reducible rules.

    Routing policy:
      - ignore linear factors for the *decision*;
      - work with the order-preserving list of distinct non-linear factor refs;
      - dispatch on the resulting signature:
          ()       -> all_linear.trivial
          (2,)     -> single_nonlinear.inherit
          (3,)     -> single_nonlinear.inherit
          (4,)     -> single_nonlinear.inherit
          (2, 2)   -> double_quadratic.C2 / V4
          (2, 3)   -> quadratic_cubic.C6 / S3@2 / D6@2

    Important design point:
      - factors are taken from the certified factorization already emitted by ReducibilityNode;
      - this procedure reuses the exact `factors_list_ref` / `unit_ref` recorded there;
      - it emits one fresh local FactorizationMonicQQ fact for theorem-rule premises,
        without rerunning factorization.
    """

    pred: str = "GaloisGroup"

    rule_all_linear: str = "galois_group.QQ.reducible.all_linear.trivial@1"
    rule_single_inherit: str = "galois_group.QQ.reducible.single_nonlinear.inherit@1"
    rule_double_quadratic_c2: str = "galois_group.QQ.reducible.double_quadratic.C2@1"
    rule_double_quadratic_v4: str = "galois_group.QQ.reducible.double_quadratic.V4@1"
    rule_quadratic_cubic_c6: str = "galois_group.QQ.reducible.quadratic_cubic.C6@1"
    rule_quadratic_cubic_s3: str = "galois_group.QQ.reducible.quadratic_cubic.S3@2"
    rule_quadratic_cubic_d6: str = "galois_group.QQ.reducible.quadratic_cubic.D6@2"

    factorization_rule: str = "factorization.QQ.monic@1"

    aux_rat_prefix: str = "rat.reducible.aux."

    group_trivial_id: str = "group.trivial"
    group_c2_id: str = "group.C2"
    group_v4_id: str = "group.V4"
    group_c6_id: str = "group.C6"
    group_s3_id: str = "group.S3"
    group_d6_id: str = "group.D6"

    def run(self, ctx: EngineContext, *, poly_ref: str) -> ProcedureResult:
        """Run the reducible Galois-group classifier."""
        red_out = _get_reducibility_out(ctx, poly_ref=poly_ref)

        factors_list_ref_raw = red_out.get("factors_list_ref")
        unit_ref_raw = red_out.get("unit_ref")

        if not isinstance(factors_list_ref_raw, str) or not factors_list_ref_raw:
            raise ValueError(
                f"ReducibilityNode output for {poly_ref!r} is missing a valid factors_list_ref."
            )
        if not isinstance(unit_ref_raw, str) or not unit_ref_raw:
            raise ValueError(
                f"ReducibilityNode output for {poly_ref!r} is missing a valid unit_ref."
            )

        factors_list_ref = factors_list_ref_raw
        unit_ref = unit_ref_raw

        factor_items = _factorization_items_from_ref(ctx, factors_list_ref)
        if len(factor_items) < 2:
            raise ValueError(
                "ReducibleGaloisGroupProcedure expects a reducible certified factorization "
                "with at least two factor occurrences."
            )

        distinct_refs = _distinct_factor_refs(factor_items)
        distinct_degrees = {ref: _poly_degree(ctx, ref) for ref in distinct_refs}
        nonlinear_refs = [ref for ref in distinct_refs if distinct_degrees[ref] > 1]
        signature = tuple(sorted(distinct_degrees[ref] for ref in nonlinear_refs))

        factorization_fact_id = _next_fact_id(ctx)
        factorization_fact = {
            "id": factorization_fact_id,
            "claim": {
                "pred": "FactorizationMonicQQ",
                "args": [
                    {"ref": poly_ref},
                    {"ref": factors_list_ref},
                    {"ref": unit_ref},
                ],
            },
            "rule": self.factorization_rule,
            "premises": [],
            "statement": "Certified factorization in Q[x] with monic factors (reused locally).",
        }

        subrun_facts, factor_runs = _run_factor_subprocedures(ctx, distinct_refs=distinct_refs)

        if signature == ():
            facts, out = self._emit_all_linear(
                ctx,
                poly_ref=poly_ref,
                factorization_fact_id=factorization_fact_id,
                distinct_refs=distinct_refs,
            )
        elif signature in {(2,), (3,), (4,)}:
            facts, out = self._emit_single_nonlinear(
                ctx,
                poly_ref=poly_ref,
                factorization_fact_id=factorization_fact_id,
                distinct_refs=distinct_refs,
                nonlinear_ref=nonlinear_refs[0],
                factor_runs=factor_runs,
            )
        elif signature == (2, 2):
            facts, out = self._emit_double_quadratic(
                ctx,
                poly_ref=poly_ref,
                factorization_fact_id=factorization_fact_id,
                distinct_refs=distinct_refs,
                quadratic_refs=nonlinear_refs,
                factor_runs=factor_runs,
            )
        elif signature == (2, 3):
            facts, out = self._emit_quadratic_cubic(
                ctx,
                poly_ref=poly_ref,
                factorization_fact_id=factorization_fact_id,
                distinct_refs=distinct_refs,
                nonlinear_refs=nonlinear_refs,
                factor_runs=factor_runs,
            )
        else:
            raise ValueError(
                "Unsupported reducible signature after ignoring linears: " f"{signature!r}."
            )

        radical_facts, radical_out = self._maybe_emit_reducible_radical_roots(
            ctx,
            poly_ref=poly_ref,
            factorization_fact_id=factorization_fact_id,
            factor_occurrence_refs=factor_items,
            factor_runs=factor_runs,
        )

        out = dict(out)
        out.update(radical_out)
        out["factors_list_ref"] = factors_list_ref
        out["unit_ref"] = unit_ref
        out["local_factorization_fact_id"] = factorization_fact_id
        out["factor_occurrence_refs"] = list(factor_items)

        source_factorization_fact_id = red_out.get("factorization_fact_id")
        if isinstance(source_factorization_fact_id, str) and source_factorization_fact_id:
            out["source_factorization_fact_id"] = source_factorization_fact_id

        return ProcedureResult(
            facts=[factorization_fact, *subrun_facts, *facts, *radical_facts],
            out=out,
        )

    def _emit_all_linear(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        factorization_fact_id: str,
        distinct_refs: list[str],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Emit the all-linear reducible branch."""
        ctx.objects.put_groupid(
            self.group_trivial_id,
            system="smallgroup",
            order=1,
            index=1,
            alias="Trivial",
        )

        degree_premises = [_degree_fact_id(ctx, ref) for ref in distinct_refs]
        fact = {
            "id": _next_fact_id(ctx),
            "claim": {
                "pred": self.pred,
                "args": [{"ref": poly_ref}, {"ref": self.group_trivial_id}],
            },
            "rule": self.rule_all_linear,
            "premises": [factorization_fact_id, *degree_premises],
            "statement": "All distinct factors are linear over Q, so the Galois group is trivial.",
        }
        return [fact], {
            "decision": "galois_group",
            "branch": "reducible",
            "case": "all_linear",
            "signature": [],
            "distinct_factor_refs": list(distinct_refs),
            "nonlinear_factor_refs": [],
            "group": "Trivial",
            "group_ref": self.group_trivial_id,
        }

    def _emit_single_nonlinear(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        factorization_fact_id: str,
        distinct_refs: list[str],
        nonlinear_ref: str,
        factor_runs: dict[str, _FactorRunInfo],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Emit the single-nonlinear reducible branch using inherit@1."""
        run_info = factor_runs[nonlinear_ref]
        subgroup_fact_id = run_info.group_fact_id
        subgroup_ref = run_info.group_ref
        degree_premises = [_degree_fact_id(ctx, ref) for ref in distinct_refs]
        irreducible_fact = _irreducible_fact_id(ctx, nonlinear_ref)

        fact = {
            "id": _next_fact_id(ctx),
            "claim": {
                "pred": self.pred,
                "args": [{"ref": poly_ref}, {"ref": subgroup_ref}],
            },
            "rule": self.rule_single_inherit,
            "premises": [factorization_fact_id, *degree_premises,
                         irreducible_fact, subgroup_fact_id],
            "statement": (
                "The splitting field is already generated by the unique distinct "
                "non-linear irreducible factor."
            ),
        }

        return [fact], {
            "decision": "galois_group",
            "branch": "reducible",
            "case": "single_nonlinear",
            "signature": [_poly_degree(ctx, nonlinear_ref)],
            "distinct_factor_refs": list(distinct_refs),
            "nonlinear_factor_refs": [nonlinear_ref],
            "controller_ref": nonlinear_ref,
            "group": _group_alias(ctx, subgroup_ref),
            "group_ref": subgroup_ref,
        }

    def _emit_double_quadratic(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        factorization_fact_id: str,
        distinct_refs: list[str],
        quadratic_refs: list[str],
        factor_runs: dict[str, _FactorRunInfo],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Emit the double-quadratic reducible branch."""
        if len(quadratic_refs) != 2:
            raise ValueError("double_quadratic branch expects exactly two distinct quadratic refs.")
        q1_ref, q2_ref = quadratic_refs
        _ = factor_runs

        disc1_nodes, disc1_out = ctx.registry.discriminant.run(ctx, poly_ref=q1_ref)
        disc2_nodes, disc2_out = ctx.registry.discriminant.run(ctx, poly_ref=q2_ref)

        d1_ref = disc1_out.get("disc_ref")
        d2_ref = disc2_out.get("disc_ref")
        if not isinstance(d1_ref, str) or not d1_ref:
            raise ValueError("Missing discriminant ref for first quadratic factor.")
        if not isinstance(d2_ref, str) or not d2_ref:
            raise ValueError("Missing discriminant ref for second quadratic factor.")

        d1 = _resolve_ratqq(ctx, d1_ref)
        d2 = _resolve_ratqq(ctx, d2_ref)
        w = d1 * d2
        w_ref = ctx.objects.new_id(self.aux_rat_prefix)
        ctx.objects.put_rat(w_ref, w)

        sq_nodes, sq_out = ctx.registry.square.run(ctx, rat_ref=w_ref)
        sq_decision = str(sq_out.get("decision", ""))
        sq_facts = sq_out.get("facts", {})
        if not isinstance(sq_facts, dict):
            raise TypeError("SquareNode out['facts'] must be a dict.")

        disc1_fact = str(disc1_out["facts"]["discriminant"])
        disc2_fact = str(disc2_out["facts"]["discriminant"])
        q1_deg_fact = _degree_fact_id(ctx, q1_ref)
        q2_deg_fact = _degree_fact_id(ctx, q2_ref)
        q1_irr_fact = _irreducible_fact_id(ctx, q1_ref)
        q2_irr_fact = _irreducible_fact_id(ctx, q2_ref)
        linear_degree_premises = _linear_degree_premises(
            ctx,
            distinct_refs=distinct_refs,
            nonlinear_refs=quadratic_refs,
        )

        if sq_decision == "square":
            ctx.objects.put_groupid(
                self.group_c2_id,
                system="smallgroup",
                order=2,
                index=1,
                alias="C2",
            )
            square_fact_raw = sq_facts.get("square")
            if square_fact_raw is None:
                raise ValueError("SquareNode square branch is missing IsSquareQQ(w).")
            square_fact = str(square_fact_raw)
            if not square_fact:
                raise ValueError("SquareNode square branch returned an empty IsSquareQQ(w) id.")

            group_ref = self.group_c2_id
            rule_id = self.rule_double_quadratic_c2
            aux_fact = square_fact
            group_name = "C2"
        elif sq_decision == "nonsquare":
            ctx.objects.put_groupid(
                self.group_v4_id,
                system="smallgroup",
                order=4,
                index=2,
                alias="V4",
            )
            nonsquare_fact_raw = sq_facts.get("non_square")
            if nonsquare_fact_raw is None:
                raise ValueError("SquareNode nonsquare branch is missing NonSquareQQ(w).")
            nonsquare_fact = str(nonsquare_fact_raw)
            if not nonsquare_fact:
                raise ValueError("SquareNode nonsquare branch returned an empty NonSquareQQ(w) id.")

            group_ref = self.group_v4_id
            rule_id = self.rule_double_quadratic_v4
            aux_fact = nonsquare_fact
            group_name = "V4"
        else:
            raise ValueError(f"Unexpected square decision for d1*d2: {sq_decision!r}")

        fact = {
            "id": _next_fact_id(ctx),
            "claim": {
                "pred": self.pred,
                "args": [{"ref": poly_ref}, {"ref": group_ref}],
            },
            "rule": rule_id,
            "premises": [
                factorization_fact_id,
                q1_deg_fact,
                q1_irr_fact,
                disc1_fact,
                q2_deg_fact,
                q2_irr_fact,
                disc2_fact,
                *linear_degree_premises,
                aux_fact,
            ],
            "statement": "Reducible [2,2] branch classified via the squarehood of d1*d2.",
        }

        return [*disc1_nodes, *disc2_nodes, *sq_nodes, fact], {
            "decision": "galois_group",
            "branch": "reducible",
            "case": "double_quadratic",
            "signature": [2, 2],
            "distinct_factor_refs": list(distinct_refs),
            "nonlinear_factor_refs": list(quadratic_refs),
            "d1_ref": d1_ref,
            "d2_ref": d2_ref,
            "product_ref": w_ref,
            "product_value": _frac_to_str(w),
            "product_squarehood": sq_out,
            "group": group_name,
            "group_ref": group_ref,
        }

    def _emit_quadratic_cubic(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        factorization_fact_id: str,
        distinct_refs: list[str],
        nonlinear_refs: list[str],
        factor_runs: dict[str, _FactorRunInfo],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Emit the quadratic-cubic reducible branch."""
        if len(nonlinear_refs) != 2:
            raise ValueError("quadratic_cubic branch expects exactly two distinct non-linear refs.")

        by_deg = {ref: _poly_degree(ctx, ref) for ref in nonlinear_refs}
        quadratics = [ref for ref in nonlinear_refs if by_deg[ref] == 2]
        cubics = [ref for ref in nonlinear_refs if by_deg[ref] == 3]
        if len(quadratics) != 1 or len(cubics) != 1:
            raise ValueError("quadratic_cubic branch expects one quadratic and one cubic factor.")
        q_ref = quadratics[0]
        c_ref = cubics[0]
        c_info = factor_runs[c_ref]

        q_deg_fact = _degree_fact_id(ctx, q_ref)
        c_deg_fact = _degree_fact_id(ctx, c_ref)
        q_irr_fact = _irreducible_fact_id(ctx, q_ref)
        c_irr_fact = _irreducible_fact_id(ctx, c_ref)
        linear_degree_premises = _linear_degree_premises(
            ctx,
            distinct_refs=distinct_refs,
            nonlinear_refs=[q_ref, c_ref],
        )

        disc_q_nodes, disc_q_out = ctx.registry.discriminant.run(ctx, poly_ref=q_ref)
        d1_ref = disc_q_out.get("disc_ref")
        if not isinstance(d1_ref, str) or not d1_ref:
            raise ValueError("Missing discriminant ref for the quadratic factor.")
        disc_q_fact = str(disc_q_out["facts"]["discriminant"])

        d2_ref = c_info.discriminant_ref
        disc_c_fact = c_info.discriminant_fact_id
        if d2_ref is None or disc_c_fact is None:
            raise ValueError("Cubic subprocedure did not emit the expected discriminant facts.")

        if c_info.square_disc_fact_id is not None:
            sq_d2_out = {
                "decision": "square",
                "facts": {
                    "square": c_info.square_disc_fact_id,
                },
            }
        elif c_info.nonsquare_disc_fact_id is not None:
            sq_d2_out = {
                "decision": "nonsquare",
                "facts": {
                    "non_square": c_info.nonsquare_disc_fact_id,
                },
            }
        else:
            raise ValueError(
                "Cubic subprocedure did not emit squarehood information "
                "for its discriminant."
            )

        if c_info.disc_square_fact_id is not None:
            ctx.objects.put_groupid(
                self.group_c6_id,
                system="smallgroup",
                order=6,
                index=1,
                alias="C6",
            )
            fact = {
                "id": _next_fact_id(ctx),
                "claim": {
                    "pred": self.pred,
                    "args": [{"ref": poly_ref}, {"ref": self.group_c6_id}],
                },
                "rule": self.rule_quadratic_cubic_c6,
                "premises": [
                    factorization_fact_id,
                    q_deg_fact,
                    q_irr_fact,
                    disc_q_fact,
                    c_deg_fact,
                    c_irr_fact,
                    disc_c_fact,
                    *linear_degree_premises,
                    c_info.disc_square_fact_id,
                ],
                "statement": (
                    "Reducible [2,3] branch with square cubic discriminant classified as C6."
                ),
            }
            return [*disc_q_nodes, fact], {
                "decision": "galois_group",
                "branch": "reducible",
                "case": "quadratic_cubic",
                "signature": [2, 3],
                "distinct_factor_refs": list(distinct_refs),
                "nonlinear_factor_refs": [q_ref, c_ref],
                "quadratic_ref": q_ref,
                "cubic_ref": c_ref,
                "d1_ref": d1_ref,
                "d2_ref": d2_ref,
                "cubic_discriminant_squarehood": sq_d2_out,
                "group": "C6",
                "group_ref": self.group_c6_id,
            }

        nonsquare_d2_fact = c_info.nonsquare_disc_fact_id
        if nonsquare_d2_fact is None:
            raise ValueError(
                "Cubic subprocedure did not emit "
                "NonSquareQQ(d2) for the [2,3] branch."
            )

        d1 = _resolve_ratqq(ctx, d1_ref)
        d2 = _resolve_ratqq(ctx, d2_ref)
        w = d1 * d2
        w_ref = ctx.objects.new_id(self.aux_rat_prefix)
        ctx.objects.put_rat(w_ref, w)

        sq_w_nodes, sq_w_out = ctx.registry.square.run(ctx, rat_ref=w_ref)
        sq_w_decision = str(sq_w_out.get("decision", ""))
        sq_w_facts = sq_w_out.get("facts", {})
        if not isinstance(sq_w_facts, dict):
            raise TypeError("SquareNode out['facts'] for d1*d2 must be a dict.")

        if sq_w_decision == "square":
            ctx.objects.put_groupid(
                self.group_s3_id,
                system="smallgroup",
                order=6,
                index=2,
                alias="S3",
            )
            square_w_raw = sq_w_facts.get("square")
            if square_w_raw is None:
                raise ValueError("SquareNode square branch is missing IsSquareQQ(d1*d2).")
            square_w_fact = str(square_w_raw)
            if not square_w_fact:
                raise ValueError("SquareNode square branch returned an empty IsSquareQQ(d1*d2) id.")

            group_ref = self.group_s3_id
            group_name = "S3"
            rule_id = self.rule_quadratic_cubic_s3
            aux_fact = square_w_fact
        elif sq_w_decision == "nonsquare":
            ctx.objects.put_groupid(
                self.group_d6_id,
                system="smallgroup",
                order=12,
                index=4,
                alias="D6",
            )
            nonsquare_w_raw = sq_w_facts.get("non_square")
            if nonsquare_w_raw is None:
                raise ValueError("SquareNode nonsquare branch is missing NonSquareQQ(d1*d2).")
            nonsquare_w_fact = str(nonsquare_w_raw)
            if not nonsquare_w_fact:
                raise ValueError(
                    "SquareNode nonsquare branch returned an empty NonSquareQQ(d1*d2) id."
                )

            group_ref = self.group_d6_id
            group_name = "D6"
            rule_id = self.rule_quadratic_cubic_d6
            aux_fact = nonsquare_w_fact
        else:
            raise ValueError(f"Unexpected square decision for d1*d2: {sq_w_decision!r}")

        fact = {
            "id": _next_fact_id(ctx),
            "claim": {
                "pred": self.pred,
                "args": [{"ref": poly_ref}, {"ref": group_ref}],
            },
            "rule": rule_id,
            "premises": [
                factorization_fact_id,
                q_deg_fact,
                q_irr_fact,
                disc_q_fact,
                c_deg_fact,
                c_irr_fact,
                disc_c_fact,
                *linear_degree_premises,
                nonsquare_d2_fact,
                aux_fact,
            ],
            "statement": "Reducible [2,3] branch classified via d2 and d1*d2 squarehood.",
        }

        return [*disc_q_nodes, *sq_w_nodes, fact], {
            "decision": "galois_group",
            "branch": "reducible",
            "case": "quadratic_cubic",
            "signature": [2, 3],
            "distinct_factor_refs": list(distinct_refs),
            "nonlinear_factor_refs": [q_ref, c_ref],
            "quadratic_ref": q_ref,
            "cubic_ref": c_ref,
            "d1_ref": d1_ref,
            "d2_ref": d2_ref,
            "cubic_discriminant_squarehood": sq_d2_out,
            "product_ref": w_ref,
            "product_value": _frac_to_str(w),
            "product_squarehood": sq_w_out,
            "group": group_name,
            "group_ref": group_ref,
        }

    def _maybe_emit_reducible_radical_roots(
        self,
        ctx: EngineContext,
        *,
        poly_ref: str,
        factorization_fact_id: str,
        factor_occurrence_refs: list[str],
        factor_runs: dict[str, _FactorRunInfo],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Compose reducible radical roots from the already-run factor subprocedures."""
        distinct_refs = _distinct_factor_refs(factor_occurrence_refs)
        if any(
            factor_runs[ref].radical_fact_id is None or factor_runs[ref].radical_roots_ref is None
            for ref in distinct_refs
        ):
            return [], {"radical_roots_supported": False}

        composed_items: list[str] = []
        for ref in factor_occurrence_refs:
            roots_ref = factor_runs[ref].radical_roots_ref
            assert roots_ref is not None
            composed_items.extend(_radical_expr_items_from_ref(ctx, roots_ref))

        roots_obj_id = ctx.objects.new_id("rlist.reducible.")
        ctx.objects.put_radical_expr_list(roots_obj_id, composed_items)

        premises = [factorization_fact_id]
        premises.extend(
            str(factor_runs[ref].radical_fact_id)
            for ref in distinct_refs
            if factor_runs[ref].radical_fact_id is not None
        )

        fact_id = _next_fact_id(ctx)
        fact = {
            "id": fact_id,
            "claim": {
                "pred": "RadicalRoots",
                "args": [{"ref": poly_ref}, {"ref": roots_obj_id}],
            },
            "rule": "radical_roots.QQ.reducible.compose@2",
            "premises": premises,
            "statement": "Canonical reducible radical roots "
            "composed from certified factor-level lists.",
        }

        radical_map = ctx.cache.setdefault("_radical_roots_fact_by_poly", {})
        if isinstance(radical_map, dict):
            radical_map[poly_ref] = fact_id
        radical_ref_map = ctx.cache.setdefault("_radical_roots_ref_by_poly", {})
        if isinstance(radical_ref_map, dict):
            radical_ref_map[poly_ref] = roots_obj_id

        return [fact], {
            "radical_roots_supported": True,
            "radical_roots_fact_id": fact_id,
            "radical_roots_ref": roots_obj_id,
        }
