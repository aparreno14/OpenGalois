# ruff: noqa: D102,D103
"""Discriminant and squarehood narrative templates."""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

from ...context import ExplainContext, FactView
from ...proof_model import Paragraph, math, par
from ..registry import rule_template
from ._helpers import obj, poly, ref


@rule_template("disc.QQ.compute@1")
def explain_discriminant(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    f_ref = ref(fact, 0)
    d_ref = ref(fact, 1)
    return (
        par(
            "The discriminant of ",
            math(poly(ctx, f_ref)),
            " is ",
            math(obj(ctx, d_ref)),
            ".",
        ),
    )


@rule_template("sqrt.QQ.check@1")
def explain_sqrt_check(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    q_ref = ref(fact, 0)
    s_ref = ref(fact, 1)
    return (
        par(
            "The certificate checks the exact identity ",
            math(rf"{obj(ctx, s_ref)}^2 = {obj(ctx, q_ref)}"),
            ".",
        ),
    )


@rule_template("is_square.QQ.lift@1")
def explain_square_lift(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    q_ref = ref(fact, 0)
    return (
        par(
            "Hence ",
            math(obj(ctx, q_ref)),
            " is a square in ",
            math(r"\mathbb{Q}"),
            ".",
        ),
    )


@rule_template("nonsquare.QQ.isqrt@1")
def explain_nonsquare(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    q_ref = ref(fact, 0)
    return (
        par(
            "The certificate proves that ",
            math(obj(ctx, q_ref)),
            " is not a square in ",
            math(r"\mathbb{Q}"),
            ".",
        ),
    )


@rule_template("disc.square.QQ.lift@1")
def explain_disc_square(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    f_ref = ref(fact, 0)
    return (
        par(
            "Therefore the discriminant of ",
            math(poly(ctx, f_ref)),
            " is a square in ",
            math(r"\mathbb{Q}"),
            ".",
        ),
    )


@rule_template("disc.nonsquare.QQ.lift@1")
def explain_disc_nonsquare(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    f_ref = ref(fact, 0)
    return (
        par(
            "Therefore the discriminant of ",
            math(poly(ctx, f_ref)),
            " is not a square in ",
            math(r"\mathbb{Q}"),
            ".",
        ),
    )

@rule_template("nonsquare.QQ.isqrt@2")
def explain_nonsquare_v2(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    q_ref = ref(fact, 0)
    q_s = obj(ctx, q_ref)
    evidence = fact.raw.get("evidence")
    obstruction = evidence.get("obstruction") if isinstance(evidence, Mapping) else None

    if isinstance(obstruction, Mapping) and obstruction.get("kind") == "negative":
        return (
            par(
                "The value ",
                math(q_s),
                " is negative. Since every square in ",
                math(r"\mathbb{Q}"),
                " is non-negative, it is not a square in ",
                math(r"\mathbb{Q}"),
                ".",
            ),
        )

    if isinstance(obstruction, Mapping) and obstruction.get("kind") == "integer_isqrt_interval":
        side = obstruction.get("side")
        lower_root = obstruction.get("lower_root")
        lower_square = obstruction.get("lower_square")
        upper_root = obstruction.get("upper_root")
        upper_square = obstruction.get("upper_square")

        try:
            q_obj = ctx.get_object(q_ref)
            value = q_obj.get("value")
            q = Fraction(value) if isinstance(value, str) else None
        except Exception:  # noqa: BLE001
            q = None

        if (
            q is not None
            and isinstance(lower_root, str)
            and isinstance(lower_square, str)
            and isinstance(upper_root, str)
            and isinstance(upper_square, str)
        ):
            if side == "numerator":
                n = q.numerator
                side_s = "numerator"
            elif side == "denominator":
                n = q.denominator
                side_s = "denominator"
            else:
                n = None
                side_s = "selected integer"

            if n is not None:
                return (
                    par(
                        "The value ",
                        math(q_s),
                        " is considered in reduced form. Its ",
                        side_s,
                        " is ",
                        math(str(n)),
                        ". Since ",
                        math(
                            rf"{lower_root}^2 = {lower_square} < {n} < "
                            rf"{upper_square} = {upper_root}^2"
                        ),
                        ", this integer is not a square in ",
                        math(r"\mathbb{Z}"),
                        ". Therefore ",
                        math(q_s),
                        " is not a square in ",
                        math(r"\mathbb{Q}"),
                        ".",
                    ),
                )

    return (
        par(
            "The certificate proves that ",
            math(q_s),
            " is not a square in ",
            math(r"\mathbb{Q}"),
            ".",
        ),
    )
