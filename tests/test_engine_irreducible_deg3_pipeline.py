from __future__ import annotations

from fractions import Fraction
from typing import Any

from opengalois.engine.engine import run_engine
from opengalois.models import AnalysisOptions


def _has_rule(facts: list[dict[str, Any]], rule_id: str) -> bool:
    return any(isinstance(f, dict) and f.get("rule") == rule_id for f in facts)


def test_engine_irreducible_deg3_disc_square_classifies_C3() -> None:
    # f(x) = x^3 - 3x - 1 has discriminant 81 (square) => C3
    coeffs = [Fraction(1), Fraction(0), Fraction(-3), Fraction(-1)]
    res = run_engine(coeffs, options=AnalysisOptions())
    assert _has_rule(res.facts, "disc.QQ.compute@1")
    assert _has_rule(res.facts, "disc.square.QQ.lift@1")
    assert _has_rule(res.facts, "galois_group.QQ.deg3.C3@1")


def test_engine_irreducible_deg3_disc_nonsquare_classifies_S3() -> None:
    # f(x) = x^3 - 2 has discriminant -108 (non-square) => S3
    coeffs = [Fraction(1), Fraction(0), Fraction(0), Fraction(-2)]
    res = run_engine(coeffs, options=AnalysisOptions())
    assert _has_rule(res.facts, "disc.QQ.compute@1")
    assert _has_rule(res.facts, "disc.nonsquare.QQ.lift@1")
    assert _has_rule(res.facts, "galois_group.QQ.deg3.S3@1")
