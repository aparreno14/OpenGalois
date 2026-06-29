from __future__ import annotations

import json
from pathlib import Path

from tests_helpers import assert_schema_valid, load_schema_validator, schema_errors

from opengalois import verify


def test_fixture_policy_ok_invalid_and_optional_tamper():
    """Enforce fixture policy without requiring tamper fixtures to exist.

    Policy:
    - ok-*.json: schema-valid AND verify-valid
    - invalid-*.json: schema-invalid (verify must be False)
    - tamper-*.json: if present, schema-valid AND verify-invalid
    """
    root = Path(__file__).resolve().parents[1]
    fx_dir = root / "examples" / "certificates" / "v2.0.0"
    v = load_schema_validator()

    ok_files = sorted(fx_dir.glob("ok-*.json"))
    invalid_files = sorted(fx_dir.glob("invalid-*.json"))
    tamper_files = sorted(fx_dir.glob("tamper-*.json"))

    assert ok_files, "Expected at least one ok-*.json fixture."
    assert invalid_files, "Expected at least one invalid-*.json fixture."

    for p in ok_files:
        cert = json.loads(p.read_text(encoding="utf-8"))
        assert_schema_valid(v, cert)
        out = verify(cert)
        assert out.verified is True, f"{p.name}: expected verified=True"

    for p in invalid_files:
        cert = json.loads(p.read_text(encoding="utf-8"))
        errs = schema_errors(v, cert)
        assert errs, f"{p.name}: expected schema-invalid fixture, but schema validated"
        out = verify(cert)
        assert out.verified is False, f"{p.name}: expected verified=False (invalid fixture)"
        assert any(c.name == "schema.conformance" and c.ok is False for c in out.checks), (
            f"{p.name}: expected schema.conformance=False"
        )

    for p in tamper_files:
        cert = json.loads(p.read_text(encoding="utf-8"))
        assert_schema_valid(v, cert)
        out = verify(cert)
        assert out.verified is False, f"{p.name}: expected verified=False (tamper fixture)"
        assert any(c.name == "schema.conformance" and c.ok is True for c in out.checks), (
            f"{p.name}: expected schema.conformance=True for tamper fixtures"
        )
