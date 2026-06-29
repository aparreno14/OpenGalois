from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from opengalois.engine.context import EngineContext, _next_fact_id
from opengalois.radicals.ast import Expr


@dataclass(frozen=True)
class CachedRadicalRoots:
    """Cached radical-roots artifacts for a polynomial reference.

    Attributes:
        fact_id: Fact identifier of the certified ``RadicalRoots`` node.
        roots_ref: Object identifier of the corresponding ``RadicalExprList``.
    """

    fact_id: str
    roots_ref: str


__all__ = [
    "CachedRadicalRoots",
    "cache_radical_roots",
    "emit_irreducible_to_depressed_fact",
    "get_cached_radical_roots",
    "load_radical_expr_list",
    "store_radical_expr_list",
]


def store_radical_expr_list(
    ctx: EngineContext,
    *,
    exprs: list[Expr],
    expr_prefix: str,
    list_prefix: str,
) -> str:
    """Store an ordered canonical list of radical expressions.

    Args:
        ctx: Engine execution context.
        exprs: Ordered radical-expression payloads.
        expr_prefix: Prefix for fresh ``RadicalExpr`` object identifiers.
        list_prefix: Prefix for the fresh ``RadicalExprList`` object identifier.

    Returns:
        Identifier of the stored ``RadicalExprList`` object.
    """
    expr_refs: list[str] = []
    for expr in exprs:
        expr_id = ctx.objects.new_id(expr_prefix)
        ctx.objects.put_radical_expr(expr_id, expr)
        expr_refs.append(expr_id)

    list_id = ctx.objects.new_id(list_prefix)
    ctx.objects.put_radical_expr_list(list_id, expr_refs)
    return list_id


def cache_radical_roots(
    ctx: EngineContext,
    *,
    poly_ref: str,
    fact_id: str,
    roots_ref: str,
) -> None:
    """Record the certified radical-roots artifacts for ``poly_ref``.

    Args:
        ctx: Engine execution context.
        poly_ref: Polynomial object identifier.
        fact_id: Fact identifier of the certified ``RadicalRoots`` node.
        roots_ref: Object identifier of the corresponding ``RadicalExprList``.
    """
    radical_map = ctx.cache.setdefault("_radical_roots_fact_by_poly", {})
    if not isinstance(radical_map, dict):
        raise TypeError("ctx.cache['_radical_roots_fact_by_poly'] must be a dict")
    radical_map[poly_ref] = fact_id

    radical_ref_map = ctx.cache.setdefault("_radical_roots_ref_by_poly", {})
    if not isinstance(radical_ref_map, dict):
        raise TypeError("ctx.cache['_radical_roots_ref_by_poly'] must be a dict")
    radical_ref_map[poly_ref] = roots_ref


def get_cached_radical_roots(ctx: EngineContext, *, poly_ref: str) -> CachedRadicalRoots:
    """Return the cached radical-roots artifacts for ``poly_ref``.

    Args:
        ctx: Engine execution context.
        poly_ref: Polynomial object identifier.

    Returns:
        Cached fact/object identifiers for the corresponding ``RadicalRoots`` fact.

    Raises:
        ValueError: If the cache entries are missing or malformed.
    """
    radical_map = ctx.cache.get("_radical_roots_fact_by_poly", {})
    if not isinstance(radical_map, dict) or poly_ref not in radical_map:
        raise ValueError(f"Missing cached RadicalRoots fact id for {poly_ref!r}.")
    fact_id = str(radical_map[poly_ref])
    if not fact_id:
        raise ValueError(f"Empty cached RadicalRoots fact id for {poly_ref!r}.")

    radical_ref_map = ctx.cache.get("_radical_roots_ref_by_poly", {})
    if not isinstance(radical_ref_map, dict) or poly_ref not in radical_ref_map:
        raise ValueError(f"Missing cached RadicalExprList ref for {poly_ref!r}.")
    roots_ref = str(radical_ref_map[poly_ref])
    if not roots_ref:
        raise ValueError(f"Empty cached RadicalExprList ref for {poly_ref!r}.")

    return CachedRadicalRoots(fact_id=fact_id, roots_ref=roots_ref)


def load_radical_expr_list(ctx: EngineContext, *, roots_ref: str) -> list[Expr]:
    """Decode a stored ``RadicalExprList`` into ordered expression payloads.

    Args:
        ctx: Engine execution context.
        roots_ref: Identifier of a ``RadicalExprList`` object.

    Returns:
        Ordered list of decoded radical-expression payloads.

    Raises:
        ValueError: If the referenced object is malformed.
    """
    roots_obj = ctx.objects.objects.get(roots_ref)
    if not isinstance(roots_obj, dict):
        raise ValueError(f"Missing RadicalExprList object: {roots_ref!r}")
    if roots_obj.get("kind") != "RadicalExprList":
        raise ValueError(f"Object {roots_ref!r} is not a RadicalExprList")

    items = roots_obj.get("items")
    if not isinstance(items, list) or not all(isinstance(x, str) and x for x in items):
        raise ValueError(f"Malformed RadicalExprList payload for {roots_ref!r}")

    exprs: list[Expr] = []
    for expr_ref in items:
        expr_obj = ctx.objects.objects.get(expr_ref)
        if not isinstance(expr_obj, dict):
            raise ValueError(f"Missing RadicalExpr object: {expr_ref!r}")
        if expr_obj.get("kind") != "RadicalExpr":
            raise ValueError(f"Object {expr_ref!r} is not a RadicalExpr")
        expr_payload = expr_obj.get("expr")
        if not isinstance(expr_payload, dict):
            raise ValueError(f"Malformed RadicalExpr payload for {expr_ref!r}")
        exprs.append(expr_payload)

    return exprs


def emit_irreducible_to_depressed_fact(
    ctx: EngineContext,
    *,
    source_poly_ref: str,
    depressed_poly_ref: str,
    normalize_fact_id: str,
    source_irreducible_fact_id: str,
    into: list[dict[str, Any]],
    rule_id: str = "irreducible.QQ.to.depressed_monic@1",
) -> str:
    """Emit ``IrreducibleQQ(g)`` from ``DepressedMonicEq(f,g)`` and ``IrreducibleQQ(f)``.

    Args:
        ctx: Engine execution context.
        source_poly_ref: Source polynomial ``f``.
        depressed_poly_ref: Depressed monic normalization ``g``.
        normalize_fact_id: Fact id of ``DepressedMonicEq(f,g)``.
        source_irreducible_fact_id: Fact id of ``IrreducibleQQ(f)``.
        into: Fact accumulator receiving the emitted fact when needed.
        rule_id: Rule identifier used to justify the transport.

    Returns:
        Identifier of the certified ``IrreducibleQQ(g)`` fact.
    """
    irr_map = ctx.cache.setdefault("_irreducible_fact_by_poly", {})
    if not isinstance(irr_map, dict):
        raise TypeError("ctx.cache['_irreducible_fact_by_poly'] must be a dict")

    if depressed_poly_ref in irr_map:
        return str(irr_map[depressed_poly_ref])

    fact_id = _next_fact_id(ctx)
    fact = {
        "id": fact_id,
        "claim": {"pred": "IrreducibleQQ", "args": [{"ref": depressed_poly_ref}]},
        "rule": rule_id,
        "premises": [normalize_fact_id, source_irreducible_fact_id],
        "statement": (
            "Irreducibility transported to the depressed monic normalization over Q."
        ),
    }
    into.append(fact)
    irr_map[depressed_poly_ref] = fact_id
    return fact_id
