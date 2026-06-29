import json
from pathlib import Path
from typing import Any, cast

from opengalois import verify


def _load_fixture(name: str) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    path = root / "examples" / "certificates" / "v2.0.0" / name
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_verify_schema_conformance_fails_for_invalid_fixture():
    """Schema check should fail for invalid fixture payloads."""
    cert = _load_fixture("invalid-missing-proof-version.json")
    result = verify(cert)

    assert result.verified is False
    assert any(c.name == "schema.conformance" and c.ok is False for c in result.checks)
