from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from opengalois import analyze, verify

Certificate = dict[str, Any]
Fact = dict[str, Any]
ObjectMap = dict[str, Any]

"""
Integration tests for the irreducible quartic pipeline.

The legacy degree-4 pipeline classified the input quartic directly with the
pair-products resolvent and emitted a final ``galois_group.QQ.deg4.*@1`` rule.
The pair-sums pipeline classifies the depressed monic working quartic with
``galois_group.QQ.deg4.*@2``/``@3`` rules. If the input is already monic and
depressed, that working quartic is the input itself and no lift fact is emitted;
otherwise the certified group is lifted back to the original input with
``galois_group.QQ.lift.depressed_monic@1``.

These tests therefore preserve the Conrad regression set, but check the current
proof shape rather than the old final-rule shape.
"""


@dataclass(frozen=True)
class QuarticCase:
    """Test fixture describing one irreducible quartic classification case."""

    label: str
    coeffs: list[int]
    expected_group: str
    expected_order: int
    expected_index: int
    expected_rule: str | tuple[str, ...]
    source: str


S4_1 = "galois_group.QQ.deg4.S4@1"
A4_1 = "galois_group.QQ.deg4.A4@1"
V4_1 = "galois_group.QQ.deg4.V4@1"
C4_1 = "galois_group.QQ.deg4.C4@1"
D4_1 = ("galois_group.QQ.deg4.D4.w1@1", "galois_group.QQ.deg4.D4.w2@1")

QUARTIC_CASES: list[QuarticCase] = [
    QuarticCase("x^4 - x - 1", [1, 0, 0, -1, -1], "S4", 24, 12, S4_1, "Example 3.2"),
    QuarticCase("x^4 + 2x + 2", [1, 0, 0, 2, 2], "S4", 24, 12, S4_1, "Table 5"),
    QuarticCase(
        "x^4 + 8x + 12",
        [1, 0, 0, 8, 12],
        "A4",
        12,
        3,
        A4_1,
        "Example 3.3 / Table 5",
    ),
    QuarticCase(
        "x^4 + 24x + 36",
        [1, 0, 0, 24, 36],
        "A4",
        12,
        3,
        A4_1,
        "Remark 4.4 exercise",
    ),
    QuarticCase(
        "x^4 + 36x + 63",
        [1, 0, 0, 36, 63],
        "V4",
        4,
        2,
        V4_1,
        "Table 5 / Table 9",
    ),
    QuarticCase(
        "x^4 + 24x + 73",
        [1, 0, 0, 24, 73],
        "V4",
        4,
        2,
        V4_1,
        "Remark 4.4 exercise",
    ),
    QuarticCase("x^4 + 4x^2 + 1", [1, 0, 4, 0, 1], "V4", 4, 2, V4_1, "Table 10"),
    QuarticCase(
        "x^4 - 4x^2 + 1",
        [1, 0, -4, 0, 1],
        "V4",
        4,
        2,
        V4_1,
        "Example 4.9",
    ),
    QuarticCase(
        "x^4 + 5x + 5",
        [1, 0, 0, 5, 5],
        "C4",
        4,
        1,
        C4_1,
        "Table 9 / Appendix A.2",
    ),
    QuarticCase("x^4 + 8x + 14", [1, 0, 0, 8, 14], "C4", 4, 1, C4_1, "Table 9"),
    QuarticCase("x^4 + 13x + 39", [1, 0, 0, 13, 39], "C4", 4, 1, C4_1, "Table 9"),
    QuarticCase(
        "x^4 - 4x^2 + 2",
        [1, 0, -4, 0, 2],
        "C4",
        4,
        1,
        C4_1,
        "Table 10 / Example 4.8",
    ),
    QuarticCase("x^4 - 5x^2 + 5", [1, 0, -5, 0, 5], "C4", 4, 1, C4_1, "Table 10"),
    QuarticCase(
        "x^4 + 3x + 3",
        [1, 0, 0, 3, 3],
        "D4",
        8,
        3,
        D4_1,
        "Table 9 / Appendix A.2",
    ),
    QuarticCase(
        "x^4 + 4x^2 - 2",
        [1, 0, 4, 0, -2],
        "D4",
        8,
        3,
        D4_1,
        "Example 3.10 / Table 10",
    ),
    QuarticCase("x^4 + 5x^2 + 2", [1, 0, 5, 0, 2], "D4", 8, 3, D4_1, "Table 10"),
    QuarticCase("x^4 - 5x^2 + 3", [1, 0, -5, 0, 3], "D4", 8, 3, D4_1, "Table 10"),
    QuarticCase(
        "x^4 - 2x^2 - 1",
        [1, 0, -2, 0, -1],
        "D4",
        8,
        3,
        D4_1,
        "Example 4.10",
    ),
]

REDUCIBLE_GUARD_CASES: list[tuple[str, list[int], str]] = [
    ("x^4 + 4", [1, 0, 0, 0, 4], "Remark 4.4"),
    ("x^4 + 3x + 20", [1, 0, 0, 3, 20], "Remark 4.4"),
]

LEGACY_DEG4_RULES = {
    "galois_group.QQ.deg4.S4@1",
    "galois_group.QQ.deg4.A4@1",
    "galois_group.QQ.deg4.V4@1",
    "galois_group.QQ.deg4.C4@1",
    "galois_group.QQ.deg4.D4.w1@1",
    "galois_group.QQ.deg4.D4.w2@1",
}

V2_RULES = {
    "galois_group.QQ.deg4.S4@2",
    "galois_group.QQ.deg4.A4@2",
    "galois_group.QQ.deg4.V4@2",
    "galois_group.QQ.deg4.C4@2",
    "galois_group.QQ.deg4.D4.w1@2",
    "galois_group.QQ.deg4.D4.w2@2",
}

V3_RULES = {
    "galois_group.QQ.deg4.V4@3",
}

LEGACY_TO_V2 = {
    "galois_group.QQ.deg4.S4@1": {"galois_group.QQ.deg4.S4@2"},
    "galois_group.QQ.deg4.A4@1": {"galois_group.QQ.deg4.A4@2"},
    "galois_group.QQ.deg4.V4@1": {"galois_group.QQ.deg4.V4@3"},
    "galois_group.QQ.deg4.C4@1": {"galois_group.QQ.deg4.C4@2"},
    "galois_group.QQ.deg4.D4.w1@1": {"galois_group.QQ.deg4.D4.w1@2"},
    "galois_group.QQ.deg4.D4.w2@1": {"galois_group.QQ.deg4.D4.w2@2"},
}

PAIR_SUMS_RESOLVENT_RULE = "resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1"
PAIR_SUMS_MPOLY_REF = "mpoly.resolvent.deg4.cubic_x1plusx2_times_x3plusx4"
GROUP_LIFT_RULE = "galois_group.QQ.lift.depressed_monic@1"


def _proof_facts(cert: Certificate) -> list[Fact]:
    proof = cert.get("proof", {})
    assert isinstance(proof, dict), "certificate.proof must be a dict"
    facts = proof.get("facts", [])
    assert isinstance(facts, list), "certificate.proof.facts must be a list"
    return facts


def _objects(cert: Certificate) -> ObjectMap:
    objs = cert.get("objects", {})
    assert isinstance(objs, dict), "certificate.objects must be a dict"
    return objs


def _get_ref(arg: Any) -> str | None:
    if isinstance(arg, dict):
        ref = arg.get("ref")
        if isinstance(ref, str):
            return ref
    return None


def _find_galois_facts_for_ref(cert: Certificate, poly_ref: str) -> list[Fact]:
    out: list[Fact] = []
    for fact in _proof_facts(cert):
        claim = fact.get("claim", {})
        if not isinstance(claim, dict) or claim.get("pred") != "GaloisGroup":
            continue
        args = claim.get("args")
        if not isinstance(args, list) or len(args) != 2:
            continue
        if _get_ref(args[0]) == poly_ref:
            out.append(fact)
    return out


def _find_input_galois_facts(cert: Certificate) -> list[Fact]:
    return _find_galois_facts_for_ref(cert, "$input")


def _final_input_galois_fact(cert: Certificate) -> Fact:
    facts = _find_input_galois_facts(cert)
    assert facts, "no GaloisGroup fact emitted for $input"
    return facts[-1]


def _decode_group_signature(cert: Certificate, fact: Fact) -> tuple[int, int, str | None]:
    claim = fact["claim"]
    assert isinstance(claim, dict)
    args = claim["args"]
    assert isinstance(args, list)
    group_ref = _get_ref(args[1])
    assert group_ref is not None, "missing group object ref"
    obj = _objects(cert)[group_ref]
    assert isinstance(obj, dict)
    assert obj["kind"] == "GroupId"
    order = obj["order"]
    index = obj["index"]
    alias = obj.get("alias")
    assert isinstance(order, int)
    assert isinstance(index, int)
    assert alias is None or isinstance(alias, str)
    return order, index, alias


def _fact_preds(cert: Certificate) -> list[str]:
    preds: list[str] = []
    for fact in _proof_facts(cert):
        claim = fact.get("claim", {})
        if not isinstance(claim, dict):
            continue
        pred = claim.get("pred")
        if isinstance(pred, str):
            preds.append(pred)
    return preds


def _find_facts_by_pred(cert: Certificate, pred: str) -> list[Fact]:
    out: list[Fact] = []
    for fact in _proof_facts(cert):
        claim = fact.get("claim", {})
        if isinstance(claim, dict) and claim.get("pred") == pred:
            out.append(fact)
    return out


def _rules_used(cert: Certificate) -> set[str]:
    return {
        str(fact.get("rule"))
        for fact in _proof_facts(cert)
        if isinstance(fact.get("rule"), str)
    }


def _rules_used_for_input(cert: Certificate) -> set[str]:
    return {
        str(fact.get("rule"))
        for fact in _find_input_galois_facts(cert)
        if isinstance(fact.get("rule"), str)
    }


def _expected_v2_rules(expected: str | tuple[str, ...]) -> set[str]:
    if isinstance(expected, str):
        return set(LEGACY_TO_V2[expected])
    out: set[str] = set()
    for rule in expected:
        out.update(LEGACY_TO_V2[rule])
    return out


def _depressed_poly_ref(cert: Certificate) -> str:
    for fact in _proof_facts(cert):
        if fact.get("rule") != "normalize.depressed_monic_QQ@1":
            continue
        claim = fact.get("claim", {})
        if not isinstance(claim, dict) or claim.get("pred") != "DepressedMonicEq":
            continue
        args = claim.get("args", [])
        if not isinstance(args, list) or len(args) != 2:
            continue
        ref = _get_ref(args[1])
        assert ref is not None
        return ref
    raise AssertionError("missing DepressedMonicEq normalization fact")


def _assert_new_classification_shape(cert: Certificate, case: QuarticCase) -> None:
    final_fact = _final_input_galois_fact(cert)
    final_rule = final_fact.get("rule")
    assert isinstance(final_rule, str)

    g_ref = _depressed_poly_ref(cert)
    g_facts = _find_galois_facts_for_ref(cert, g_ref)
    assert g_facts, "missing GaloisGroup(g,G) classification fact"

    g_rules = {str(fact.get("rule")) for fact in g_facts if isinstance(fact.get("rule"), str)}
    expected_v2 = _expected_v2_rules(case.expected_rule)
    assert g_rules & expected_v2, (
        f"{case.label}: expected depressed-monic classification rule in "
        f"{sorted(expected_v2)}, got {sorted(g_rules)}"
    )

    if g_ref == "$input":
        assert final_rule in expected_v2, (
            f"{case.label}: already-depressed input should be classified directly; "
            f"expected one of {sorted(expected_v2)}, got {final_rule!r}"
        )
        assert GROUP_LIFT_RULE not in _rules_used(cert)
    else:
        assert final_rule == GROUP_LIFT_RULE

    used = _rules_used(cert)
    assert LEGACY_DEG4_RULES.isdisjoint(used), (
        f"{case.label}: legacy degree-4 rules must not be emitted by the pair-sums "
        f"pipeline; found {sorted(LEGACY_DEG4_RULES & used)}"
    )

    resolvents = _find_facts_by_pred(cert, "ResolventQQ")
    assert len(resolvents) == 1
    resolvent = resolvents[0]
    assert resolvent.get("rule") == PAIR_SUMS_RESOLVENT_RULE
    claim = resolvent.get("claim")
    assert isinstance(claim, dict)
    args = claim.get("args")
    assert isinstance(args, list) and len(args) == 3
    assert _get_ref(args[1]) == g_ref
    assert _get_ref(args[2]) == PAIR_SUMS_MPOLY_REF


def _assert_expected_branch_artifacts(cert: Certificate, case: QuarticCase) -> None:
    preds = _fact_preds(cert)

    if case.expected_group != "V4":
        assert "Discriminant" in preds
    assert "ResolventQQ" in preds
    assert "DepressedMonicEq" in preds

    if case.expected_group in {"S4", "A4"}:
        irred_facts = _find_facts_by_pred(cert, "IrreducibleQQ")
        assert len(irred_facts) >= 2, (
            f"{case.label}: expected IrreducibleQQ for both the quartic and its cubic resolvent"
        )

    if case.expected_group == "V4":
        assert "FactorizationMonicQQ" in preds
        assert "DiscSquareQQ" not in preds
        assert "DiscNonSquareQQ" not in preds

    if case.expected_group == "C4":
        assert "FactorizationMonicQQ" in preds
        square_facts = _find_facts_by_pred(cert, "IsSquareQQ")
        assert len(square_facts) >= 2, (
            f"{case.label}: expected two IsSquareQQ facts for the Kappe-Warren auxiliary values"
        )

    if case.expected_group == "D4":
        assert "FactorizationMonicQQ" in preds
        nonsquare_facts = _find_facts_by_pred(cert, "NonSquareQQ")
        assert len(nonsquare_facts) >= 2, (
            f"{case.label}: expected NonSquareQQ facts for the quartic discriminant "
            "and at least one Kappe-Warren auxiliary value"
        )


@pytest.mark.parametrize(
    "case",
    QUARTIC_CASES,
    ids=[f"{case.label} [{case.source}]" for case in QUARTIC_CASES],
)
def test_irreducible_quartic_pipeline_classifies_all_conrad_examples(case: QuarticCase) -> None:
    result = analyze(case.coeffs, explain=False)
    cert: Certificate = result.certificate

    verified = verify(cert)
    assert verified.verified, f"{case.label}: generated certificate did not verify"

    final_fact = _final_input_galois_fact(cert)
    order, index, alias = _decode_group_signature(cert, final_fact)
    assert (order, index) == (case.expected_order, case.expected_index), (
        f"{case.label}: expected group signature {(case.expected_order, case.expected_index)}, "
        f"got {(order, index)}"
    )

    if alias is not None:
        assert alias == case.expected_group, (
            f"{case.label}: expected group alias {case.expected_group!r}, got {alias!r}"
        )

    _assert_new_classification_shape(cert, case)
    _assert_expected_branch_artifacts(cert, case)


@pytest.mark.parametrize(
    ("label", "coeffs", "source"),
    REDUCIBLE_GUARD_CASES,
    ids=[f"{label} [{source}]" for label, _, source in REDUCIBLE_GUARD_CASES],
)
def test_reducible_conrad_warning_examples_do_not_trigger_irreducible_quartic_classification(
    label: str,
    coeffs: list[int],
    source: str,
) -> None:
    result = analyze(coeffs, explain=False)
    cert: Certificate = result.certificate

    input_group_facts = _find_input_galois_facts(cert)
    if not input_group_facts:
        return

    forbidden = LEGACY_DEG4_RULES | V2_RULES | V3_RULES
    used = _rules_used_for_input(cert)
    assert forbidden.isdisjoint(used), (
        f"{label} ({source}) is reducible in Conrad's paper and must not be classified by "
        f"the irreducible quartic pipeline; found rules {sorted(used & forbidden)}"
    )
