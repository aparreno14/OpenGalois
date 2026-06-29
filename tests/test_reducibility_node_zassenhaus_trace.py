from __future__ import annotations

from opengalois import analyze


def test_analyze_emits_zassenhaus_trace_for_irreducible_quadratic() -> None:
    cert = analyze([1, 0, 1], explain=False).certificate
    facts = cert["proof"]["facts"]

    irred_facts = [
        fact for fact in facts
        if fact.get("claim", {}).get("pred") == "IrreducibleQQ"
    ]

    assert irred_facts
    assert any(fact.get("rule") == "irreducible.QQ.zassenhaus_trace@1" for fact in irred_facts)

    fact = next(fact for fact in irred_facts if fact.get("rule") == "irreducible.QQ.zassenhaus_trace@1")
    evidence = fact.get("evidence")
    assert evidence["prime"] == "3"
    assert evidence["ell"] == 0
    assert evidence["mod_p_factorization"]["factors_desc"] == [["1", "0", "1"]]
