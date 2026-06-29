"""Local canonicalization for radical-expression ASTs.

This module implements only the small structural rewrites allowed by the current
ruleset policy. It does not attempt algebraic normalization, expression
reordering by commutativity, or symbolic equivalence checking.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction

from .ast import Expr, ExprLike, canonical_qq_string, qq_fraction

__all__ = ["canon", "canon_list"]


def canon(expr: ExprLike) -> Expr:
    """Return the locally canonical form of an AST node.

    Args:
        expr: Input expression payload.

    Returns:
        Canonicalized expression.

    Raises:
        TypeError: If ``expr`` is not mapping-like.
        ValueError: If the node shape is invalid.
    """
    if not isinstance(expr, Mapping):
        raise TypeError("RadicalExpr node must be a mapping")

    kind_obj = expr.get("kind")
    if not isinstance(kind_obj, str):
        raise ValueError("RadicalExpr node must contain a string 'kind'")
    kind = kind_obj

    if kind == "qq":
        return _canon_qq(expr)
    if kind == "zeta":
        return _canon_zeta(expr)
    if kind == "neg":
        _require_exact_keys(expr, {"kind", "arg"})
        arg = canon(_expect_expr(expr, "arg"))
        arg_q = qq_fraction(arg)
        if arg_q is not None:
            return _qq_literal(-arg_q)
        if arg.get("kind") == "neg":
            return canon(_expect_expr(arg, "arg"))
        return {"kind": "neg", "arg": arg}
    if kind in {"add", "sub", "mul", "div"}:
        _require_exact_keys(expr, {"kind", "left", "right"})
        left = canon(_expect_expr(expr, "left"))
        right = canon(_expect_expr(expr, "right"))
        return _canon_binary(kind, left, right)
    if kind == "pow_int":
        _require_exact_keys(expr, {"kind", "base", "exp"})
        base = canon(_expect_expr(expr, "base"))
        exp = expr.get("exp")
        if isinstance(exp, bool) or not isinstance(exp, int):
            raise ValueError("pow_int.exp must be a non-boolean integer")
        return _canon_pow_int(base, exp)
    if kind == "root":
        _require_exact_keys(expr, {"kind", "n", "arg"})
        n = expr.get("n")
        if isinstance(n, bool) or not isinstance(n, int) or n < 2:
            raise ValueError("root.n must be a non-boolean integer >= 2")
        arg = canon(_expect_expr(expr, "arg"))
        arg_q = qq_fraction(arg)
        if arg_q == 0:
            return _qq_literal(Fraction(0, 1))
        if arg_q == 1:
            return _qq_literal(Fraction(1, 1))
        return {"kind": "root", "n": n, "arg": arg}

    raise ValueError(f"Unknown RadicalExpr node kind: {kind!r}")



def canon_list(exprs: Sequence[ExprLike]) -> list[Expr]:
    """Canonicalize a sequence of expressions elementwise.

    Args:
        exprs: Expressions to canonicalize.

    Returns:
        Canonicalized list preserving the input order.
    """
    return [canon(expr) for expr in exprs]



def _canon_qq(expr: Mapping[str, object]) -> Expr:
    """Canonicalize a ``qq`` node.

    Args:
        expr: Raw ``qq`` payload.

    Returns:
        Canonical ``qq`` node.

    Raises:
        ValueError: If the node shape is invalid.
    """
    keys = set(expr)
    if keys == {"kind", "value_qq"}:
        value_qq = expr.get("value_qq")
        if not isinstance(value_qq, str):
            raise ValueError("qq.value_qq must be a string")
        return {"kind": "qq", "value_qq": canonical_qq_string(value_qq)}
    if keys == {"kind", "ref"}:
        ref = expr.get("ref")
        if not isinstance(ref, str) or not ref:
            raise ValueError("qq.ref must be a non-empty object id")
        return {"kind": "qq", "ref": ref}
    raise ValueError("qq node must contain exactly {'kind','value_qq'} or {'kind','ref'}")



def _canon_zeta(expr: Mapping[str, object]) -> Expr:
    """Canonicalize a ``zeta`` node.

    Args:
        expr: Raw ``zeta`` payload.

    Returns:
        Canonical ``zeta`` node.

    Raises:
        ValueError: If the node shape is invalid.
    """
    _require_exact_keys(expr, {"kind", "n", "k"})
    n = expr.get("n")
    k = expr.get("k")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("zeta.n must be a non-boolean integer >= 1")
    if isinstance(k, bool) or not isinstance(k, int) or not (0 <= k < n):
        raise ValueError("zeta.k must be a non-boolean integer with 0 <= k < n")
    return {"kind": "zeta", "n": n, "k": k}



def _canon_binary(kind: str, left: Expr, right: Expr) -> Expr:
    """Canonicalize a binary expression with local rational simplifications.

    Args:
        kind: Binary node kind.
        left: Canonical left operand.
        right: Canonical right operand.

    Returns:
        Canonicalized binary expression.

    Raises:
        ValueError: If ``kind`` is unsupported.
    """
    left_q = qq_fraction(left)
    right_q = qq_fraction(right)

    if kind == "add":
        if left_q == 0:
            return right
        if right_q == 0:
            return left
        if left_q is not None and right_q is not None:
            return _qq_literal(left_q + right_q)
        return {"kind": "add", "left": left, "right": right}

    if kind == "sub":
        if right_q == 0:
            return left
        if left_q == 0:
            return canon({"kind": "neg", "arg": right})
        if left_q is not None and right_q is not None:
            return _qq_literal(left_q - right_q)
        return {"kind": "sub", "left": left, "right": right}

    if kind == "mul":
        if left_q == 0 or right_q == 0:
            return _qq_literal(Fraction(0, 1))
        if left_q == 1:
            return right
        if right_q == 1:
            return left
        if left_q is not None and right_q is not None:
            return _qq_literal(left_q * right_q)
        return {"kind": "mul", "left": left, "right": right}

    if kind == "div":
        if left_q == 0 and right_q != 0:
            return _qq_literal(Fraction(0, 1))
        if right_q == 1:
            return left
        if left_q is not None and right_q is not None and right_q != 0:
            return _qq_literal(left_q / right_q)
        return {"kind": "div", "left": left, "right": right}

    raise ValueError(f"Unsupported binary kind: {kind!r}")



def _canon_pow_int(base: Expr, exp: int) -> Expr:
    """Canonicalize an integer-power node.

    Args:
        base: Canonical base expression.
        exp: Integer exponent.

    Returns:
        Canonicalized power expression.
    """
    if exp == 0:
        return _qq_literal(Fraction(1, 1))
    if exp == 1:
        return base

    base_q = qq_fraction(base)
    if base_q is not None and (exp > 0 or (exp < 0 and base_q != 0)):
        return _qq_literal(base_q**exp)

    return {"kind": "pow_int", "base": base, "exp": exp}



def _qq_literal(value: Fraction) -> Expr:
    """Build a canonical rational literal.

    Args:
        value: Rational value.

    Returns:
        Canonical literal ``qq`` node.
    """
    return {"kind": "qq", "value_qq": canonical_qq_string(value)}



def _require_exact_keys(obj: Mapping[str, object], expected: set[str]) -> None:
    """Validate the exact set of keys in a node payload.

    Args:
        obj: Mapping to validate.
        expected: Exact key set.

    Raises:
        ValueError: If the keys do not match exactly.
    """
    actual = set(obj)
    if actual != expected:
        raise ValueError(f"Expected keys {sorted(expected)!r}, got {sorted(actual)!r}")



def _expect_expr(obj: Mapping[str, object], key: str) -> ExprLike:
    """Extract a child expression from a payload.

    Args:
        obj: Parent payload.
        key: Child key to extract.

    Returns:
        Child expression payload.

    Raises:
        ValueError: If the child is not mapping-like.
    """
    value = obj.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a RadicalExpr mapping")
    return value
