# src/opengalois/engine/objects.py
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from ..codec.rationals import _frac_to_str
from ..polyops.desc_qx import _trim_leading_zeros_desc

_POLY_KIND = "PolyQQ"
_MPOLY_KIND = "MPolyQQ"
_RAT_KIND = "RatQQ"
_LIST_KIND = "PolyQQList"
_RADICAL_EXPR_KIND = "RadicalExpr"
_RADICAL_EXPR_LIST_KIND = "RadicalExprList"
_GROUP_KIND = "GroupId"
_INT_KIND = "IntZ"


def _canonical_q_string(value: Any) -> str:
    """Validate and return a canonical rational string."""
    if not isinstance(value, str) or not value:
        raise TypeError("Canonical Q values must be non-empty strings")
    try:
        q = Fraction(value)
    except Exception as exc:  # pragma: no cover - Fraction chooses the exact error type
        raise ValueError(f"Invalid rational string: {value!r}") from exc
    out = _frac_to_str(q)
    if out != value:
        raise ValueError(f"Rational string is not canonical: {value!r}")
    return out


def _collision_checked_put(
    objects: dict[str, dict[str, Any]],
    obj_id: str,
    payload: dict[str, Any],
) -> str:
    prev = objects.get(obj_id)
    if prev is not None and prev != payload:
        raise ValueError(f"Object id collision with different payload: {obj_id}")
    objects[obj_id] = payload
    return obj_id


def _normalize_radical_expr_node(
    node: Any,
    *,
    objects: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Normalize and validate a RadicalExpr AST node."""
    if not isinstance(node, dict):
        raise TypeError("RadicalExpr AST node must be a dict")

    kind = node.get("kind")
    if not isinstance(kind, str) or not kind:
        raise TypeError("RadicalExpr AST node is missing a non-empty 'kind'")

    keys = set(node)

    if kind == "qq":
        allowed = {"kind", "value_qq", "ref"}
        if keys - allowed:
            raise ValueError("qq node contains unknown keys")
        has_value = "value_qq" in node
        has_ref = "ref" in node
        if has_value == has_ref:
            raise ValueError("qq node must contain exactly one of 'value_qq' or 'ref'")
        if has_value:
            return {"kind": "qq", "value_qq": _canonical_q_string(node["value_qq"])}
        ref = node["ref"]
        if not isinstance(ref, str) or not ref:
            raise TypeError("qq.ref must be a non-empty string")
        target = objects.get(ref)
        if not isinstance(target, dict) or target.get("kind") != _RAT_KIND:
            raise ValueError("qq.ref must point to an existing RatQQ object")
        return {"kind": "qq", "ref": ref}

    if kind == "zeta":
        if keys != {"kind", "n", "k"}:
            raise ValueError("zeta node must contain exactly 'kind', 'n', and 'k'")
        n = node["n"]
        k = node["k"]
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise TypeError("zeta.n must be an int >= 1")
        if not isinstance(k, int) or isinstance(k, bool) or not (0 <= k < n):
            raise TypeError("zeta.k must be an int with 0 <= k < n")
        return {"kind": "zeta", "n": n, "k": k}

    if kind == "neg":
        if keys != {"kind", "arg"}:
            raise ValueError("neg node must contain exactly 'kind' and 'arg'")
        return {"kind": "neg", "arg": _normalize_radical_expr_node(node["arg"], objects=objects)}

    if kind in {"add", "sub", "mul", "div"}:
        if keys != {"kind", "left", "right"}:
            raise ValueError(f"{kind} node must contain exactly 'kind', 'left', and 'right'")
        return {
            "kind": kind,
            "left": _normalize_radical_expr_node(node["left"], objects=objects),
            "right": _normalize_radical_expr_node(node["right"], objects=objects),
        }

    if kind == "pow_int":
        if keys != {"kind", "base", "exp"}:
            raise ValueError("pow_int node must contain exactly 'kind', 'base', and 'exp'")
        exp = node["exp"]
        if not isinstance(exp, int) or isinstance(exp, bool):
            raise TypeError("pow_int.exp must be an int")
        return {
            "kind": "pow_int",
            "base": _normalize_radical_expr_node(node["base"], objects=objects),
            "exp": exp,
        }

    if kind == "root":
        if keys != {"kind", "n", "arg"}:
            raise ValueError("root node must contain exactly 'kind', 'n', and 'arg'")
        n = node["n"]
        if not isinstance(n, int) or isinstance(n, bool) or n < 2:
            raise TypeError("root.n must be an int >= 2")
        return {
            "kind": "root",
            "n": n,
            "arg": _normalize_radical_expr_node(node["arg"], objects=objects),
        }

    raise ValueError(f"Unknown RadicalExpr node kind: {kind!r}")


@dataclass
class ObjectStore:
    """Deterministic storage for mathematical artifacts and intermediate objects.

    Ensures that objects generated during the proof construction receive stable,
    deterministic IDs and maintain correct canonical representations.

    Attributes:
        objects (dict[str, dict[str, Any]]): The internal dictionary mapping
            object IDs to their payload data.
        _counters (dict[str, int]): Internal counters used to generate stable
            sequential IDs per prefix.
    """
    objects: dict[str, dict[str, Any]] = field(default_factory=dict)
    _counters: dict[str, int] = field(default_factory=dict)

    def new_id(self, prefix: str) -> str:
        """Generates a deterministic, sequential ID for a given prefix.

        Args:
            prefix (str): The prefix string (e.g., 'poly', 'factor').

        Returns:
            str: A unique identifier combining the prefix and an incremented counter.
        """
        k = self._counters.get(prefix, 0) + 1
        self._counters[prefix] = k
        return f"{prefix}{k}"

    def put_mpoly(self, obj_id: str, *, nvars: int,
                  terms: list[tuple[list[int], Fraction]]) -> str:
        """Stores a multivariate polynomial over Q in canonical sparse form.

        Args:
            obj_id (str): The target identifier for the polynomial.
            nvars (int): Number of variables in the ambient ring Q[x1,...,xn].
            terms (list[tuple[list[int], Fraction]]): Nonzero terms given as
                pairs ``(exp, coeff)`` where ``exp`` is an exponent vector of
                length ``nvars`` and ``coeff`` is a rational coefficient.

        Returns:
            str: The identifier under which the multivariate polynomial was stored.

        Raises:
            TypeError: If the payload is malformed.
            ValueError: If the payload is not canonical or collides with an
                existing object id with different contents.
        """
        if not isinstance(nvars, int) or isinstance(nvars, bool) or nvars < 1:
            raise TypeError("MPolyQQ.nvars must be an int >= 1")

        normalized: list[dict[str, Any]] = []
        seen: set[tuple[int, ...]] = set()
        prev_exp: tuple[int, ...] | None = None
        for exp, coeff in terms:
            if not isinstance(exp, list) or len(exp) != nvars:
                raise TypeError("Each exponent vector must be a list of length nvars")
            if any((not isinstance(e, int)) or isinstance(e, bool) or e < 0 for e in exp):
                raise TypeError("Exponent entries must be ints >= 0")
            if coeff == 0:
                raise ValueError("MPolyQQ terms must not contain zero coefficients")
            exp_t = tuple(exp)
            if exp_t in seen:
                raise ValueError("MPolyQQ terms must not repeat exponent vectors")
            if prev_exp is not None and prev_exp <= exp_t:
                raise ValueError("MPolyQQ terms must be in descending lexicographic order")
            seen.add(exp_t)
            prev_exp = exp_t
            normalized.append({"exp": exp, "coeff_qq": _frac_to_str(coeff)})

        payload = {"kind": _MPOLY_KIND, "nvars": nvars, "terms": normalized}
        return _collision_checked_put(self.objects, obj_id, payload)

    def put_poly(self, obj_id: str, coeffs_desc: list[Fraction]) -> str:
        """Stores a polynomial in the object store.

        Trims leading zeros, determines the degree, and formats the coefficients
        into canonical strings. It also prevents overriding an existing object ID
        with a different payload.

        Args:
            obj_id (str): The target identifier for the polynomial.
            coeffs_desc (list[Fraction]): Coefficients of the polynomial in
                descending order.

        Returns:
            str: The identifier under which the polynomial was stored.

        Raises:
            ValueError: If the `obj_id` already exists but contains a different payload.
        """
        coeffs = _trim_leading_zeros_desc(coeffs_desc)
        if not coeffs:
            raise ValueError("Cannot store the zero polynomial")
        payload = {
            "kind": _POLY_KIND,
            "coeffs_qq": [_frac_to_str(c) for c in coeffs] if coeffs else ["0"],
        }
        return _collision_checked_put(self.objects, obj_id, payload)

    def put_rat(self, obj_id: str, value: Fraction) -> str:
        """Stores a rational number in the object store.

        Args:
            obj_id (str): The target identifier for the rational number.
            value (Fraction): The rational number to store.

        Returns:
            str: The identifier under which the rational number was stored.

        Raises:
            ValueError: If the `obj_id` already exists but contains a different payload.
        """
        payload = {"kind": _RAT_KIND, "value": _frac_to_str(value)}
        return _collision_checked_put(self.objects, obj_id, payload)

    def put_poly_list(self, obj_id: str, items: list[str]) -> str:
        """Stores a list of polynomial object references in the object store.

        Args:
            obj_id (str): The target identifier for the list of polynomials.
            items (list[str]): A list of object IDs representing polynomials.

        Returns:
            str: The identifier under which the list of polynomials was stored.

        Raises:
            ValueError: If the `obj_id` already exists but contains a different payload.
        """
        payload = {"kind": _LIST_KIND, "items": items}
        return _collision_checked_put(self.objects, obj_id, payload)

    def put_radical_expr(self, obj_id: str, expr: dict[str, Any]) -> str:
        """Stores a canonical scalar radical expression.

        The object is intentionally syntactic: only structural well-formedness
        of the AST is enforced here. Rule-specific mathematical meaning belongs
        to the proof rule that references the object.
        """
        payload = {
            "kind": _RADICAL_EXPR_KIND,
            "expr": _normalize_radical_expr_node(expr, objects=self.objects),
        }
        return _collision_checked_put(self.objects, obj_id, payload)

    def put_radical_expr_list(self, obj_id: str, items: list[str]) -> str:
        """Stores an ordered list of RadicalExpr object references."""
        if not isinstance(items, list):
            raise TypeError("RadicalExprList.items must be a list")
        normalized: list[str] = []
        for item in items:
            if not isinstance(item, str) or not item:
                raise TypeError("RadicalExprList items must be non-empty strings")
            target = self.objects.get(item)
            if not isinstance(target, dict) or target.get("kind") != _RADICAL_EXPR_KIND:
                raise ValueError("RadicalExprList items must "
                                 "reference existing RadicalExpr objects")
            normalized.append(item)
        payload = {"kind": _RADICAL_EXPR_LIST_KIND, "items": normalized}
        return _collision_checked_put(self.objects, obj_id, payload)

    def put_groupid(self, obj_id: str, *, system: str, order: int, index: int, alias: str |
                    None = None) -> str:
        """Stores a group identifier in the object store.

        Args:
            obj_id (str): The target identifier for the group.
            system (str): The group system (e.g., 'smallgroup').
            order (int): The order of the group.
            index (int): The index of the group in the system.
            alias (str | None, optional): An optional alias for the group.

        Returns:
            str: The identifier under which the group was stored.
        """
        payload = {"kind": _GROUP_KIND, "system": system, "order": order, "index": index}
        if alias is not None:
            payload["alias"] = alias
        return _collision_checked_put(self.objects, obj_id, payload)

    def put_int(self, obj_id: str, value: int) -> str:
        """Stores an integer (IntZ) in canonical string form."""
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("IntZ value must be an int (not bool)")
        payload = {"kind": _INT_KIND, "value": str(value)}
        return _collision_checked_put(self.objects, obj_id, payload)
