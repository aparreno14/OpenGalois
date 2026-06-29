# ruff: noqa: D102,D103
"""Radical-solvability narrative templates for the clean renderer."""

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
from ...proof_model import Inline, Paragraph, ProofBlock, display_math, math, par
from ..registry import rule_template
from ._helpers import group, poly, ref


def _poly_coeffs_qq(ctx: ExplainContext, object_ref: str) -> list[str] | None:
    try:
        obj_map = ctx.get_object(object_ref)
    except Exception:  # noqa: BLE001
        return None
    coeffs = obj_map.get("coeffs_qq")
    if not isinstance(coeffs, Sequence) or isinstance(coeffs, (str, bytes)):
        return None
    if not all(isinstance(c, str) for c in coeffs):
        return None
    return list(coeffs)


def _same_poly(ctx: ExplainContext, left_ref: str, right_ref: str) -> bool:
    left = _poly_coeffs_qq(ctx, left_ref)
    right = _poly_coeffs_qq(ctx, right_ref)
    return left is not None and right is not None and left == right


def _normalization_identity_from_premises(fact: FactView, ctx: ExplainContext) -> bool:
    f_ref = ref(fact, 0)
    for premise_id in fact.premises:
        premise = ctx.get_fact(premise_id)
        if premise.pred != "DepressedMonicEq":
            continue
        try:
            original_ref = ref(premise, 0)
            normalized_ref = ref(premise, 1)
        except Exception:  # noqa: BLE001
            continue
        if original_ref == f_ref and _same_poly(ctx, original_ref, normalized_ref):
            return True
    return False


def _is_depressed_quartic_biquadratic(ctx: ExplainContext, object_ref: str) -> bool:
    """Return true for a depressed quartic with zero linear term."""
    coeffs = _poly_coeffs_qq(ctx, object_ref)
    if coeffs is None or len(coeffs) != 5:
        return False
    # Descending order: y^4 + 0*y^3 + c*y^2 + d*y + e.
    return coeffs[0] == "1" and coeffs[1] == "0" and coeffs[3] == "0"


def _poly_degree(ctx: ExplainContext, object_ref: str) -> int | None:
    coeffs = _poly_coeffs_qq(ctx, object_ref)
    if coeffs is None:
        return None
    return len(coeffs) - 1


def _used_as_ferrari_resolvent_roots(fact: FactView, ctx: ExplainContext) -> bool:
    """Detect the auxiliary cubic-resolvent root fact consumed by Ferrari."""
    for candidate in ctx.facts:
        if candidate.pred != "RadicalRoots":
            continue
        if candidate.rule_id not in {
            "radical_roots.QQ.deg4.ferrari.depressed_monic@1",
            "radical_roots.QQ.deg4.ferrari.depressed_monic@2",
        }:
            continue
        if fact.fact_id in candidate.premises:
            return True
    return False


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


@rule_template("solvable_by_radicals.QQ.from_galois_group@1")
def explain_solvable_from_group(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    f_s = poly(ctx, ref(fact, 0))
    group_ref = _group_ref_from_premise_or_claim(fact, ctx)
    group_s = group(ctx, group_ref) if group_ref is not None else "G"
    return (
        par(
            "The Galois group already found for ",
            math(f_s),
            " is ",
            math(group_s),
            ". ",
            *_solvability_reason_parts(group_ref, ctx),
        ),
        par(
            "Therefore ",
            math(f_s),
            " is solvable by radicals.",
        ),
    )


@rule_template("nonsolvable_by_radicals.QQ.from_galois_group@1")
def explain_nonsolvable_from_group(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    f_s = poly(ctx, ref(fact, 0))
    group_s = _group_from_premise_or_claim(fact, ctx)
    return (
        par(
            "The Galois group already found for ",
            math(f_s),
            " is ",
            math(group_s),
            ". This group is not solvable.",
        ),
        par(
            "Therefore ",
            math(f_s),
            " is not solvable by radicals.",
        ),
    )


@rule_template("radical_roots.QQ.deg1.trivial@1")
def explain_radicals_deg1(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    f_s = poly(ctx, ref(fact, 0))
    roots_s = radical_list_latex(ctx, ref(fact, 1))
    return (
        par(
            "Since ",
            math(f_s),
            " is linear, its only root lies in ",
            math(r"\mathbb{Q}"),
            ". Hence the polynomial is solvable by radicals in the trivial ",
            "sense. The certified root is ",
            math(roots_s),
            ".",
        ),
    )


@rule_template("radical_roots.QQ.deg2.quadratic_formula@1")
def explain_radicals_deg2(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return _radical_roots_sentence(
        fact,
        ctx,
        "Every quadratic is solvable by radicals: adjoining the square root "
        "of its discriminant gives the splitting field. Applying the classical "
        "quadratic formula, the roots are",
    )


@rule_template("radical_roots.QQ.deg3.cardano.depressed_monic@1")
def explain_cardano_v1(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return _radical_roots_sentence(
        fact,
        ctx,
        "Every cubic is solvable by radicals: in the irreducible case the "
        "Galois group is either C_3 or S_3, both solvable. Using the "
        "Cardano--Descartes formula for the depressed cubic, the roots are",
    )


@rule_template("radical_roots.QQ.deg3.cardano.depressed_monic@2")
def explain_cardano_v2(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return _radical_roots_sentence(
        fact,
        ctx,
        "Every cubic is solvable by radicals: in the irreducible case the "
        "Galois group is either C_3 or S_3, both solvable. Using the "
        "Cardano--Descartes formula for the depressed cubic, the roots are",
    )


@rule_template("radical_roots.QQ.reducible.compose@1")
def explain_reducible_compose_v1(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return _radical_roots_sentence(
        fact,
        ctx,
        "Since the polynomial factors and each irreducible factor has the "
        "certified roots above, the roots of the original polynomial are",
    )


@rule_template("radical_roots.QQ.reducible.compose@2")
def explain_reducible_compose(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return _radical_roots_sentence(
        fact,
        ctx,
        "Since the polynomial factors and the roots of each factor are known, "
        "the roots of the original polynomial are",
    )


@rule_template("radical_roots.QQ.deg4.ferrari.depressed_monic@1")
def explain_ferrari_v1(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return _explain_ferrari_common(fact, ctx)


@rule_template("radical_roots.QQ.deg4.ferrari.depressed_monic@2")
def explain_ferrari_v2(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return _explain_ferrari_common(fact, ctx)


def _explain_ferrari_common(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_ref = ref(fact, 0)
    if _is_depressed_quartic_biquadratic(ctx, f_ref):
        return _explain_biquadratic_quartic_roots(fact, ctx)

    return _radical_roots_sentence(
        fact,
        ctx,
        "Every quartic is solvable by radicals. In the non-biquadratic "
        "depressed case, OpenGalois applies Ferrari's method in the quartic "
        "variable. The auxiliary cubic resolvent roots have already been "
        "certified above; after undoing any normalization of that auxiliary "
        "cubic, one of those roots is the parameter s used below. The roots "
        "of the depressed quartic are",
    )


def _explain_biquadratic_quartic_roots(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    roots_ref = ref(fact, 1)
    intro = par(
        "The depressed quartic has zero linear term, so this is the ",
        "biquadratic case. OpenGalois uses the change of variable ",
        math(r"z=x^2"),
        " and solves the resulting quadratic in ",
        math("z"),
        ".",
    )
    if not radical_list_needs_display(ctx, roots_ref):
        roots_s = radical_list_latex(ctx, roots_ref)
        return (
            intro,
            par("The certified roots of ", math(f_s), " are ", math(roots_s), "."),
        )
    return (
        intro,
        par("The certified roots of ", math(f_s), " are:"),
        *_radical_display_blocks(ctx, roots_ref),
    )



@rule_template("radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1")
def explain_euler_symmetric_quartic(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return _radical_roots_sentence(
        fact,
        ctx,
        "Every quartic is solvable by radicals: all subgroups of S_4 are "
        "solvable. Using the symmetric Euler form for the depressed quartic "
        "and the roots of the resolvent, the roots are",
    )


@rule_template("radical_roots.QQ.deg5.mcclintock.depressed_monic@1")
def explain_mcclintock_quintic(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    roots_ref = ref(fact, 1)
    intro = par(
        "The rational root of Dummit's resolvent places the quintic in the ",
        "solvable case: equivalently, the Galois group is contained in a ",
        "conjugate of ",
        math(r"F_{20}"),
        ". Since ",
        math(r"C_5 \triangleleft F_{20}"),
        " and the quotient is ",
        math(r"C_4"),
        ", this group is solvable. Using the degree-five procedure based ",
        "on McClintock's method, the roots are for ",
        math(f_s),
        ":",
    )
    if not radical_list_needs_display(ctx, roots_ref):
        roots_s = radical_list_latex(ctx, roots_ref)
        return (intro, par(math(roots_s), "."))
    return (intro, *_radical_display_blocks(ctx, roots_ref))


@rule_template("radical_roots.QQ.lift.depressed_monic@1")
def explain_lift_depressed_monic(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    f_ref = ref(fact, 0)
    roots_ref = ref(fact, 1)

    if _normalization_identity_from_premises(fact, ctx):
        if not radical_list_needs_display(ctx, roots_ref):
            roots_s = radical_list_latex(ctx, roots_ref)
            return (
                par(
                    "Since the normalization is the identity, the radical expressions ",
                    "obtained for the depressed-monic polynomial are already the roots ",
                    "of ",
                    math(f_s),
                    ": ",
                    math(roots_s),
                    ".",
                ),
            )
        return (
            par(
                "Since the normalization is the identity, no affine transport of ",
                "the radical expressions is needed: the roots obtained for the ",
                "depressed-monic polynomial are already roots of ",
                math(f_s),
                ".",
            ),
        )

    if _used_as_ferrari_resolvent_roots(fact, ctx):
        if not radical_list_needs_display(ctx, roots_ref):
            roots_s = radical_list_latex(ctx, roots_ref)
            return (
                par(
                    "Undoing the depressed normalization of the auxiliary cubic ",
                    "gives the resolvent roots used by Ferrari: ",
                    math(roots_s),
                    ".",
                ),
            )
        return (
            par(
                "Undoing the depressed normalization of the auxiliary cubic gives ",
                "the resolvent roots used by Ferrari:",
            ),
            *_radical_display_blocks(ctx, roots_ref),
        )

    if not radical_list_needs_display(ctx, roots_ref):
        roots_s = radical_list_latex(ctx, roots_ref)
        if _poly_degree(ctx, f_ref) == 4:
            return (
                par(
                    "Finally, undoing the affine normalization of the original ",
                    "quartic gives the roots ",
                    math(roots_s),
                    " for ",
                    math(f_s),
                    ".",
                ),
            )
        return (
            par(
                "Transporting the roots through the inverse affine normalization ",
                "amounts to undoing the Tschirnhaus translation. Therefore the ",
                "roots of the original polynomial are ",
                math(roots_s),
                " for ",
                math(f_s),
                ".",
            ),
        )

    if _poly_degree(ctx, f_ref) == 4:
        return (
            par(
                "Finally, undoing the affine normalization of the original quartic ",
                "gives the roots:",
            ),
            *_radical_display_blocks(ctx, roots_ref),
        )

    return (
        par(
            "Transporting the roots through the inverse affine normalization ",
            "amounts to undoing the Tschirnhaus translation. Therefore the roots ",
            "of the original polynomial are:",
        ),
        *_radical_display_blocks(ctx, roots_ref),
    )


def _radical_roots_sentence(
    fact: FactView,
    ctx: ExplainContext,
    prefix: str,
) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    roots_ref = ref(fact, 1)
    if not radical_list_needs_display(ctx, roots_ref):
        roots_s = radical_list_latex(ctx, roots_ref)
        return (
            par(prefix, " ", math(roots_s), " for ", math(f_s), "."),
        )
    return (
        par(prefix, " for ", math(f_s), ":"),
        *_radical_display_blocks(ctx, roots_ref),
    )


def _radical_display_blocks(ctx: ExplainContext, roots_ref: str) -> tuple[ProofBlock, ...]:
    blocks: list[ProofBlock] = []
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
                    "-th root of unity. Its powers give the conjugate ",
                    "radical expressions.",
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
        blocks.append(par("With this notation, the certified roots are"))
    blocks.append(display_math(roots_s))
    return tuple(blocks)


def _group_ref_from_premise_or_claim(fact: FactView, ctx: ExplainContext) -> str | None:
    if len(fact.args) > 1:
        return ref(fact, 1)
    for premise_id in fact.premises:
        premise = ctx.get_fact(premise_id)
        if premise.pred == "GaloisGroup" and len(premise.args) > 1:
            return premise.ref_arg(1)
    return None


def _group_from_premise_or_claim(fact: FactView, ctx: ExplainContext) -> str:
    group_ref = _group_ref_from_premise_or_claim(fact, ctx)
    return group(ctx, group_ref) if group_ref is not None else "G"


def _group_alias_from_ref(group_ref: str | None, ctx: ExplainContext) -> str:
    if group_ref is None:
        return ""
    value = ctx.get_object(group_ref)
    for key in ("alias", "label", "value", "name", "id"):
        raw = value.get(key)
        if isinstance(raw, str) and raw:
            return raw
    return group_ref.rsplit(".", 1)[-1]


def _solvability_reason_parts(
    group_ref: str | None,
    ctx: ExplainContext,
) -> tuple[Inline | str, ...]:
    alias = _group_alias_from_ref(group_ref, ctx)
    if alias in {"C1", "C2", "C3", "C4", "C5", "C6", "V4"}:
        return ("It is abelian, hence solvable.",)
    if alias in {"S3", "D4", "D5", "D6"}:
        return (
            "It is dihedral, or the cubic group ",
            math(r"S_3"),
            ", with a cyclic rotation subgroup and abelian quotient; ",
            "hence it is solvable.",
        )
    if alias == "A4":
        return (
            "It has the solvable tower ",
            math(r"1 \triangleleft V_4 \triangleleft A_4"),
            ", with abelian quotients.",
        )
    if alias == "S4":
        return (
            "It has the solvable tower ",
            math(r"1 \triangleleft V_4 \triangleleft A_4 \triangleleft S_4"),
            ", with abelian quotients.",
        )
    if alias == "F20":
        return (
            "It has the solvable tower ",
            math(r"C_5 \triangleleft F_{20}"),
            ", with quotient ",
            math(r"C_4"),
            ".",
        )
    return ("This group is solvable.",)


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