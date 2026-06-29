from __future__ import annotations

from typing import Any

from opengalois import analyze, verify


def _radical_rules(cert: dict[str, Any]) -> list[str]:
    return [
        fact.get("rule", "")
        for fact in cert.get("proof", {}).get("facts", [])
        if fact.get("claim", {}).get("pred") == "RadicalRoots"
    ]


def test_engine_emits_cardano_v2_for_irreducible_depressed_cubic() -> None:
    # x^3 + x + 1 is irreducible over QQ and already depressed monic.
    result = analyze([1, 0, 1, 1], explain=False)
    cert = result.certificate
    assert "radical_roots.QQ.deg3.cardano.depressed_monic@2" in _radical_rules(cert)
    verified = verify(cert)
    assert verified.verified


def test_engine_emits_cardano_v2_p_zero_branch_for_x3_plus_2() -> None:
    # x^3 + 2 is irreducible over QQ and exercises the p = 0 branch.
    result = analyze([1, 0, 0, 2], explain=False)
    cert = result.certificate
    assert "radical_roots.QQ.deg3.cardano.depressed_monic@2" in _radical_rules(cert)
    verified = verify(cert)
    assert verified.verified
