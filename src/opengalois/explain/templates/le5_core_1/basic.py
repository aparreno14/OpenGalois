# ruff: noqa: D102,D103
"""Basic le5-core narrative templates.

The prose is intentionally conservative. The user can later replace these
sentences without touching the proof-construction and renderer code.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ...context import ExplainContext, FactView
from ...math_render import equation_poly, factorization_latex, is_resolvent_polynomial, object_latex
from ...proof_model import Paragraph, math, par
from ..registry import rule_template
from ._helpers import obj, poly, ref


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


def _modular_factor_latex(coeffs_desc: Sequence[str], *, variable: str = "x") -> str:
    coeffs = [int(c) for c in coeffs_desc]
    degree = len(coeffs) - 1
    terms: list[str] = []
    for i, coeff in enumerate(coeffs):
        if coeff == 0:
            continue
        exp = degree - i
        if exp == 0:
            monomial = str(coeff)
        elif exp == 1:
            monomial = variable if coeff == 1 else rf"{coeff}{variable}"
        else:
            monomial = rf"{variable}^{exp}" if coeff == 1 else rf"{coeff}{variable}^{exp}"
        terms.append(monomial)
    return " + ".join(terms) if terms else "0"


def _zassenhaus_evidence_parts(fact: FactView) -> tuple[str, str, list[str]]:
    evidence = fact.raw.get("evidence")
    p = "p"
    ell = r"\ell"
    factors_latex: list[str] = []

    if not isinstance(evidence, Mapping):
        return p, ell, factors_latex

    raw_p = evidence.get("prime")
    raw_ell = evidence.get("ell")
    if isinstance(raw_p, str) and raw_p:
        p = raw_p
    if isinstance(raw_ell, int):
        ell = str(raw_ell)

    mod_fac = evidence.get("mod_p_factorization")
    if not isinstance(mod_fac, Mapping):
        return p, ell, factors_latex

    raw_factors = mod_fac.get("factors_desc")
    if not isinstance(raw_factors, list):
        return p, ell, factors_latex

    for factor in raw_factors:
        if not isinstance(factor, list) or not factor or not all(isinstance(c, 
                                                                            str) for c in factor):
            continue
        factors_latex.append(_modular_factor_latex(factor))

    return p, ell, factors_latex


@rule_template("degree.QQ@1")
def explain_degree(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    f_ref = ref(fact, 0)
    degree_ref = ref(fact, 1)
    return (
        par(
            "The polynomial ",
            math(poly(ctx, f_ref)),
            " has degree ",
            math(obj(ctx, degree_ref)),
            ".",
        ),
    )


@rule_template("irreducible.QQ.deg1_trivial@1")
def explain_irreducible_deg1(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    return (
        par(
            "The polynomial ",
            math(poly(ctx, ref(fact, 0))),
            " is linear, hence irreducible over ",
            math(r"\mathbb{Q}"),
            ".",
        ),
    )


@rule_template("irreducible.QQ.deg5_recompute@1")
def explain_irreducible_recompute(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    return (
        par(
            "The polynomial ",
            math(poly(ctx, ref(fact, 0))),
            " is irreducible over ",
            math(r"\mathbb{Q}"),
            ".",
        ),
    )


@rule_template("irreducible.QQ.to.depressed_monic@1")
def explain_irreducible_depressed_transfer(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[Paragraph, ...]:
    return (
        par("Irreducibility is preserved by the certified affine normalization."),
        par(
            "Therefore ",
            math(poly(ctx, ref(fact, 0))),
            " is irreducible over ",
            math(r"\mathbb{Q}"),
            ".",
        ),
    )


@rule_template("normalize.depressed_monic_QQ@1")
def explain_depressed_monic(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    f_ref = ref(fact, 0)
    g_ref = ref(fact, 1)

    if _same_poly(ctx, f_ref, g_ref):
        return (
            par(
                "The polynomial ",
                math(poly(ctx, f_ref)),
                " is already monic and depressed, so the normalization step is ",
                "the identity.",
            ),
        )

    return (
        par(
            "The certified depressed-monic normalization of ",
            math(poly(ctx, f_ref)),
            " is ",
            math(object_latex(ctx, g_ref, symbolic_input=False)),
            ".",
        ),
    )


@rule_template("factorization.QQ.monic@1")
def explain_factorization(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    poly_ref = ref(fact, 0)
    variable = "y" if is_resolvent_polynomial(ctx, poly_ref) else "x"
    return (
        par(
            "Over ",
            math(r"\mathbb{Q}"),
            ", the certified monic factorization is ",
            math(factorization_latex(ctx, fact.args, variable=variable)),
            ".",
        ),
    )


@rule_template("resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1")
def explain_resolvent_deg4_a(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    return _explain_resolvent_deg4(fact, ctx)


@rule_template("resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1")
def explain_resolvent_deg4_b(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    return _explain_resolvent_deg4(fact, ctx)


def _explain_resolvent_deg4(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    r_ref = ref(fact, 0)
    f_ref = ref(fact, 1)
    return (
        par(
            "The associated cubic resolvent of ",
            math(poly(ctx, f_ref)),
            " is ",
            math(equation_poly(ctx, r_ref, name="R", variable="y")),
            ".",
        ),
    )


@rule_template("resolvent.QQ.compute.deg5.sextic_dummit_F20@1")
def explain_resolvent_deg5_dummit(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[Paragraph, ...]:
    r_ref = ref(fact, 0)
    f_ref = ref(fact, 1)
    return (
        par(
            "The associated Dummit sextic resolvent of ",
            math(poly(ctx, f_ref)),
            " is ",
            math(equation_poly(ctx, r_ref, name="R", variable="y")),
            ".",
        ),
        par(
            "This resolvent is built from an auxiliary expression whose ",
            "stabilizer in ",
            math("S_5"),
            " is the Frobenius group ",
            math("F_{20}"),
            ". Thus rational roots of the resolvent detect containment in ",
            "a conjugate of ",
            math("F_{20}"),
            ".",
        ),
    )


@rule_template("irreducible.QQ.dummit_resolvent@1")
def explain_irreducible_dummit_resolvent(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[Paragraph, ...]:
    r_ref = ref(fact, 0)
    return (
        par(
            "The Dummit resolvent ",
            math(poly(ctx, r_ref)),
            " has no rational root. In the certified degree-five setting, ",
            "this is recorded as irreducibility of the resolvent.",
        ),
    )

@rule_template("irreducible.QQ.zassenhaus_trace@1")
def explain_irreducible_zassenhaus_trace(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[Paragraph, ...]:
    f_s = poly(ctx, ref(fact, 0))
    p, ell, factors_latex = _zassenhaus_evidence_parts(fact)

    if factors_latex:
        factorization_s = r" \cdot ".join(rf"({factor})" for factor in factors_latex)
    else:
        factorization_s = r"\prod_i g_i"

    if len(factors_latex) == 1:
        return (
            par(
                "To prove irreducibility, we first replace ",
                math(f_s),
                " by its primitive integer part ",
                math(r"F\in\mathbb{Z}[x]"),
                ". By Gauss' lemma, it is sufficient to check whether ",
                math("F"),
                " is irreducible over ",
                math(r"\mathbb{Z}[x]"),
                ".",
            ),
            par(
                "The chosen prime is ",
                math(rf"p={p}"),
                ", so that the reduction ",
                math(r"F \bmod p"),
                " is squarefree and has the same degree. The modular ",
                "factorization in ",
                math(rf"\mathbb{{F}}_{{{p}}}[x]"),
                " into irreducible factors is ",
                math(factors_latex[0]),
                ".",
            ),
            par(
                "Since the modular factorization has a single factor of the same ",
                "degree, ",
                math(r"F\bmod p"),
                " is irreducible in ",
                math(rf"\mathbb{{F}}_{{{p}}}[x]"),
                ". Therefore ",
                math("F"),
                " is irreducible in ",
                math(r"\mathbb{Z}[x]"),
                ", and hence ",
                math(f_s),
                " is irreducible in ",
                math(r"\mathbb{Q}[x]"),
                ".",
            ),
        )

    return (
        par(
            "To prove irreducibility, we first replace ",
            math(f_s),
            " by its primitive integer part ",
            math(r"F\in\mathbb{Z}[x]"),
            ". By Gauss' lemma, it is sufficient to check whether ",
            math("F"),
            " is irreducible over ",
            math(r"\mathbb{Z}[x]"),
            ".",
        ),
        par(
            "The chosen prime is ",
            math(rf"p={p}"),
            ", so that the reduction ",
            math(r"F \bmod p"),
            " is squarefree and has the same degree. The modular factorization in ",
            math(rf"\mathbb{{F}}_{{{p}}}[x]"),
            " into irreducible factors is ",
            math(rf"{factorization_s}"),
            ".",
        ),
        par(
            "The candidates for irreducible factors of ",
            math("F"),
            " are obtained from factor combinations: products of these modular ",
            "factors lifted to a sufficiently large prime power.",
        ),
        par(
            "Here ",
            math(rf"\ell={ell}"),
            ", so the recombination is tested modulo the prime power ",
            math(rf"{p}^{{{ell}}}"),
            ".",
        ),
        par(
            "We test all factor combinations of degree at most ",
            math(r"\lfloor \deg(F)/2 \rfloor"),
            ". For each one, we perform the required Hensel lifting and then ",
            "check exact divisibility in ",
            math(r"\mathbb{Z}[x]"),
            ". None gives a proper divisor of ",
            math("F"),
            ".",
        ),
        par(
            "Therefore ",
            math("F"),
            " is irreducible in ",
            math(r"\mathbb{Z}[x]"),
            ", and hence ",
            math(f_s),
            " is irreducible in ",
            math(r"\mathbb{Q}[x]"),
            ".",
        ),
    )
