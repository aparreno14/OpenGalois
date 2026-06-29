from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest

from opengalois.engine.context import EngineContext
from opengalois.engine.objects import ObjectStore
from opengalois.engine.registry import EngineRegistry
from opengalois.models import AnalysisOptions


def _Q(coeffs: list[int]) -> list[Fraction]:
    return [Fraction(c) for c in coeffs]


def _new_ctx(coeffs: list[int]) -> EngineContext:
    ctx = EngineContext(
        options=AnalysisOptions(),
        objects=ObjectStore(),
        registry=EngineRegistry.default(),
    )
    ctx.cache["$input_poly"] = _Q(coeffs)
    return ctx


def _run_reducible(coeffs: list[int]):
    ctx = _new_ctx(coeffs)
    red_nodes, red_out = ctx.registry.reducibility.run(ctx, poly_ref="$input")
    assert red_out["decision"] == "reducible"
    proc_res = ctx.registry.reducible.run(ctx, poly_ref="$input")
    return ctx, red_nodes, red_out, proc_res


def _last_galois_group_fact(facts: list[dict[str, Any]]) -> dict[str, Any]:
    for fact in reversed(facts):
        claim = fact.get("claim", {})
        if claim.get("pred") == "GaloisGroup":
            return fact
    raise AssertionError("No GaloisGroup fact found")


@pytest.mark.parametrize(
    ("name", "coeffs", "expected_case", "expected_signature", "expected_group", "expected_rule"),
    [
        (
            "all_linear",
            [1, -2, -1, 2],                   # (x-1)(x+1)(x-2)
            "all_linear",
            [],
            "Trivial",
            "galois_group.QQ.reducible.all_linear.trivial@1",
        ),
        (
            "single_quadratic",
            [1, 2, -5, -4, 6],               # (x^2-2)(x-1)(x+3)
            "single_nonlinear",
            [2],
            "C2",
            "galois_group.QQ.reducible.single_nonlinear.inherit@1",
        ),
        (
            "single_cubic",
            [1, -2, -1, 1, 2],               # (x^3-x-1)(x-2)
            "single_nonlinear",
            [3],
            "S3",
            "galois_group.QQ.reducible.single_nonlinear.inherit@1",
        ),
        (
            "single_quartic",
            [1, -1, 0, 0, -2, 2],            # (x^4-2)(x-1)
            "single_nonlinear",
            [4],
            "D4",
            "galois_group.QQ.reducible.single_nonlinear.inherit@1",
        ),
        (
            "double_quadratic_c2",
            [1, 0, -10, 0, 16],              # (x^2-2)(x^2-8)
            "double_quadratic",
            [2, 2],
            "C2",
            "galois_group.QQ.reducible.double_quadratic.C2@1",
        ),
        (
            "double_quadratic_v4",
            [1, 0, -5, 0, 6],                # (x^2-2)(x^2-3)
            "double_quadratic",
            [2, 2],
            "V4",
            "galois_group.QQ.reducible.double_quadratic.V4@1",
        ),
        (
            "quadratic_cubic_c6",
            [1, 0, -5, -1, 6, 2],            # (x^2-2)(x^3-3x-1)
            "quadratic_cubic",
            [2, 3],
            "C6",
            "galois_group.QQ.reducible.quadratic_cubic.C6@1",
        ),
        (
            "quadratic_cubic_s3",
            [1, 0, 22, -1, -23, -23],        # (x^2+23)(x^3-x-1)
            "quadratic_cubic",
            [2, 3],
            "S3",
            "galois_group.QQ.reducible.quadratic_cubic.S3@2",
        ),
        (
            "quadratic_cubic_d6",
            [1, 0, -24, -1, 23, 23],         # (x^2-23)(x^3-x-1)
            "quadratic_cubic",
            [2, 3],
            "D6",
            "galois_group.QQ.reducible.quadratic_cubic.D6@2",
        ),
    ],
)
def test_reducible_procedure_routes_all_supported_signatures(
    name: str,
    coeffs: list[int],
    expected_case: str,
    expected_signature: list[int],
    expected_group: str,
    expected_rule: str,
) -> None:
    _ = name
    ctx, red_nodes, red_out, proc_res = _run_reducible(coeffs)

    assert red_nodes
    assert red_out["decision"] == "reducible"
    assert proc_res.facts, "Procedure should emit local factorization + branch facts"

    first_fact = proc_res.facts[0]
    assert first_fact["claim"]["pred"] == "FactorizationMonicQQ"
    assert first_fact["claim"]["args"][0]["ref"] == "$input"
    assert first_fact["claim"]["args"][1]["ref"] == "list.factors"
    assert first_fact["claim"]["args"][2]["ref"] == "rat.unit"

    out = proc_res.out
    assert out["decision"] == "galois_group"
    assert out["branch"] == "reducible"
    assert out["case"] == expected_case
    assert out["signature"] == expected_signature
    assert out["group"] == expected_group

    final_fact = _last_galois_group_fact(proc_res.facts)
    assert final_fact["rule"] == expected_rule
    assert final_fact["claim"]["args"][0]["ref"] == "$input"

    # Branch-specific deeper checks
    if expected_case == "double_quadratic":
        sq = out["product_squarehood"]
        assert sq["decision"] in {"square", "nonsquare"}
        if expected_group == "C2":
            assert sq["decision"] == "square"
        else:
            assert sq["decision"] == "nonsquare"

    if expected_case == "quadratic_cubic":
        d2_sq = out["cubic_discriminant_squarehood"]
        assert d2_sq["decision"] in {"square", "nonsquare"}

        if expected_group == "C6":
            assert d2_sq["decision"] == "square"
            assert "product_squarehood" not in out
        else:
            assert d2_sq["decision"] == "nonsquare"
            prod_sq = out["product_squarehood"]
            assert prod_sq["decision"] in {"square", "nonsquare"}
            if expected_group == "S3":
                assert prod_sq["decision"] == "square"
            else:
                assert prod_sq["decision"] == "nonsquare"

    # Sanity: the procedure should have cached subgroup facts for reused irreducible controllers.
    gg_map = ctx.cache.get("_galois_group_fact_by_poly", {})
    assert isinstance(gg_map, dict)


def test_reducible_procedure_collapses_repeated_nonlinear_factor_signature() -> None:
    # (x^2-2)^2 (x-1) -> distinct non-linear signature must be [2], not [2,2]
    coeffs = [1, -1, -4, 4, 4, -4]

    _ctx, _red_nodes, _red_out, proc_res = _run_reducible(coeffs)

    out = proc_res.out
    assert out["case"] == "single_nonlinear"
    assert out["signature"] == [2]
    assert len(out["nonlinear_factor_refs"]) == 1

    final_fact = _last_galois_group_fact(proc_res.facts)
    assert final_fact["rule"] == "galois_group.QQ.reducible.single_nonlinear.inherit@1"