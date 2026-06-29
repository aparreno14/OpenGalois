# ruff: noqa: D102,D103
"""Small helpers shared by le5-core narrative templates."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...context import ExplainContext, FactView
from ...math_render import group_latex, object_latex, polynomial_name
from ...proof_model import Inline, Paragraph, math, par

JsonMap = Mapping[str, Any]


def ref(fact: FactView, index: int) -> str:
    return fact.ref_arg(index)


def obj(ctx: ExplainContext, object_ref: str, *, symbolic_input: bool = True) -> str:
    return object_latex(ctx, object_ref, symbolic_input=symbolic_input)


def poly(ctx: ExplainContext, object_ref: str) -> str:
    return polynomial_name(ctx, object_ref)


def group(ctx: ExplainContext, object_ref: str) -> str:
    value = ctx.get_object(object_ref)
    for key in ("alias", "label", "value", "name", "id"):
        raw = value.get(key)
        if isinstance(raw, str) and raw:
            return group_latex(raw)
    return group_latex(object_ref.rsplit(".", 1)[-1])


def one_sentence(*parts: Inline | str) -> tuple[Paragraph, ...]:
    parsed: list[Inline | str] = []
    for part in parts:
        if isinstance(part, Paragraph):
            raise TypeError("one_sentence expects inline parts, not Paragraph")
        parsed.append(part)
    return (par(*parsed),)


def simple_fact_sentence(fact: FactView, ctx: ExplainContext) -> tuple[Paragraph, ...]:
    return (
        par(
            "The certified fact is ",
            math(_generic_claim(fact, ctx)),
            ".",
        ),
    )


def _generic_claim(fact: FactView, ctx: ExplainContext) -> str:
    rendered_args = [obj(ctx, ref(fact, idx)) for idx in range(len(fact.args))]
    return rf"\operatorname{{{fact.pred}}}({', '.join(rendered_args)})"
