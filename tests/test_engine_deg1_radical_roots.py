from __future__ import annotations

from fractions import Fraction
from typing import Any, cast

from opengalois.engine.context import EngineContext, _ensure_degree_fact
from opengalois.engine.objects import ObjectStore
from opengalois.engine.procedures.irreducible.deg1 import IrreducibleDeg1Procedure
from opengalois.models import AnalysisOptions
from opengalois.radicals import decode_expr_list_payloads, qq


def test_irreducible_deg1_procedure_emits_radical_roots() -> None:
    ctx = EngineContext(
        options=AnalysisOptions(),
        objects=ObjectStore(),
        registry=cast(Any, None),
    )
    ctx.cache["$input_poly"] = [Fraction(2, 1), Fraction(-3, 1)]

    degree_fact_id, degree = _ensure_degree_fact(ctx, poly_ref="$input")
    assert degree == 1

    result = IrreducibleDeg1Procedure().run(ctx, poly_ref="$input")

    assert [fact["claim"]["pred"] for fact in result.facts] == ["GaloisGroup", "RadicalRoots"]
    assert result.facts[0]["premises"] == [degree_fact_id]
    assert result.facts[1]["premises"] == [degree_fact_id]

    roots_ref = result.facts[1]["claim"]["args"][1]["ref"]
    roots_payload = ctx.objects.objects[roots_ref]
    decoded = decode_expr_list_payloads(roots_payload, ctx.objects.objects)
    assert decoded == [qq(Fraction(3, 2))]
