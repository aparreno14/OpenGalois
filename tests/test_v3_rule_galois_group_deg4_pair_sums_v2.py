from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from opengalois.rulesets import get_ruleset
from opengalois.verify import RULE_CHECKERS, verify_certificate

Certificate = dict[str, Any]
Fact = dict[str, Any]

RULESET_ID = "le5-core@1"
RULE_IDS = [
    "galois_group.QQ.deg4.S4@2",
    "galois_group.QQ.deg4.A4@2",
    "galois_group.QQ.deg4.V4@2",
    "galois_group.QQ.deg4.V4@3",
    "galois_group.QQ.deg4.C4@2",
    "galois_group.QQ.deg4.D4.w1@2",
    "galois_group.QQ.deg4.D4.w2@2",
]


def _load_fixture(kind: str, name: str) -> Certificate:
    path = Path("fixtures") / "v3" / RULESET_ID / kind / name
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _facts(cert: Certificate) -> list[Fact]:
    proof = cert.get("proof")
    assert isinstance(proof, dict)
    facts = proof.get("facts")
    assert isinstance(facts, list)
    return facts


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_deg4_pair_sums_v2_rules_are_allowed_and_implemented(rule_id: str) -> None:
    ruleset = get_ruleset(RULESET_ID)
    assert rule_id in ruleset.allowed_rules
    assert rule_id in RULE_CHECKERS


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_deg4_pair_sums_v2_ok_fixture_verifies(rule_id: str) -> None:
    cert = _load_fixture("ok", f"{rule_id}_001.json")
    result = verify_certificate(cert)
    assert result.verified, [c for c in result.checks if not c.ok]


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_deg4_pair_sums_v2_bad_fixture_rejects(rule_id: str) -> None:
    cert = _load_fixture("bad", f"{rule_id}_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_deg4_pair_sums_v2_rejects_pair_products_family(rule_id: str) -> None:
    """A global certificate with the pair-products family must be rejected.

    The exact failing check is intentionally not asserted here.  Once the
    ResolventQQ premise itself is corrupted, the verifier may reject before the
    final Galois-group rule reaches its own family check.
    """
    cert = _load_fixture("ok", f"{rule_id}_001.json")
    objects = cert.get("objects")
    assert isinstance(objects, dict)
    objects["mpoly.bad.pair_products"] = {
        "kind": "MPolyQQ",
        "nvars": 4,
        "terms": [
            {"exp": [1, 1, 0, 0], "coeff_qq": "1"},
            {"exp": [0, 0, 1, 1], "coeff_qq": "1"},
        ],
    }

    for fact in _facts(cert):
        if fact.get("rule") != rule_id:
            continue
        premises = fact.get("premises")
        assert isinstance(premises, list)
        for prem_id in premises:
            prem = next(x for x in _facts(cert) if x.get("id") == prem_id)
            claim = prem.get("claim")
            assert isinstance(claim, dict)
            if claim.get("pred") != "ResolventQQ":
                continue
            args = claim.get("args")
            assert isinstance(args, list)
            args[2] = {"ref": "mpoly.bad.pair_products"}
            break
        break

    result = verify_certificate(cert)
    assert not result.verified


def test_deg4_v4_v3_requires_degree_premises_for_all_linear_factors() -> None:
    cert = _load_fixture("ok", "galois_group.QQ.deg4.V4@3_001.json")
    for fact in _facts(cert):
        if fact.get("rule") == "galois_group.QQ.deg4.V4@3":
            premises = fact.get("premises")
            assert isinstance(premises, list)
            premises.pop()
            break
    result = verify_certificate(cert)
    assert not result.verified
