from __future__ import annotations

from typing import Any

from opengalois.api import analyze, verify
from opengalois.models import GaloisGroup


def _facts(result) -> list[dict[str, Any]]:
    cert = result.certificate
    proof = cert.get("proof", {})
    facts = proof.get("facts", [])
    assert isinstance(facts, list)
    return facts


def _fact_by_id(result, fact_id: str) -> dict[str, Any]:
    for fact in _facts(result):
        if fact.get("id") == fact_id:
            return fact
    raise AssertionError(f"Missing fact id: {fact_id}")


def _facts_by_rule(result, rule_id: str) -> list[dict[str, Any]]:
    return [f for f in _facts(result) if f.get("rule") == rule_id]


def _last_galois_group_fact(result) -> dict[str, Any]:
    for fact in reversed(_facts(result)):
        claim = fact.get("claim", {})
        if claim.get("pred") == "GaloisGroup":
            return fact
    raise AssertionError("No GaloisGroup fact found")


def _premise_preds(result, fact: dict[str, Any]) -> list[str]:
    premises = fact.get("premises", [])
    assert isinstance(premises, list)
    return [_fact_by_id(result, pid)["claim"]["pred"] for pid in premises]


def _assert_verified(result) -> None:
    vr = verify(result.certificate)
    assert vr.verified, tuple((c.name, c.ok, c.details) for c in vr.checks)


def test_deg5_pipeline_s5_valid_certificate() -> None:
    coeffs = [1, 0, -3, -3, -3, -3]

    result = analyze(coeffs)

    assert result.galois_group == GaloisGroup.S5

    final_fact = _last_galois_group_fact(result)
    assert final_fact["rule"] == "galois_group.QQ.deg5.S5@1"
    assert _premise_preds(result, final_fact) == [
        "Degree",
        "IrreducibleQQ",
        "DiscNonSquareQQ",
        "ResolventQQ",
        "IrreducibleQQ",
    ]

    irred_resolvent = _facts_by_rule(result, "irreducible.QQ.dummit_resolvent@1")
    assert len(irred_resolvent) == 1
    assert _premise_preds(result, irred_resolvent[0]) == [
        "ResolventQQ",
        "Degree",
        "IrreducibleQQ",
    ]

    _assert_verified(result)


def test_deg5_pipeline_a5_valid_certificate() -> None:
    coeffs = [1, 0, 0, 0, 20, -16]

    result = analyze(coeffs)

    assert result.galois_group == GaloisGroup.A5

    final_fact = _last_galois_group_fact(result)
    assert final_fact["rule"] == "galois_group.QQ.deg5.A5@1"
    assert _premise_preds(result, final_fact) == [
        "Degree",
        "IrreducibleQQ",
        "DiscSquareQQ",
        "ResolventQQ",
        "IrreducibleQQ",
    ]

    irred_resolvent = _facts_by_rule(result, "irreducible.QQ.dummit_resolvent@1")
    assert len(irred_resolvent) == 1
    assert _premise_preds(result, irred_resolvent[0]) == [
        "ResolventQQ",
        "Degree",
        "IrreducibleQQ",
    ]

    _assert_verified(result)


def test_deg5_pipeline_f20_valid_certificate() -> None:
    coeffs = [1, 0, 0, 0, 15, 12]

    result = analyze(coeffs)

    assert result.galois_group == GaloisGroup.F20

    final_fact = _last_galois_group_fact(result)
    assert final_fact["rule"] == "galois_group.QQ.deg5.F20@1"
    assert _premise_preds(result, final_fact) == [
        "Degree",
        "IrreducibleQQ",
        "DiscNonSquareQQ",
        "ResolventQQ",
        "FactorizationMonicQQ",
        "Degree",
    ]

    assert _facts_by_rule(result, "irreducible.QQ.dummit_resolvent@1") == []

    _assert_verified(result)


def test_deg5_pipeline_d5_valid_certificate() -> None:
    coeffs = [1, 0, 0, 0, -5, 12]

    result = analyze(coeffs)

    assert result.galois_group == GaloisGroup.D5

    final_fact = _last_galois_group_fact(result)
    assert final_fact["rule"] == "galois_group.QQ.deg5.D5@1"
    assert _premise_preds(result, final_fact) == [
        "Degree",
        "IrreducibleQQ",
        "Discriminant",
        "SqrtQQ",
        "ResolventQQ",
        "FactorizationMonicQQ",
        "Degree",
        "Discriminant",
        "NonSquareQQ",
        "Discriminant",
        "NonSquareQQ",
    ]

    assert _facts_by_rule(result, "irreducible.QQ.dummit_resolvent@1") == []

    _assert_verified(result)


def test_deg5_pipeline_c5_valid_certificate() -> None:
    coeffs = [1, 0, -110, -55, 2310, 979]

    result = analyze(coeffs)

    assert result.galois_group == GaloisGroup.C5

    final_fact = _last_galois_group_fact(result)
    assert final_fact["rule"] == "galois_group.QQ.deg5.C5@1"
    assert _premise_preds(result, final_fact) == [
        "Degree",
        "IrreducibleQQ",
        "Discriminant",
        "SqrtQQ",
        "ResolventQQ",
        "FactorizationMonicQQ",
        "Degree",
        "Discriminant",
        "IsSquareQQ",
        "Discriminant",
        "IsSquareQQ",
    ]

    assert _facts_by_rule(result, "irreducible.QQ.dummit_resolvent@1") == []

    _assert_verified(result)
