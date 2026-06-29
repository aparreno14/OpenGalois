from __future__ import annotations

import pytest

from opengalois import analyze, verify

LEGACY_DEG4_RULES = {
    "galois_group.QQ.deg4.S4@1",
    "galois_group.QQ.deg4.A4@1",
    "galois_group.QQ.deg4.V4@1",
    "galois_group.QQ.deg4.C4@1",
    "galois_group.QQ.deg4.D4.w1@1",
    "galois_group.QQ.deg4.D4.w2@1",
}


@pytest.mark.parametrize(
    ("coeffs", "expected_order", "expected_index", "expected_group"),
    [
        ([1, 0, 0, -1, -1], 24, 12, "S4"),
        ([1, 0, 0, 8, 12], 12, 3, "A4"),
        ([1, 0, 0, 36, 63], 4, 2, "V4"),
        ([1, 0, 0, 5, 5], 4, 1, "C4"),
        ([1, 0, 0, 3, 3], 8, 3, "D4"),
    ],
)
def test_deg4_pair_sums_v2_preserves_group_classification(
    coeffs: list[int],
    expected_order: int,
    expected_index: int,
    expected_group: str,
) -> None:
    result = analyze(coeffs, explain=False)
    cert = result.certificate
    verification = verify(cert)

    assert verification.verified, [c for c in verification.checks if not c.ok]
    assert cert["summary"]["galois_group"] == expected_group

    final_group = None
    for fact in reversed(cert["proof"]["facts"]):
        claim = fact.get("claim", {})
        if claim.get("pred") == "GaloisGroup" and claim["args"][0]["ref"] == "$input":
            final_group = cert["objects"][claim["args"][1]["ref"]]
            break

    assert final_group is not None
    assert final_group["system"] == "smallgroup"
    assert final_group["order"] == expected_order
    assert final_group["index"] == expected_index

    rules = [fact["rule"] for fact in cert["proof"]["facts"]]
    assert "galois_group.QQ.lift.depressed_monic@1" not in rules
    assert not (set(rules) & LEGACY_DEG4_RULES)
    assert any(
        rule.startswith("galois_group.QQ.deg4.") and (rule.endswith("@2") or rule.endswith("@3"))
        for rule in rules
    )
