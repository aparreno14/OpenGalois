from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois.verify import verify_certificate

ROOT = Path(__file__).resolve().parents[1]


def _load_json(relpath: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((ROOT / relpath).read_text(encoding="utf-8")))


def _details_for_rule(result, rule_id: str) -> str:
    for check in result.checks:
        if check.name == f"v3.rule.{rule_id}":
            return str(check.details)
    raise AssertionError(f"missing rule check for {rule_id}")


def test_solvable_by_radicals_rule_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/solvable_by_radicals.QQ.from_galois_group@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_solvable_by_radicals_rule_bad_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/bad/solvable_by_radicals.QQ.from_galois_group@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
    assert "E_GROUP_NOT_RESOLVABLE" in _details_for_rule(
        result,
        "solvable_by_radicals.QQ.from_galois_group@1",
    )


def test_nonsolvable_by_radicals_rule_ok_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/ok/nonsolvable_by_radicals.QQ.from_galois_group@1_001.json")
    result = verify_certificate(cert)
    assert result.verified


def test_nonsolvable_by_radicals_rule_bad_fixture() -> None:
    cert = _load_json("fixtures/v3/le5-core@1/bad/nonsolvable_by_radicals.QQ.from_galois_group@1_fail_001.json")
    result = verify_certificate(cert)
    assert not result.verified
    assert "E_GROUP_RESOLUBLE" in _details_for_rule(
        result,
        "nonsolvable_by_radicals.QQ.from_galois_group@1",
    )
