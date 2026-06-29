# src/opengalois/engine/context.py
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING, Any, cast

from opengalois.codec.rationals import _parse_fraction
from opengalois.polyops.desc_qx import _trim_leading_zeros_desc

from ..models import AnalysisOptions
from .objects import _POLY_KIND, ObjectStore

if TYPE_CHECKING:
    from .registry import EngineRegistry
    
_INPUT_REF = "$input"
    
def _resolve_poly_desc_QQ(ctx: EngineContext, poly_ref: str) -> list[Fraction]:
    """Resolve a polynomial reference to descending QQ coefficients.

    Resolution order:
      1) '$input' -> ctx.cache['$input_poly']
      2) ctx.cache[poly_ref]
      3) ctx.objects.objects[poly_ref] (kind=poly_qq_desc)

    Args:
        ctx (EngineContext): Engine context.
        poly_ref (str): Reference id.

    Returns:
        list[Fraction]: Polynomial coefficients in descending order.

    Raises:
        KeyError: If the reference cannot be resolved.
        ValueError: If the resolved object is not a valid poly_qq_desc.
    """
    if poly_ref == _INPUT_REF:
        p = ctx.cache.get("$input_poly")
        if not isinstance(p, list):
            raise KeyError("Missing ctx.cache['$input_poly'] for $input resolution.")
        return cast(list[Fraction], p)

    cached = ctx.cache.get(poly_ref)
    if isinstance(cached, list):
        return cast(list[Fraction], cached)

    obj = ctx.objects.objects.get(poly_ref)
    if obj is None:
        raise KeyError(f"Cannot resolve polynomial ref {poly_ref!r} from cache or objects.")

    if not isinstance(obj, Mapping) or obj.get("kind") != _POLY_KIND:
        raise ValueError(f"Object {poly_ref!r} is not kind={_POLY_KIND!r}.")

    coeffs_qq = obj.get("coeffs_qq")
    if not isinstance(coeffs_qq, list) or not all(isinstance(x, str) for x in coeffs_qq):
        raise ValueError(f"Object {poly_ref!r} has invalid coeffs_qq.")

    pQ = [_parse_fraction(s) for s in cast(Sequence[str], coeffs_qq)]
    pQ = _trim_leading_zeros_desc(pQ)
    if not pQ:
        raise ValueError("poly_qq_desc cannot represent the zero polynomial.")
    return pQ

def _next_fact_id(ctx: EngineContext) -> str:
    """Generate deterministic fact ids F1, F2, ... stored in ctx.cache."""
    i = int(ctx.cache.get("_fact_i", 0)) + 1
    ctx.cache["_fact_i"] = i
    return f"F{i}"

def _ensure_degree_fact(
    ctx: EngineContext,
    *,
    poly_ref: str,
    into: list[dict[str, Any]] | None = None,
) -> tuple[str, int]:
    """Ensure a Degree(poly_ref, n) fact exists and return (fact_id, n).

    Reuses a previously emitted Degree fact for the same `poly_ref` if present.
    """
    by_poly = ctx.cache.setdefault("_degree_fact_by_poly", {})
    if not isinstance(by_poly, dict):
        raise TypeError("ctx.cache['_degree_fact_by_poly'] must be a dict")

    if poly_ref in by_poly:
        p = _resolve_poly_desc_QQ(ctx, poly_ref)
        return cast(str, by_poly[poly_ref]), (len(p) - 1)

    p = _resolve_poly_desc_QQ(ctx, poly_ref)
    deg = len(p) - 1

    int_obj_id = f"int.{deg}"
    ctx.objects.put_int(int_obj_id, deg)

    fid = _next_fact_id(ctx)
    fact = {
        "id": fid,
        "claim": {"pred": "Degree", "args": [{"ref": poly_ref}, {"ref": int_obj_id}]},
        "rule": "degree.QQ@1",
        "premises": [],
        "statement": f"Degree of polynomial is {deg}.",
    }
    by_poly[poly_ref] = fid

    if into is not None:
        into.append(fact)

    return fid, deg

@dataclass
class EngineContext:
    """State and dependencies shared across the engine's execution.

    This context acts as the central hub for the analysis engine, carrying
    the user options, the object store for canonical artifacts, the node
    registry, and temporary runtime caches.

    Attributes:
        options (AnalysisOptions): Configuration options for the analysis.
        objects (ObjectStore): The deterministic store for polynomial artifacts.
        registry (EngineRegistry): Registry containing available nodes and pipelines.
        cache (dict[str, Any]): Non-normative temporary cache used to avoid
            recomputations internally. This is never serialized into the certificate.
    """
    options: AnalysisOptions
    objects: ObjectStore
    registry: EngineRegistry
    # Non-normative caches (never serialized directly)
    cache: dict[str, Any] = field(default_factory=dict)
