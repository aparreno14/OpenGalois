from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest

from opengalois.engine.engine import run_engine
from opengalois.models import AnalysisOptions


def _Q(coeffs: list[int]) -> list[Fraction]:
    return [Fraction(c) for c in coeffs]


def _last_galois_group_fact(facts: list[dict[str, Any]]) -> dict[str, Any]:
    for fact in reversed(facts):
        claim = fact.get("claim", {})
        if claim.get("pred") == "GaloisGroup":
            return fact
    raise AssertionError("No GaloisGroup fact found")


@pytest.mark.parametrize(
    ("coeffs", "expected_group", "expected_rule"),
    [
        ([1, -2, -1, 2], "Trivial", "galois_group.QQ.reducible.all_linear.trivial@1"),
        ([1, 2, -5, -4, 6], "C2", "galois_group.QQ.reducible.single_nonlinear.inherit@1"),
        ([1, -2, -1, 1, 2], "S3", "galois_group.QQ.reducible.single_nonlinear.inherit@1"),
        ([1, 0, -10, 0, 16], "C2", "galois_group.QQ.reducible.double_quadratic.C2@1"),
        ([1, 0, -5, 0, 6], "V4", "galois_group.QQ.reducible.double_quadratic.V4@1"),
        ([1, 0, -5, -1, 6, 2], "C6", "galois_group.QQ.reducible.quadratic_cubic.C6@1"),
        ([1, 0, 22, -1, -23, -23], "S3", "galois_group.QQ.reducible.quadratic_cubic.S3@2"),
        ([1, 0, -24, -1, 23, 23], "D6", "galois_group.QQ.reducible.quadratic_cubic.D6@2"),
    ],
)
def test_run_engine_dispatches_reducible_pipeline(
    coeffs: list[int],
    expected_group: str,
    expected_rule: str,
) -> None:
    result = run_engine(_Q(coeffs), options=AnalysisOptions())

    final_fact = _last_galois_group_fact(result.facts)
    assert final_fact["rule"] == expected_rule

    assert result.summary["status"] == "reducible"
    assert result.summary["galois_group"] == expected_group
    assert result.summary["solvable_by_radicals"] is True




@pytest.mark.parametrize(
    ("coeffs", "expected_rule", "expected_group"),
    [
        ([1, 0, -2], "galois_group.QQ.deg2.C2@1", "C2"),
        ([1, 0, -1, -1], "galois_group.QQ.deg3.S3@1", "S3"),
    ],
)
def test_run_engine_irreducible_wiring_still_works(
    coeffs: list[int],
    expected_rule: str,
    expected_group: str,
) -> None:
    result = run_engine(_Q(coeffs), options=AnalysisOptions())

    final_fact = _last_galois_group_fact(result.facts)
    assert final_fact["rule"] == expected_rule

    if expected_group != "UNKNOWN":
        assert result.summary["status"] == "irreducible"
        assert result.summary["galois_group"] == expected_group