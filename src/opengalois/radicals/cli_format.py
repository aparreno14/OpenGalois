"""Scheme-aware CLI formatting helpers for radical roots."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction

from .ast import Expr, ExprLike, add, mul, qq, qq_fraction, sub, zeta
from .canon import canon
from .codec import decode_expr_list_payloads
from .render import AliasBinding, RenderStyle, render_text
from .schemes import deg5_mcclintock_depressed_monic as mcclintock_scheme

__all__ = ["CliRadicalLines", "format_cli_radical_lines"]


@dataclass(frozen=True)
class CliRadicalLines:
    """Rendered alias and root lines for the CLI."""

    aliases: list[tuple[str, str]]
    roots: list[str]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class _CliRadicalLayout:
    """Internal alias-aware layout before rendering to text."""

    aliases: list[tuple[str, Expr]]
    roots: list[Expr]


def format_cli_radical_lines(
    certificate: Mapping[str, object],
    radical_fact: Mapping[str, object],
    exprs: Sequence[ExprLike],
    *,
    style: RenderStyle = "unicode",
) -> CliRadicalLines:
    """Format a certified radical-root block for the CLI.

    Args:
        certificate: Full certificate mapping.
        radical_fact: The concrete ``RadicalRoots`` fact to format.
        exprs: Decoded radical-root expressions in certified order.
        style: Rendering style.

    Returns:
        Alias lines and root lines ready for CLI wrapping.
    """
    layout = _build_layout(certificate, radical_fact, exprs)
    return _render_layout(layout, style=style)


def _build_layout(
    certificate: Mapping[str, object],
    radical_fact: Mapping[str, object],
    exprs: Sequence[ExprLike],
) -> _CliRadicalLayout:
    """Build an alias-aware layout for a ``RadicalRoots`` fact."""
    rule_id = radical_fact.get("rule")
    if not isinstance(rule_id, str):
        return _fallback_layout(exprs)

    if rule_id == "radical_roots.QQ.lift.depressed_monic@1":
        lifted = _build_lift_layout(certificate, radical_fact)
        if lifted is not None:
            return lifted
        return _fallback_layout(exprs)

    if rule_id in {
        "radical_roots.QQ.deg3.cardano.depressed_monic@1",
        "radical_roots.QQ.deg3.cardano.depressed_monic@2",
    }:
        cardano = _build_cardano_layout(exprs, rule_id=rule_id)
        if cardano is not None:
            return cardano
        return _fallback_layout(exprs)

    if rule_id == "radical_roots.QQ.deg4.ferrari.depressed_monic@2":
        ferrari = _build_ferrari_layout(exprs)
        if ferrari is not None:
            return ferrari
        return _fallback_layout(exprs)

    if rule_id == "radical_roots.QQ.deg5.mcclintock.depressed_monic@1":
        mcclintock = _build_mcclintock_layout(certificate, radical_fact, exprs)
        if mcclintock is not None:
            return mcclintock
        return _fallback_layout(exprs)

    return _fallback_layout(exprs)


def _render_layout(layout: _CliRadicalLayout, *, style: RenderStyle) -> CliRadicalLines:
    """Render a layout with progressive alias visibility."""
    canonical_aliases = [(name, canon(expr)) for name, expr in layout.aliases]
    canonical_roots = [canon(expr) for expr in layout.roots]
    pruned_aliases = _prune_unused_aliases(canonical_aliases, canonical_roots)

    rendered_aliases: list[tuple[str, str]] = []
    active_aliases: list[AliasBinding] = []

    for name, expr in pruned_aliases:
        rendered = render_text(expr, style=style, aliases=active_aliases)
        rendered_aliases.append((name, rendered))
        active_aliases.append((name, expr))

    zeta_aliases = _render_zeta_aliases(
        [expr for _, expr in pruned_aliases] + canonical_roots,
        style=style,
    )

    rendered_roots = [
        render_text(expr, style=style, aliases=pruned_aliases) for expr in canonical_roots
    ]
    return CliRadicalLines(
        aliases=[*zeta_aliases, *rendered_aliases],
        roots=rendered_roots,
    )


def _fallback_layout(exprs: Sequence[ExprLike]) -> _CliRadicalLayout:
    """Return the plain layout with no aliases."""
    return _CliRadicalLayout(aliases=[], roots=[dict(expr) for expr in exprs])


def _prune_unused_aliases(
    aliases: Sequence[tuple[str, Expr]],
    roots: Sequence[Expr],
) -> list[tuple[str, Expr]]:
    """Drop aliases that are not used by roots or by later surviving aliases."""
    kept_reversed: list[tuple[str, Expr]] = []
    live_exprs: list[Expr] = list(roots)

    for name, expr in reversed(aliases):
        if any(_contains_subexpr(live, expr) for live in live_exprs):
            kept_reversed.append((name, expr))
            live_exprs.append(expr)

    kept_reversed.reverse()
    return kept_reversed


def _build_cardano_layout(
    exprs: Sequence[ExprLike],
    *,
    rule_id: str,
) -> _CliRadicalLayout | None:
    """Build aliasing for the canonical Cardano schemes."""
    if len(exprs) != 3:
        return None

    if rule_id == "radical_roots.QQ.deg3.cardano.depressed_monic@1":
        first = dict(exprs[0])
        if first.get("kind") != "add":
            return None

        u = _expect_expr(first, "left")
        v = _expect_expr(first, "right")
        expected = [
            add(u, v),
            add(mul(zeta(3, 1), u), mul(zeta(3, 2), v)),
            add(mul(zeta(3, 2), u), mul(zeta(3, 1), v)),
        ]
        if not _expr_lists_equal(exprs, expected):
            return None

        return _CliRadicalLayout(
            aliases=[("u", u), ("v", v)],
            roots=[dict(expr) for expr in exprs],
        )

    # Cardano @2 has two canonical branches.
    # If p = 0, the scheme uses w = cbrt(-q) directly.
    w = dict(exprs[0])
    expected_p_zero = [
        w,
        mul(zeta(3, 1), w),
        mul(zeta(3, 2), w),
    ]
    if _expr_lists_equal(exprs, expected_p_zero):
        return _CliRadicalLayout(
            aliases=[("w", w)],
            roots=[dict(expr) for expr in exprs],
        )

    first = dict(exprs[0])
    if first.get("kind") != "add":
        return None

    u = _expect_expr(first, "left")
    alpha_over_u = _expect_expr(first, "right")
    expected = [
        add(u, alpha_over_u),
        add(mul(zeta(3, 1), u), mul(zeta(3, 2), alpha_over_u)),
        add(mul(zeta(3, 2), u), mul(zeta(3, 1), alpha_over_u)),
    ]
    if not _expr_lists_equal(exprs, expected):
        return None

    display_roots = _cardano_v2_display_roots(u, alpha_over_u)

    return _CliRadicalLayout(
        aliases=[("u", u)],
        roots=display_roots if display_roots is not None else [dict(expr) for expr in exprs],
    )


def _cardano_v2_display_roots(u: ExprLike, alpha_over_u: ExprLike) -> list[Expr] | None:
    """Return a sign-clean display form for Cardano v2."""
    split = _split_rational_divisor(alpha_over_u, denominator=u)
    if split is None:
        return None

    sign, positive_alpha_over_u = split
    term2 = mul(zeta(3, 2), positive_alpha_over_u)
    term3 = mul(zeta(3, 1), positive_alpha_over_u)

    if sign < 0:
        return [
            sub(u, positive_alpha_over_u),
            sub(mul(zeta(3, 1), u), term2),
            sub(mul(zeta(3, 2), u), term3),
        ]

    return [
        add(u, positive_alpha_over_u),
        add(mul(zeta(3, 1), u), term2),
        add(mul(zeta(3, 2), u), term3),
    ]


def _split_rational_divisor(
    expr: ExprLike,
    *,
    denominator: ExprLike,
) -> tuple[int, Expr] | None:
    """Split ``q / denominator`` into its sign and positive quotient."""
    if expr.get("kind") != "div":
        return None
    right = _expect_expr(expr, "right")
    if canon(right) != canon(denominator):
        return None

    left = _expect_expr(expr, "left")
    q = qq_fraction(left)
    if q is None or q == 0:
        return None

    sign = -1 if q < 0 else 1
    positive_q = -q if q < 0 else q
    if positive_q.denominator == 1:
        numerator = qq(positive_q.numerator)
        denominator_expr = dict(denominator)
    else:
        numerator = qq(positive_q.numerator)
        denominator_expr = mul(qq(positive_q.denominator), dict(denominator))

    return sign, {"kind": "div", "left": numerator, "right": denominator_expr}


def _render_zeta_aliases(
    exprs: Sequence[ExprLike],
    *,
    style: RenderStyle,
) -> list[tuple[str, str]]:
    """Render explanatory alias lines for primitive roots of unity."""
    return [
        (
            render_text(zeta(order, 1), style=style),
            f"primitive {_ordinal(order)} root of unity",
        )
        for order in _collect_zeta_orders(exprs)
    ]


def _collect_zeta_orders(exprs: Sequence[ExprLike]) -> tuple[int, ...]:
    """Return all root-of-unity orders appearing in the expressions."""
    orders: set[int] = set()
    for expr in exprs:
        _collect_zeta_orders_from_expr(dict(expr), orders)
    return tuple(sorted(orders))


def _collect_zeta_orders_from_expr(expr: ExprLike, orders: set[int]) -> None:
    """Collect root-of-unity orders from a single expression."""
    kind = expr.get("kind")
    if kind == "zeta":
        orders.add(_expect_int(expr, "n"))
        return
    if kind == "neg":
        _collect_zeta_orders_from_expr(_expect_expr(expr, "arg"), orders)
        return
    if kind in {"add", "sub", "mul", "div"}:
        _collect_zeta_orders_from_expr(_expect_expr(expr, "left"), orders)
        _collect_zeta_orders_from_expr(_expect_expr(expr, "right"), orders)
        return
    if kind == "pow_int":
        _collect_zeta_orders_from_expr(_expect_expr(expr, "base"), orders)
        return
    if kind == "root":
        _collect_zeta_orders_from_expr(_expect_expr(expr, "arg"), orders)


def _ordinal(value: int) -> str:
    """Return a compact English ordinal such as ``3rd`` or ``5th``."""
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


def _build_ferrari_layout(exprs: Sequence[ExprLike]) -> _CliRadicalLayout | None:
    """Build aliasing for the simplified Ferrari quartic scheme."""
    if len(exprs) != 4:
        return None

    extracted = _extract_ferrari_s(exprs)
    if extracted is None:
        return None

    return _CliRadicalLayout(
        aliases=[("s", extracted)],
        roots=[dict(expr) for expr in exprs],
    )


def _extract_ferrari_s(exprs: Sequence[ExprLike]) -> Expr | None:
    """Extract the Ferrari resolvent root ``s`` from the general branch."""
    first = dict(exprs[0])
    second = dict(exprs[1])
    third = dict(exprs[2])
    fourth = dict(exprs[3])

    if first.get("kind") != "div" or second.get("kind") != "div":
        return None
    if third.get("kind") != "div" or fourth.get("kind") != "div":
        return None

    if _rendered_two(_expect_expr(first, "right")) is False:
        return None
    if _rendered_two(_expect_expr(second, "right")) is False:
        return None
    if _rendered_two(_expect_expr(third, "right")) is False:
        return None
    if _rendered_two(_expect_expr(fourth, "right")) is False:
        return None

    num1 = _expect_expr(first, "left")
    num2 = _expect_expr(second, "left")
    num3 = _expect_expr(third, "left")
    num4 = _expect_expr(fourth, "left")

    if num1.get("kind") != "add" or num2.get("kind") != "sub":
        return None
    if num3.get("kind") != "add" or num4.get("kind") != "sub":
        return None

    u = _expect_expr(num1, "left")
    sqrt_delta1 = _expect_expr(num1, "right")
    if _expect_expr(num2, "left") != u or _expect_expr(num2, "right") != sqrt_delta1:
        return None

    neg_u = _expect_expr(num3, "left")
    sqrt_delta2 = _expect_expr(num3, "right")
    if _expect_expr(num4, "left") != neg_u or _expect_expr(num4, "right") != sqrt_delta2:
        return None

    if neg_u.get("kind") != "neg":
        return None
    if _expect_expr(neg_u, "arg") != u:
        return None

    if u.get("kind") != "root" or _expect_int(u, "n") != 2:
        return None
    u_arg = _expect_expr(u, "arg")
    if u_arg.get("kind") != "neg":
        return None

    return _expect_expr(u_arg, "arg")


def _build_lift_layout(
    certificate: Mapping[str, object],
    radical_fact: Mapping[str, object],
) -> _CliRadicalLayout | None:
    """Build aliasing for the depressed-monic lift rule."""
    facts = _fact_index(certificate)
    norm_fact: Mapping[str, object] | None = None
    base_fact: Mapping[str, object] | None = None

    for premise_id in _premise_ids(radical_fact):
        premise_fact = facts.get(premise_id)
        if premise_fact is None:
            continue
        pred = _claim_pred(premise_fact)
        if pred == "DepressedMonicEq":
            norm_fact = premise_fact
        elif pred == "RadicalRoots":
            base_fact = premise_fact

    if norm_fact is None or base_fact is None:
        return None

    base_exprs = _decode_fact_roots(certificate, base_fact)
    if base_exprs is None:
        return None

    base_layout = _build_layout(certificate, base_fact, base_exprs)
    shift = _extract_normalization_shift(norm_fact)
    if shift is None:
        return None

    shifted_roots = [sub(expr, qq(shift)) for expr in base_layout.roots]
    return _CliRadicalLayout(aliases=base_layout.aliases, roots=shifted_roots)


def _build_mcclintock_layout(
    certificate: Mapping[str, object],
    radical_fact: Mapping[str, object],
    exprs: Sequence[ExprLike],
) -> _CliRadicalLayout | None:
    """Build minimal aliasing for the McClintock quintic scheme."""
    coeffs = _resolve_claim_poly_coeffs(certificate, radical_fact)
    theta = _extract_mcclintock_theta(certificate, radical_fact)
    if coeffs is None or theta is None:
        return None

    try:
        quintic = mcclintock_scheme.DepressedQuintic.from_desc_coeffs(coeffs)
        invariants = mcclintock_scheme.compute_invariants(quintic, theta)
        branch = mcclintock_scheme.classify_branch(quintic, invariants)
    except (TypeError, ValueError, ZeroDivisionError):
        return None

    try:
        case = _build_mcclintock_case(quintic, invariants, branch.tag)
    except (TypeError, ValueError, ZeroDivisionError):
        return None

    case_roots = getattr(case, "roots", None)
    if not isinstance(case_roots, list):
        return None
    if not _expr_lists_equal(exprs, case_roots):
        return None

    return _CliRadicalLayout(
        aliases=_mcclintock_aliases(case),
        roots=[dict(expr) for expr in exprs],
    )


def _build_mcclintock_case(
    quintic: mcclintock_scheme.DepressedQuintic,
    invariants: mcclintock_scheme.QuinticInvariants,
    branch_tag: str,
) -> object:
    """Recompute the concrete McClintock branch result."""
    if branch_tag == "general":
        lam = invariants.lambda_if_s_nonzero
        if lam is None:
            raise ValueError("Missing lambda in general branch.")
        r1_sq_s = mcclintock_scheme.general_r1_sq(quintic, invariants.s2, lam)
        if mcclintock_scheme.zero_test_affine_in_s(r1_sq_s, invariants.s2):
            return mcclintock_scheme.build_general_r1_zero_case(quintic, invariants)
        return mcclintock_scheme.build_general_case(quintic, invariants)

    if branch_tag == "s2_eq_c2":
        return mcclintock_scheme.build_s_eq_c_case(quintic, invariants)

    if branch_tag == "s_eq_0_ct_ne_0":
        t2 = invariants.t2_if_s0
        if t2 is None:
            raise ValueError("Missing T^2 in S = 0 branch.")
        r1_sq_t = mcclintock_scheme.s0_r1_sq(quintic, t2)
        if mcclintock_scheme.zero_test_affine_in_t(r1_sq_t, t2):
            return mcclintock_scheme.build_s_eq_0_r1_zero_case(quintic, invariants)
        return mcclintock_scheme.build_s_eq_0_r1_nonzero_case(quintic, invariants)

    if branch_tag == "s_eq_t_eq_0":
        return mcclintock_scheme.build_s_eq_t_eq_0_case(quintic, invariants)

    if branch_tag == "s_eq_c_eq_0":
        return mcclintock_scheme.build_s_eq_c_eq_0_case(quintic, invariants)

    raise ValueError(f"Unsupported McClintock branch: {branch_tag!r}")


def _mcclintock_aliases(case: object) -> list[tuple[str, Expr]]:
    """Return the minimal alias list chosen for a McClintock branch."""
    aliases: list[tuple[str, Expr]] = []

    def add_alias(name: str, expr: Expr) -> None:
        if qq_fraction(expr) is None:
            aliases.append((name, expr))

    if isinstance(case, mcclintock_scheme.GeneralCaseAST):
        add_alias("S", case.S)
        add_alias("T", case.T)
        add_alias("R1", case.R1)
        add_alias("u1", case.u1)
        add_alias("u2", case.u2)
        add_alias("u3", case.u3)
        add_alias("u4", case.u4)
        return aliases

    if isinstance(case, mcclintock_scheme.GeneralR1ZeroR2NonzeroCaseAST):
        add_alias("S", case.S)
        add_alias("T", case.T)
        add_alias("R2", case.R)
        add_alias("u1", case.u1)
        add_alias("u2", case.u2)
        add_alias("u3", case.u3)
        add_alias("u4", case.u4)
        return aliases

    if isinstance(case, mcclintock_scheme.GeneralR1ZeroR2ZeroCaseAST):
        add_alias("S", case.S)
        add_alias("T", case.T)
        add_alias("u1", case.u1)
        add_alias("u2", case.u2)
        add_alias("u3", case.u3)
        add_alias("u4", case.u4)
        return aliases

    if isinstance(case, mcclintock_scheme.SZeroR1NonzeroCaseAST):
        add_alias("T", case.T)
        add_alias("R1", case.R1)
        add_alias("u1", case.u1)
        add_alias("u2", case.u2)
        add_alias("u3", case.u3)
        add_alias("u4", case.u4)
        return aliases

    if isinstance(case, mcclintock_scheme.SZeroR1ZeroR2NonzeroCaseAST):
        add_alias("T", case.T)
        add_alias("R2", case.R2)
        add_alias("u1", case.u1)
        add_alias("u2", case.u2)
        add_alias("u3", case.u3)
        add_alias("u4", case.u4)
        return aliases

    if isinstance(case, mcclintock_scheme.SZeroR1ZeroR2ZeroCaseAST):
        add_alias("T", case.T)
        add_alias("u1", case.u1)
        add_alias("u2", case.u2)
        add_alias("u3", case.u3)
        add_alias("u4", case.u4)
        return aliases

    if isinstance(case, mcclintock_scheme.SEqualCGenericCaseAST):
        add_alias("u1", case.u1)
        add_alias("u2", case.u2)
        add_alias("u3", case.u3)
        return aliases

    if isinstance(case, mcclintock_scheme.SEqualTZeroCaseAST):
        add_alias("u1", case.u1)
        add_alias("u2", case.u2)
        add_alias("u3", case.u3)
        add_alias("u4", case.u4)
        return aliases

    if isinstance(case, mcclintock_scheme.SEqualCZeroTrivialCaseAST):
        add_alias("u1", case.u1)
        return aliases

    if isinstance(case, mcclintock_scheme.SEqualCZeroNontrivialCaseAST):
        add_alias("u1", case.u1)
        add_alias("u3", case.u3)
        return aliases

    return aliases


def _extract_mcclintock_theta(
    certificate: Mapping[str, object],
    radical_fact: Mapping[str, object],
) -> Fraction | None:
    """Extract the rational resolvent root used by the McClintock rule."""
    facts = _fact_index(certificate)
    objects = _object_index(certificate)

    factorization_fact: Mapping[str, object] | None = None
    for premise_id in _premise_ids(radical_fact):
        premise_fact = facts.get(premise_id)
        if premise_fact is not None and _claim_pred(premise_fact) == "FactorizationMonicQQ":
            factorization_fact = premise_fact
            break

    if factorization_fact is None:
        return None

    args = _claim_args(factorization_fact)
    if len(args) != 3:
        return None

    factors_ref = _extract_ref_arg(args[1])
    if factors_ref is None:
        return None

    factors_obj = objects.get(factors_ref)
    if not isinstance(factors_obj, Mapping) or factors_obj.get("kind") != "PolyQQList":
        return None

    items = factors_obj.get("items")
    if not isinstance(items, list):
        return None

    for item in items:
        if not isinstance(item, str):
            continue
        poly_obj = objects.get(item)
        coeffs = _poly_coeffs_from_object(poly_obj)
        if coeffs is None or len(coeffs) != 2 or coeffs[0] != "1":
            continue
        try:
            return -Fraction(coeffs[1])
        except (ValueError, ZeroDivisionError):
            return None

    return None


def _resolve_claim_poly_coeffs(
    certificate: Mapping[str, object],
    radical_fact: Mapping[str, object],
) -> list[str] | None:
    """Resolve the polynomial coefficients of the formatted ``RadicalRoots`` fact."""
    args = _claim_args(radical_fact)
    if not args:
        return None

    poly_ref = _extract_ref_arg(args[0])
    if poly_ref is None:
        return None

    if poly_ref == "$input":
        input_obj = certificate.get("input")
        if isinstance(input_obj, Mapping):
            coeffs = input_obj.get("coeffs_qq")
            if isinstance(coeffs, list) and all(isinstance(x, str) for x in coeffs):
                return list(coeffs)
        return None

    objects = _object_index(certificate)
    return _poly_coeffs_from_object(objects.get(poly_ref))


def _decode_fact_roots(
    certificate: Mapping[str, object],
    radical_fact: Mapping[str, object],
) -> list[Expr] | None:
    """Decode the radical-root list referenced by a fact."""
    args = _claim_args(radical_fact)
    if len(args) != 2:
        return None

    roots_ref = _extract_ref_arg(args[1])
    if roots_ref is None:
        return None

    objects = _object_index(certificate)
    list_payload = objects.get(roots_ref)
    if not isinstance(list_payload, Mapping):
        return None

    try:
        return decode_expr_list_payloads(list_payload, objects)
    except (KeyError, TypeError, ValueError):
        return None


def _fact_index(certificate: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    """Return a mapping from fact ids to fact payloads."""
    proof_obj = certificate.get("proof")
    if not isinstance(proof_obj, Mapping):
        return {}

    facts_obj = proof_obj.get("facts")
    if not isinstance(facts_obj, list):
        return {}

    out: dict[str, Mapping[str, object]] = {}
    for fact in facts_obj:
        if not isinstance(fact, Mapping):
            continue
        fact_id = fact.get("id")
        if isinstance(fact_id, str):
            out[fact_id] = fact
    return out


def _object_index(certificate: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    """Return a mapping from object ids to object payloads."""
    objects_obj = certificate.get("objects")
    if not isinstance(objects_obj, Mapping):
        return {}

    out: dict[str, Mapping[str, object]] = {}
    for key, value in objects_obj.items():
        if isinstance(key, str) and isinstance(value, Mapping):
            out[key] = value
    return out


def _extract_normalization_shift(norm_fact: Mapping[str, object]) -> Fraction | None:
    """Extract the rational Tschirnhaus shift from normalization evidence."""
    evidence = norm_fact.get("evidence")
    if not isinstance(evidence, Mapping):
        return None

    shift_obj = evidence.get("tschirnhaus_shift")
    if not isinstance(shift_obj, str):
        return None

    try:
        return Fraction(shift_obj)
    except (ValueError, ZeroDivisionError):
        return None


def _claim_pred(fact: Mapping[str, object]) -> str | None:
    """Return the predicate name of a fact claim."""
    claim = fact.get("claim")
    if not isinstance(claim, Mapping):
        return None

    pred = claim.get("pred")
    return pred if isinstance(pred, str) else None


def _claim_args(fact: Mapping[str, object]) -> list[object]:
    """Return the raw claim arguments of a fact."""
    claim = fact.get("claim")
    if not isinstance(claim, Mapping):
        return []

    args = claim.get("args")
    if not isinstance(args, list):
        return []
    return args


def _premise_ids(fact: Mapping[str, object]) -> list[str]:
    """Return the premise ids of a fact."""
    premises = fact.get("premises")
    if not isinstance(premises, list):
        return []
    return [premise for premise in premises if isinstance(premise, str)]


def _extract_ref_arg(arg: object) -> str | None:
    """Extract a claim argument of the form ``{"ref": ...}``."""
    if not isinstance(arg, Mapping):
        return None

    ref = arg.get("ref")
    if not isinstance(ref, str) or not ref:
        return None
    return ref


def _poly_coeffs_from_object(obj: object) -> list[str] | None:
    """Extract ``coeffs_qq`` from a ``PolyQQ`` object."""
    if not isinstance(obj, Mapping) or obj.get("kind") != "PolyQQ":
        return None

    coeffs = obj.get("coeffs_qq")
    if not isinstance(coeffs, list) or not all(isinstance(x, str) for x in coeffs):
        return None
    return list(coeffs)


def _expr_lists_equal(left: Sequence[ExprLike], right: Sequence[ExprLike]) -> bool:
    """Return whether two expression lists are structurally equal."""
    if len(left) != len(right):
        return False
    return all(lhs == rhs for lhs, rhs in zip(left, right, strict=False))


def _contains_subexpr(haystack: ExprLike, needle: ExprLike) -> bool:
    """Return whether ``needle`` occurs as an exact subtree of ``haystack``."""
    if haystack == needle:
        return True

    kind = haystack.get("kind")
    if not isinstance(kind, str):
        return False

    if kind == "neg":
        return _contains_subexpr(_expect_expr(haystack, "arg"), needle)

    if kind in {"add", "sub", "mul", "div"}:
        return _contains_subexpr(_expect_expr(haystack, "left"), needle) or _contains_subexpr(
            _expect_expr(haystack, "right"), needle
        )

    if kind == "pow_int":
        return _contains_subexpr(_expect_expr(haystack, "base"), needle)

    if kind == "root":
        return _contains_subexpr(_expect_expr(haystack, "arg"), needle)

    return False


def _rendered_two(expr: ExprLike) -> bool:
    """Return whether an expression is the literal rational ``2``."""
    value = qq_fraction(expr)
    return value == 2 if value is not None else False


def _expect_expr(expr: ExprLike, key: str) -> Expr:
    """Extract a child expression from a node."""
    value = expr.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a RadicalExpr mapping")
    return dict(value)


def _expect_int(expr: ExprLike, key: str) -> int:
    """Extract an integer field from a node."""
    value = expr.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be a non-boolean integer")
    return value



