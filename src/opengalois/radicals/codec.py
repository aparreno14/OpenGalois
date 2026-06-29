"""Certificate-object encoding and decoding for radical expressions.

This module bridges the lightweight AST representation used by
``opengalois.radicals`` and the object payloads stored in v3 certificates. It
contains no rule-specific mathematics; it only validates and translates the
structural object forms for ``RadicalExpr`` and ``RadicalExprList``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import TypeAlias

from .ast import Expr, ExprLike
from .canon import canon, canon_list

RatRefResolver: TypeAlias = Callable[[str], bool]
"""Predicate used to validate that a ``qq.ref`` id resolves to a ``RatQQ`` object."""

__all__ = [
    "RatRefResolver",
    "build_expr_object_bundle",
    "decode_expr_list_payloads",
    "decode_expr_list_refs",
    "expr_from_object_payload",
    "expr_list_to_object_payload",
    "expr_to_object_payload",
    "validate_expr_payload",
]


def expr_to_object_payload(expr: ExprLike) -> dict[str, object]:
    """Encode a single expression as a ``RadicalExpr`` object payload.

    Args:
        expr: Expression to encode.

    Returns:
        Object payload with kind ``RadicalExpr``.
    """
    return {"kind": "RadicalExpr", "expr": canon(expr)}



def expr_from_object_payload(
    payload: Mapping[str, object],
    *,
    rat_ref_resolver: RatRefResolver | None = None,
) -> Expr:
    """Decode and validate a ``RadicalExpr`` object payload.

    Args:
        payload: Object payload to decode.
        rat_ref_resolver: Optional validator for ``qq.ref`` identifiers.

    Returns:
        Canonical AST expression.

    Raises:
        TypeError: If ``payload`` is not mapping-like.
        ValueError: If the payload shape is invalid.
    """
    if set(payload) != {"kind", "expr"}:
        raise ValueError("RadicalExpr object must contain exactly 'kind' and 'expr'")
    if payload.get("kind") != "RadicalExpr":
        raise ValueError("RadicalExpr.kind must be 'RadicalExpr'")
    return validate_expr_payload(payload["expr"], rat_ref_resolver=rat_ref_resolver)



def expr_list_to_object_payload(expr_refs: Sequence[str]) -> dict[str, object]:
    """Encode an ordered list of ``RadicalExpr`` object ids.

    Args:
        expr_refs: Ordered object identifiers.

    Returns:
        Object payload with kind ``RadicalExprList``.

    Raises:
        ValueError: If some identifier is empty.
    """
    refs = list(expr_refs)
    if not all(isinstance(item, str) and item for item in refs):
        raise ValueError("expr_refs must be a sequence of non-empty ids")
    return {"kind": "RadicalExprList", "items": refs}



def decode_expr_list_refs(payload: Mapping[str, object]) -> list[str]:
    """Decode a ``RadicalExprList`` object payload into its ordered refs.

    Args:
        payload: List-object payload.

    Returns:
        Ordered list of referenced expression ids.

    Raises:
        ValueError: If the payload shape is invalid.
    """
    if set(payload) != {"kind", "items"}:
        raise ValueError("RadicalExprList object must contain exactly 'kind' and 'items'")
    if payload.get("kind") != "RadicalExprList":
        raise ValueError("RadicalExprList.kind must be 'RadicalExprList'")
    items = payload.get("items")
    if not isinstance(items, list) or not all(isinstance(item, str) and item for item in items):
        raise ValueError("RadicalExprList.items must be a list[str] of non-empty ids")
    return list(items)



def decode_expr_list_payloads(
    list_payload: Mapping[str, object],
    objects: Mapping[str, Mapping[str, object]],
    *,
    rat_ref_resolver: RatRefResolver | None = None,
) -> list[Expr]:
    """Resolve a ``RadicalExprList`` payload against an object mapping.

    Args:
        list_payload: ``RadicalExprList`` object payload.
        objects: Mapping from object id to object payload.
        rat_ref_resolver: Optional validator for ``qq.ref`` identifiers.

    Returns:
        Decoded expressions in the order prescribed by the list object.

    Raises:
        KeyError: If some referenced object id is missing.
        ValueError: If any referenced object has invalid shape.
    """
    exprs: list[Expr] = []
    for item_id in decode_expr_list_refs(list_payload):
        try:
            obj = objects[item_id]
        except KeyError as exc:
            raise KeyError(f"Missing RadicalExpr object id: {item_id!r}") from exc
        exprs.append(expr_from_object_payload(obj, rat_ref_resolver=rat_ref_resolver))
    return exprs



def build_expr_object_bundle(
    exprs: Sequence[ExprLike],
    *,
    expr_id_prefix: str = "rexpr",
    list_id: str = "rlist",
) -> tuple[dict[str, dict[str, object]], str]:
    """Build expression objects plus a single list object.

    This helper is convenient for tests and small proof fragments. The returned
    object dictionary is ready to merge into ``certificate.objects``.

    Args:
        exprs: Expressions to materialize as ``RadicalExpr`` objects.
        expr_id_prefix: Prefix used for generated expression ids.
        list_id: Object id used for the generated ``RadicalExprList``.

    Returns:
        Pair ``(objects, list_id)`` where ``objects`` contains the expression
        objects and the list object.

    Raises:
        ValueError: If ids are empty or collide.
    """
    if not expr_id_prefix:
        raise ValueError("expr_id_prefix must be non-empty")
    if not list_id:
        raise ValueError("list_id must be non-empty")

    objects: dict[str, dict[str, object]] = {}
    expr_refs: list[str] = []
    for index, expr in enumerate(canon_list(exprs), start=1):
        obj_id = f"{expr_id_prefix}.{index}"
        if obj_id in objects:
            raise ValueError(f"Duplicate generated object id: {obj_id!r}")
        objects[obj_id] = expr_to_object_payload(expr)
        expr_refs.append(obj_id)

    if list_id in objects:
        raise ValueError(f"list_id collides with an expression id: {list_id!r}")
    objects[list_id] = expr_list_to_object_payload(expr_refs)
    return objects, list_id



def validate_expr_payload(
    payload: object,
    *,
    rat_ref_resolver: RatRefResolver | None = None,
) -> Expr:
    """Validate a raw AST payload and return its canonicalized form.

    Args:
        payload: Raw AST payload to validate.
        rat_ref_resolver: Optional validator for ``qq.ref`` identifiers.

    Returns:
        Canonical AST expression.

    Raises:
        TypeError: If the payload is not mapping-like.
        ValueError: If the payload shape is invalid.
    """
    if not isinstance(payload, Mapping):
        raise TypeError("RadicalExpr payload must be a mapping")

    kind_obj = payload.get("kind")
    if not isinstance(kind_obj, str):
        raise ValueError("RadicalExpr node must contain a string 'kind'")
    kind = kind_obj

    if kind == "qq":
        keys = set(payload)
        if keys == {"kind", "ref"}:
            ref = payload.get("ref")
            if not isinstance(ref, str) or not ref:
                raise ValueError("qq.ref must be a non-empty object id")
            if rat_ref_resolver is not None and not rat_ref_resolver(ref):
                raise ValueError(f"qq.ref does not resolve to a RatQQ object: {ref!r}")
            return canon({"kind": "qq", "ref": ref})
        if keys == {"kind", "value_qq"}:
            value_qq = payload.get("value_qq")
            if not isinstance(value_qq, str):
                raise ValueError("qq.value_qq must be a string")
            return canon({"kind": "qq", "value_qq": value_qq})
        raise ValueError("qq node must contain exactly {'kind','value_qq'} or {'kind','ref'}")

    if kind == "zeta":
        _require_exact_keys(payload, {"kind", "n", "k"})
        n = payload.get("n")
        k = payload.get("k")
        if isinstance(n, bool) or not isinstance(n, int):
            raise ValueError("zeta.n must be a non-boolean integer")
        if isinstance(k, bool) or not isinstance(k, int):
            raise ValueError("zeta.k must be a non-boolean integer")
        return canon({"kind": "zeta", "n": n, "k": k})

    if kind == "neg":
        _require_exact_keys(payload, {"kind", "arg"})
        return canon(
            {
                "kind": "neg",
                "arg": validate_expr_payload(payload["arg"], rat_ref_resolver=rat_ref_resolver),
            }
        )

    if kind in {"add", "sub", "mul", "div"}:
        _require_exact_keys(payload, {"kind", "left", "right"})
        return canon(
            {
                "kind": kind,
                "left": validate_expr_payload(payload["left"], rat_ref_resolver=rat_ref_resolver),
                "right": validate_expr_payload(payload["right"], rat_ref_resolver=rat_ref_resolver),
            }
        )

    if kind == "pow_int":
        _require_exact_keys(payload, {"kind", "base", "exp"})
        exp = payload.get("exp")
        if isinstance(exp, bool) or not isinstance(exp, int):
            raise ValueError("pow_int.exp must be a non-boolean integer")
        return canon(
            {
                "kind": "pow_int",
                "base": validate_expr_payload(payload["base"], rat_ref_resolver=rat_ref_resolver),
                "exp": exp,
            }
        )

    if kind == "root":
        _require_exact_keys(payload, {"kind", "n", "arg"})
        n = payload.get("n")
        if isinstance(n, bool) or not isinstance(n, int) or n < 2:
            raise ValueError("root.n must be a non-boolean integer >= 2")
        return canon(
            {
                "kind": "root",
                "n": n,
                "arg": validate_expr_payload(payload["arg"], rat_ref_resolver=rat_ref_resolver),
            }
        )

    raise ValueError(f"Unknown RadicalExpr node kind: {kind!r}")



def _require_exact_keys(obj: Mapping[str, object], expected: set[str]) -> None:
    """Validate the exact set of keys in an object payload.

    Args:
        obj: Mapping to validate.
        expected: Exact key set.

    Raises:
        ValueError: If the keys do not match exactly.
    """
    actual = set(obj)
    if actual != expected:
        raise ValueError(f"Expected keys {sorted(expected)!r}, got {sorted(actual)!r}")
