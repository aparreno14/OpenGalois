# ruff: noqa: D102,D103
r"""Mathematical rendering helpers for clean Markdown/LaTeX explanations.

The helpers here return LaTeX math fragments. Markdown wraps the same fragments
in ``$...$`` and LaTeX wraps them in ``\(...\)``. This prevents the previous
failure mode where plain text such as ``x^4`` was escaped as text in LaTeX.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any, cast

from .context import ExplainContext

JsonMap = Mapping[str, Any]


_GROUP_LATEX: dict[str, str] = {
    "C1": "C_1",
    "C2": "C_2",
    "C3": "C_3",
    "C4": "C_4",
    "C5": "C_5",
    "C6": "C_6",
    "V4": "V_4",
    "D4": "D_4",
    "D5": "D_5",
    "D6": "D_6",
    "S3": "S_3",
    "S4": "S_4",
    "S5": "S_5",
    "A4": "A_4",
    "A5": "A_5",
    "F20": "F_{20}",
}


def rational_latex(value: str | int | Fraction) -> str:
    """Render a rational value as a LaTeX math fragment."""
    q = value if isinstance(value, Fraction) else Fraction(str(value))
    if q.denominator == 1:
        return str(q.numerator)
    return rf"\frac{{{q.numerator}}}{{{q.denominator}}}"


def _coeffs_from_poly(obj: JsonMap) -> list[str]:
    coeffs = obj.get("coeffs_qq", obj.get("coeffs"))
    if not isinstance(coeffs, Sequence) or isinstance(coeffs, (str, bytes)):
        return []
    return [str(c) for c in coeffs]


def poly_latex(obj: JsonMap, variable: str = "x") -> str:
    """Render a univariate polynomial object as LaTeX."""
    coeffs = _coeffs_from_poly(obj)
    if not coeffs:
        return "?"
    degree = len(coeffs) - 1
    terms: list[tuple[int, str]] = []
    for offset, coeff_s in enumerate(coeffs):
        coeff = Fraction(coeff_s)
        if coeff == 0:
            continue
        exp = degree - offset
        abs_coeff = abs(coeff)
        if exp == 0:
            body = rational_latex(abs_coeff)
        else:
            if abs_coeff == 1:
                coeff_part = ""
            else:
                coeff_part = rational_latex(abs_coeff)
            if exp == 1:
                body = f"{coeff_part}{variable}"
            else:
                body = f"{coeff_part}{variable}^{{{exp}}}"
        sign = -1 if coeff < 0 else 1
        terms.append((sign, body))
    if not terms:
        return "0"

    first_sign, first_body = terms[0]
    rendered = first_body if first_sign > 0 else f"-{first_body}"
    for sign, body in terms[1:]:
        op = "-" if sign < 0 else "+"
        rendered += f" {op} {body}"
    return rendered


def group_latex(value: str) -> str:
    """Render a group identifier as LaTeX."""
    return _GROUP_LATEX.get(value, value.replace("_", r"\_"))


def object_latex(ctx: ExplainContext, ref: str, *, symbolic_input: bool = True) -> str:
    """Render an object reference as a LaTeX math fragment."""
    if symbolic_input and ref == "$input":
        return "f"
    obj = ctx.get_object(ref)
    kind = obj.get("kind")
    if kind == "PolyQQ":
        return poly_latex(obj)
    if kind == "RatQQ":
        value = obj.get("value_qq", obj.get("value"))
        return rational_latex(str(value)) if value is not None else "?"
    if kind == "IntZ":
        value = obj.get("value", obj.get("value_z"))
        return str(value) if value is not None else "?"
    if kind == "GroupId":
        value = _group_value(obj, fallback=ref)
        return group_latex(value)
    if kind == "PolyQQList":
        return poly_list_latex(ctx, ref)
    if kind == "RadicalExpr":
        return radical_expr_latex(_expr_payload(obj), ctx)
    if kind == "RadicalExprList":
        return radical_list_latex(ctx, ref)
    if kind == "MPolyQQ":
        return mpoly_latex(obj)
    return str(ref).replace("_", r"\_")


def polynomial_name(ctx: ExplainContext, ref: str) -> str:
    """Return the preferred mathematical name for a polynomial reference."""
    return "f" if ref == "$input" else object_latex(ctx, ref, symbolic_input=False)


def equation_poly(
    ctx: ExplainContext,
    ref: str,
    name: str = "f",
    variable: str = "x",
) -> str:
    """Render ``name(x)=...`` for a polynomial reference."""
    poly_obj = ctx.get_object(ref)
    return rf"{name}({variable}) = {poly_latex(poly_obj, variable=variable)}"


def poly_list_latex(ctx: ExplainContext, ref: str) -> str:
    obj = ctx.get_object(ref)
    items = _sequence_field(obj, "items", "refs")
    rendered: list[str] = []
    for item in items:
        item_ref = _item_ref(item)
        if item_ref is not None:
            rendered.append(object_latex(ctx, item_ref, symbolic_input=False))
    return r"\left[" + ", ".join(rendered) + r"\right]"


def radical_list_latex(ctx: ExplainContext, ref: str) -> str:
    rendered = radical_list_items_latex(ctx, ref)
    return r"\left[" + ", ".join(rendered) + r"\right]"


def radical_list_items_latex(ctx: ExplainContext, ref: str) -> list[str]:
    obj = ctx.get_object(ref)
    items = _sequence_field(obj, "items", "exprs")
    rendered: list[str] = []
    for item in items:
        item_ref = _item_ref(item)
        if item_ref is not None:
            rendered.append(object_latex(ctx, item_ref, symbolic_input=False))
        elif isinstance(item, Mapping):
            rendered.append(radical_expr_latex(item, ctx))
    return rendered


def radical_list_display_latex(
    ctx: ExplainContext,
    ref: str,
    *,
    prefix: str = "r",
) -> str:
    items = radical_list_items_latex(ctx, ref)
    return _aligned_equations(items, prefix=prefix)


def radical_list_display_with_aliases_latex(
    ctx: ExplainContext,
    ref: str,
    *,
    prefix: str = "r",
) -> tuple[str | None, str]:
    """Render a radical list, introducing light aliases for long quintic output.

    The aliasing is intentionally conservative.  It is only enabled for the
    long degree-five pattern, where five expressions involve roots of unity and
    repeatedly contain the same nested radicals.  Smaller formulas are left
    untouched so that the proof remains close to the actual certificate.
    """
    payloads = radical_list_item_payloads(ctx, ref)
    if not _looks_like_quintic_radical_list(payloads):
        return None, radical_list_display_latex(ctx, ref, prefix=prefix)

    aliases = _select_radical_aliases(payloads, ctx, max_aliases=3)
    if not aliases:
        return None, radical_list_display_latex(ctx, ref, prefix=prefix)

    alias_map: dict[str, str] = {}
    alias_lines: list[str] = []
    for index, (key, name, expr) in enumerate(aliases):
        rhs = _radical_expr_latex_with_aliases(expr, ctx, alias_map)
        suffix = r"\\" if index < len(aliases) - 1 else ""
        alias_lines.append(rf"{name} &:= {rhs}{suffix}")
        alias_map[key] = name

    rendered_roots = [
        _radical_expr_latex_with_aliases(expr, ctx, alias_map)
        for expr in payloads
    ]

    aliases_display = "\n".join([r"\begin{aligned}", *alias_lines, r"\end{aligned}"])
    return aliases_display, _aligned_equations(rendered_roots, prefix=prefix)


def radical_list_item_payloads(ctx: ExplainContext, ref: str) -> list[JsonMap]:
    obj = ctx.get_object(ref)
    items = _sequence_field(obj, "items", "exprs")
    payloads: list[JsonMap] = []
    for item in items:
        item_ref = _item_ref(item)
        if item_ref is not None:
            item_obj = ctx.get_object(item_ref)
            if item_obj.get("kind") == "RadicalExpr":
                payloads.append(_expr_payload(item_obj))
        elif isinstance(item, Mapping):
            payloads.append(cast(JsonMap, item))
    return payloads


def radical_list_zeta_orders(ctx: ExplainContext, ref: str) -> tuple[int, ...]:
    orders: set[int] = set()
    for expr in radical_list_item_payloads(ctx, ref):
        for node in _walk_expr(expr):
            if node.get("kind") == "zeta":
                n = node.get("n")
                if isinstance(n, int):
                    orders.add(n)
                elif isinstance(n, str) and n.isdigit():
                    orders.add(int(n))
    return tuple(sorted(orders))


def radical_list_contains_zeta(ctx: ExplainContext, ref: str) -> bool:
    return bool(radical_list_zeta_orders(ctx, ref))


def radical_list_needs_display(ctx: ExplainContext, ref: str) -> bool:
    items = radical_list_items_latex(ctx, ref)
    joined = ", ".join(items)
    return len(joined) > 80 or any(r"\sqrt" in item or r"\zeta" in item for item in items)


def _aligned_equations(items: list[str], *, prefix: str) -> str:
    if not items:
        return r"\left[\right]"
    lines: list[str] = [r"\begin{aligned}"]
    for index, item in enumerate(items, start=1):
        suffix = r"\\" if index < len(items) else ""
        lines.append(rf"{prefix}_{{{index}}} &:= {item}{suffix}")
    lines.append(r"\end{aligned}")
    return "\n".join(lines)


def _looks_like_quintic_radical_list(payloads: list[JsonMap]) -> bool:
    if len(payloads) != 5:
        return False
    has_zeta = any(node.get("kind") == "zeta" for expr in payloads for node in _walk_expr(expr))
    has_fifth_root = any(
        node.get("kind") == "root" and node.get("n") == 5
        for expr in payloads
        for node in _walk_expr(expr)
    )
    return has_zeta and has_fifth_root


def _select_radical_aliases(
    payloads: list[JsonMap],
    ctx: ExplainContext,
    *,
    max_aliases: int,
) -> list[tuple[str, str, JsonMap]]:
    counts: dict[str, int] = {}
    nodes: dict[str, JsonMap] = {}
    for expr in payloads:
        for node in _walk_expr(expr):
            if node.get("kind") != "root":
                continue
            rendered = radical_expr_latex(node, ctx)
            if len(rendered) < 10:
                continue
            key = _expr_key(node)
            counts[key] = counts.get(key, 0) + 1
            nodes[key] = node

    candidates = [
        (key, nodes[key])
        for key, count in counts.items()
        if count >= 2
    ]
    candidates.sort(key=lambda item: len(radical_expr_latex(item[1], ctx)), reverse=True)
    selected = candidates[:max_aliases]
    selected.sort(key=lambda item: len(_expr_key(item[1])))

    used: set[str] = set()
    sqrt_names = iter(["a", "b", "c"])
    other_names = iter(["u", "v", "w"])
    out: list[tuple[str, str, JsonMap]] = []
    for key, expr in selected:
        n = expr.get("n")
        if n == 5 and "u" not in used:
            name = "u"
        elif n == 2:
            name = next((candidate for candidate in sqrt_names if candidate not in used), "a")
        else:
            name = next((candidate for candidate in other_names if candidate not in used), "u")
        used.add(name)
        out.append((key, name, expr))
    return out


def _walk_expr(expr: JsonMap) -> list[JsonMap]:
    out: list[JsonMap] = [expr]
    kind = expr.get("kind")
    if kind in {"neg"}:
        out.extend(_walk_expr(_child(expr, "arg")))
    elif kind in {"add", "sub", "mul", "div"}:
        out.extend(_walk_expr(_child(expr, "left")))
        out.extend(_walk_expr(_child(expr, "right")))
    elif kind == "pow_int":
        out.extend(_walk_expr(_child(expr, "base")))
    elif kind == "root":
        out.extend(_walk_expr(_child(expr, "arg")))
    return out


def _expr_key(expr: JsonMap) -> str:
    return json.dumps(expr, sort_keys=True, separators=(",", ":"))


def _radical_expr_latex_with_aliases(
    expr: JsonMap,
    ctx: ExplainContext | None,
    aliases: Mapping[str, str],
) -> str:
    alias = aliases.get(_expr_key(expr))
    if alias is not None:
        return alias

    kind = expr.get("kind")
    if kind == "qq":
        ref = expr.get("ref")
        if isinstance(ref, str) and ctx is not None:
            return object_latex(ctx, ref, symbolic_input=False)
        value = expr.get("value_qq", expr.get("value"))
        return rational_latex(str(value)) if value is not None else "?"
    if kind == "zeta":
        n = expr.get("n", "?")
        k = expr.get("k", 1)
        zeta_base = rf"\zeta_{{{n}}}"
        return zeta_base if k == 1 else rf"{zeta_base}^{{{k}}}"
    if kind == "neg":
        return "-" + _paren_if_needed_alias(_child(expr, "arg"), ctx, aliases)
    if kind in {"add", "sub", "mul", "div"}:
        left = _child(expr, "left")
        right = _child(expr, "right")
        left_s = _radical_expr_latex_with_aliases(left, ctx, aliases)
        right_s = _radical_expr_latex_with_aliases(right, ctx, aliases)
        if kind == "add":
            return rf"{left_s} + {right_s}"
        if kind == "sub":
            return rf"{left_s} - {right_s}"
        if kind == "mul":
            left_wrapped = _paren_if_needed_alias(left, ctx, aliases)
            right_wrapped = _paren_if_needed_alias(right, ctx, aliases)
            return rf"{left_wrapped}{right_wrapped}"
        if left.get("kind") == "neg":
            numerator = _radical_expr_latex_with_aliases(_child(left, "arg"), ctx, aliases)
            return rf"-\frac{{{numerator}}}{{{right_s}}}"
        return rf"\frac{{{left_s}}}{{{right_s}}}"
    if kind == "pow_int":
        base_expr = _child(expr, "base")
        exp = expr.get("exp", "?")
        return rf"{_paren_if_needed_alias(base_expr, ctx, aliases)}^{{{exp}}}"
    if kind == "root":
        n = expr.get("n")
        arg = _radical_expr_latex_with_aliases(_child(expr, "arg"), ctx, aliases)
        if n == 2:
            return rf"\sqrt{{{arg}}}"
        return rf"\sqrt[{n}]{{{arg}}}"
    return "?"


def _paren_if_needed_alias(
    expr: JsonMap,
    ctx: ExplainContext | None,
    aliases: Mapping[str, str],
) -> str:
    inner = _radical_expr_latex_with_aliases(expr, ctx, aliases)
    kind = expr.get("kind")
    if kind in {"add", "sub"}:
        return rf"\left({inner}\right)"
    return inner


def poly_list_product_latex(
    ctx: ExplainContext,
    ref: str,
    *,
    variable: str = "x",
) -> str:
    """Render a PolyQQList as a product of factors."""
    obj = ctx.get_object(ref)
    items = _sequence_field(obj, "items", "refs")
    rendered: list[str] = []
    for item in items:
        item_ref = _item_ref(item)
        if item_ref is None:
            continue
        factor_obj = ctx.get_object(item_ref)
        factor_s = poly_latex(factor_obj, variable=variable)
        rendered.append(_factor_parenthesize(factor_s))
    if not rendered:
        return "1"
    return r"\cdot ".join(rendered)


def _factor_parenthesize(factor: str) -> str:
    if " + " in factor or " - " in factor or factor.startswith("-"):
        return rf"\left({factor}\right)"
    return factor


def _sequence_field(obj: JsonMap, *names: str) -> list[object]:
    for name in names:
        value = obj.get(name)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return list(value)
    return []


def _item_ref(item: object) -> str | None:
    if isinstance(item, str) and item:
        return item
    if isinstance(item, Mapping):
        raw = item.get("ref")
        return raw if isinstance(raw, str) and raw else None
    return None


def _group_value(obj: JsonMap, *, fallback: str) -> str:
    for key in ("alias", "label", "value", "name", "id"):
        value = obj.get(key)
        if isinstance(value, str) and value:
            return value
    return fallback.rsplit(".", 1)[-1] if fallback else "?"


def _expr_payload(obj: JsonMap) -> JsonMap:
    expr = obj.get("expr", obj.get("value", obj))
    return cast(JsonMap, expr) if isinstance(expr, Mapping) else obj


def radical_expr_latex(expr: JsonMap, ctx: ExplainContext | None = None) -> str:
    """Render a radical AST as a LaTeX math fragment."""
    kind = expr.get("kind")
    if kind == "qq":
        ref = expr.get("ref")
        if isinstance(ref, str) and ctx is not None:
            return object_latex(ctx, ref, symbolic_input=False)
        value = expr.get("value_qq", expr.get("value"))
        return rational_latex(str(value)) if value is not None else "?"
    if kind == "zeta":
        n = expr.get("n", "?")
        k = expr.get("k", 1)
        zeta_base = rf"\zeta_{{{n}}}"
        return zeta_base if k == 1 else rf"{zeta_base}^{{{k}}}"
    if kind == "neg":
        return "-" + _paren_if_needed(_child(expr, "arg"), ctx)
    if kind in {"add", "sub", "mul", "div"}:
        left = _child(expr, "left")
        right = _child(expr, "right")
        left_s = radical_expr_latex(left, ctx)
        right_s = radical_expr_latex(right, ctx)
        if kind == "add":
            return rf"{left_s} + {right_s}"
        if kind == "sub":
            return rf"{left_s} - {right_s}"
        if kind == "mul":
            return rf"{_paren_if_needed(left, ctx)}{_paren_if_needed(right, ctx)}"
        if left.get("kind") == "neg":
            numerator = radical_expr_latex(_child(left, "arg"), ctx)
            return rf"-\frac{{{numerator}}}{{{right_s}}}"
        return rf"\frac{{{left_s}}}{{{right_s}}}"
    if kind == "pow_int":
        base_expr = _child(expr, "base")
        exp = expr.get("exp", "?")
        return rf"{_paren_if_needed(base_expr, ctx)}^{{{exp}}}"
    if kind == "root":
        n = expr.get("n")
        arg = radical_expr_latex(_child(expr, "arg"), ctx)
        if n == 2:
            return rf"\sqrt{{{arg}}}"
        return rf"\sqrt[{n}]{{{arg}}}"
    return "?"


def _child(expr: JsonMap, key: str) -> JsonMap:
    child = expr.get(key)
    return cast(JsonMap, child) if isinstance(child, Mapping) else {}


def _paren_if_needed(expr: JsonMap, ctx: ExplainContext | None) -> str:
    inner = radical_expr_latex(expr, ctx)
    kind = expr.get("kind")
    if kind in {"add", "sub"}:
        return rf"\left({inner}\right)"
    return inner


def mpoly_latex(obj: JsonMap) -> str:
    """Best-effort LaTeX for simple multivariate-polynomial payloads."""
    value = obj.get("latex", obj.get("expr", obj.get("value", obj.get("text"))))
    if value is None:
        return "?"
    return str(value).replace("*", "").replace("^", "^")


def factorization_latex(
    ctx: ExplainContext,
    fact_args: tuple[JsonMap, ...],
    *,
    variable: str = "x",
) -> str:
    """Render ``FactorizationMonicQQ(f, factors, unit)``."""
    if len(fact_args) < 3:
        return "?"
    poly_ref = _arg_ref(fact_args[0])
    factors_ref = _arg_ref(fact_args[1])
    unit_ref = _arg_ref(fact_args[2])
    poly_obj = ctx.get_object(poly_ref)
    poly_s = poly_latex(poly_obj, variable=variable)
    unit_s = object_latex(ctx, unit_ref, symbolic_input=False)
    factors_s = poly_list_product_latex(ctx, factors_ref, variable=variable)
    if unit_s == "1":
        return rf"{poly_s} = {factors_s}"
    return rf"{poly_s} = {unit_s}\cdot {factors_s}"


def is_resolvent_polynomial(ctx: ExplainContext, ref: str) -> bool:
    for fact in ctx.facts:
        if fact.pred == "ResolventQQ" and fact.ref_arg(0) == ref:
            return True
    return False


def _arg_ref(arg: JsonMap) -> str:
    ref = arg.get("ref")
    return ref if isinstance(ref, str) else "?"
