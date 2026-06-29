import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from opengalois import analyze


def test_analyze_certificate_validates_against_schema_v2_0_0():
    """Analyze output validates against schema v2.0.0."""
    cert = analyze([1, 0, 0, 0, -1, -1], explain=False).certificate

    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "certificate" / "2.0.0.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(cert), key=lambda e: e.path)

    if errors:
        e0 = errors[0]
        path = "$" + "".join(f"[{p!r}]" if isinstance(p, str) else f"[{p}]" for p in e0.path)
        pytest.fail(f"Schema validation failed at {path}: {e0.message}")
