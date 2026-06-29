"""Human-readable rendering helpers for radical-expression ASTs.

The functions in this module are non-normative. They are intended for CLI
output, debugging, and explain-style views derived from the certificate.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Literal, TypeAlias

from .ast import Expr, ExprLike

RenderStyle: TypeAlias = Literal["unicode", "ascii"]
"""Supported text-rendering styles."""

AliasBinding: TypeAlias = tuple[str, ExprLike]
"""Local alias binding used only by the non-normative CLI renderer."""

__all__ = ["RenderStyle", "render_text", "render_text_list"]

_PRECEDENCE: dict[str, int] = {
    "qq": 100,
    "zeta": 100,
    "root": 95,
    "pow_int": 90,
    "neg": 80,
    "mul": 70,
    "div": 70,
    "add": 60,
    "sub": 60,
}

_SUPERSCRIPT_MAP = str.maketrans(
    {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
        "-": "⁻",
    }
)
_SUBSCRIPT_MAP = str.maketrans(
    {
        "0": "₀",
        "1": "₁",
        "2": "₂",
        "3": "₃",
        "4": "₄",
        "5": "₅",
        "6": "₆",
        "7": "₇",
        "8": "₈",
        "9": "₉",
        "-": "₋",
    }
)


def render_text(
    expr: ExprLike,
    *,
    style: RenderStyle = "unicode",
    aliases: Sequence[AliasBinding] | None = None,
) -> str:
    """Render an expression as human-readable text.

    Args:
        expr: Expression to render.
        style: Text style. Use ``"unicode"`` for a prettier terminal view or
            ``"ascii"`` for a portable fallback.
        aliases: Optional local aliases to substitute by exact structural
            equality during rendering.

    Returns:
        Human-readable rendering.
    """
    return _render(
        expr,
        parent_precedence=0,
        style=style,
        aliases=tuple(aliases or ()),
    )


def render_text_list(
    exprs: Sequence[ExprLike],
    *,
    style: RenderStyle = "unicode",
    aliases: Sequence[AliasBinding] | None = None,
) -> list[str]:
    """Render a sequence of expressions as human-readable text.

    Args:
        exprs: Expressions to render.
        style: Text style. Use ``"unicode"`` for a prettier terminal view or
            ``"ascii"`` for a portable fallback.
        aliases: Optional local aliases to substitute by exact structural
            equality during rendering.

    Returns:
        Human-readable rendering for each expression.
    """
    return [render_text(expr, style=style, aliases=aliases) for expr in exprs]


def _render(
    expr: ExprLike,
    parent_precedence: int,
    *,
    style: RenderStyle,
    aliases: tuple[AliasBinding, ...],
) -> str:
    """Render a single expression using precedence-aware parentheses.

    Args:
        expr: Expression to render.
        parent_precedence: Parent precedence level.
        style: Text style.
        aliases: Local aliases to substitute by exact structural equality.

    Returns:
        Human-readable rendering.

    Raises:
        ValueError: If the expression kind is unknown.
    """
    alias_name = _match_alias(expr, aliases)
    if alias_name is not None:
        return alias_name

    kind = _expect_str(expr, "kind")
    try:
        precedence = _PRECEDENCE[kind]
    except KeyError as exc:
        raise ValueError(f"Unknown RadicalExpr node kind: {kind!r}") from exc

    if kind == "qq":
        rendered = _render_qq(expr)
    elif kind == "zeta":
        rendered = _render_zeta(expr, style=style)
    elif kind == "neg":
        rendered = _render_neg(expr, precedence, style=style, aliases=aliases)
    elif kind == "add":
        rendered = _render_add(expr, precedence, style=style, aliases=aliases)
    elif kind == "sub":
        rendered = _render_sub(expr, precedence, style=style, aliases=aliases)
    elif kind == "mul":
        rendered = _render_mul(expr, precedence, style=style, aliases=aliases)
    elif kind == "div":
        rendered = _render_div(expr, precedence, style=style, aliases=aliases)
    elif kind == "pow_int":
        rendered = _render_pow_int(expr, precedence, style=style, aliases=aliases)
    elif kind == "root":
        rendered = _render_root(expr, style=style, aliases=aliases)
    else:
        raise ValueError(f"Unknown RadicalExpr node kind: {kind!r}")

    if precedence < parent_precedence:
        return f"({rendered})"
    return rendered


def _match_alias(
    expr: ExprLike,
    aliases: tuple[AliasBinding, ...],
) -> str | None:
    """Return the first alias whose payload matches ``expr`` exactly."""
    for name, aliased_expr in aliases:
        if expr == aliased_expr:
            return name
    return None


def _render_signed(
    expr: ExprLike,
    parent_precedence: int,
    *,
    style: RenderStyle,
    aliases: tuple[AliasBinding, ...],
) -> tuple[int, str]:
    """Render an expression as a signed term.

    If the whole expression matches a local alias, keep it as an alias and do
    not peel off its leading sign. Otherwise, split only an explicit syntactic
    leading sign.
    """
    alias_name = _match_alias(expr, aliases)
    if alias_name is not None:
        return 1, alias_name

    sign, unsigned_expr = _split_leading_sign(expr)
    rendered = _render(
        unsigned_expr,
        parent_precedence,
        style=style,
        aliases=aliases,
    )
    return sign, rendered


def _render_neg(
    expr: ExprLike,
    precedence: int,
    *,
    style: RenderStyle,
    aliases: tuple[AliasBinding, ...],
) -> str:
    """Render a ``neg`` node."""
    arg = _expect_expr(expr, "arg")
    return "-" + _render(arg, precedence, style=style, aliases=aliases)


def _render_add(
    expr: ExprLike,
    precedence: int,
    *,
    style: RenderStyle,
    aliases: tuple[AliasBinding, ...],
) -> str:
    """Render an ``add`` node with sign normalization."""
    left = _expect_expr(expr, "left")
    right = _expect_expr(expr, "right")
    left_s = _render(left, precedence, style=style, aliases=aliases)

    right_sign, right_s = _render_signed(
        right,
        precedence + 1,
        style=style,
        aliases=aliases,
    )
    sep = " - " if right_sign < 0 else " + "
    return f"{left_s}{sep}{right_s}"


def _render_sub(
    expr: ExprLike,
    precedence: int,
    *,
    style: RenderStyle,
    aliases: tuple[AliasBinding, ...],
) -> str:
    """Render a ``sub`` node with sign normalization."""
    left = _expect_expr(expr, "left")
    right = _expect_expr(expr, "right")
    left_s = _render(left, precedence, style=style, aliases=aliases)

    right_sign, right_s = _render_signed(
        right,
        precedence + 1,
        style=style,
        aliases=aliases,
    )
    sep = " + " if right_sign < 0 else " - "
    return f"{left_s}{sep}{right_s}"


def _render_mul(
    expr: ExprLike,
    precedence: int,
    *,
    style: RenderStyle,
    aliases: tuple[AliasBinding, ...],
) -> str:
    """Render a ``mul`` node with flattened factors and local sign cleanup."""
    op = " · " if style == "unicode" else " * "

    sign = 1
    parts: list[str] = []
    rational_acc = Fraction(1, 1)

    for factor in _collect_mul_factors(expr, aliases):
        alias_name = _match_alias(factor, aliases)
        if alias_name is not None:
            _append_rational_factor(parts, rational_acc)
            rational_acc = Fraction(1, 1)
            parts.append(alias_name)
            continue

        factor_sign, unsigned_factor = _split_leading_sign(factor)
        sign *= factor_sign

        factor_q = _qq_fraction(unsigned_factor)
        if factor_q is not None:
            rational_acc *= factor_q
            continue

        _append_rational_factor(parts, rational_acc)
        rational_acc = Fraction(1, 1)
        parts.append(_render(unsigned_factor, precedence, style=style, aliases=aliases))

    _append_rational_factor(parts, rational_acc)

    if not parts:
        parts.append("1")

    sign_prefix = "-" if sign < 0 else ""
    return sign_prefix + op.join(parts)


def _render_div(
    expr: ExprLike,
    precedence: int,
    *,
    style: RenderStyle,
    aliases: tuple[AliasBinding, ...],
) -> str:
    """Render a ``div`` node with light sign normalization."""
    left = _expect_expr(expr, "left")
    right = _expect_expr(expr, "right")

    left_sign, left_s = _render_signed(left, precedence, style=style, aliases=aliases)
    right_sign, right_s = _render_signed(
        right,
        precedence + 1,
        style=style,
        aliases=aliases,
    )
    sign_prefix = "-" if left_sign * right_sign < 0 else ""
    return f"{sign_prefix}{left_s} / {right_s}"


def _collect_mul_factors(
    expr: ExprLike,
    aliases: tuple[AliasBinding, ...],
) -> list[Expr]:
    """Collect multiplication factors while preserving exact alias boundaries."""
    if _match_alias(expr, aliases) is not None:
        return [dict(expr)]

    kind = _expect_str(expr, "kind")
    if kind != "mul":
        return [dict(expr)]

    factors: list[Expr] = []
    factors.extend(_collect_mul_factors(_expect_expr(expr, "left"), aliases))
    factors.extend(_collect_mul_factors(_expect_expr(expr, "right"), aliases))
    return factors


def _append_rational_factor(parts: list[str], value: Fraction) -> None:
    """Append a non-trivial rational factor to ``parts``."""
    if value == 1:
        return
    parts.append(str(value))


def _qq_fraction(expr: ExprLike) -> Fraction | None:
    """Return the rational value of a literal ``qq`` node when available."""
    if _expect_str(expr, "kind") != "qq":
        return None

    value = expr.get("value_qq")
    if not isinstance(value, str):
        return None
    return Fraction(value)


def _render_qq(expr: ExprLike) -> str:
    """Render a ``qq`` node.

    Args:
        expr: ``qq`` node.

    Returns:
        Text rendering.
    """
    value = expr.get("value_qq")
    if isinstance(value, str):
        return value
    return f"qq_ref({_expect_str(expr, 'ref')})"


def _render_zeta(expr: ExprLike, *, style: RenderStyle) -> str:
    """Render a ``zeta`` node.

    Args:
        expr: ``zeta`` node.
        style: Text style.

    Returns:
        Text rendering.
    """
    n = _expect_int(expr, "n")
    k = _expect_int(expr, "k")
    if style == "unicode":
        base = "ζ" + _to_subscript(n)
        if k == 1:
            return base
        return base + _to_superscript(k)
    base = f"zeta_{n}"
    if k == 1:
        return base
    return f"{base}^{k}"


def _render_pow_int(
    expr: ExprLike,
    precedence: int,
    *,
    style: RenderStyle,
    aliases: tuple[AliasBinding, ...],
) -> str:
    """Render a ``pow_int`` node.

    Args:
        expr: ``pow_int`` node.
        precedence: Local precedence.
        style: Text style.
        aliases: Local aliases.

    Returns:
        Text rendering.
    """
    base = _render(_expect_expr(expr, "base"), precedence, style=style, aliases=aliases)
    exp = _expect_int(expr, "exp")
    if style == "unicode":
        return base + _to_superscript(exp)
    return f"{base}^{exp}"


def _render_root(
    expr: ExprLike,
    *,
    style: RenderStyle,
    aliases: tuple[AliasBinding, ...],
) -> str:
    """Render a ``root`` node.

    Args:
        expr: ``root`` node.
        style: Text style.
        aliases: Local aliases.

    Returns:
        Text rendering.
    """
    n = _expect_int(expr, "n")
    arg = _render(_expect_expr(expr, "arg"), 0, style=style, aliases=aliases)
    if style == "unicode":
        if n == 2:
            return f"√({arg})"
        if n == 3:
            return f"∛({arg})"
        return f"{_to_superscript(n)}√({arg})"
    if n == 2:
        return f"sqrt({arg})"
    if n == 3:
        return f"cbrt({arg})"
    return f"root_{n}({arg})"


def _split_leading_sign(expr: ExprLike) -> tuple[int, Expr]:
    """Split an obvious leading sign from an expression.

    This helper is intentionally conservative. It only peels off a leading
    negative sign when that sign is syntactically explicit in the AST.

    Args:
        expr: Expression to inspect.

    Returns:
        A pair ``(sign, unsigned_expr)`` where ``sign`` is either ``1`` or
        ``-1``.
    """
    kind = _expect_str(expr, "kind")
    if kind == "neg":
        return -1, _expect_expr(expr, "arg")

    if kind == "qq":
        value = expr.get("value_qq")
        if isinstance(value, str) and value.startswith("-"):
            return -1, {"kind": "qq", "value_qq": value[1:]}

    if kind in {"mul", "div"}:
        left = _expect_expr(expr, "left")
        left_sign, left_expr = _split_leading_sign(left)
        if left_sign < 0:
            left_q = _qq_fraction(left_expr)
            if left_q == 1 and kind == "mul":
                return -1, _expect_expr(expr, "right")
            return -1, {
                "kind": kind,
                "left": left_expr,
                "right": _expect_expr(expr, "right"),
            }

    return 1, dict(expr)


def _to_superscript(value: int) -> str:
    """Convert an integer to a Unicode superscript string.

    Args:
        value: Integer exponent.

    Returns:
        Unicode superscript string.
    """
    return str(value).translate(_SUPERSCRIPT_MAP)


def _to_subscript(value: int) -> str:
    """Convert an integer to a Unicode subscript string.

    Args:
        value: Integer value.

    Returns:
        Unicode subscript string.
    """
    return str(value).translate(_SUBSCRIPT_MAP)


def _expect_expr(expr: ExprLike, key: str) -> Expr:
    """Extract a child expression.

    Args:
        expr: Parent node.
        key: Child key.

    Returns:
        Child expression.

    Raises:
        ValueError: If the child is missing or malformed.
    """
    value = expr.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a RadicalExpr mapping")
    return dict(value)


def _expect_int(expr: ExprLike, key: str) -> int:
    """Extract an integer field.

    Args:
        expr: Parent node.
        key: Field key.

    Returns:
        Integer field value.

    Raises:
        ValueError: If the field is missing or malformed.
    """
    value = expr.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be a non-boolean integer")
    return value


def _expect_str(expr: ExprLike, key: str) -> str:
    """Extract a string field.

    Args:
        expr: Parent node.
        key: Field key.

    Returns:
        String field value.

    Raises:
        ValueError: If the field is missing or malformed.
    """
    value = expr.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value
