from __future__ import annotations

from typing import Any

from opengalois import analyze, verify

Certificate = dict[str, Any]


def _has_rule(cert: Certificate, rule_id: str) -> bool:
    facts = cert.get("proof", {}).get("facts", [])
    assert isinstance(facts, list)
    return any(isinstance(node, dict) and node.get("rule") == rule_id for node in facts)


def test_analyze_quartic_depressed_general_emits_ferrari_v2_without_lift_and_verifies() -> None:
    """A monic depressed quartic uses Ferrari directly on $input.

    After identity normalization, the procedure emits DepressedMonicEq($input,$input)
    and no longer needs radical_roots.QQ.lift.depressed_monic@1.
    """
    result = analyze([1, 0, 0, 1, 1], explain=False)
    cert: Certificate = result.certificate

    assert _has_rule(cert, "resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1")
    assert _has_rule(cert, "radical_roots.QQ.deg4.ferrari.depressed_monic@2")
    assert not _has_rule(cert, "radical_roots.QQ.lift.depressed_monic@1")
    assert verify(cert).verified


def test_analyze_quartic_nondepressed_general_emits_ferrari_v2_and_lift_and_verifies() -> None:
    """A non-depressed irreducible quartic still lifts Ferrari roots back to $input."""
    result = analyze([1, 1, 1, 1, 1], explain=False)
    cert: Certificate = result.certificate

    assert _has_rule(cert, "resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1")
    assert _has_rule(cert, "radical_roots.QQ.deg4.ferrari.depressed_monic@2")
    assert _has_rule(cert, "radical_roots.QQ.lift.depressed_monic@1")
    assert verify(cert).verified


def test_analyze_quartic_biquadratic_branch_emits_ferrari_v2_and_verifies() -> None:
    result = analyze([1, 0, 2, 0, 2], explain=False)
    cert: Certificate = result.certificate

    assert _has_rule(cert, "radical_roots.QQ.deg4.ferrari.depressed_monic@2")
    assert verify(cert).verified
