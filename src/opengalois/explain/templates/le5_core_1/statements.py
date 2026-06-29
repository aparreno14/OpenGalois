# ruff: noqa: D102,D103
"""Goal-statement templates for le5-core certificates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from ...context import ExplainContext, FactView
from ...math_render import (
    radical_list_display_with_aliases_latex,
    radical_list_latex,
    radical_list_needs_display,
    radical_list_zeta_orders,
)
from ...proof_model import ProofBlock, display_math, math, par
from ..registry import statement_template
from ._helpers import group, obj, poly, ref

JsonMap = Mapping[str, Any]


def _expr_key(expr: Mapping[str, Any]) -> str:
    import json

    return json.dumps(expr, sort_keys=True, separators=(",", ":"))


def _child(expr: Mapping[str, Any], key: str) -> JsonMap:
    value = expr.get(key)
    return cast(JsonMap, value) if isinstance(value, Mapping) else {"kind": "qq", "value_qq": "?"}


def _radical_expr_latex_with_aliases(
    expr: JsonMap,
    ctx: ExplainContext,
    aliases: Mapping[str, str],
) -> str:
    from ...math_render import object_latex, radical_expr_latex, rational_latex

    alias = aliases.get(_expr_key(expr))
    if alias is not None:
        return alias

    kind = expr.get("kind")
    if kind == "qq":
        ref_value = expr.get("ref")
        if isinstance(ref_value, str):
            return object_latex(ctx, ref_value, symbolic_input=False)
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
            return rf"{_paren_if_needed_alias(left, ctx, aliases)}\
                {_paren_if_needed_alias(right, ctx, aliases)}"
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

    return radical_expr_latex(expr, ctx)


def _paren_if_needed_alias(
    expr: JsonMap,
    ctx: ExplainContext,
    aliases: Mapping[str, str],
) -> str:
    inner = _radical_expr_latex_with_aliases(expr, ctx, aliases)
    return rf"\left({inner}\right)" if expr.get("kind") in {"add", "sub"} else inner


def _aligned_equations(items: Sequence[str], *, prefix: str = "r") -> str:
    if not items:
        return r"\left[\right]"
    lines = [r"\begin{aligned}"]
    for index, item in enumerate(items, start=1):
        suffix = r"\\" if index < len(items) else ""
        lines.append(rf"{prefix}_{{{index}}} &:= {item}{suffix}")
    lines.append(r"\end{aligned}")
    return "\n".join(lines)


@statement_template("GaloisGroup")
def statement_galois_group(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    g_s = group(ctx, ref(fact, 1))
    return (
        par(
            "The Galois group of ",
            math(f_s),
            " over ",
            math(r"\mathbb{Q}"),
            " is ",
            math(g_s),
            ".",
        ),
    )


@statement_template("SolvableByRadicals")
def statement_solvable(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (par("The polynomial ", math(f_s), " is solvable by radicals."),)


@statement_template("NonSolvableByRadicals")
def statement_nonsolvable(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (par("The polynomial ", math(f_s), " is not solvable by radicals."),)


@statement_template("RadicalRoots")
def statement_radical_roots(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    roots_ref = ref(fact, 1)
    if not radical_list_needs_display(ctx, roots_ref):
        roots_s = radical_list_latex(ctx, roots_ref)
        return (
            par(
                "The certified radical roots of ",
                math(f_s),
                " are ",
                math(roots_s),
                ".",
            ),
        )
    blocks: list[ProofBlock] = [par("The certified radical roots of ", math(f_s), " are:")]
    orders = radical_list_zeta_orders(ctx, roots_ref)
    if orders:
        zetas = ", ".join(rf"\zeta_{{{order}}}" for order in orders)
        if len(orders) == 1:
            blocks.append(
                par(
                    "Here ",
                    math(zetas),
                    " denotes a primitive ",
                    math(str(orders[0])),
                    "-th root of unity.",
                )
            )
        else:
            blocks.append(
                par(
                    "Here ",
                    math(zetas),
                    " denote primitive roots of unity of the indicated orders.",
                )
            )
    aliases_s, roots_s = _radical_display_with_generic_aliases_latex(ctx, roots_ref)
    if aliases_s is not None:
        blocks.append(par("To keep the expressions readable, set"))
        blocks.append(display_math(aliases_s))
        blocks.append(par("With this notation, the roots are"))
    blocks.append(display_math(roots_s))
    return tuple(blocks)


@statement_template("Degree")
def statement_degree(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        par(
            "The polynomial ",
            math(poly(ctx, ref(fact, 0))),
            " has degree ",
            math(obj(ctx, ref(fact, 1))),
            ".",
        ),
    )


@statement_template("NonSquareQQ")
def statement_nonsquare(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        par(
            "The rational number ",
            math(obj(ctx, ref(fact, 0))),
            " is not a square in ",
            math(r"\mathbb{Q}"),
            ".",
        ),
    )
    
@statement_template("IrreducibleQQ")
def statement_irreducible(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        par(
            "The polynomial ",
            math(poly(ctx, ref(fact, 0))),
            " is irreducible over ",
            math(r"\mathbb{Q}"),
            ".",
        ),
    )

# ---------------------------------------------------------------------------
# Scheme-aware radical aliases
# ---------------------------------------------------------------------------
#
# Keep this at the end of the file so it overrides the earlier generic helper
# without removing any existing templates.  The alias layout is delegated to the
# same scheme-aware machinery used by the terminal renderer:
#
#   - Cardano-v2 uses u.
#   - Ferrari-v2 uses s.
#   - depressed-monic lift inherits the aliases of the base radical rule.
#   - McClintock keeps its existing scheme-specific aliases.
#
# The output is still LaTeX, but the alias *selection* is the CLI one.

def _radical_fact_for_roots_ref(ctx: ExplainContext, roots_ref: str) -> FactView | None:
    for candidate in ctx.facts:
        try:
            if candidate.pred != "RadicalRoots":
                continue
            if len(candidate.args) != 2:
                continue
            if candidate.ref_arg(1) == roots_ref:
                return candidate
        except Exception:  # noqa: BLE001
            continue
    return None


def _cli_scheme_layout_for_roots(
    ctx: ExplainContext,
    roots_ref: str,
) -> tuple[list[tuple[str, JsonMap]], list[JsonMap]] | None:
    from opengalois.radicals.cli_format import _build_layout, _prune_unused_aliases
    from opengalois.radicals.codec import decode_expr_list_payloads

    radical_fact = _radical_fact_for_roots_ref(ctx, roots_ref)
    if radical_fact is None:
        return None

    try:
        roots_obj = ctx.get_object(roots_ref)
        exprs = decode_expr_list_payloads(roots_obj, ctx.objects)
        layout = _build_layout(ctx.certificate, radical_fact.raw, exprs)
        aliases = _prune_unused_aliases(layout.aliases, layout.roots)
    except Exception:  # noqa: BLE001
        return None

    if not aliases:
        return None

    return (
        [(name, cast(JsonMap, expr)) for name, expr in aliases],
        [cast(JsonMap, expr) for expr in layout.roots],
    )


def _radical_display_with_generic_aliases_latex(
    ctx: ExplainContext,
    roots_ref: str,
    *,
    prefix: str = "r",
) -> tuple[str | None, str]:
    layout = _cli_scheme_layout_for_roots(ctx, roots_ref)
    if layout is None:
        return radical_list_display_with_aliases_latex(ctx, roots_ref, prefix=prefix)

    aliases, roots = layout

    alias_map: dict[str, str] = {}
    alias_lines: list[str] = []
    for index, (name, expr) in enumerate(aliases):
        rhs = _radical_expr_latex_with_aliases(expr, ctx, alias_map)
        suffix = r"\\" if index < len(aliases) - 1 else ""
        alias_lines.append(rf"{name} &:= {rhs}{suffix}")
        alias_map[_expr_key(expr)] = name

    rendered_roots = [
        _radical_expr_latex_with_aliases(expr, ctx, alias_map)
        for expr in roots
    ]

    aliases_display = "\n".join([r"\begin{aligned}", *alias_lines, r"\end{aligned}"])
    return aliases_display, _aligned_equations(rendered_roots, prefix=prefix)
