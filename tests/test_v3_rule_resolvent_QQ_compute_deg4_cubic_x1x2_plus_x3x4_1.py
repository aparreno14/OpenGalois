from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from opengalois.verify import verify_certificate

RULE_ID = "resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _load(relpath: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((REPO_ROOT / relpath).read_text(encoding="utf-8")))


def test_resolvent_QQ_compute_deg4_cubic_x1x2_plus_x3x4_1_ok() -> None:
    cert = _load("fixtures/v3/le5-core@1/ok/resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1_001.json")
    res = verify_certificate(cert)
    assert res.verified, res


def test_resolvent_QQ_compute_deg4_cubic_x1x2_plus_x3x4_1_bad() -> None:
    cert = _load("fixtures/v3/le5-core@1/bad/resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1_fail_001.json")
    res = verify_certificate(cert)
    assert not res.verified
    assert any((not c.ok) and ("E_MISMATCH" in c.details) for c in res.checks)
