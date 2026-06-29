# ruff: noqa: D102,D103
"""Fact-graph traversal utilities for explanations."""

from __future__ import annotations

from .context import ExplainContext, FactView
from .errors import ExplainInvalidCertificateError

_INTERESTING_PREDS: tuple[str, ...] = (
    "GaloisGroup",
    "SolvableByRadicals",
    "NonSolvableByRadicals",
    "RadicalRoots",
)


def dependency_subgraph(ctx: ExplainContext, target_fact_id: str) -> tuple[FactView, ...]:
    """Return the premise-closed subgraph of a target fact.

    The returned order follows the certificate order. Since valid certificates
    require premises to precede conclusions, this is the topological order used
    by the clean proof renderer.
    """
    visited: set[str] = set()

    def visit(fact_id: str) -> None:
        if fact_id in visited:
            return
        fact = ctx.get_fact(fact_id)
        for premise_id in fact.premises:
            if premise_id not in ctx.fact_by_id:
                raise ExplainInvalidCertificateError(
                    f"fact {fact.fact_id} references unknown premise {premise_id}"
                )
            visit(premise_id)
        visited.add(fact_id)

    visit(target_fact_id)
    return tuple(fact for fact in ctx.facts if fact.fact_id in visited)


def merge_dependency_subgraphs(
    ctx: ExplainContext,
    target_fact_ids: tuple[str, ...],
) -> tuple[FactView, ...]:
    """Return the union of several target subgraphs in topological order."""
    selected: set[str] = set()
    for target in target_fact_ids:
        for fact in dependency_subgraph(ctx, target):
            selected.add(fact.fact_id)
    return tuple(fact for fact in ctx.facts if fact.fact_id in selected)


def infer_interesting_fact_ids(ctx: ExplainContext) -> tuple[str, ...]:
    """Infer final goals when a certificate predates explicit proof.goals."""
    selected: dict[str, str] = {}
    for fact in ctx.facts:
        if fact.pred in _INTERESTING_PREDS:
            try:
                if fact.ref_arg(0) != "$input":
                    continue
            except ExplainInvalidCertificateError:
                continue
            selected[fact.pred] = fact.fact_id

    ordered: list[str] = []
    for pred in _INTERESTING_PREDS:
        fact_id = selected.get(pred)
        if fact_id is not None:
            ordered.append(fact_id)
    if ordered:
        return tuple(ordered)
    return (ctx.facts[-1].fact_id,)


def select_target_fact_ids(
    ctx: ExplainContext,
    target: str | None = None,
) -> tuple[str, ...]:
    """Select the fact goal(s) to explain."""
    if target is not None:
        ctx.get_fact(target)
        return (target,)
    if ctx.goals:
        return ctx.goals
    return infer_interesting_fact_ids(ctx)
