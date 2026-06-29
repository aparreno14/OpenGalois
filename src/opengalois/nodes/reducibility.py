from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING, Any, cast

from opengalois.algorithms.factorization import (
    factorize_le5_multiplicity,
    zassenhaus_irreducibility_trace_le5,
)
from opengalois.engine.context import _ensure_degree_fact, _next_fact_id, _resolve_poly_desc_QQ
from opengalois.polyops.desc_qx import _leading, _trim_leading_zeros_desc

if TYPE_CHECKING:
    from opengalois.engine.context import EngineContext


def _normalize_factor_output(raw: Any) -> list[tuple[list[Fraction], int]]:
    """Normalize factorization output to [(poly_desc, multiplicity), ...].

    Supported shapes:
      - (unit, [(poly, e), ...])  -> unit part ignored here; ReducibilityNode uses lc(input)
      - [(poly, e), ...]
      - [poly, poly, ...]         -> multiplicity 1 for each entry
    """
    if isinstance(raw, tuple) and len(raw) == 2:
        raw = raw[1]

    if not isinstance(raw, list):
        raise TypeError("factorize_le5 must return a list (or (unit, list)).")

    if not raw:
        return []

    if all(
        isinstance(x, tuple)
        and len(x) == 2
        and isinstance(x[0], list)
        and isinstance(x[1], int)
        for x in raw
    ):
        out: list[tuple[list[Fraction], int]] = []
        for poly, e in cast(list[tuple[list[Fraction], int]], raw):
            out.append((_trim_leading_zeros_desc(poly), int(e)))
        return out

    if all(isinstance(x, list) for x in raw):
        out2: list[tuple[list[Fraction], int]] = []
        for poly in cast(list[list[Fraction]], raw):
            out2.append((_trim_leading_zeros_desc(poly), 1))
        return out2

    raise TypeError("Unsupported factorize_le5 output shape.")


def _is_nontrivial_factorization(
    original: list[Fraction],
    factors: list[tuple[list[Fraction], int]],
) -> bool:
    """Return True iff the factorization is genuinely nontrivial."""
    original = _trim_leading_zeros_desc(original)
    if not original or not factors:
        return False

    if len(factors) >= 2:
        return True

    poly, multiplicity = factors[0]
    poly = _trim_leading_zeros_desc(poly)
    if multiplicity > 1 and len(poly) > 1:
        return True

    return False


@dataclass(frozen=True)
class ReducibilityNode:
    """Decision-tree node that emits v3 facts, preserving v2 logic.

    Preserved behavior:
      - If reducible: emit FactorizationMonicQQ(f, factors, unit) and IrreducibleQQ(f_i)
        for each irreducible factor.
      - If irreducible: emit IrreducibleQQ(f).

    Important implementation detail:
      - The root input keeps the historical deterministic refs:
          * unit ref      = "rat.unit"
          * factors ref   = "list.factors"
      - Nested reducibility calls (e.g. reducibility of the quartic resolvent) allocate
        fresh refs to avoid object-id collisions inside the same certificate.
    """

    # v3 predicates
    factorization_pred: str = "FactorizationMonicQQ"
    irreducible_pred: str = "IrreducibleQQ"

    # v3 rules
    factorization_rule: str = "factorization.QQ.monic@1"
    irreducible_rule_deg1: str = "irreducible.QQ.deg1_trivial@1"
    irreducible_rule_deg2_5: str = "irreducible.QQ.deg5_recompute@1"
    irreducible_rule_zassenhaus_trace: str = "irreducible.QQ.zassenhaus_trace@1"

    # object prefixes / default object ids
    factor_id_prefix: str = "poly.f"
    unit_id: str = "rat.unit"
    factors_list_id: str = "list.factors"

    def _factor_list_obj_id(self, ctx: EngineContext, *, poly_ref: str) -> str:
        """Return a collision-safe PolyQQList object id for this factorization."""
        if poly_ref == "$input":
            return self.factors_list_id
        return ctx.objects.new_id("list.factors.")

    def _unit_obj_id(self, ctx: EngineContext, *, poly_ref: str) -> str:
        """Return a collision-safe RatQQ object id for the factorization unit."""
        if poly_ref == "$input":
            return self.unit_id
        return ctx.objects.new_id("rat.unit.")

    def run(self, ctx: EngineContext, *, poly_ref: str) -> tuple[list[dict[str, Any]], 
                                                                 dict[str, Any]]:
        """Run reducibility analysis and emit FactNodes.

        Args:
            ctx: Engine context containing cache and object store.
            poly_ref: Reference to the polynomial being analyzed ('$input' or an object id).

        Returns:
            (facts, out), where:
              - facts is the list of emitted fact nodes
              - out contains at least:
                    {
                      "poly_ref": ...,
                      "decision": "irreducible" | "reducible",
                    }
                and in the reducible branch additionally:
                    {
                      "factor_refs": [...],        # one ref per base irreducible factor
                      "factors_list_ref": "...",   # PolyQQList ref used in FactorizationMonicQQ
                      "unit_ref": "...",           # RatQQ ref used in FactorizationMonicQQ
                      "factorization_fact_id": "...",
                    }
        """
        pQ = _resolve_poly_desc_QQ(ctx, poly_ref)
        pQ = _trim_leading_zeros_desc(pQ)
        if not pQ:
            raise ValueError("Zero polynomial")

        unit = _leading(pQ)
        if unit == 0:
            raise ValueError("Leading coefficient is zero")

        # factorize the monic normalization
        monic = [c / unit for c in pQ]
        raw = factorize_le5_multiplicity(monic)
        facs = _normalize_factor_output(raw)

        # Always emit/reuse Degree fact for the analyzed polynomial (input or factor).
        facts_prefix: list[dict[str, Any]] = []
        input_degree_fact_id, _ = _ensure_degree_fact(ctx, poly_ref=poly_ref, into=facts_prefix)

        # Reducible branch: emit factorization + irreducible for each factor
        if _is_nontrivial_factorization(monic, facs):
            factor_entries: list[dict[str, Any]] = []  # non-normative compact multiplicity view
            factor_refs: list[str] = []                # one ref per base factor
            items: list[str] = []                      # PolyQQList.items with multiplicity
            facts: list[dict[str, Any]] = list(facts_prefix)

            for poly, e in facs:
                poly = _trim_leading_zeros_desc(poly)
                if not poly or len(poly) < 2:
                    continue

                obj_id = ctx.objects.new_id(self.factor_id_prefix)
                ctx.objects.put_poly(obj_id, poly)
                ctx.cache[obj_id] = poly

                factor_entries.append({"ref": obj_id, "multiplicity": int(e)})
                factor_refs.append(obj_id)
                items.extend([obj_id] * int(e))

                deg = len(poly) - 1
                evidence: dict[str, Any] | None = None
                if deg == 1:
                    rule_id = self.irreducible_rule_deg1
                    statement = "Irreducible over Q (linear factor)."
                else:
                    evidence = zassenhaus_irreducibility_trace_le5(poly)
                    if evidence is not None:
                        rule_id = self.irreducible_rule_zassenhaus_trace
                        statement = "Irreducible over Q by Zassenhaus recombination."
                    else:
                        rule_id = self.irreducible_rule_deg2_5
                        statement = "Irreducible over Q (per-factor)."
                factor_degree_fact_id, _ = _ensure_degree_fact(ctx, poly_ref=obj_id, into=facts)

                irred_fact = {
                    "id": _next_fact_id(ctx),
                    "claim": {"pred": self.irreducible_pred, "args": [{"ref": obj_id}]},
                    "rule": rule_id,
                    "premises": [factor_degree_fact_id],
                    "statement": statement,
                }
                if evidence is not None:
                    irred_fact["evidence"] = evidence
                facts.append(irred_fact)

                irred_map = ctx.cache.setdefault("_irreducible_fact_by_poly", {})
                if not isinstance(irred_map, dict):
                    raise TypeError("ctx.cache['_irreducible_fact_by_poly'] must be a dict")
                irred_map[obj_id] = irred_fact["id"]

            # Store unit + factor-list objects for the factorization fact.
            unit_obj_id = self._unit_obj_id(ctx, poly_ref=poly_ref)
            factors_list_obj_id = self._factor_list_obj_id(ctx, poly_ref=poly_ref)

            ctx.objects.put_rat(unit_obj_id, unit)
            ctx.objects.put_poly_list(factors_list_obj_id, items)

            fact0: dict[str, Any] = {
                "id": _next_fact_id(ctx),
                "claim": {
                    "pred": self.factorization_pred,
                    "args": [
                        {"ref": poly_ref},
                        {"ref": factors_list_obj_id},
                        {"ref": unit_obj_id},
                    ],
                },
                "rule": self.factorization_rule,
                "premises": [],
                "statement": "Factorization in Q[x] with monic factors.",
                # UX/debug parity only (non-normative)
                "data": {"factors_compact": factor_entries},
            }

            facts.insert(0, fact0)
            out = {
                "poly_ref": poly_ref,
                "decision": "reducible",
                "factor_refs": factor_refs,
                "factors_list_ref": factors_list_obj_id,
                "unit_ref": unit_obj_id,
                "factorization_fact_id": fact0["id"],
            }

            red_out_map = ctx.cache.setdefault("_reducibility_out_by_poly", {})
            if not isinstance(red_out_map, dict):
                raise TypeError("ctx.cache['_reducibility_out_by_poly'] must be a dict")
            red_out_map[poly_ref] = dict(out)

            return facts, out

        # Irreducible branch: emit IrreducibleQQ(f)
        deg0 = len(pQ) - 1
        evidence0: dict[str, Any] | None = None
        if deg0 == 1:
            rule_id0 = self.irreducible_rule_deg1
            statement0 = "Irreducible over Q."
        else:
            evidence0 = zassenhaus_irreducibility_trace_le5(pQ)
            if evidence0 is not None:
                rule_id0 = self.irreducible_rule_zassenhaus_trace
                statement0 = "Irreducible over Q by Zassenhaus recombination."
            else:
                rule_id0 = self.irreducible_rule_deg2_5
                statement0 = "Irreducible over Q."

        fact = {
            "id": _next_fact_id(ctx),
            "claim": {"pred": self.irreducible_pred, "args": [{"ref": poly_ref}]},
            "rule": rule_id0,
            "premises": [input_degree_fact_id],
            "statement": statement0,
        }
        if evidence0 is not None:
            fact["evidence"] = evidence0

        irred_map = ctx.cache.setdefault("_irreducible_fact_by_poly", {})
        if not isinstance(irred_map, dict):
            raise TypeError("ctx.cache['_irreducible_fact_by_poly'] must be a dict")
        irred_map[poly_ref] = fact["id"]

        out = {
            "poly_ref": poly_ref,
            "decision": "irreducible",
            "irreducible_fact_id": fact["id"],
        }

        red_out_map = ctx.cache.setdefault("_reducibility_out_by_poly", {})
        if not isinstance(red_out_map, dict):
            raise TypeError("ctx.cache['_reducibility_out_by_poly'] must be a dict")
        red_out_map[poly_ref] = dict(out)

        return [*facts_prefix, fact], out