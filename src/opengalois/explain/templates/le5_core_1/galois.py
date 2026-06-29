# ruff: noqa: D102,D103
"""Galois-group narrative templates for the clean renderer.

These templates deliberately keep the proof style close to the rule notes:
classification first, then the discriminant, then the relevant resolvent or
field-theoretic distinction.  The prose is mathematical, but it avoids turning
an explanation into a checklist of verifier operations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction

from ...context import ExplainContext, FactView
from ...math_render import rational_latex
from ...proof_model import Inline, ProofBlock, display_math, math, par
from ..registry import rule_template
from ._helpers import group, poly, ref


@rule_template("galois_group.QQ.deg1.trivial@1")
def explain_galois_deg1(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (
        par(
            "The polynomial ",
            math(f_s),
            " has degree ",
            math("1"),
            ". Its only root is rational, so its splitting field is ",
            math(r"\mathbb{Q}"),
            " itself.",
        ),
        par("Therefore the only automorphism is the identity."),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg2.C2@1")
def explain_galois_deg2_c2(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (
        par(
            "The polynomial ",
            math(f_s),
            " has degree ",
            math("2"),
            " and is irreducible over ",
            math(r"\mathbb{Q}"),
            ". Hence its roots are obtained by adjoining a square root of its ",
            "discriminant.",
        ),
        par(
            "Since the polynomial is irreducible, this square root is not already ",
            "rational, while its square is rational. Thus the splitting field has ",
            "degree ",
            math("2"),
            ", and the only group of order ",
            math("2"),
            " is ",
            math("C_2"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg3.C3@1")
def explain_galois_deg3_c3(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (
        par(
            "Since ",
            math(f_s),
            " has degree ",
            math("3"),
            " and is irreducible, its Galois group is a transitive subgroup of ",
            math("S_3"),
            ". Therefore the only possibilities are ",
            math("C_3"),
            " and ",
            math("S_3"),
            ".",
        ),
        par(
            "The discriminant is a square in ",
            math(r"\mathbb{Q}"),
            ". The square root of the discriminant is the Vandermonde product ",
            "up to sign, and odd permutations change its sign. Since this square ",
            "root is rational, every automorphism must fix it, so no odd ",
            "permutation can occur.",
        ),
        par(
            "Thus the group is contained in ",
            math("A_3"),
            ". The only transitive possibility left is ",
            math("C_3"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg3.S3@1")
def explain_galois_deg3_s3(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (
        par(
            "Since ",
            math(f_s),
            " has degree ",
            math("3"),
            " and is irreducible, its Galois group is a transitive subgroup of ",
            math("S_3"),
            ". Therefore the only possibilities are ",
            math("C_3"),
            " and ",
            math("S_3"),
            ".",
        ),
        par(
            "Here the discriminant is not a square in ",
            math(r"\mathbb{Q}"),
            ". The splitting field is obtained by adjoining one root of the ",
            "cubic and a square root of the discriminant:",
        ),
        display_math(
            r"\begin{tikzcd}[row sep=large, column sep=large]"
            "\n"
            r"& K_f=\mathbb{Q}(\alpha,\sqrt{\Delta}) "
            r"\arrow[dl, dash] \arrow[dr, dash] & \\" 
            "\n"
            "\\mathbb{Q}(\\alpha) \\arrow[dr, dash, \"3\"'] && "
            "\\mathbb{Q}(\\sqrt{\\Delta}) \\arrow[dl, dash, \"2\"] \\\\"
            "\n"
            r"& \mathbb{Q} &"
            "\n"
            r"\end{tikzcd}"
        ),
        par(
            "The quadratic part does not collapse, so the splitting field has ",
            "degree ",
            math("6"),
            ". Since the splitting field is Galois, the Galois group also has ",
            "order ",
            math("6"),
            ". Hence the group is ",
            math("S_3"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg4.S4@2")
@rule_template("galois_group.QQ.deg4.S4@1")
def explain_galois_deg4_s4(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        *_quartic_transitive_setup(fact, ctx, square_discriminant=False),
        *_quartic_resolvent_setup(),
        par(
            "In this case the cubic resolvent is irreducible over ",
            math(r"\mathbb{Q}"),
            ". Thus the Galois action on the three pairings is transitive, and ",
            "the group fixes no pairing.",
        ),
        par(
            "Consequently ",
            math("G_f"),
            " is not contained in any conjugate of ",
            math("D_4"),
            ". The non-square discriminant has already excluded the alternating ",
            "groups, so the only remaining transitive possibility is ",
            math("S_4"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg4.A4@2")
@rule_template("galois_group.QQ.deg4.A4@1")
def explain_galois_deg4_a4(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        *_quartic_transitive_setup(fact, ctx, square_discriminant=True),
        *_quartic_resolvent_setup(),
        par(
            "In this case the cubic resolvent is irreducible over ",
            math(r"\mathbb{Q}"),
            ". Thus the action on the three pairings is transitive.",
        ),
        par(
            "Inside ",
            math("A_4"),
            ", this excludes ",
            math("V_4"),
            ", which fixes all three pairings. The only remaining possibility is ",
            math("A_4"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg4.V4@3")
def explain_galois_deg4_v4_v3(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (
        par(
            "Since ",
            math(f_s),
            " has degree ",
            math("4"),
            " and is irreducible, its Galois group is a transitive subgroup of ",
            math("S_4"),
            ".",
        ),
        *_quartic_resolvent_setup(),
        par(
            "Here the cubic resolvent splits completely over ",
            math(r"\mathbb{Q}"),
            ". Hence ",
            math("G_f"),
            " fixes all three pairings.",
        ),
        display_math(
            r"G_f\subseteq "
            r"\bigcap_{i=1}^{3}\operatorname{Stab}_{S_4}(\rho_i)=V_4"
        ),
        par(
            "Since the quartic is irreducible, ",
            math("G_f"),
            " is transitive on the four roots. The transitive subgroup obtained ",
            "in this situation is therefore ",
            math("V_4"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg4.V4@2")
@rule_template("galois_group.QQ.deg4.V4@1")
def explain_galois_deg4_v4(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        *_quartic_transitive_setup(fact, ctx, square_discriminant=True),
        *_quartic_resolvent_setup(),
        par(
            "Here the cubic resolvent splits completely over ",
            math(r"\mathbb{Q}"),
            ". Hence ",
            math("G_f"),
            " fixes all three pairings.",
        ),
        display_math(
            r"G_f\subseteq "
            r"\bigcap_{i=1}^{3}\operatorname{Stab}_{S_4}(\rho_i)=V_4"
        ),
        par(
            "The square discriminant has already restricted the group to ",
            math("A_4"),
            " or ",
            math("V_4"),
            ". Fixing all three pairings excludes ",
            math("A_4"),
            ", so the group is ",
            math("V_4"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg4.C4@2")
@rule_template("galois_group.QQ.deg4.C4@1")
def explain_galois_deg4_c4(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        *_quartic_transitive_setup(fact, ctx, square_discriminant=False),
        *_quartic_reducible_resolvent_step(fact, ctx),
        *_quartic_kappe_warren_setup(fact, ctx),
        par(
            "In this certificate both ",
            math("W_1"),
            " and ",
            math("W_2"),
            " are squares in ",
            math(r"\mathbb{Q}"),
            ". Thus the two auxiliary quadratics split over the discriminant ",
            "field ",
            math(r"\mathbb{Q}(\sqrt{\Delta_f})"),
            ". This is the cyclic branch of the Kappe--Warren criterion.",
        ),
        par(
            "Therefore the remaining group is the cyclic group of order ",
            math("4"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg4.D4.w1@2")
@rule_template("galois_group.QQ.deg4.D4.w1@1")
def explain_galois_deg4_d4_w1(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return _explain_galois_deg4_d4(fact, ctx, witness="W_1")


@rule_template("galois_group.QQ.deg4.D4.w2@2")
@rule_template("galois_group.QQ.deg4.D4.w2@1")
def explain_galois_deg4_d4_w2(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return _explain_galois_deg4_d4(fact, ctx, witness="W_2")


@rule_template("galois_group.QQ.reducible.all_linear.trivial@1")
def explain_reducible_all_linear(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (
        par(
            "The polynomial ",
            math(f_s),
            " decomposes into linear factors over ",
            math(r"\mathbb{Q}"),
            ". Hence all its roots are rational.",
        ),
        par(
            "The splitting field is therefore ",
            math(r"\mathbb{Q}"),
            ", and the only automorphism is the identity.",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.reducible.single_nonlinear.inherit@1")
def explain_reducible_single_nonlinear(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (
        par(
            "The polynomial ",
            math(f_s),
            " decomposes into linear factors except for one non-linear ",
            "irreducible factor.",
        ),
        par(
            "Linear factors already split over ",
            math(r"\mathbb{Q}"),
            ". Therefore the splitting field of ",
            math(f_s),
            " is the same as the splitting field of that unique non-linear ",
            "factor. Hence the Galois group is inherited from it.",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.reducible.double_quadratic.C2@1")
def explain_reducible_double_quadratic_c2(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return (
        *_double_quadratic_setup(fact, ctx),
        par(
            "In this case the product of the two discriminants is a square in ",
            math(r"\mathbb{Q}"),
            ". Thus the two square roots are proportional. The splitting field ",
            "is generated by only one of them, so the extension has degree ",
            math("2"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.reducible.double_quadratic.V4@1")
def explain_reducible_double_quadratic_v4(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return (
        *_double_quadratic_setup(fact, ctx),
        par(
            "In this case the product of the two discriminants is not a square ",
            "in ",
            math(r"\mathbb{Q}"),
            ". Hence neither square root belongs to the quadratic field ",
            "generated by the other.",
        ),
        par(
            "The splitting field is therefore a biquadratic extension of ",
            math(r"\mathbb{Q}"),
            ", and the Galois group is ",
            math("V_4"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.reducible.quadratic_cubic.C6@1")
def explain_reducible_quadratic_cubic_c6(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return (
        *_quadratic_cubic_setup(fact, ctx),
        par(
            "The cubic factor has square discriminant, so its Galois group is ",
            math("C_3"),
            ". Hence its splitting field has degree ",
            math("3"),
            " over ",
            math(r"\mathbb{Q}"),
            ".",
        ),
        par(
            "The quadratic factor is irreducible, so its splitting field has ",
            "degree ",
            math("2"),
            ". Since ",
            math("2"),
            " and ",
            math("3"),
            " are coprime, the compositum has degree ",
            math("6"),
            ". Therefore the group is ",
            math(r"C_2\times C_3\cong C_6"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.reducible.quadratic_cubic.S3@1")
def explain_reducible_quadratic_cubic_s3_v1(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return _explain_reducible_quadratic_cubic_s3(fact, ctx)


@rule_template("galois_group.QQ.reducible.quadratic_cubic.S3@2")
def explain_reducible_quadratic_cubic_s3_v2(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return _explain_reducible_quadratic_cubic_s3(fact, ctx)


@rule_template("galois_group.QQ.reducible.quadratic_cubic.D6@1")
def explain_reducible_quadratic_cubic_d6_v1(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return _explain_reducible_quadratic_cubic_d6(fact, ctx)


@rule_template("galois_group.QQ.reducible.quadratic_cubic.D6@2")
def explain_reducible_quadratic_cubic_d6_v2(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return _explain_reducible_quadratic_cubic_d6(fact, ctx)


@rule_template("galois_group.QQ.deg5.S5@1")
def explain_galois_deg5_s5(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        *_quintic_transitive_setup(fact, ctx),
        par(
            "Since the discriminant is not a square in ",
            math(r"\mathbb{Q}"),
            ", the Galois group is not contained in ",
            math("A_5"),
            ". Therefore only ",
            math("S_5"),
            " and ",
            math("F_{20}"),
            " remain.",
        ),
        par(
            "Here the resolvent ",
            math("R"),
            " enters. Since ",
            math("R"),
            " is irreducible, the action of ",
            math("G_f"),
            " on the six roots of Dummit's resolvent is transitive. In ",
            "particular, ",
            math("G_f"),
            " fixes none of these roots.",
        ),
        par(
            "Thus ",
            math("G_f"),
            " cannot be contained in any conjugate of ",
            math("F_{20}"),
            ". The case ",
            math("F_{20}"),
            " is excluded, and the only remaining possibility is ",
            math("S_5"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg5.A5@1")
def explain_galois_deg5_a5(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        *_quintic_transitive_setup(fact, ctx),
        par(
            "Since the discriminant is a square in ",
            math(r"\mathbb{Q}"),
            ", the Galois group is contained in ",
            math("A_5"),
            ". Therefore only ",
            math("A_5"),
            ", ",
            math("D_5"),
            " and ",
            math("C_5"),
            " remain.",
        ),
        par(
            "Here the resolvent ",
            math("R"),
            " enters. Since ",
            math("R"),
            " is irreducible, the action of ",
            math("G_f"),
            " on the six roots of Dummit's resolvent is transitive. In ",
            "particular, ",
            math("G_f"),
            " fixes none of these roots.",
        ),
        par(
            "Hence ",
            math("G_f"),
            " cannot be contained in any conjugate of ",
            math("F_{20}"),
            ". Since the groups ",
            math("D_5"),
            " and ",
            math("C_5"),
            " are contained in such conjugates, both are excluded. The only ",
            "remaining possibility is ",
            math("A_5"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg5.F20@1")
def explain_galois_deg5_f20(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        *_quintic_transitive_setup(fact, ctx),
        par(
            "Since the discriminant is not a square in ",
            math(r"\mathbb{Q}"),
            ", the Galois group is not contained in ",
            math("A_5"),
            ". Therefore only ",
            math("S_5"),
            " and ",
            math("F_{20}"),
            " remain.",
        ),
        *_dummit_linear_factor_step(),
        par(
            "Consequently the group is contained in a conjugate of ",
            math("F_{20}"),
            ". Since the discriminant is not a square, the group is not ",
            "contained in ",
            math("A_5"),
            ", so the subgroups ",
            math("D_5"),
            " and ",
            math("C_5"),
            " are excluded. Thus the group is ",
            math("F_{20}"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg5.D5@1")
def explain_galois_deg5_d5(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    witness = _quintic_d5_nonsquare_witness(fact, ctx)
    witness_sentence: tuple[Inline | str, ...]
    if witness is None:
        witness_sentence = (
            "Here at least one of ",
            math(r"\Delta_{q_1}"),
            " and ",
            math(r"\Delta_{q_2}"),
            " is not a square in ",
            math(r"\mathbb{Q}"),
            ".",
        )
    else:
        witness_sentence = (
            "Here ",
            math(witness),
            " is not a square in ",
            math(r"\mathbb{Q}"),
            ".",
        )

    return (
        *_quintic_d5_c5_common(fact, ctx),
        *_quintic_dummit_quadratics_step(fact, ctx),
        par(
            "The cyclic case occurs only when both auxiliary quadratics split ",
            "over ",
            math(r"\mathbb{Q}"),
            ", equivalently when both of these discriminants are squares in ",
            math(r"\mathbb{Q}"),
            ". OpenGalois checks both quadratics, since a degenerate value in ",
            "one of them does not by itself force the cyclic case.",
        ),
        par(
            *witness_sentence,
            " Thus the cyclic case ",
            math("C_5"),
            " is excluded. The remaining possibility is ",
            math("D_5"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.deg5.C5@1")
def explain_galois_deg5_c5(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        *_quintic_d5_c5_common(fact, ctx),
        *_quintic_dummit_quadratics_step(fact, ctx),
        par(
            "The cyclic case occurs exactly when both auxiliary quadratics split ",
            "over ",
            math(r"\mathbb{Q}"),
            ", equivalently when both discriminants are squares in ",
            math(r"\mathbb{Q}"),
            ".",
        ),
        par(
            "In this certificate both ",
            math(r"\Delta_{q_1}"),
            " and ",
            math(r"\Delta_{q_2}"),
            " are squares in ",
            math(r"\mathbb{Q}"),
            ". Hence both Dummit quadratics split over ",
            math(r"\mathbb{Q}"),
            ", so the remaining group is the cyclic group ",
            math("C_5"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


@rule_template("galois_group.QQ.lift.depressed_monic@1")
def explain_galois_lift_depressed_monic(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (
        par(
            "The polynomial was first transformed into depressed monic form by ",
            "an invertible affine change of variable over ",
            math(r"\mathbb{Q}"),
            ". Such a change only rewrites the roots; it does not change the ",
            "splitting field.",
        ),
        par(
            "Therefore the Galois group of ",
            math(f_s),
            " is the same as the Galois group already obtained for its ",
            "depressed monic normalization.",
        ),
        *_conclusion(fact, ctx),
    )


def _conclusion(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    g_s = group(ctx, ref(fact, 1))
    return (
        par(
            "Consequently ",
            math(rf"\operatorname{{Gal}}({f_s}/\mathbb{{Q}}) \cong {g_s}"),
            ".",
        ),
    )


def _quartic_transitive_setup(
    fact: FactView,
    ctx: ExplainContext,
    *,
    square_discriminant: bool,
) -> tuple[ProofBlock, ...]:
    disc_sentence: tuple[Inline | str, ...]
    f_s = poly(ctx, ref(fact, 0))
    if square_discriminant:
        disc_sentence = (
            "The discriminant of ",
            math(f_s),
            " is a square in ",
            math(r"\mathbb{Q}"),
            ". Hence ",
            math(r"G_f\subseteq A_4"),
            ", and only ",
            math("A_4"),
            " and ",
            math("V_4"),
            " remain.",
        )
    else:
        disc_sentence = (
            "The discriminant of ",
            math(f_s),
            " is not a square in ",
            math(r"\mathbb{Q}"),
            ". Hence ",
            math("G_f"),
            " is not contained in the alternating group, and the alternating ",
            "possibilities ",
            math("A_4"),
            " and ",
            math("V_4"),
            " are excluded.",
        )
    return (
        par(
            "Since ",
            math(f_s),
            " has degree ",
            math("4"),
            " and is irreducible, its Galois group ",
            math("G_f"),
            " is a transitive subgroup of ",
            math("S_4"),
            ". The transitive possibilities are ",
            math("C_4"),
            ", ",
            math("V_4"),
            ", ",
            math("D_4"),
            ", ",
            math("A_4"),
            " and ",
            math("S_4"),
            ".",
        ),
        par(*disc_sentence),
    )


def _quartic_resolvent_setup() -> tuple[ProofBlock, ...]:
    return (
        par(
            "OpenGalois uses the cubic resolvent attached to the pair-sums ",
            "invariant ",
            math(r"\rho=(x_1+x_2)(x_3+x_4)"),
            ". Its three roots correspond to the three ways of pairing the four ",
            "roots of the quartic.",
        ),
        par(
            "The stabilizer in ",
            math("S_4"),
            " of one such value is isomorphic to ",
            math("D_4"),
            ". Thus this resolvent detects whether the Galois group fixes a ",
            "pairing, equivalently whether it is contained in a conjugate of ",
            math("D_4"),
            ".",
        ),
    )


def _quartic_reducible_resolvent_step(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    data = _quartic_kw_data(fact, ctx)

    if data is None:
        root_part: tuple[Inline | str, ...] = (
            "The certified factorization identifies the unique rational root of ",
            "the resolvent; denote it by ",
            math("r'"),
            ".",
        )
    else:
        root_part = (
            "The certified factorization has unique linear factor ",
            math(data["linear_factor"]),
            ", so the unique rational root of the resolvent is ",
            math(rf"r'={data['root']}"),
            ".",
        )

    return (
        *_quartic_resolvent_setup(),
        par(
            "Here the cubic resolvent is reducible. Since the discriminant has ",
            "already excluded the alternating possibilities, this is precisely ",
            "the branch where only ",
            math("C_4"),
            " and ",
            math("D_4"),
            " can remain.",
        ),
        par(*root_part),
        par(
            "This rational value is fixed by ",
            math("G_f"),
            ", so ",
            math("G_f"),
            " fixes the corresponding pairing of the four roots and is ",
            "contained in the associated conjugate of ",
            math("D_4"),
            ".",
        ),
    )


def _quartic_kappe_warren_setup(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    data = _quartic_kw_data(fact, ctx)

    if data is None:
        return (
            par(
                "It remains to distinguish the cyclic and dihedral cases. Write the ",
                "monic quartic as ",
                math(r"T^4+aT^3+bT^2+cT+d"),
                ". The unique rational root of the pair-sums resolvent is denoted ",
                "by ",
                math("r'"),
                ".",
            ),
            par(
                "With this choice of resolvent, the Kappe--Warren auxiliary ",
                "quadratics are",
            ),
            display_math(
                r"Q_1(T)=T^2+aT+r',\qquad "
                r"Q_2(T)=T^2-(b-r')T+d."
            ),
            par(
                "Their discriminants are",
            ),
            display_math(
                r"\Delta_{Q_1}=a^2-4r',\qquad "
                r"\Delta_{Q_2}=(b-r')^2-4d."
            ),
            par(
                "OpenGalois checks whether these quadratics split over ",
                math(r"\mathbb{Q}(\sqrt{\Delta_f})"),
                " through the rational square tests",
            ),
            display_math(
                r"W_1=\Delta_{Q_1}\Delta_f,\qquad "
                r"W_2=\Delta_{Q_2}\Delta_f."
            ),
        )

    return (
        par(
            "It remains to distinguish the cyclic and dihedral cases. The ",
            "monic quartic is written as ",
            math(r"T^4+aT^3+bT^2+cT+d"),
            ", and the rational root just found is ",
            math(rf"r'={data['root']}"),
            ".",
        ),
        par(
            "With this choice of resolvent, the Kappe--Warren auxiliary ",
            "quadratics become the concrete polynomials",
        ),
        display_math(
            rf"Q_1(T)=T^2+aT+r'={data['q1']},\qquad "
            rf"Q_2(T)=T^2-(b-r')T+d={data['q2']}."
        ),
        par(
            "Their discriminants are",
        ),
        display_math(
            rf"\Delta_{{Q_1}}=a^2-4r'={data['delta_q1']},\qquad "
            rf"\Delta_{{Q_2}}=(b-r')^2-4d={data['delta_q2']}."
        ),
        par(
            "The Kappe--Warren criterion asks whether these quadratic data split ",
            "over the discriminant field ",
            math(r"\mathbb{Q}(\sqrt{\Delta_f})"),
            ". OpenGalois records this as the two rational square tests",
        ),
        display_math(
            rf"W_1=\Delta_{{Q_1}}\Delta_f={data['w1']},\qquad "
            rf"W_2=\Delta_{{Q_2}}\Delta_f={data['w2']}."
        ),
    )



def _quartic_kw_data(fact: FactView, ctx: ExplainContext) -> Mapping[str, str] | None:
    """Return concrete Kappe--Warren display data when it can be read exactly."""
    f_ref = ref(fact, 0)
    coeffs = _monic_quartic_coeffs(ctx, f_ref)
    delta_f = _discriminant_value(fact, ctx, f_ref)
    root = _unique_linear_resolvent_root(fact, ctx, f_ref)

    if coeffs is None or delta_f is None or root is None:
        return None

    a, b, _c, d = coeffs
    delta_q1 = a * a - 4 * root
    delta_q2 = (b - root) * (b - root) - 4 * d
    w1 = delta_q1 * delta_f
    w2 = delta_q2 * delta_f

    q1 = _poly_latex_desc([Fraction(1), a, root], variable="T")
    q2 = _poly_latex_desc([Fraction(1), -(b - root), d], variable="T")

    return {
        "root": rational_latex(root),
        "linear_factor": _linear_factor_latex(root),
        "q1": q1,
        "q2": q2,
        "delta_q1": rational_latex(delta_q1),
        "delta_q2": rational_latex(delta_q2),
        "w1": rational_latex(w1),
        "w2": rational_latex(w2),
    }


def _monic_quartic_coeffs(
    ctx: ExplainContext,
    object_ref: str,
) -> tuple[Fraction, Fraction, Fraction, Fraction] | None:
    try:
        obj = ctx.get_object(object_ref)
    except Exception:  # noqa: BLE001
        return None

    coeffs_raw = obj.get("coeffs_qq", obj.get("coeffs"))
    if not isinstance(coeffs_raw, Sequence) or isinstance(coeffs_raw, (str, bytes)):
        return None
    if len(coeffs_raw) != 5:
        return None

    try:
        coeffs = [Fraction(str(c)) for c in coeffs_raw]
    except Exception:  # noqa: BLE001
        return None

    lc = coeffs[0]
    if lc == 0:
        return None
    monic = [c / lc for c in coeffs]
    return monic[1], monic[2], monic[3], monic[4]


def _discriminant_value(fact: FactView, ctx: ExplainContext, f_ref: str) -> Fraction | None:
    for premise in _premises_with_pred(fact, ctx, "Discriminant"):
        try:
            if ref(premise, 0) != f_ref:
                continue
            return _rat_value(ctx, ref(premise, 1))
        except Exception:  # noqa: BLE001
            continue
    return None


def _unique_linear_resolvent_root(
    fact: FactView,
    ctx: ExplainContext,
    f_ref: str,
) -> Fraction | None:
    resolvent_ref = _resolvent_ref(fact, ctx, f_ref)
    if resolvent_ref is None:
        return None

    for premise in _premises_with_pred(fact, ctx, "FactorizationMonicQQ"):
        try:
            if ref(premise, 0) != resolvent_ref:
                continue
            factors_obj = ctx.get_object(ref(premise, 1))
        except Exception:  # noqa: BLE001
            continue

        items = factors_obj.get("items")
        if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
            continue

        roots: list[Fraction] = []
        for item in items:
            if isinstance(item, str):
                root_value = _linear_root(ctx, item)
                if root_value is not None:
                    roots.append(root_value)
        if len(roots) == 1:
            return roots[0]
    return None


def _resolvent_ref(fact: FactView, ctx: ExplainContext, f_ref: str) -> str | None:
    for premise in _premises_with_pred(fact, ctx, "ResolventQQ"):
        try:
            if ref(premise, 1) == f_ref:
                return ref(premise, 0)
        except Exception:  # noqa: BLE001
            continue
    return None


def _premises_with_pred(
    fact: FactView,
    ctx: ExplainContext,
    pred: str,
) -> tuple[FactView, ...]:
    found: list[FactView] = []
    for premise_id in fact.premises:
        try:
            premise = ctx.get_fact(premise_id)
        except Exception:  # noqa: BLE001
            continue
        if premise.pred == pred:
            found.append(premise)
    return tuple(found)


def _linear_root(ctx: ExplainContext, poly_ref: str) -> Fraction | None:
    try:
        obj = ctx.get_object(poly_ref)
    except Exception:  # noqa: BLE001
        return None
    coeffs_raw = obj.get("coeffs_qq", obj.get("coeffs"))
    if not isinstance(coeffs_raw, Sequence) or isinstance(coeffs_raw, (str, bytes)):
        return None
    if len(coeffs_raw) != 2:
        return None
    try:
        lead = Fraction(str(coeffs_raw[0]))
        const = Fraction(str(coeffs_raw[1]))
    except Exception:  # noqa: BLE001
        return None
    if lead == 0:
        return None
    return -const / lead


def _rat_value(ctx: ExplainContext, rat_ref: str) -> Fraction | None:
    try:
        obj = ctx.get_object(rat_ref)
    except Exception:  # noqa: BLE001
        return None
    if obj.get("kind") != "RatQQ":
        return None
    value = obj.get("value_qq", obj.get("value"))
    if value is None:
        return None
    try:
        return Fraction(str(value))
    except Exception:  # noqa: BLE001
        return None


def _linear_factor_latex(root: Fraction, *, variable: str = "T") -> str:
    if root == 0:
        return variable
    if root > 0:
        return rf"{variable}-{rational_latex(root)}"
    return rf"{variable}+{rational_latex(-root)}"


def _poly_latex_desc(coeffs: Sequence[Fraction], *, variable: str) -> str:
    terms: list[tuple[int, str]] = []
    degree = len(coeffs) - 1
    for offset, coeff in enumerate(coeffs):
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
                body = rf"{coeff_part}{variable}^{{{exp}}}"
        terms.append((-1 if coeff < 0 else 1, body))

    if not terms:
        return "0"

    first_sign, first_body = terms[0]
    rendered = first_body if first_sign > 0 else f"-{first_body}"
    for sign, body in terms[1:]:
        rendered += " - " if sign < 0 else " + "
        rendered += body
    return rendered


def _explain_galois_deg4_d4(
    fact: FactView,
    ctx: ExplainContext,
    *,
    witness: str,
) -> tuple[ProofBlock, ...]:
    return (
        *_quartic_transitive_setup(fact, ctx, square_discriminant=False),
        *_quartic_reducible_resolvent_step(fact, ctx),
        *_quartic_kappe_warren_setup(fact, ctx),
        par(
            "In this certificate ",
            math(witness),
            " is not a square in ",
            math(r"\mathbb{Q}"),
            ". Therefore at least one of the two auxiliary quadratics does not ",
            "split over ",
            math(r"\mathbb{Q}(\sqrt{\Delta_f})"),
            ". The cyclic case is excluded.",
        ),
        par(
            "The remaining possibility is the dihedral group ",
            math("D_4"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


def _double_quadratic_setup(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    data = _double_quadratic_factor_data(fact, ctx)

    if data is None:
        return (
            par(
                "The polynomial ",
                math(f_s),
                " decomposes over ",
                math(r"\mathbb{Q}"),
                " with exactly two irreducible quadratic factors.",
            ),
            par(
                "The splitting field is generated by adjoining the square roots ",
                "of the two quadratic discriminants.",
            ),
        )

    quadratic_parts = data["quadratics"]
    linear_parts = data["linears"]

    blocks: list[ProofBlock] = []
    if not linear_parts:
        blocks.extend(
            (
                par(
                    "The certified factorization of ",
                    math(f_s),
                    " has exactly two irreducible quadratic factors over ",
                    math(r"\mathbb{Q}"),
                    ":",
                ),
                display_math(
                    rf"q_1(X)={quadratic_parts[0]},\qquad "
                    rf"q_2(X)={quadratic_parts[1]}."
                ),
                par(
                    "Thus the splitting field is generated by adjoining the ",
                    "square roots of the two quadratic discriminants.",
                ),
            )
        )
    else:
        blocks.append(
            par(
                "The certified factorization of ",
                math(f_s),
                " has ",
                _linear_factor_count_phrase(len(linear_parts)),
                " and two irreducible quadratic factors over ",
                math(r"\mathbb{Q}"),
                ":",
            )
        )
        blocks.append(
            display_math(
                rf"{_linear_factor_display(linear_parts)},\qquad "
                rf"q_1(X)={quadratic_parts[0]},\qquad "
                rf"q_2(X)={quadratic_parts[1]}."
            )
        )
        blocks.append(
            par(
                "The linear factor already splits over ",
                math(r"\mathbb{Q}"),
                ". Hence the splitting field is generated by adjoining the ",
                "square roots of the two quadratic discriminants.",
            )
        )

    return tuple(blocks)


def _double_quadratic_factor_data(
    fact: FactView,
    ctx: ExplainContext,
) -> Mapping[str, tuple[str, ...]] | None:
    """Read the concrete factor shape for the reducible [2,2] branch."""
    f_ref = ref(fact, 0)
    factor_refs = _factorization_items_for(fact, ctx, f_ref)
    if factor_refs is None:
        return None

    distinct_refs = tuple(dict.fromkeys(factor_refs))
    linears: list[str] = []
    quadratics: list[str] = []

    for factor_ref in distinct_refs:
        deg = _degree_value_from_premises(fact, ctx, factor_ref)
        if deg == 1:
            linears.append(poly(ctx, factor_ref))
        elif deg == 2:
            quadratics.append(poly(ctx, factor_ref))

    if len(quadratics) != 2:
        return None

    return {
        "linears": tuple(linears),
        "quadratics": tuple(quadratics),
    }


def _factorization_items_for(
    fact: FactView,
    ctx: ExplainContext,
    f_ref: str,
) -> tuple[str, ...] | None:
    for premise in _premises_with_pred(fact, ctx, "FactorizationMonicQQ"):
        try:
            if ref(premise, 0) != f_ref:
                continue
            factors_obj = ctx.get_object(ref(premise, 1))
        except Exception:  # noqa: BLE001
            continue

        items = factors_obj.get("items")
        if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
            continue

        refs = tuple(item for item in items if isinstance(item, str))
        if refs:
            return refs
    return None


def _degree_value_from_premises(
    fact: FactView,
    ctx: ExplainContext,
    poly_ref: str,
) -> int | None:
    for premise in _premises_with_pred(fact, ctx, "Degree"):
        try:
            if ref(premise, 0) != poly_ref:
                continue
            obj = ctx.get_object(ref(premise, 1))
        except Exception:  # noqa: BLE001
            continue

        if obj.get("kind") != "IntZ":
            continue
        value = obj.get("value")
        if value is None:
            continue
        try:
            return int(str(value))
        except Exception:  # noqa: BLE001
            continue
    return None


def _linear_factor_count_phrase(count: int) -> str:
    if count == 1:
        return "one linear factor"
    return f"{count} linear factors"


def _linear_factor_display(linear_parts: Sequence[str]) -> str:
    if len(linear_parts) == 1:
        return rf"\ell(X)={linear_parts[0]}"
    return r",\qquad ".join(
        rf"\ell_{idx}(X)={linear_part}"
        for idx, linear_part in enumerate(linear_parts, start=1)
    )


def _quadratic_cubic_setup(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (
        par(
            "The polynomial ",
            math(f_s),
            " decomposes into one irreducible quadratic factor and one ",
            "irreducible cubic factor.",
        ),
        par(
            "Therefore the splitting field of ",
            math(f_s),
            " is the compositum of the splitting fields of these two factors.",
        ),
    )


def _explain_reducible_quadratic_cubic_s3(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return (
        *_quadratic_cubic_setup(fact, ctx),
        par(
            "The cubic factor has non-square discriminant, so its Galois group ",
            "is ",
            math("S_3"),
            ". If ",
            math(r"\alpha"),
            " is one of its roots and ",
            math(r"\Delta_{q_3}"),
            " is its discriminant, then its splitting field is ",
            math(r"\mathbb{Q}(\alpha,\sqrt{\Delta_{q_3}})"),
            ".",
        ),
        par(
            "In this case ",
            math(r"\Delta_{q_2}\Delta_{q_3}"),
            " is a square in ",
            math(r"\mathbb{Q}"),
            ". Equivalently, the quadratic fields ",
            math(r"\mathbb{Q}(\sqrt{\Delta_{q_2}})"),
            " and ",
            math(r"\mathbb{Q}(\sqrt{\Delta_{q_3}})"),
            " are the same.",
        ),
        par(
            "Thus the quadratic factor adds no new quadratic extension to the ",
            "cubic splitting field. Therefore the splitting field of the whole ",
            "polynomial is the splitting field of the cubic factor, and the ",
            "Galois group is ",
            math("S_3"),
            ".",
        ),
        *_conclusion(fact, ctx),
    )


def _explain_reducible_quadratic_cubic_d6(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    return (
        *_quadratic_cubic_setup(fact, ctx),
        par(
            "The cubic factor has non-square discriminant, so its Galois group ",
            "is ",
            math("S_3"),
            ". If ",
            math(r"\alpha"),
            " is one root of the cubic factor ",
            math("q_3"),
            ", then its splitting field is ",
            math(r"\mathbb{Q}(\alpha,\sqrt{\Delta_{q_3}})"),
            ". The quadratic factor ",
            math("q_2"),
            " splits over ",
            math(r"\mathbb{Q}(\sqrt{\Delta_{q_2}})"),
            ".",
        ),
        par(
            "Therefore the splitting field of the product is the compositum",
        ),
        display_math(
            r"\mathbb{Q}_f="
            r"\mathbb{Q}(\alpha,\sqrt{\Delta_{q_3}},\sqrt{\Delta_{q_2}})."
        ),
        par(
            "In this case ",
            math(r"\Delta_{q_2}\Delta_{q_3}"),
            " is not a square in ",
            math(r"\mathbb{Q}"),
            ". Hence",
        ),
        display_math(
            r"[\mathbb{Q}(\sqrt{\Delta_{q_2}},"
            r"\sqrt{\Delta_{q_3}}):\mathbb{Q}]=4."
        ),
        par(
            "On the other hand, ",
            math(r"[\mathbb{Q}(\alpha):\mathbb{Q}]=3"),
            ". Since ",
            math("3"),
            " and ",
            math("4"),
            " are coprime, the splitting field has degree ",
            math("12"),
            ".",
        ),
        par(
            "A priori the Galois group embeds in ",
            math(r"S_3\times C_2"),
            ", which also has order ",
            math("12"),
            ". Therefore the full product occurs:",
        ),
        display_math(
            r"G_f\cong S_3\times C_2\cong D_6."
        ),
        *_conclusion(fact, ctx),
    )


def _quintic_transitive_setup(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    f_s = poly(ctx, ref(fact, 0))
    return (
        par(
            "Since ",
            math(f_s),
            " has degree ",
            math("5"),
            " and is irreducible, its Galois group is a transitive subgroup of ",
            math("S_5"),
            ". The possibilities are ",
            math("S_5"),
            ", ",
            math("A_5"),
            ", ",
            math("F_{20}"),
            ", ",
            math("D_5"),
            " and ",
            math("C_5"),
            ".",
        ),
    )


def _dummit_linear_factor_step() -> tuple[ProofBlock, ...]:
    return (
        par(
            "Here the resolvent ",
            math("R"),
            " enters. Dummit's sextic resolvent is built so that its six roots ",
            "correspond to the six conjugates of ",
            math("F_{20}"),
            " in ",
            math("S_5"),
            ".",
        ),
        par(
            "If ",
            math("R"),
            " has a rational root, then ",
            math("G_f"),
            " fixes one of these roots; equivalently, ",
            math("G_f"),
            " is contained in the corresponding stabilizer, which is a ",
            "conjugate of ",
            math("F_{20}"),
            ". The certificate exhibits such a linear factor.",
        ),
    )


def _dummit_linear_factor_step_concrete(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    f_ref = ref(fact, 0)
    theta = _unique_linear_resolvent_root(fact, ctx, f_ref)

    if theta is None:
        factor_sentence: tuple[Inline | str, ...] = (
            "The certificate exhibits the unique linear factor of this ",
            "resolvent; denote its rational root by ",
            math(r"\theta"),
            ".",
        )
    else:
        factor_sentence = (
            "The certified factorization has unique linear factor ",
            math(_linear_factor_latex(theta, variable="Y")),
            ", so the rational root of the resolvent is ",
            math(rf"\theta={rational_latex(theta)}"),
            ".",
        )

    return (
        par(
            "Here the resolvent ",
            math("R"),
            " enters. Dummit's sextic resolvent is built so that its six roots ",
            "correspond to the six conjugates of ",
            math("F_{20}"),
            " in ",
            math("S_5"),
            ".",
        ),
        par(*factor_sentence),
        par(
            "Thus ",
            math("G_f"),
            " fixes one of these six roots and is contained in the ",
            "corresponding stabilizer, a conjugate of ",
            math("F_{20}"),
            ".",
        ),
    )


def _quintic_dummit_quadratics_step(
    fact: FactView,
    ctx: ExplainContext,
) -> tuple[ProofBlock, ...]:
    data = _quintic_dummit_quadratic_data(fact, ctx)

    if data is None:
        return (
            par(
                "To distinguish the two remaining cases, OpenGalois constructs ",
                "Dummit's two auxiliary quadratics ",
                math("q_1"),
                " and ",
                math("q_2"),
                ".",
            ),
            par(
                "Their discriminants, denoted ",
                math(r"\Delta_{q_1}"),
                " and ",
                math(r"\Delta_{q_2}"),
                ", decide whether the quadratics split over ",
                math(r"\mathbb{Q}"),
                ".",
            ),
        )

    return (
        par(
            "To distinguish the two remaining cases, OpenGalois constructs ",
            "Dummit's two auxiliary quadratics. In this certificate they are",
        ),
        display_math(
            rf"q_1(Y)={data['q1']},\qquad "
            rf"q_2(Y)={data['q2']}."
        ),
        par(
            "Their discriminants are",
        ),
        display_math(
            rf"\Delta_{{q_1}}={data['delta_q1']},\qquad "
            rf"\Delta_{{q_2}}={data['delta_q2']}."
        ),
    )


def _quintic_dummit_quadratic_data(
    fact: FactView,
    ctx: ExplainContext,
) -> Mapping[str, str] | None:
    f_ref = ref(fact, 0)
    rows: list[tuple[str, str, str]] = []

    for premise in _premises_with_pred(fact, ctx, "Discriminant"):
        try:
            poly_ref = ref(premise, 0)
        except Exception:  # noqa: BLE001
            continue
        if poly_ref == f_ref:
            continue

        coeffs = _poly_coeffs(ctx, poly_ref)
        if coeffs is None or len(coeffs) != 3:
            continue

        disc = _rat_value(ctx, ref(premise, 1))
        if disc is None:
            continue

        rows.append((_poly_latex_desc(coeffs, variable="Y"), rational_latex(disc), ref(premise, 1)))

    if len(rows) < 2:
        return None

    q1, d1, d1_ref = rows[0]
    q2, d2, d2_ref = rows[1]
    return {
        "q1": q1,
        "q2": q2,
        "delta_q1": d1,
        "delta_q2": d2,
        "delta_q1_ref": d1_ref,
        "delta_q2_ref": d2_ref,
    }


def _quintic_d5_nonsquare_witness(fact: FactView, ctx: ExplainContext) -> str | None:
    data = _quintic_dummit_quadratic_data(fact, ctx)
    if data is None:
        return None

    nonsquare_refs = {
        ref(premise, 0)
        for premise in _premises_with_pred(fact, ctx, "NonSquareQQ")
    }
    if data["delta_q1_ref"] in nonsquare_refs:
        return r"\Delta_{q_1}"
    if data["delta_q2_ref"] in nonsquare_refs:
        return r"\Delta_{q_2}"
    return None


def _poly_coeffs(ctx: ExplainContext, object_ref: str) -> tuple[Fraction, ...] | None:
    try:
        obj = ctx.get_object(object_ref)
    except Exception:  # noqa: BLE001
        return None

    coeffs_raw = obj.get("coeffs_qq", obj.get("coeffs"))
    if not isinstance(coeffs_raw, Sequence) or isinstance(coeffs_raw, (str, bytes)):
        return None

    try:
        return tuple(Fraction(str(c)) for c in coeffs_raw)
    except Exception:  # noqa: BLE001
        return None


def _quintic_d5_c5_common(fact: FactView, ctx: ExplainContext) -> tuple[ProofBlock, ...]:
    return (
        *_quintic_transitive_setup(fact, ctx),
        par(
            "Since the discriminant is a square in ",
            math(r"\mathbb{Q}"),
            ", the Galois group is contained in ",
            math("A_5"),
            ". Therefore only ",
            math("A_5"),
            ", ",
            math("D_5"),
            " and ",
            math("C_5"),
            " remain.",
        ),
        *_dummit_linear_factor_step_concrete(fact, ctx),
        par(
            "Combining this containment with ",
            math(r"G_f\subseteq A_5"),
            " gives ",
            math(r"G_f\subseteq F_{20}\cap A_5\cong D_5"),
            ". Hence the group is either ",
            math("D_5"),
            " or ",
            math("C_5"),
            ".",
        ),
    )





