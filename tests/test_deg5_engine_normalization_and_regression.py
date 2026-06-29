from __future__ import annotations

from fractions import Fraction
from typing import Any

from opengalois.api import analyze, verify
from opengalois.engine.procedures.irreducible.deg5 import _find_rational_root_QQ_desc
from opengalois.models import GaloisGroup


def _facts(result) -> list[dict[str, Any]]:
    cert = result.certificate
    proof = cert.get("proof", {})
    facts = proof.get("facts", [])
    assert isinstance(facts, list)
    return facts


def _facts_by_pred(result, pred: str) -> list[dict[str, Any]]:
    return [f for f in _facts(result) if f.get("claim", {}).get("pred") == pred]


def _facts_by_rule(result, rule_id: str) -> list[dict[str, Any]]:
    return [f for f in _facts(result) if f.get("rule") == rule_id]


def _last_galois_group_fact(result) -> dict[str, Any]:
    for fact in reversed(_facts(result)):
        if fact.get("claim", {}).get("pred") == "GaloisGroup":
            return fact
    raise AssertionError("No GaloisGroup fact found")


def test_deg5_already_depressed_emits_identity_normalization_without_lift() -> None:
    # g(x) = x^5 - 3x^3 - 3x^2 - 3x - 3
    result = analyze([1, 0, -3, -3, -3, -3])

    assert result.galois_group == GaloisGroup.S5

    dm_facts = _facts_by_pred(result, "DepressedMonicEq")
    assert len(dm_facts) == 1
    dm_fact = dm_facts[0]
    assert dm_fact["claim"]["args"] == [{"ref": "$input"}, {"ref": "$input"}]
    assert dm_fact["rule"] == "normalize.depressed_monic_QQ@1"

    # Even with explicit normalization, there is no group lift when the input is
    # already the depressed representative.
    assert _facts_by_rule(result, "galois_group.QQ.lift.depressed_monic@1") == []

    final_fact = _last_galois_group_fact(result)
    assert final_fact["claim"]["args"][0] == {"ref": "$input"}

    vr = verify(result.certificate)
    assert vr.verified


def test_deg5_nondepressed_monic_normalizes_and_lifts() -> None:
    # f(x) = g(x + 1), where g(x) = x^5 - 3x^3 - 3x^2 - 3x - 3
    # Expanded form:
    # x^5 + 5x^4 + 7x^3 - 2x^2 - 13x - 11
    result = analyze([1, 5, 7, -2, -13, -11])

    assert result.galois_group == GaloisGroup.S5

    dm_facts = _facts_by_pred(result, "DepressedMonicEq")
    assert len(dm_facts) == 1

    lift_facts = _facts_by_rule(result, "galois_group.QQ.lift.depressed_monic@1")
    assert len(lift_facts) == 1

    lift_fact = lift_facts[0]
    assert lift_fact["claim"]["pred"] == "GaloisGroup"
    assert lift_fact["claim"]["args"][0] == {"ref": "$input"}

    final_fact = _last_galois_group_fact(result)
    assert final_fact["id"] == lift_fact["id"]

    vr = verify(result.certificate)
    assert vr.verified


def test_deg5_nonmonic_nondepressed_normalizes_and_lifts() -> None:
    # 2 * (x^5 + 5x^4 + 7x^3 - 2x^2 - 13x - 11)
    result = analyze([2, 10, 14, -4, -26, -22])

    assert result.galois_group == GaloisGroup.S5

    dm_facts = _facts_by_pred(result, "DepressedMonicEq")
    assert len(dm_facts) == 1

    lift_facts = _facts_by_rule(result, "galois_group.QQ.lift.depressed_monic@1")
    assert len(lift_facts) == 1

    final_fact = _last_galois_group_fact(result)
    assert final_fact["id"] == lift_facts[0]["id"]
    assert final_fact["claim"]["args"][0] == {"ref": "$input"}

    vr = verify(result.certificate)
    assert vr.verified


def test_find_rational_root_large_constant_term_regression() -> None:
    # (x - 5) * (x^5 + 72052137128893934375)
    coeffs = [
        Fraction(1, 1),
        Fraction(-5, 1),
        Fraction(0, 1),
        Fraction(0, 1),
        Fraction(0, 1),
        Fraction(72052137128893934375, 1),
        Fraction(-360260685644469671875, 1),
    ]

    root = _find_rational_root_QQ_desc(coeffs)

    assert root == Fraction(5, 1)
