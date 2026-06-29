# src/opengalois/engine/engine.py
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from ..models import AnalysisOptions
from ..polyops.desc_qx import _trim_leading_zeros_desc
from .context import EngineContext
from .objects import ObjectStore
from .registry import EngineRegistry


@dataclass
class EngineResult:
    """Encapsulates the final output of the analysis engine.

    Attributes:
        objects (dict[str, Any]): The collection of all canonical objects generated.
        facts (list[dict[str, Any]]): The list of proof facts generated.
        summary (dict[str, Any]): A human-readable or UX-focused summary of the analysis.
    """

    objects: dict[str, Any]
    facts: list[dict[str, Any]]
    summary: dict[str, Any]


_UNSOLVABLE_GROUPS = {"S5", "A5"}


def _summary_from_proc_out(
    *,
    decision: str,
    proc_out: dict[str, Any],
) -> dict[str, Any]:
    """Build a lightweight engine summary from a procedure output map."""
    group = proc_out.get("group")
    if not isinstance(group, str) or not group:
        return {
            "status": "unclassified",
            "solvable_by_radicals": None,
            "galois_group": "UNKNOWN",
            "transitive_group_id": None,
        }

    status = "reducible" if decision == "reducible" else "irreducible"
    return {
        "status": status,
        "solvable_by_radicals": group not in _UNSOLVABLE_GROUPS,
        "galois_group": group,
        "transitive_group_id": None,
    }


def _extract_group_fact_info(facts: list[dict[str, Any]]) -> tuple[str, str]:
    """Extract the last emitted GaloisGroup fact id and its GroupId ref."""
    for fact in reversed(facts):
        claim = fact.get("claim", {})
        if claim.get("pred") != "GaloisGroup":
            continue
        fid = fact.get("id")
        args = claim.get("args")
        if not isinstance(fid, str) or not fid:
            raise ValueError("Malformed GaloisGroup fact id in procedure output.")
        if not isinstance(args, list) or len(args) != 2:
            raise ValueError("Malformed GaloisGroup claim in procedure output.")
        group_ref = args[1].get("ref") if isinstance(args[1], dict) else None
        if not isinstance(group_ref, str) or not group_ref:
            raise ValueError("Malformed GroupId reference in procedure output.")
        return fid, group_ref
    raise ValueError("Procedure output does not contain a GaloisGroup fact.")


def _is_monic_depressed_quintic(coeffs: list[Fraction]) -> bool:
    """Return True iff the polynomial is exactly a monic depressed quintic.

    Expected descending form:
        x^5 + 0*x^4 + a*x^3 + b*x^2 + c*x + d
    """
    trimmed = _trim_leading_zeros_desc(coeffs)
    return len(trimmed) == 6 and trimmed[0] == 1 and trimmed[1] == 0


def run_engine(coeffs: list[Fraction], *, options: AnalysisOptions) -> EngineResult:
    """Main entry point to execute the analysis engine on a polynomial.

    Orchestrates the context creation, initial parsing, and node dispatching based
    on the degree of the input polynomial.

    Args:
        coeffs (list[Fraction]): Input polynomial coefficients in descending order.
        options (AnalysisOptions): Configuration options for the analysis.

    Returns:
        EngineResult: The complete result including objects, proof facts, and summary.
    """
    coeffs = _trim_leading_zeros_desc(coeffs)
    deg = len(coeffs) - 1

    ctx = EngineContext(options=options, objects=ObjectStore(), registry=EngineRegistry.default())
    ctx.cache["$input_poly"] = coeffs

    facts: list[dict[str, Any]] = []

    red = ctx.registry.reducibility
    red_nodes, red_out = red.run(ctx, poly_ref="$input")
    facts.extend(red_nodes)

    decision = str(red_out.get("decision", ""))

    if decision == "irreducible":
        proc = ctx.registry.irreducible_procedures.get(deg)
        if proc is None:
            raise ValueError(f"No irreducible procedure registered for degree {deg}")
        proc_res = proc.run(ctx, poly_ref="$input")
        facts.extend(proc_res.facts)
        summary = _summary_from_proc_out(decision=decision, proc_out=proc_res.out)
        return EngineResult(objects=ctx.objects.objects, facts=facts, summary=summary)

    if decision == "reducible":
        proc_res = ctx.registry.reducible.run(ctx, poly_ref="$input")
        facts.extend(proc_res.facts)
        summary = _summary_from_proc_out(decision=decision, proc_out=proc_res.out)
        return EngineResult(objects=ctx.objects.objects, facts=facts, summary=summary)

    summary = {
        "status": "unclassified",
        "solvable_by_radicals": None,
        "galois_group": "UNKNOWN",
        "transitive_group_id": None,
    }
    return EngineResult(objects=ctx.objects.objects, facts=facts, summary=summary)
