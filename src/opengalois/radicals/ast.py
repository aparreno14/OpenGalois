"""Core AST constructors for radical expressions.

This module defines the in-memory representation used by the radical-roots
integration layer. The representation is intentionally close to the certificate
payload shape: each expression is a small mapping with a ``kind`` tag and the
fields required by that node.

The module exposes convenience constructors that always pass through the local,
ruleset-level canonicalizer. This keeps AST construction lightweight while still
respecting the small structural simplifications allowed by the current ruleset.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import TypeAlias

Expr: TypeAlias = dict[str, object]
"""Canonical in-memory representation of a radical-expression node."""

ExprLike: TypeAlias = Mapping[str, object]
"""Read-only view over a radical-expression node."""


__all__ = [
    "Expr",
    "ExprLike",
    "add",
    "canonical_qq_string",
    "div",
    "is_one",
    "is_qq",
    "is_zero",
    "mul",
    "neg",
    "pow_int",
    "qq",
    "qq_fraction",
    "qq_ref",
    "root",
    "sub",
    "zeta",
]


def canonical_qq_string(value: Fraction | int | str) -> str:
    """Return the canonical textual encoding of a rational number.

    Args:
        value: Rational literal given as a ``Fraction``, an ``int``, or a string
            such as ``"3"`` or ``"-7/5"``.

    Returns:
        The canonical string form used by the certificate layer.

    Raises:
        TypeError: If ``value`` has an unsupported type.
        ValueError: If ``value`` is a malformed rational string.
    """
    q = _to_fraction(value)
    if q.denominator == 1:
        return str(q.numerator)
    return f"{q.numerator}/{q.denominator}"



def qq(value: Fraction | int | str) -> Expr:
    """Build a rational literal node.

    Args:
        value: Rational value to encode.

    Returns:
        Canonical ``qq`` node.
    """
    return _canonize({"kind": "qq", "value_qq": canonical_qq_string(value)})



def qq_ref(ref: str) -> Expr:
    """Build a rational-reference node.

    Args:
        ref: Object identifier expected to resolve to a ``RatQQ`` object.

    Returns:
        Canonical ``qq`` reference node.

    Raises:
        ValueError: If ``ref`` is empty.
    """
    if not ref:
        raise ValueError("qq_ref() expects a non-empty object id")
    return _canonize({"kind": "qq", "ref": ref})



def zeta(n: int, k: int) -> Expr:
    """Build a root-of-unity node.

    Args:
        n: Order of the root of unity.
        k: Exponent in the canonical range ``0 <= k < n``.

    Returns:
        Canonical ``zeta`` node.

    Raises:
        ValueError: If ``n`` or ``k`` are out of range.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("zeta() requires an integer n >= 1")
    if isinstance(k, bool) or not isinstance(k, int) or not (0 <= k < n):
        raise ValueError("zeta() requires an integer k with 0 <= k < n")
    return _canonize({"kind": "zeta", "n": n, "k": k})



def neg(arg: ExprLike) -> Expr:
    """Build a unary negation node.

    Args:
        arg: Child expression.

    Returns:
        Canonical negated expression.
    """
    return _canonize({"kind": "neg", "arg": dict(arg)})



def add(left: ExprLike, right: ExprLike) -> Expr:
    """Build an addition node.

    Args:
        left: Left operand.
        right: Right operand.

    Returns:
        Canonical sum expression.
    """
    return _canonize({"kind": "add", "left": dict(left), "right": dict(right)})



def sub(left: ExprLike, right: ExprLike) -> Expr:
    """Build a subtraction node.

    Args:
        left: Left operand.
        right: Right operand.

    Returns:
        Canonical difference expression.
    """
    return _canonize({"kind": "sub", "left": dict(left), "right": dict(right)})



def mul(left: ExprLike, right: ExprLike) -> Expr:
    """Build a multiplication node.

    Args:
        left: Left operand.
        right: Right operand.

    Returns:
        Canonical product expression.
    """
    return _canonize({"kind": "mul", "left": dict(left), "right": dict(right)})



def div(left: ExprLike, right: ExprLike) -> Expr:
    """Build a division node.

    Args:
        left: Left operand.
        right: Right operand.

    Returns:
        Canonical quotient expression.
    """
    return _canonize({"kind": "div", "left": dict(left), "right": dict(right)})



def pow_int(base: ExprLike, exp: int) -> Expr:
    """Build an integer-power node.

    Args:
        base: Base expression.
        exp: Integer exponent.

    Returns:
        Canonical power expression.

    Raises:
        ValueError: If ``exp`` is not a non-boolean integer.
    """
    if isinstance(exp, bool) or not isinstance(exp, int):
        raise ValueError("pow_int() requires a non-boolean integer exponent")
    return _canonize({"kind": "pow_int", "base": dict(base), "exp": exp})



def root(n: int, arg: ExprLike) -> Expr:
    """Build an ``n``-th root node.

    Args:
        n: Radical index.
        arg: Radicand expression.

    Returns:
        Canonical root expression.

    Raises:
        ValueError: If ``n`` is not a non-boolean integer >= 2.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError("root() requires a non-boolean integer n >= 2")
    return _canonize({"kind": "root", "n": n, "arg": dict(arg)})



def is_qq(expr: ExprLike) -> bool:
    """Return whether ``expr`` is a ``qq`` node.

    Args:
        expr: Expression to inspect.

    Returns:
        ``True`` if the node kind is ``qq``.
    """
    return expr.get("kind") == "qq"



def qq_fraction(expr: ExprLike) -> Fraction | None:
    """Decode a literal ``qq`` node into a ``Fraction`` when possible.

    Reference nodes are not decoded and return ``None``.

    Args:
        expr: Expression to inspect.

    Returns:
        The corresponding ``Fraction`` for literal ``qq`` nodes, or ``None`` for
        all other expressions.
    """
    if not is_qq(expr):
        return None
    value = expr.get("value_qq")
    if not isinstance(value, str):
        return None
    return _to_fraction(value)



def is_zero(expr: ExprLike) -> bool:
    """Return whether ``expr`` is the literal rational zero.

    Args:
        expr: Expression to inspect.

    Returns:
        ``True`` iff ``expr`` is the literal ``0``.
    """
    q = qq_fraction(expr)
    return q == 0 if q is not None else False



def is_one(expr: ExprLike) -> bool:
    """Return whether ``expr`` is the literal rational one.

    Args:
        expr: Expression to inspect.

    Returns:
        ``True`` iff ``expr`` is the literal ``1``.
    """
    q = qq_fraction(expr)
    return q == 1 if q is not None else False



def _canonize(expr: Expr) -> Expr:
    """Apply local AST canonicalization.

    Args:
        expr: Raw expression payload.

    Returns:
        Canonicalized expression.
    """
    from .canon import canon

    return canon(expr)



def _to_fraction(value: Fraction | int | str) -> Fraction:
    """Convert a supported rational literal to ``Fraction``.

    Args:
        value: Rational literal.

    Returns:
        Exact rational value.

    Raises:
        TypeError: If ``value`` has an unsupported type.
        ValueError: If ``value`` is a malformed rational string.
    """
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise TypeError(f"Unsupported qq literal type: {type(value)!r}")
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        stripped = value.strip()
        if "/" in stripped:
            numerator, denominator = stripped.split("/", 1)
            return Fraction(int(numerator.strip()), int(denominator.strip()))
        return Fraction(int(stripped), 1)
    raise TypeError(f"Unsupported qq literal type: {type(value)!r}")
