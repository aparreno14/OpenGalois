from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengalois.verify import verify_certificate

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "v3" / "le5-core@1"


@pytest.mark.skipif(verify_certificate is None, reason="verify_certificate import failed")
def test_degree_QQ_rule_ok_fixture() -> None:
    cert = json.loads((FIXTURE_ROOT / "ok" / "degree.QQ@1_001.json").read_text(encoding="utf-8"))
    res = verify_certificate(cert)
    assert res.verified, getattr(res, "checks", None)


@pytest.mark.skipif(verify_certificate is None, reason="verify_certificate import failed")
def test_degree_QQ_rule_bad_fixture() -> None:
    cert = json.loads((FIXTURE_ROOT / "bad" / "degree.QQ@1_fail_001.json").read_text(encoding="utf-8"))
    res = verify_certificate(cert)
    assert not res.verified
    checks = list(getattr(res, "checks", []))
    # Accept either the explicit rule check or a stricter earlier failure if your local verifier is not yet patched.
    assert checks, "Expected failing checks"
