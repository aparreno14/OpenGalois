from __future__ import annotations

from typing import Any

from opengalois import analyze, verify

Certificate = dict[str, Any]
Fact = dict[str, Any]
ObjectMap = dict[str, Any]

LEGACY_DEG4_RULES = {
    "galois_group.QQ.deg4.S4@1",
    "galois_group.QQ.deg4.A4@1",
    "galois_group.QQ.deg4.V4@1",
    "galois_group.QQ.deg4.C4@1",
    "galois_group.QQ.deg4.D4.w1@1",
    "galois_group.QQ.deg4.D4.w2@1",
}

NEW_DEG4_RULES = {
    "galois_group.QQ.deg4.S4@2",
    "galois_group.QQ.deg4.A4@2",
    "galois_group.QQ.deg4.V4@3",
    "galois_group.QQ.deg4.C4@2",
    "galois_group.QQ.deg4.D4.w1@2",
    "galois_group.QQ.deg4.D4.w2@2",
}

PAIR_SUMS_RESOLVENT_RULE = "resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1"
PAIR_SUMS_MPOLY_REF = "mpoly.resolvent.deg4.cubic_x1plusx2_times_x3plusx4"


def _facts(cert: Certificate) -> list[Fact]:
    proof = cert.get("proof")
    assert isinstance(proof, dict)
    facts = proof.get("facts")
    assert isinstance(facts, list)
    return facts


def _objects(cert: Certificate) -> ObjectMap:
    objects = cert.get("objects")
    assert isinstance(objects, dict)
    return objects


def _rules(cert: Certificate) -> list[str]:
    out: list[str] = []
    for fact in _facts(cert):
        rule = fact.get("rule")
        assert isinstance(rule, str)
        out.append(rule)
    return out


def _final_input_group_object(cert: Certificate) -> ObjectMap:
    for fact in reversed(_facts(cert)):
        claim = fact.get("claim", {})
        if not isinstance(claim, dict) or claim.get("pred") != "GaloisGroup":
            continue
        args = claim.get("args", [])
        if not isinstance(args, list) or len(args) != 2:
            continue
        first_arg = args[0]
        second_arg = args[1]
        if not isinstance(first_arg, dict) or not isinstance(second_arg, dict):
            continue
        if first_arg.get("ref") == "$input":
            group_ref = second_arg.get("ref")
            assert isinstance(group_ref, str)
            group_obj = _objects(cert)[group_ref]
            assert isinstance(group_obj, dict)
            return group_obj
    raise AssertionError("missing final GaloisGroup($input,G) fact")


def _resolvent_facts(cert: Certificate) -> list[Fact]:
    out: list[Fact] = []
    for fact in _facts(cert):
        claim = fact.get("claim", {})
        if isinstance(claim, dict) and claim.get("pred") == "ResolventQQ":
            out.append(fact)
    return out


def test_deg4_pipeline_uses_pair_sums_resolvent_and_v2_rule() -> None:
    result = analyze([1, 0, 0, -1, -1], explain=False)
    cert: Certificate = result.certificate

    verification = verify(cert)
    assert verification.verified, [c for c in verification.checks if not c.ok]

    rules = _rules(cert)
    assert "galois_group.QQ.deg4.S4@2" in rules
    assert "galois_group.QQ.lift.depressed_monic@1" not in rules
    assert not (LEGACY_DEG4_RULES & set(rules))
    assert NEW_DEG4_RULES & set(rules)

    group_obj = _final_input_group_object(cert)
    assert group_obj["kind"] == "GroupId"
    assert group_obj["order"] == 24
    assert group_obj["index"] == 12

    resolvents = _resolvent_facts(cert)
    assert len(resolvents) == 1
    assert resolvents[0]["rule"] == PAIR_SUMS_RESOLVENT_RULE

    claim = resolvents[0]["claim"]
    assert isinstance(claim, dict)
    args = claim["args"]
    assert isinstance(args, list)
    assert args[1]["ref"] == "$input"
    p_ref = args[2]["ref"]
    assert p_ref == PAIR_SUMS_MPOLY_REF

    p_obj = _objects(cert)[p_ref]
    assert p_obj["terms"] == [
        {"exp": [1, 0, 1, 0], "coeff_qq": "1"},
        {"exp": [1, 0, 0, 1], "coeff_qq": "1"},
        {"exp": [0, 1, 1, 0], "coeff_qq": "1"},
        {"exp": [0, 1, 0, 1], "coeff_qq": "1"},
    ]


def test_deg4_pipeline_lifts_group_for_non_depressed_input() -> None:
    # This is (y^4 - y - 1) translated back to x by y = x - 1.
    result = analyze([1, -4, 6, -5, 1], explain=False)
    cert: Certificate = result.certificate

    verification = verify(cert)
    assert verification.verified, [c for c in verification.checks if not c.ok]

    rules = _rules(cert)
    assert "galois_group.QQ.deg4.S4@2" in rules
    assert "galois_group.QQ.lift.depressed_monic@1" in rules
    assert not (LEGACY_DEG4_RULES & set(rules))

    resolvents = _resolvent_facts(cert)
    assert len(resolvents) == 1
    claim = resolvents[0]["claim"]
    assert isinstance(claim, dict)
    args = claim["args"]
    assert isinstance(args, list)
    assert isinstance(args[1], dict)
    assert isinstance(args[1].get("ref"), str)
    assert args[1]["ref"].startswith("poly.depressed_monic.")


def test_deg4_pipeline_reuses_same_pair_sums_resolvent_for_ferrari() -> None:
    result = analyze([1, 0, 0, 5, 5], explain=False)
    cert: Certificate = result.certificate

    verification = verify(cert)
    assert verification.verified, [c for c in verification.checks if not c.ok]

    resolvents = _resolvent_facts(cert)
    assert len(resolvents) == 1
    resolvent_fact_id = resolvents[0]["id"]

    ferrari_facts = [
        fact
        for fact in _facts(cert)
        if fact.get("rule") == "radical_roots.QQ.deg4.ferrari.depressed_monic@2"
    ]
    assert len(ferrari_facts) == 1
    premises = ferrari_facts[0].get("premises")
    assert isinstance(premises, list)
    assert resolvent_fact_id in premises


def test_deg4_pipeline_classifies_v4_before_discriminant_with_v3_rule() -> None:
    result = analyze([1, 0, 0, 36, 63], explain=False)
    cert: Certificate = result.certificate

    verification = verify(cert)
    assert verification.verified, [c for c in verification.checks if not c.ok]

    rules = _rules(cert)
    assert "galois_group.QQ.deg4.V4@3" in rules
    assert "galois_group.QQ.deg4.V4@2" not in rules
    assert "galois_group.QQ.lift.depressed_monic@1" not in rules
    assert not (LEGACY_DEG4_RULES & set(rules))
    assert "disc.square.QQ.lift@1" not in rules
    assert "disc.nonsquare.QQ.lift@1" not in rules

    v4_fact = next(fact for fact in _facts(cert) if fact.get("rule") == "galois_group.QQ.deg4.V4@3")
    premises = v4_fact.get("premises")
    assert isinstance(premises, list)
    premise_facts = [fact for fact in _facts(cert) if fact.get("id") in premises]
    factor_degree_premises = []
    for fact in premise_facts:
        claim = fact.get("claim", {})
        if not isinstance(claim, dict) or claim.get("pred") != "Degree":
            continue
        args = claim.get("args")
        if not isinstance(args, list) or len(args) != 2:
            continue
        obj_ref = args[1].get("ref") if isinstance(args[1], dict) else None
        if obj_ref == "int.1":
            factor_degree_premises.append(fact)
    assert len(factor_degree_premises) == 3
