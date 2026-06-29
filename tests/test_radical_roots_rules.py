from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

from opengalois.verify import (
    _cardano_root_payloads_for_depressed_cubic,
    _quartic_root_payloads_ferrari_depressed,
    _quartic_root_payloads_resolvent_symmetric_depressed,
    verify_certificate,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_json(relpath: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((ROOT / relpath).read_text(encoding="utf-8")))


def _details_for_rule(result, rule_id: str) -> str:
    for check in result.checks:
        if check.name == f"v3.rule.{rule_id}":
            return str(check.details)
    raise AssertionError(f"missing rule check for {rule_id}")


def test_radical_roots_deg1_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg1.trivial@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_radical_roots_deg1_bad_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg1.trivial@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
    assert "E_MISMATCH" in _details_for_rule(result, "radical_roots.QQ.deg1.trivial@1")


def test_radical_roots_deg2_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg2.quadratic_formula@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_radical_roots_deg2_bad_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg2.quadratic_formula@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
    assert "E_MISMATCH" in _details_for_rule(result, "radical_roots.QQ.deg2.quadratic_formula@1")


def test_radical_roots_reducible_compose_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/radical_roots.QQ.reducible.compose@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_radical_roots_reducible_compose_bad_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/bad/radical_roots.QQ.reducible.compose@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
    assert "E_MISMATCH" in _details_for_rule(result, "radical_roots.QQ.reducible.compose@1")


def test_radical_roots_deg3_cardano_depressed_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg3.cardano.depressed_monic@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_radical_roots_deg3_cardano_depressed_bad_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg3.cardano.depressed_monic@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
    assert "E_MISMATCH" in _details_for_rule(result, "radical_roots.QQ.deg3.cardano.depressed_monic@1")


def test_radical_roots_lift_depressed_monic_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/radical_roots.QQ.lift.depressed_monic@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_radical_roots_lift_depressed_monic_bad_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/bad/radical_roots.QQ.lift.depressed_monic@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
    assert "E_MISMATCH" in _details_for_rule(result, "radical_roots.QQ.lift.depressed_monic@1")


def test_cardano_helper_collapses_zero_radicals() -> None:
    payloads = _cardano_root_payloads_for_depressed_cubic([Fraction(1, 1), Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)])
    assert payloads is not None
    root1 = payloads[0]["expr"]
    assert root1 == {"kind": "qq", "value_qq": "0"}


def test_resolvent_deg4_alt_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_resolvent_deg4_alt_bad_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/bad/resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
    assert "E_MISMATCH" in _details_for_rule(result, "resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1")


def test_radical_roots_deg4_ferrari_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg4.ferrari.depressed_monic@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_radical_roots_deg4_ferrari_biquadratic_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg4.ferrari.depressed_monic@1_002.json")
    result = verify_certificate(cert)
    assert result.verified


def test_radical_roots_deg4_ferrari_bad_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg4.ferrari.depressed_monic@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
    assert "E_MISMATCH" in _details_for_rule(result, "radical_roots.QQ.deg4.ferrari.depressed_monic@1")


def test_radical_roots_deg4_resolvent_symmetric_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_radical_roots_deg4_resolvent_symmetric_biquadratic_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1_002.json")
    result = verify_certificate(cert)
    assert result.verified


def test_radical_roots_deg4_resolvent_symmetric_bad_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/bad/radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
    assert "E_MISMATCH" in _details_for_rule(result, "radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1")



def test_quartic_d_zero_helpers_remain_defined_and_rule_distinct() -> None:
    poly = [Fraction(1, 1), Fraction(0, 1), Fraction(0, 1), Fraction(0, 1), Fraction(1, 1)]
    resolvent_roots = [
        {"kind": "RadicalExpr", "expr": {"kind": "qq", "value_qq": "0"}},
        {"kind": "RadicalExpr", "expr": {"kind": "qq", "value_qq": "2"}},
        {"kind": "RadicalExpr", "expr": {"kind": "qq", "value_qq": "-2"}},
    ]
    ferrari = _quartic_root_payloads_ferrari_depressed(poly, resolvent_roots)
    symmetric = _quartic_root_payloads_resolvent_symmetric_depressed(poly, resolvent_roots)
    assert ferrari is not None
    assert symmetric is not None
    assert len(ferrari) == 4
    assert len(symmetric) == 4
    assert ferrari != symmetric
