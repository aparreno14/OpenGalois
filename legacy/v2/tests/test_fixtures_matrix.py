import json
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator

from opengalois import verify


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _schema_validator() -> Draft202012Validator:
    schema_path = _repo_root() / "schemas" / "certificate" / "2.0.0.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _fixtures_dir() -> Path:
    return _repo_root() / "examples" / "certificates" / "v2.0.0"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _schema_errors(validator: Draft202012Validator, cert: dict[str, Any]) -> list[str]:
    errors = sorted(validator.iter_errors(cert), key=lambda e: list(e.path))
    out: list[str] = []
    for e in errors[:5]:
        path = "$" + "".join(f"[{p!r}]" if isinstance(p, str) else f"[{p}]" for p in e.path)
        out.append(f"{path}: {e.message}")
    return out


def test_fixture_matrix_ok_tamper_invalid():
    """Enforce fixture policy.
    
    - ok-*.json: schema-valid AND verify-valid
    
    - tamper-*.json: schema-valid AND verify-invalid
    
    - invalid-*.json: schema-invalid (and therefore verify-invalid)
    """
    fx_dir = _fixtures_dir()
    validator = _schema_validator()

    ok_files = sorted(fx_dir.glob("ok-*.json"))
    tamper_files = sorted(fx_dir.glob("tamper-*.json"))
    invalid_files = sorted(fx_dir.glob("invalid-*.json"))

    assert ok_files, "Expected at least one ok-*.json fixture."
    assert tamper_files, "Expected at least one tamper-*.json fixture."
    assert invalid_files, "Expected at least one invalid-*.json fixture."

    # --- OK fixtures: must validate schema and verify() must accept.
    for p in ok_files:
        cert = _load(p)
        errs = _schema_errors(validator, cert)
        if errs:
            pytest.fail(f"{p.name}: expected schema-valid, got errors:\n" + "\n".join(errs))

        v = verify(cert)
        assert v.verified is True, f"{p.name}: expected verified=True"

    # --- TAMPER fixtures: must validate schema, but verify() must reject.
    for p in tamper_files:
        cert = _load(p)
        errs = _schema_errors(validator, cert)
        if errs:
            pytest.fail(f"{p.name}: expected schema-valid tamper, got errors:\n" + "\n".join(errs))

        v = verify(cert)
        assert v.verified is False, f"{p.name}: expected verified=False (tamper fixture)"

        # Defense-in-depth: ensure failure is not just schema.
        assert any(c.name == "schema.conformance" and c.ok is True for c in v.checks), (
            f"{p.name}: expected schema.conformance=True for tamper fixtures"
        )

    # --- INVALID fixtures: must fail schema validation.
    for p in invalid_files:
        cert = _load(p)
        errs = _schema_errors(validator, cert)
        assert errs, f"{p.name}: expected schema-invalid, but schema validated"

        v = verify(cert)
        assert v.verified is False, f"{p.name}: expected verified=False (invalid fixture)"
        assert any(c.name == "schema.conformance" and c.ok is False for c in v.checks), (
            f"{p.name}: expected schema.conformance=False for invalid fixtures"
        )
